#!/usr/bin/env python3
"""
WHIS Isolation Forest Anomaly Detection
CPU-friendly, offline-trained anomaly scoring for hosts and users
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Model configuration
MODEL_DIR = Path("ai-training/models/artifacts")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

class WhisAnomalyDetector:
    """Anomaly detector optimized for security operations"""
    
    def __init__(self, contamination=0.1, random_state=42):
        self.contamination = contamination
        self.random_state = random_state
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_names = {}
        
    def prepare_features(self, df: pd.DataFrame, table_type: str) -> pd.DataFrame:
        """Prepare features for anomaly detection"""
        
        feature_df = df.copy()
        
        if table_type == "auth_events":
            # Authentication-specific features
            features = [
                "hour_of_day", "is_weekend", "is_off_hours", 
                "fail_count_1h", "success_after_fail_15m", "is_admin"
            ]
            
            # Encode categorical features
            if "asset_class" in feature_df.columns:
                if "asset_class_encoder" not in self.encoders:
                    self.encoders["asset_class_encoder"] = LabelEncoder()
                    feature_df["asset_class_encoded"] = self.encoders["asset_class_encoder"].fit_transform(
                        feature_df["asset_class"]
                    )
                else:
                    feature_df["asset_class_encoded"] = self.encoders["asset_class_encoder"].transform(
                        feature_df["asset_class"]
                    )
                features.append("asset_class_encoded")
                
        elif table_type == "process_events":
            # Process-specific features  
            features = [
                "hour_of_day", "cmd_len", "cmd_entropy", 
                "has_encoded", "signed_parent", "rare_parent_child_7d"
            ]
            
        elif table_type == "admin_events":
            # Admin change features
            features = [
                "off_hours", "recent_4625s_actor_1h"
            ]
            
            # Encode method
            if "method_encoder" not in self.encoders:
                self.encoders["method_encoder"] = LabelEncoder()
                feature_df["method_encoded"] = self.encoders["method_encoder"].fit_transform(
                    feature_df["method"]
                )
            else:
                feature_df["method_encoded"] = self.encoders["method_encoder"].transform(
                    feature_df["method"]
                )
            features.append("method_encoded")
            
        # Convert boolean columns to int
        for col in features:
            if col in feature_df.columns and feature_df[col].dtype == 'bool':
                feature_df[col] = feature_df[col].astype(int)
        
        # Store feature names for later use
        self.feature_names[table_type] = features
        
        return feature_df[features]
    
    def train(self, auth_df: pd.DataFrame, process_df: pd.DataFrame, admin_df: pd.DataFrame):
        """Train anomaly detectors for each data type"""
        
        print("🧠 Training Isolation Forest models...")
        
        datasets = {
            "auth_events": auth_df,
            "process_events": process_df, 
            "admin_events": admin_df
        }
        
        results = {}
        
        for table_type, df in datasets.items():
            print(f"\n📊 Training {table_type} detector...")
            
            # Prepare features
            X = self.prepare_features(df, table_type)
            y = df["is_suspicious"] if "is_suspicious" in df.columns else None
            
            print(f"  Features: {list(X.columns)}")
            print(f"  Samples: {len(X)} ({X.isna().sum().sum()} nulls)")
            
            # Handle missing values
            X = X.fillna(X.mean())
            
            # Scale features
            self.scalers[table_type] = StandardScaler()
            X_scaled = self.scalers[table_type].fit_transform(X)
            
            # Train Isolation Forest
            self.models[table_type] = IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_jobs=-1,
                verbose=0
            )
            
            # Fit the model
            self.models[table_type].fit(X_scaled)
            
            # Evaluate if we have labels
            if y is not None:
                # Get anomaly predictions (-1 for anomaly, 1 for normal)
                y_pred_if = self.models[table_type].predict(X_scaled)
                y_pred_binary = (y_pred_if == -1).astype(int)  # Convert to 0/1
                
                # Get anomaly scores (lower = more anomalous)
                anomaly_scores = self.models[table_type].score_samples(X_scaled)
                
                # Convert to 0-1 scale (higher = more anomalous)  
                normalized_scores = 1 - (anomaly_scores - anomaly_scores.min()) / (
                    anomaly_scores.max() - anomaly_scores.min()
                )
                
                # Calculate metrics
                if len(np.unique(y)) > 1:  # Need both classes for AUC
                    auc_score = roc_auc_score(y, normalized_scores)
                    print(f"  AUC: {auc_score:.3f}")
                else:
                    auc_score = None
                    print("  AUC: N/A (single class)")
                
                # Classification report
                print("  Classification Report:")
                print(classification_report(
                    y, y_pred_binary, 
                    target_names=["Normal", "Suspicious"],
                    zero_division=0
                ))
                
                # Get classification metrics safely
                report_dict = classification_report(y, y_pred_binary, output_dict=True, zero_division=0)
                if "1" in report_dict:
                    precision = report_dict["1"]["precision"]
                    recall = report_dict["1"]["recall"]
                else:
                    precision = 0.0
                    recall = 0.0
                
                results[table_type] = {
                    "auc": auc_score,
                    "precision": precision,
                    "recall": recall,
                    "samples": len(X),
                    "features": list(X.columns)
                }
            else:
                results[table_type] = {"samples": len(X), "features": list(X.columns)}
        
        return results
    
    def predict_anomaly_score(self, X: pd.DataFrame, table_type: str) -> np.ndarray:
        """Get anomaly scores (0-1, higher = more suspicious)"""
        
        if table_type not in self.models:
            raise ValueError(f"No model trained for {table_type}")
        
        # Prepare features
        X_features = self.prepare_features(X, table_type)
        X_features = X_features.fillna(X_features.mean())
        
        # Scale
        X_scaled = self.scalers[table_type].transform(X_features)
        
        # Get raw scores
        raw_scores = self.models[table_type].score_samples(X_scaled)
        
        # Normalize to 0-1 (higher = more anomalous)
        normalized_scores = 1 - (raw_scores - raw_scores.min()) / (
            raw_scores.max() - raw_scores.min() + 1e-8
        )
        
        return normalized_scores
    
    def get_feature_importance(self, X: pd.DataFrame, table_type: str, top_n: int = 5) -> List[str]:
        """Get top contributing features for anomalies"""
        
        if table_type not in self.models:
            return []
        
        X_features = self.prepare_features(X, table_type)
        X_features = X_features.fillna(X_features.mean())
        
        # Simple feature importance based on variance
        feature_vars = X_features.var().sort_values(ascending=False)
        top_features = feature_vars.head(top_n).index.tolist()
        
        return top_features
    
    def save_model(self, model_name: str = "whis_anomaly_detector"):
        """Save trained models and artifacts"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = MODEL_DIR / f"{model_name}_{timestamp}"
        model_path.mkdir(exist_ok=True)
        
        # Save models
        joblib.dump(self.models, model_path / "models.joblib")
        joblib.dump(self.scalers, model_path / "scalers.joblib") 
        joblib.dump(self.encoders, model_path / "encoders.joblib")
        
        # Save metadata
        metadata = {
            "model_name": model_name,
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "contamination": self.contamination,
            "model_types": list(self.models.keys()),
            "feature_names": self.feature_names,
            "use_case": "Security anomaly detection",
            "intended_use": "Advisory scoring for SOAR decision graph",
            "limitations": [
                "Synthetic training data - validate on real events",
                "CPU-only inference suitable for real-time scoring", 
                "Scores should be used as advisory signals only"
            ]
        }
        
        with open(model_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"💾 Model saved: {model_path}")
        return model_path
        
    @classmethod
    def load_model(cls, model_path: str):
        """Load trained model from disk"""
        model_dir = Path(model_path)
        
        detector = cls()
        detector.models = joblib.load(model_dir / "models.joblib")
        detector.scalers = joblib.load(model_dir / "scalers.joblib")
        detector.encoders = joblib.load(model_dir / "encoders.joblib")
        
        with open(model_dir / "metadata.json", "r") as f:
            metadata = json.load(f)
        detector.feature_names = metadata["feature_names"]
        
        return detector

def main():
    print("="*60)
    print("🤖 WHIS Isolation Forest Training")
    print("="*60)
    
    # Load feature store data
    feature_store_dir = Path("ai-training/feature_store/tables")
    
    auth_df = pd.read_parquet(feature_store_dir / "auth_events.parquet")
    process_df = pd.read_parquet(feature_store_dir / "process_events.parquet")
    admin_df = pd.read_parquet(feature_store_dir / "admin_events.parquet")
    
    print(f"📊 Loaded data:")
    print(f"  Auth events: {len(auth_df)} rows")
    print(f"  Process events: {len(process_df)} rows") 
    print(f"  Admin events: {len(admin_df)} rows")
    
    # Train anomaly detector
    detector = WhisAnomalyDetector(contamination=0.15)
    results = detector.train(auth_df, process_df, admin_df)
    
    # Save model
    model_path = detector.save_model()
    
    print("\n" + "="*60)
    print("✅ ANOMALY DETECTION MODEL READY")
    print("="*60)
    
    for table_type, metrics in results.items():
        print(f"\n📈 {table_type.title()}:")
        if "auc" in metrics and metrics["auc"]:
            print(f"  AUC: {metrics['auc']:.3f}")
            print(f"  Precision: {metrics['precision']:.3f}")
            print(f"  Recall: {metrics['recall']:.3f}")
        print(f"  Features: {len(metrics['features'])}")
    
    print(f"\n🎯 Next steps:")
    print("  1. Wire anomaly scores into WHIS API")
    print("  2. Add /api/analyze/host/<host_id> endpoint")
    print("  3. Include scores in decision graph logic")
    print("  4. Monitor model drift over time")

if __name__ == "__main__":
    main()
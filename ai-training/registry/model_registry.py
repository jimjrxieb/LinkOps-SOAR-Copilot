#!/usr/bin/env python3
"""
📦 WHIS Model Registry
=====================
Centralized model and adapter versioning with rollback capabilities.
Makes it IMPOSSIBLE to lose track of what's trained on what.

Features:
- Adapter versioning with metadata
- Dataset lineage tracking
- Automated promotion workflows
- Rollback capabilities
- Integration with MLflow Model Registry
"""

import os
import json
import yaml
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import mlflow
import mlflow.pyfunc
from mlflow.tracking import MlflowClient


class WhisModelRegistry:
    """Model registry for WHIS adapters and configurations"""
    
    def __init__(self, registry_path: str = "ai-training/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        self.models_path = self.registry_path / "models"
        self.datasets_path = self.registry_path / "datasets" 
        self.metadata_path = self.registry_path / "metadata.json"
        
        self.models_path.mkdir(exist_ok=True)
        self.datasets_path.mkdir(exist_ok=True)
        
        # Initialize MLflow client
        self.client = MlflowClient()
        self._ensure_registered_model()
        
        # Load or create registry metadata
        self.metadata = self._load_metadata()
        
    def _ensure_registered_model(self):
        """Ensure WHIS model is registered in MLflow"""
        try:
            self.client.get_registered_model("whis-soar-copilot")
        except:
            # Create registered model if doesn't exist
            self.client.create_registered_model(
                "whis-soar-copilot",
                description="WHIS SOAR Copilot with LoRA adapters"
            )
            print("📝 Created registered model: whis-soar-copilot")
            
    def _load_metadata(self) -> Dict[str, Any]:
        """Load registry metadata"""
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        else:
            return {
                "adapters": {},
                "datasets": {},
                "deployments": {},
                "lineage": {},
                "created_at": datetime.now().isoformat()
            }
            
    def _save_metadata(self):
        """Save registry metadata"""
        self.metadata["updated_at"] = datetime.now().isoformat()
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
            
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
        
    def register_dataset(self, dataset_path: str, name: str, version: str, 
                        metadata: Optional[Dict] = None) -> str:
        """Register dataset with versioning"""
        print(f"📚 Registering dataset: {name} v{version}")
        
        dataset_file = Path(dataset_path)
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
        # Calculate dataset hash for integrity
        dataset_hash = self._calculate_file_hash(dataset_file)
        
        # Create versioned dataset directory
        dataset_dir = self.datasets_path / name / version
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy dataset to registry
        registry_dataset_path = dataset_dir / dataset_file.name
        shutil.copy2(dataset_file, registry_dataset_path)
        
        # Store metadata
        dataset_metadata = {
            "name": name,
            "version": version,
            "original_path": str(dataset_file),
            "registry_path": str(registry_dataset_path),
            "hash": dataset_hash,
            "size_bytes": dataset_file.stat().st_size,
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.metadata["datasets"][f"{name}:{version}"] = dataset_metadata
        self._save_metadata()
        
        # Log to MLflow
        with mlflow.start_run(run_name=f"dataset_registration_{name}_v{version}"):
            mlflow.log_artifact(str(registry_dataset_path), "datasets")
            mlflow.log_params({
                "dataset_name": name,
                "dataset_version": version,
                "dataset_hash": dataset_hash,
                "dataset_size": dataset_file.stat().st_size
            })
            
        print(f"✅ Dataset registered: {name}:{version} (hash: {dataset_hash[:8]})")
        return f"{name}:{version}"
        
    def register_adapter(self, adapter_path: str, name: str, version: str,
                        dataset_reference: str, eval_metrics: Optional[Dict] = None,
                        metadata: Optional[Dict] = None) -> str:
        """Register trained adapter with lineage"""
        print(f"🧠 Registering adapter: {name} v{version}")
        
        adapter_dir = Path(adapter_path)
        if not adapter_dir.exists():
            raise FileNotFoundError(f"Adapter not found: {adapter_path}")
            
        # Create versioned adapter directory  
        registry_adapter_dir = self.models_path / name / version
        registry_adapter_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy adapter files to registry
        shutil.copytree(adapter_dir, registry_adapter_dir, dirs_exist_ok=True)
        
        # Calculate adapter hash
        adapter_config_file = registry_adapter_dir / "adapter_config.json"
        adapter_hash = self._calculate_file_hash(adapter_config_file) if adapter_config_file.exists() else "unknown"
        
        # Store metadata
        adapter_metadata = {
            "name": name,
            "version": version,
            "original_path": str(adapter_dir),
            "registry_path": str(registry_adapter_dir),
            "dataset_reference": dataset_reference,
            "hash": adapter_hash,
            "eval_metrics": eval_metrics or {},
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "status": "registered"
        }
        
        self.metadata["adapters"][f"{name}:{version}"] = adapter_metadata
        
        # Track lineage
        self.metadata["lineage"][f"{name}:{version}"] = {
            "dataset": dataset_reference,
            "training_timestamp": metadata.get("training_timestamp") if metadata else None,
            "base_model": metadata.get("base_model") if metadata else None
        }
        
        self._save_metadata()
        
        # Register with MLflow Model Registry
        model_uri = f"file://{registry_adapter_dir}"
        try:
            model_version = self.client.create_model_version(
                "whis-soar-copilot",
                model_uri,
                run_id=None,  # Can link to training run if available
                description=f"LoRA adapter {name} v{version} trained on {dataset_reference}"
            )
            
            # Set tags for easier discovery
            self.client.set_model_version_tag(
                "whis-soar-copilot",
                model_version.version,
                "adapter_name", 
                name
            )
            self.client.set_model_version_tag(
                "whis-soar-copilot", 
                model_version.version,
                "adapter_version",
                version
            )
            self.client.set_model_version_tag(
                "whis-soar-copilot",
                model_version.version, 
                "dataset_reference",
                dataset_reference
            )
            
            adapter_metadata["mlflow_version"] = model_version.version
            self.metadata["adapters"][f"{name}:{version}"] = adapter_metadata
            self._save_metadata()
            
        except Exception as e:
            print(f"⚠️ Failed to register with MLflow: {e}")
            
        print(f"✅ Adapter registered: {name}:{version} (hash: {adapter_hash[:8]})")
        return f"{name}:{version}"
        
    def promote_adapter(self, adapter_reference: str, stage: str) -> bool:
        """Promote adapter to staging/production"""
        print(f"🚀 Promoting adapter {adapter_reference} to {stage}")
        
        if adapter_reference not in self.metadata["adapters"]:
            raise ValueError(f"Adapter not found: {adapter_reference}")
            
        adapter_info = self.metadata["adapters"][adapter_reference]
        
        # Check if adapter meets promotion criteria
        if not self._check_promotion_criteria(adapter_info, stage):
            print(f"❌ Adapter {adapter_reference} does not meet {stage} criteria")
            return False
            
        try:
            # Promote in MLflow Registry
            if "mlflow_version" in adapter_info:
                self.client.transition_model_version_stage(
                    "whis-soar-copilot",
                    adapter_info["mlflow_version"],
                    stage.title()  # MLflow expects "Staging", "Production", etc.
                )
                
            # Update local metadata
            adapter_info["status"] = stage.lower()
            adapter_info["promoted_at"] = datetime.now().isoformat()
            self.metadata["adapters"][adapter_reference] = adapter_info
            
            # Track deployment
            self.metadata["deployments"][stage] = {
                "adapter": adapter_reference,
                "deployed_at": datetime.now().isoformat(),
                "metrics": adapter_info["eval_metrics"]
            }
            
            self._save_metadata()
            
            print(f"✅ Adapter {adapter_reference} promoted to {stage}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to promote adapter: {e}")
            return False
            
    def _check_promotion_criteria(self, adapter_info: Dict, stage: str) -> bool:
        """Check if adapter meets promotion criteria"""
        metrics = adapter_info.get("eval_metrics", {})
        
        if stage == "staging":
            required_metrics = {
                "fine_tune_f1": 0.70,
                "ragas_faithfulness": 0.70,
                "security_tests_passed": True
            }
        elif stage == "production":
            required_metrics = {
                "fine_tune_f1": 0.75,
                "ragas_faithfulness": 0.75,
                "security_tests_passed": True,
                "p95_latency_ms": 3000  # Max latency
            }
        else:
            return True  # Unknown stage, allow
            
        for metric, threshold in required_metrics.items():
            if metric not in metrics:
                print(f"❌ Missing required metric: {metric}")
                return False
                
            if isinstance(threshold, bool):
                if metrics[metric] != threshold:
                    print(f"❌ {metric}: {metrics[metric]} (required: {threshold})")
                    return False
            elif isinstance(threshold, (int, float)):
                if metric.endswith("_ms"):  # Latency metrics (lower is better)
                    if metrics[metric] > threshold:
                        print(f"❌ {metric}: {metrics[metric]}ms > {threshold}ms")
                        return False
                else:  # Score metrics (higher is better)
                    if metrics[metric] < threshold:
                        print(f"❌ {metric}: {metrics[metric]} < {threshold}")
                        return False
                        
        return True
        
    def rollback_deployment(self, stage: str, target_version: Optional[str] = None) -> bool:
        """Rollback deployment to previous or specific version"""
        print(f"🔄 Rolling back {stage} deployment")
        
        if stage not in self.metadata["deployments"]:
            print(f"❌ No deployment found for stage: {stage}")
            return False
            
        current_deployment = self.metadata["deployments"][stage]
        current_adapter = current_deployment["adapter"]
        
        if target_version:
            target_adapter = target_version
        else:
            # Find previous version (simplified - would need more sophisticated logic)
            print(f"⚠️ Automatic rollback not implemented. Please specify target version.")
            return False
            
        if target_adapter not in self.metadata["adapters"]:
            print(f"❌ Target adapter not found: {target_adapter}")
            return False
            
        # Promote target adapter
        return self.promote_adapter(target_adapter, stage)
        
    def get_current_deployment(self, stage: str) -> Optional[Dict]:
        """Get currently deployed adapter for stage"""
        return self.metadata["deployments"].get(stage)
        
    def list_adapters(self, status: Optional[str] = None) -> List[Dict]:
        """List all registered adapters"""
        adapters = []
        for ref, info in self.metadata["adapters"].items():
            if status is None or info.get("status") == status:
                adapters.append(info)
        return sorted(adapters, key=lambda x: x["registered_at"], reverse=True)
        
    def list_datasets(self) -> List[Dict]:
        """List all registered datasets"""
        return list(self.metadata["datasets"].values())
        
    def get_adapter_lineage(self, adapter_reference: str) -> Optional[Dict]:
        """Get training lineage for adapter"""
        return self.metadata["lineage"].get(adapter_reference)
        
    def health_check(self) -> Dict[str, Any]:
        """Check registry health and return status"""
        health = {
            "registry_path": str(self.registry_path),
            "total_adapters": len(self.metadata["adapters"]),
            "total_datasets": len(self.metadata["datasets"]),
            "deployments": dict(self.metadata["deployments"]),
            "mlflow_connection": True,
            "last_updated": self.metadata.get("updated_at", "unknown")
        }
        
        try:
            # Test MLflow connection
            self.client.get_registered_model("whis-soar-copilot")
        except Exception as e:
            health["mlflow_connection"] = False
            health["mlflow_error"] = str(e)
            
        return health


def main():
    """CLI interface for model registry"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WHIS Model Registry")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Register dataset command
    dataset_parser = subparsers.add_parser("register-dataset", help="Register dataset")
    dataset_parser.add_argument("--path", required=True, help="Dataset file path")
    dataset_parser.add_argument("--name", required=True, help="Dataset name")
    dataset_parser.add_argument("--version", required=True, help="Dataset version")
    
    # Register adapter command
    adapter_parser = subparsers.add_parser("register-adapter", help="Register adapter")
    adapter_parser.add_argument("--path", required=True, help="Adapter directory path")
    adapter_parser.add_argument("--name", required=True, help="Adapter name")
    adapter_parser.add_argument("--version", required=True, help="Adapter version")
    adapter_parser.add_argument("--dataset", required=True, help="Dataset reference")
    
    # Promote command
    promote_parser = subparsers.add_parser("promote", help="Promote adapter")
    promote_parser.add_argument("--adapter", required=True, help="Adapter reference")
    promote_parser.add_argument("--stage", required=True, choices=["staging", "production"])
    
    # List commands
    subparsers.add_parser("list-adapters", help="List all adapters")
    subparsers.add_parser("list-datasets", help="List all datasets")
    subparsers.add_parser("health", help="Check registry health")
    
    args = parser.parse_args()
    
    registry = WhisModelRegistry()
    
    if args.command == "register-dataset":
        registry.register_dataset(args.path, args.name, args.version)
    elif args.command == "register-adapter":
        registry.register_adapter(args.path, args.name, args.version, args.dataset)
    elif args.command == "promote":
        registry.promote_adapter(args.adapter, args.stage)
    elif args.command == "list-adapters":
        adapters = registry.list_adapters()
        print(json.dumps(adapters, indent=2))
    elif args.command == "list-datasets":
        datasets = registry.list_datasets()
        print(json.dumps(datasets, indent=2))
    elif args.command == "health":
        health = registry.health_check()
        print(json.dumps(health, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
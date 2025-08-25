#!/usr/bin/env python3
"""
WHIS Feature Store - Create ML-ready datasets from threat intelligence
Builds redacted, sampled tables for safe ML experimentation
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import random
from typing import Dict, List, Any

# Feature store configuration
FEATURE_STORE_DIR = Path("ai-training/feature_store/tables")
FEATURE_STORE_DIR.mkdir(parents=True, exist_ok=True)

def hash_pii(value: str, salt: str = "whis_ml_salt") -> str:
    """Hash PII for privacy protection"""
    return hashlib.sha256(f"{value}_{salt}".encode()).hexdigest()[:16]

def generate_auth_events(n_samples: int = 1000) -> pd.DataFrame:
    """Generate synthetic authentication events based on threat patterns"""
    
    # Base data from our threat intelligence
    users = [f"user_{i:04d}" for i in range(1, 101)]
    hosts = [f"WS-{i:03d}" for i in range(1, 51)] + ["DC01", "DC02", "MAIL01", "WEB01"]
    source_ips = [
        "10.50.1.0/24",  # Internal
        "192.168.1.0/24",  # Internal  
        "203.0.113.0/24",  # External (suspicious)
        "198.51.100.0/24"  # External (legitimate)
    ]
    
    events = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(n_samples):
        timestamp = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        user = random.choice(users)
        host = random.choice(hosts)
        
        # Generate realistic patterns
        is_weekend = timestamp.weekday() >= 5
        is_off_hours = timestamp.hour < 7 or timestamp.hour > 19
        is_admin = "admin" in user or random.random() < 0.05
        
        # Simulate attack patterns from our threat intelligence
        is_suspicious = False
        event_code = "4624"  # Success
        
        # 15% failed attempts
        if random.random() < 0.15:
            event_code = "4625"  # Failed
            is_suspicious = True
            
        # Weekend/off-hours activity is more suspicious
        if (is_weekend or is_off_hours) and random.random() < 0.3:
            is_suspicious = True
            
        # Admin accounts are higher risk
        if is_admin and random.random() < 0.2:
            is_suspicious = True
            
        # Generate source IP based on suspicion
        if is_suspicious:
            src_ip = "203.0.113." + str(random.randint(1, 254))  # External suspicious
        else:
            src_ip = "10.50.1." + str(random.randint(1, 254))    # Internal
            
        events.append({
            "ts": timestamp,
            "user_hash": hash_pii(user),
            "src_ip_hash": hash_pii(src_ip),
            "host": host,
            "event_code": event_code,
            "is_success": event_code == "4624",
            "hour_of_day": timestamp.hour,
            "is_weekend": is_weekend,
            "is_off_hours": is_off_hours,
            "asset_class": "domain_controller" if "DC" in host else "workstation",
            "is_admin": is_admin,
            "is_suspicious": is_suspicious,  # Ground truth label
            "schema_ver": "1.0"
        })
    
    df = pd.DataFrame(events)
    
    # Add rolling window features (simulating real feature engineering)
    df = df.sort_values("ts").reset_index(drop=True)
    
    # Simple window features (avoiding complex rolling for now)
    df["fail_count_1h"] = df.groupby("user_hash")["is_success"].transform(
        lambda x: (~x).rolling(window=10, min_periods=1).sum()
    )
    
    df["success_after_fail_15m"] = df.groupby("user_hash")["is_success"].transform(
        lambda x: (x & (~x).shift(1, fill_value=False))
    )
    
    return df

def generate_process_events(n_samples: int = 800) -> pd.DataFrame:
    """Generate synthetic process events with threat patterns"""
    
    processes = [
        # Normal processes
        ("explorer.exe", "winlogon.exe", False, 0.1),
        ("chrome.exe", "explorer.exe", False, 0.2),
        ("notepad.exe", "explorer.exe", False, 0.1),
        ("outlook.exe", "explorer.exe", False, 0.15),
        # Suspicious processes (from our threat intel)
        ("powershell.exe", "winword.exe", True, 0.8),  # Document macro
        ("cmd.exe", "powershell.exe", True, 0.7),      # Command chaining
        ("rundll32.exe", "svchost.exe", True, 0.6),    # DLL sideloading
        ("regsvr32.exe", "cmd.exe", True, 0.9),        # Registry manipulation
    ]
    
    events = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(n_samples):
        timestamp = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        # Select process based on weights
        process_data = random.choices(
            processes, 
            weights=[p[3] for p in processes]
        )[0]
        
        child_proc, parent_proc, is_suspicious, _ = process_data
        
        # Generate command line
        if is_suspicious:
            cmd_lines = [
                "-EncodedCommand JABzAD0ATgBlAHcALQBPAGIAagBlAGMAdAA=",  # Encoded PS
                "/c whoami && net user",                                  # Recon
                "-windowstyle hidden -exec bypass",                      # Bypass
            ]
            cmd_line = random.choice(cmd_lines)
            cmd_entropy = random.uniform(4.5, 7.2)  # High entropy
        else:
            cmd_lines = [
                "",  # No args
                "/open document.docx", 
                "-url https://company.com"
            ]
            cmd_line = random.choice(cmd_lines)
            cmd_entropy = random.uniform(1.2, 3.8)  # Normal entropy
            
        events.append({
            "ts": timestamp,
            "host": f"WS-{random.randint(1, 50):03d}",
            "parent_proc": parent_proc,
            "child_proc": child_proc,
            "cmd_line_hash": hash_pii(cmd_line),
            "cmd_len": len(cmd_line),
            "cmd_entropy": cmd_entropy,
            "has_encoded": "encoded" in cmd_line.lower(),
            "signed_parent": not is_suspicious or random.random() < 0.3,
            "user_hash": hash_pii(f"user_{random.randint(1, 100):04d}"),
            "hour_of_day": timestamp.hour,
            "is_suspicious": is_suspicious,  # Ground truth
            "schema_ver": "1.0"
        })
    
    df = pd.DataFrame(events)
    
    # Add rare parent-child combinations
    parent_child_counts = df.groupby(["parent_proc", "child_proc"]).size()
    df["rare_parent_child_7d"] = df.apply(
        lambda row: parent_child_counts[(row["parent_proc"], row["child_proc"])] <= 2,
        axis=1
    )
    
    return df

def generate_admin_events(n_samples: int = 200) -> pd.DataFrame:
    """Generate admin privilege changes from threat patterns"""
    
    events = []
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(n_samples):
        timestamp = base_time + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        is_off_hours = timestamp.hour < 7 or timestamp.hour > 19
        
        # Simulate privilege escalation patterns
        is_suspicious = False
        if is_off_hours and random.random() < 0.4:
            is_suspicious = True
        if random.random() < 0.1:  # 10% base rate
            is_suspicious = True
            
        method = "GUI" if not is_suspicious else random.choice(["CLI", "API"])
        
        events.append({
            "ts": timestamp,
            "host": f"WS-{random.randint(1, 50):03d}",
            "actor_user_hash": hash_pii(f"user_{random.randint(1, 100):04d}"),
            "target_user_hash": hash_pii(f"user_{random.randint(1, 100):04d}"),
            "method": method,
            "off_hours": is_off_hours,
            "asset_class": random.choice(["workstation", "server"]),
            "is_suspicious": is_suspicious,  # Ground truth
            "schema_ver": "1.0"
        })
    
    df = pd.DataFrame(events)
    
    # Add recent failed auth context
    df["recent_4625s_actor_1h"] = np.random.poisson(0.5, len(df))
    
    return df

def save_feature_tables():
    """Save all feature tables with metadata"""
    
    print("🏗️ Creating WHIS Feature Store tables...")
    
    # Generate feature tables
    auth_df = generate_auth_events(1000)
    process_df = generate_process_events(800) 
    admin_df = generate_admin_events(200)
    
    # Save tables
    tables = {
        "auth_events": auth_df,
        "process_events": process_df,
        "admin_events": admin_df
    }
    
    for table_name, df in tables.items():
        
        # Save main table
        table_path = FEATURE_STORE_DIR / f"{table_name}.parquet"
        df.to_parquet(table_path, index=False)
        print(f"📊 Saved {table_name}: {len(df)} rows → {table_path}")
        
        # Save metadata
        metadata = {
            "table_name": table_name,
            "schema_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "row_count": len(df),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "suspicious_rate": df["is_suspicious"].mean() if "is_suspicious" in df.columns else 0.0,
            "time_range": {
                "start": df["ts"].min().isoformat(),
                "end": df["ts"].max().isoformat()
            },
            "privacy": {
                "pii_columns": ["user_hash", "src_ip_hash", "cmd_line_hash"],
                "hash_method": "SHA256 + salt",
                "retention_days": 90
            }
        }
        
        metadata_path = FEATURE_STORE_DIR / f"{table_name}.metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        print(f"📋 Saved metadata → {metadata_path}")
    
    # Create feature store catalog
    catalog = {
        "feature_store_version": "1.0",
        "created_at": datetime.now().isoformat(),
        "tables": list(tables.keys()),
        "total_rows": sum(len(df) for df in tables.values()),
        "use_cases": [
            "anomaly_detection",
            "incident_likelihood",
            "privilege_escalation_detection"
        ],
        "data_sources": [
            "synthetic_based_on_open_malsec_patterns",
            "threat_intelligence_derived"
        ]
    }
    
    catalog_path = FEATURE_STORE_DIR / "catalog.json"
    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=2, default=str)
    print(f"📚 Saved catalog → {catalog_path}")
    
    return tables

def main():
    print("="*60)
    print("🧪 WHIS AI Lab - Feature Store Creation")
    print("="*60)
    
    tables = save_feature_tables()
    
    print("\n" + "="*60)
    print("✅ FEATURE STORE READY")
    print("="*60)
    
    total_rows = sum(len(df) for df in tables.values())
    suspicious_events = sum(df["is_suspicious"].sum() for df in tables.values())
    
    print(f"📊 Total events: {total_rows:,}")
    print(f"🚨 Suspicious events: {suspicious_events} ({suspicious_events/total_rows:.1%})")
    print(f"📁 Location: {FEATURE_STORE_DIR}")
    
    print(f"\n🎯 Ready for ML experiments:")
    print("  • Isolation Forest (anomaly detection)")
    print("  • LogReg/LightGBM (incident classification)")
    print("  • Time series analysis (trend detection)")
    
    print(f"\n🔒 Privacy features:")
    print("  • PII hashed with salt")
    print("  • Synthetic data based on real threat patterns")
    print("  • 90-day retention policy")

if __name__ == "__main__":
    main()
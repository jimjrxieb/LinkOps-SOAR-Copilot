#!/usr/bin/env python3
"""
🔒 PII Detection and Redaction Pipeline
=====================================
Sanitizes training data to prevent model from memorizing sensitive information.
CRITICAL for GDPR/HIPAA compliance.

Security measures:
- Detects and redacts PII patterns
- Audit logging for compliance
- Safe fallbacks for unknown patterns
"""

import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import yaml

class PIIRedactor:
    """PII detection and redaction for training data"""
    
    def __init__(self, config_path: str = "configs/data_governance.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.patterns = self._compile_patterns()
        self.audit_log = []
        
    def _load_config(self) -> Dict[str, Any]:
        """Load data governance configuration"""
        if not self.config_path.exists():
            # Create default config if not exists
            default_config = {
                "pii_patterns": {
                    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    "ssn": r'\b\d{3}-?\d{2}-?\d{4}\b',
                    "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
                    "api_key": r'\b[A-Za-z0-9]{32,}\b',
                    "password_field": r'(?i)(password|pwd|pass)\s*[:=]\s*[^\s]+',
                    "token": r'(?i)(token|jwt|bearer)\s*[:=]\s*[A-Za-z0-9._-]+',
                    "secret": r'(?i)(secret|key)\s*[:=]\s*[A-Za-z0-9._-]+',
                    "username": r'(?i)(username|user|login)\s*[:=]\s*[A-Za-z0-9._-]+',
                    "aws_key": r'\bAKIA[0-9A-Z]{16}\b',
                    "private_key": r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----'
                },
                "redaction_policy": {
                    "method": "hash",  # hash, mask, or remove
                    "preserve_format": True,
                    "audit_enabled": True
                },
                "security": {
                    "strict_mode": True,
                    "unknown_pattern_action": "flag",  # flag, redact, or ignore
                    "min_redaction_length": 4
                }
            }
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, indent=2)
            
            return default_config
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for efficiency"""
        compiled = {}
        for pattern_name, pattern in self.config["pii_patterns"].items():
            try:
                compiled[pattern_name] = re.compile(pattern)
            except re.error as e:
                print(f"⚠️  Invalid regex for {pattern_name}: {e}")
                
        return compiled
        
    def _hash_sensitive_data(self, text: str) -> str:
        """Hash sensitive data while preserving format"""
        if self.config["redaction_policy"]["preserve_format"]:
            # Keep first and last character, hash middle
            if len(text) <= self.config["security"]["min_redaction_length"]:
                return "X" * len(text)
            
            prefix = text[0]
            suffix = text[-1]
            middle_hash = hashlib.sha256(text[1:-1].encode()).hexdigest()[:6]
            return f"{prefix}{middle_hash}{suffix}"
        else:
            return hashlib.sha256(text.encode()).hexdigest()[:8]
            
    def _mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data with X's"""
        if self.config["redaction_policy"]["preserve_format"]:
            return text[0] + "X" * (len(text) - 2) + text[-1] if len(text) > 2 else "X" * len(text)
        else:
            return "X" * len(text)
            
    def detect_and_redact(self, text: str, context: str = "unknown") -> Tuple[str, List[Dict]]:
        """Detect and redact PII in text"""
        redacted_text = text
        detections = []
        
        for pattern_name, pattern in self.patterns.items():
            matches = list(pattern.finditer(text))
            
            for match in matches:
                original = match.group()
                start, end = match.span()
                
                # Choose redaction method
                method = self.config["redaction_policy"]["method"]
                if method == "hash":
                    replacement = self._hash_sensitive_data(original)
                elif method == "mask":
                    replacement = self._mask_sensitive_data(original)
                elif method == "remove":
                    replacement = "[REDACTED]"
                else:
                    replacement = "[REDACTED]"
                    
                # Replace in text
                redacted_text = redacted_text.replace(original, replacement, 1)
                
                # Log detection
                detection = {
                    "pattern": pattern_name,
                    "original": original,
                    "replacement": replacement,
                    "position": (start, end),
                    "context": context,
                    "timestamp": datetime.now().isoformat()
                }
                detections.append(detection)
                
                # Audit logging
                if self.config["redaction_policy"]["audit_enabled"]:
                    self.audit_log.append({
                        "event": "pii_detection",
                        "pattern": pattern_name,
                        "context": context,
                        "redacted": True,
                        "timestamp": datetime.now().isoformat(),
                        "hash": hashlib.sha256(original.encode()).hexdigest()[:8]
                    })
                    
        return redacted_text, detections
        
    def sanitize_dataset(self, dataset_path: str, output_path: str) -> Dict[str, Any]:
        """Sanitize entire dataset file"""
        print(f"🔒 Sanitizing dataset: {dataset_path}")
        
        dataset_file = Path(dataset_path)
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
            
        # Load dataset
        with open(dataset_file, 'r') as f:
            if dataset_path.endswith('.jsonl'):
                data = [json.loads(line) for line in f if line.strip()]
            else:
                data = json.load(f)
                
        sanitized_data = []
        total_detections = 0
        
        for i, example in enumerate(data):
            sanitized_example = {}
            
            for field, value in example.items():
                if isinstance(value, str):
                    sanitized_value, detections = self.detect_and_redact(
                        value, 
                        context=f"dataset_{dataset_file.stem}_example_{i}_field_{field}"
                    )
                    sanitized_example[field] = sanitized_value
                    total_detections += len(detections)
                else:
                    sanitized_example[field] = value
                    
            sanitized_data.append(sanitized_example)
            
        # Save sanitized dataset
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            if output_path.endswith('.jsonl'):
                for example in sanitized_data:
                    f.write(json.dumps(example) + '\n')
            else:
                json.dump(sanitized_data, f, indent=2)
                
        # Generate report
        report = {
            "input_file": str(dataset_file),
            "output_file": str(output_file),
            "total_examples": len(data),
            "total_detections": total_detections,
            "patterns_detected": list(set(d["pattern"] for d in self.audit_log)),
            "sanitization_timestamp": datetime.now().isoformat(),
            "config_hash": self._get_config_hash()
        }
        
        print(f"✅ Sanitized {len(data)} examples, {total_detections} PII detections")
        return report
        
    def generate_audit_report(self) -> str:
        """Generate PII audit report"""
        report_dir = Path("ai-training/data/governance/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"pii_audit_{timestamp}.json"
        
        audit_summary = {
            "total_events": len(self.audit_log),
            "patterns_detected": list(set(event["pattern"] for event in self.audit_log)),
            "contexts": list(set(event["context"] for event in self.audit_log)),
            "events": self.audit_log,
            "report_timestamp": datetime.now().isoformat()
        }
        
        with open(report_path, 'w') as f:
            json.dump(audit_summary, f, indent=2)
            
        print(f"📋 PII audit report: {report_path}")
        return str(report_path)
        
    def _get_config_hash(self) -> str:
        """Get configuration hash for versioning"""
        config_str = yaml.dump(self.config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:8]


def main():
    """Main PII redaction execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PII detection and redaction")
    parser.add_argument("--dataset", required=True, help="Dataset to sanitize")
    parser.add_argument("--output", required=True, help="Output path for sanitized dataset")
    parser.add_argument("--config", default="configs/data_governance.yaml", help="Config file")
    parser.add_argument("--audit-report", action="store_true", help="Generate audit report")
    
    args = parser.parse_args()
    
    # Initialize redactor
    redactor = PIIRedactor(args.config)
    
    # Sanitize dataset
    report = redactor.sanitize_dataset(args.dataset, args.output)
    print(f"📊 Sanitization report: {json.dumps(report, indent=2)}")
    
    # Generate audit report if requested
    if args.audit_report:
        audit_path = redactor.generate_audit_report()
        print(f"📋 Audit report saved: {audit_path}")


if __name__ == "__main__":
    main()
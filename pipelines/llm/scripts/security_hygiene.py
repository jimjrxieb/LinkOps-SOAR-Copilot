#!/usr/bin/env python3
"""
Security Hygiene and Safety Controls for Whis Training
Non-negotiable security requirements per mentor guidance
"""

import os
import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class SecurityHygiene:
    """Enforce security controls for Whis training and deployment"""
    
    def __init__(self):
        self.findings = []
        self.fixes_applied = []
    
    def check_token_security(self) -> Dict:
        """Check for hardcoded tokens and enforce env-only policy"""
        print("🔑 Checking token security...")
        
        # Files to scan for potential token leaks
        files_to_check = [
            "*.py", "*.ipynb", "*.json", "*.yaml", "*.yml", "*.md",
            "*.txt", "*.sh", "*.env"
        ]
        
        token_patterns = [
            r'hf_[a-zA-Z0-9]{34}',  # HuggingFace tokens
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI tokens  
            r'ghp_[a-zA-Z0-9]{36}', # GitHub tokens
            r'AIza[0-9A-Za-z-_]{35}', # Google API keys
        ]
        
        findings = []
        
        # Scan current directory and subdirectories
        for pattern in files_to_check:
            for file_path in Path(".").rglob(pattern):
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            for token_pattern in token_patterns:
                                matches = re.findall(token_pattern, content)
                                if matches:
                                    findings.append({
                                        "file": str(file_path),
                                        "pattern": token_pattern,
                                        "matches": len(matches),
                                        "severity": "HIGH"
                                    })
                    except Exception as e:
                        pass  # Skip files we can't read
        
        # Check environment variables (good practice)
        env_tokens = []
        for key, value in os.environ.items():
            if any(pattern in key.upper() for pattern in ["TOKEN", "KEY", "SECRET"]):
                env_tokens.append(key)
        
        result = {
            "hardcoded_tokens": findings,
            "env_tokens": env_tokens,
            "status": "SECURE" if not findings else "NEEDS_ATTENTION",
            "recommendation": "All tokens should be in environment variables only"
        }
        
        if findings:
            print(f"⚠️ Found {len(findings)} potential token exposures")
            for finding in findings:
                print(f"   - {finding['file']}: {finding['matches']} matches")
        else:
            print("✅ No hardcoded tokens found")
        
        print(f"✅ Environment tokens: {len(env_tokens)} found")
        
        return result
    
    def validate_approval_flags(self) -> Dict:
        """Ensure all Assistant outputs include approval_required: true for LC actions"""
        print("🚦 Validating approval requirement flags...")
        
        issues = []
        
        # Check training data for proper approval flags
        data_files = list(Path(".").rglob("*dataset*.json"))
        
        for data_file in data_files:
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                examples = []
                if isinstance(data, list):
                    examples = data
                elif "examples" in data:
                    examples = data["examples"]
                elif isinstance(data, dict):
                    for key, items in data.items():
                        if isinstance(items, list):
                            examples.extend(items)
                
                # Check assistant mode examples
                for i, example in enumerate(examples):
                    if isinstance(example, dict):
                        output = example.get("output", "").lower()
                        tags = example.get("tags", [])
                        
                        is_assistant = any("assistant" in str(tag).lower() for tag in tags)
                        has_lc_action = any(term in output for term in ["limacharlie", "lc", "isolation", "block"])
                        has_approval = "approval" in output and "required" in output and "true" in output
                        
                        if is_assistant and has_lc_action and not has_approval:
                            issues.append({
                                "file": str(data_file),
                                "example_index": i,
                                "issue": "Assistant mode LC action without approval_required: true"
                            })
                            
            except Exception as e:
                pass  # Skip files we can't parse
        
        result = {
            "validation_issues": issues,
            "files_checked": len(data_files),
            "status": "COMPLIANT" if not issues else "NEEDS_FIX",
            "policy": "All LimaCharlie actions must have approval_required: true"
        }
        
        if issues:
            print(f"⚠️ Found {len(issues)} approval flag issues")
            for issue in issues[:3]:  # Show first 3
                print(f"   - {issue['file']} example {issue['example_index']}")
        else:
            print("✅ All assistant examples have proper approval flags")
        
        return result
    
    def check_pii_redaction(self) -> Dict:
        """Verify no real PII in training data"""
        print("🔒 Checking PII redaction...")
        
        # Patterns that might indicate real data
        suspicious_patterns = [
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # Real IP addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Potential names
        ]
        
        # Acceptable synthetic patterns (RFC 5737, etc.)
        allowed_ips = [
            r'192\.168\.',  # Private range
            r'10\.',        # Private range  
            r'203\.0\.113\.', # RFC 5737 documentation
            r'198\.51\.100\.', # RFC 5737 documentation
            r'172\.(1[6-9]|2[0-9]|3[0-1])\.', # Private range
        ]
        
        findings = []
        data_files = list(Path(".").rglob("*dataset*.json"))
        
        for data_file in data_files:
            try:
                with open(data_file, 'r') as f:
                    content = f.read()
                
                # Check for suspicious patterns
                for pattern in suspicious_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Filter out allowed patterns for IPs
                        if pattern == suspicious_patterns[0]:  # IP pattern
                            filtered_matches = []
                            for match in matches:
                                if not any(re.match(allowed, match) for allowed in allowed_ips):
                                    filtered_matches.append(match)
                            matches = filtered_matches
                        
                        if matches:
                            findings.append({
                                "file": str(data_file),
                                "pattern_type": "IP" if pattern == suspicious_patterns[0] else "Other",
                                "matches": matches[:5],  # First 5 matches
                                "count": len(matches)
                            })
                            
            except Exception as e:
                pass
        
        result = {
            "pii_findings": findings,
            "files_checked": len(data_files),
            "status": "CLEAN" if not findings else "NEEDS_REVIEW",
            "policy": "Only synthetic/redacted data allowed in training"
        }
        
        if findings:
            print(f"⚠️ Found {len(findings)} potential PII issues")
            for finding in findings[:2]:  # Show first 2
                print(f"   - {finding['file']}: {finding['count']} {finding['pattern_type']} matches")
        else:
            print("✅ No PII detected - data appears properly redacted")
        
        return result
    
    def validate_lora_only_policy(self) -> Dict:
        """Ensure only LoRA adapters are saved, not merged base weights"""
        print("💾 Validating LoRA-only save policy...")
        
        model_dirs = [p for p in Path(".").rglob("*model*") if p.is_dir()]
        
        violations = []
        compliant_dirs = []
        
        for model_dir in model_dirs:
            # Check for base model files (large weights)
            base_model_files = [
                "pytorch_model.bin", "model.safetensors", 
                "pytorch_model-*.bin", "model-*.safetensors"
            ]
            
            lora_files = [
                "adapter_model.safetensors", "adapter_config.json",
                "adapter_model.bin"
            ]
            
            has_base_weights = any(
                list(model_dir.glob(pattern)) for pattern in base_model_files
            )
            has_lora_adapter = any(
                list(model_dir.glob(pattern)) for pattern in lora_files  
            )
            
            if has_base_weights:
                violations.append({
                    "directory": str(model_dir),
                    "issue": "Contains full base model weights"
                })
            elif has_lora_adapter:
                compliant_dirs.append(str(model_dir))
        
        result = {
            "violations": violations,
            "compliant_dirs": compliant_dirs,
            "status": "COMPLIANT" if not violations else "POLICY_VIOLATION",
            "policy": "Save only LoRA adapters, not merged base weights"
        }
        
        if violations:
            print(f"⚠️ Found {len(violations)} base weight violations")
            for violation in violations:
                print(f"   - {violation['directory']}")
        else:
            print(f"✅ LoRA-only policy compliant ({len(compliant_dirs)} directories)")
        
        return result
    
    def generate_security_report(self) -> Dict:
        """Generate comprehensive security audit report"""
        print("\n🛡️ SECURITY HYGIENE AUDIT")
        print("=" * 50)
        
        # Run all checks
        token_check = self.check_token_security()
        approval_check = self.validate_approval_flags()  
        pii_check = self.check_pii_redaction()
        lora_check = self.validate_lora_only_policy()
        
        # Calculate overall score
        checks = [token_check, approval_check, pii_check, lora_check]
        passed = sum(1 for check in checks if check["status"] in ["SECURE", "COMPLIANT", "CLEAN"])
        total = len(checks)
        
        overall_status = "SECURE" if passed == total else "NEEDS_ATTENTION"
        
        report = {
            "audit_timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "score": f"{passed}/{total}",
            "checks": {
                "token_security": token_check,
                "approval_flags": approval_check,
                "pii_redaction": pii_check,
                "lora_only_policy": lora_check
            },
            "recommendations": [
                "Rotate HuggingFace token after demo",
                "Keep all tokens in environment variables only",
                "Ensure all LC actions have approval_required: true",
                "Use only synthetic data in training examples",
                "Save only LoRA adapters, not full model weights"
            ]
        }
        
        print(f"\n📊 Security Score: {passed}/{total}")
        print(f"🔒 Overall Status: {overall_status}")
        
        if overall_status == "SECURE":
            print("🎉 All security checks passed!")
        else:
            print("⚠️ Security issues found - review recommendations")
        
        # Save report
        with open("security_audit_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print("💾 Security report saved to: security_audit_report.json")
        
        return report

def main():
    """Run security hygiene audit"""
    hygiene = SecurityHygiene()
    report = hygiene.generate_security_report()
    
    return report["overall_status"] == "SECURE"

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
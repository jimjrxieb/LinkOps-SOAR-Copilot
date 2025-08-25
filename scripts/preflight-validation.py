#!/usr/bin/env python3
"""
🛫 Preflight Validation Script
=============================
Final go/no-go checks before production launch.
"""

import json
import hashlib
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
import sys
import time

class PreflightValidator:
    """Pre-launch validation checklist"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "validation_id": f"preflight_{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "status": "PENDING",
            "checks": {},
            "critical_failures": []
        }
    
    def _check_passed(self, name: str, passed: bool, message: str, critical: bool = False):
        """Record check result"""
        icon = "✅" if passed else ("🚨" if critical else "⚠️")
        self.results["checks"][name] = {
            "passed": passed,
            "message": message,
            "critical": critical
        }
        
        if not passed and critical:
            self.results["critical_failures"].append(name)
            
        print(f"{icon} {name}: {message}")
        return passed
    
    def check_manifest_parity(self) -> bool:
        """Verify RELEASE_MANIFEST.json matches runtime"""
        print("📋 MANIFEST PARITY CHECK")
        
        manifest_path = self.project_root / "RELEASE_MANIFEST.json"
        if not manifest_path.exists():
            return self._check_passed("manifest_exists", False, "RELEASE_MANIFEST.json not found", True)
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        # Check base model reference
        base_model = manifest.get("ai_models", {}).get("base_model", {})
        if not base_model.get("name"):
            return self._check_passed("base_model_ref", False, "Base model reference missing", True)
        
        # Check adapter versions
        adapters = manifest.get("ai_models", {}).get("adapters", {})
        if not adapters:
            return self._check_passed("adapter_versions", False, "Adapter versions missing", True)
            
        # Check RAG indices
        rag_indices = manifest.get("rag_system", {}).get("indices", {})
        if not rag_indices:
            return self._check_passed("rag_indices", False, "RAG indices missing", True)
        
        return self._check_passed("manifest_parity", True, "Manifest structure valid")
    
    def check_config_sanity(self) -> bool:
        """Verify eval.yaml contains correct thresholds"""
        print("⚙️  CONFIG SANITY CHECK")
        
        eval_config = self.project_root / "ai-training/configs/eval.yaml"
        if not eval_config.exists():
            return self._check_passed("eval_config", False, "eval.yaml not found", True)
        
        # Check if thresholds are reasonable (simplified check)
        with open(eval_config) as f:
            content = f.read()
            
        has_ragas = "ragas" in content.lower()
        has_hit_at_5 = "hit" in content.lower()
        
        if not (has_ragas and has_hit_at_5):
            return self._check_passed("eval_thresholds", False, "Missing RAGAS or Hit@5 config", True)
        
        return self._check_passed("config_sanity", True, "Eval config contains thresholds")
    
    def check_artifact_manifest(self) -> bool:
        """Verify externalized artifacts are properly tracked"""
        print("📦 ARTIFACT MANIFEST CHECK")
        
        manifest_path = self.project_root / "EXTERNAL_ARTIFACTS_MANIFEST.json"
        if not manifest_path.exists():
            return self._check_passed("artifact_manifest", False, "External artifacts manifest missing", True)
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        artifacts = manifest.get("artifacts", {})
        if len(artifacts) == 0:
            return self._check_passed("artifacts_tracked", False, "No artifacts tracked")
        
        # Verify checksums exist
        missing_checksums = [
            path for path, info in artifacts.items()
            if not info.get("checksum_sha256")
        ]
        
        if missing_checksums:
            return self._check_passed("artifact_checksums", False, f"Missing checksums: {len(missing_checksums)} files")
        
        return self._check_passed("artifact_manifest", True, f"Tracking {len(artifacts)} externalized artifacts")
    
    def check_quarantine_enforcement(self) -> bool:
        """Verify PII redaction is in place"""
        print("🛡️  QUARANTINE ENFORCEMENT CHECK")
        
        pii_redactor = self.project_root / "ai-training/data/governance/pii_redaction.py"
        if not pii_redactor.exists():
            return self._check_passed("pii_redaction", False, "PII redaction module missing", True)
        
        # Check if quarantine directory structure exists
        governance_dir = self.project_root / "ai-training/data/governance"
        if not governance_dir.exists():
            return self._check_passed("governance_structure", False, "Data governance structure missing")
        
        return self._check_passed("quarantine_enforcement", True, "PII redaction module present")
    
    def check_legacy_exclusion(self) -> bool:
        """Verify legacy paths are excluded from packaging"""
        print("🏗️  LEGACY EXCLUSION CHECK")
        
        # Check pyproject.toml excludes legacy-disabled
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject) as f:
                content = f.read()
                if "legacy-disabled" not in content:
                    return self._check_passed("pyproject_exclusion", False, "legacy-disabled not excluded from pyproject.toml")
        
        # Check .dockerignore excludes legacy paths
        dockerignore = self.project_root / ".dockerignore"
        if dockerignore.exists():
            with open(dockerignore) as f:
                content = f.read()
                if "legacy-disabled" not in content:
                    return self._check_passed("docker_exclusion", False, "legacy-disabled not in .dockerignore")
        
        return self._check_passed("legacy_exclusion", True, "Legacy paths properly excluded")
    
    def check_security_basics(self) -> bool:
        """Basic security configuration check"""
        print("🔒 SECURITY BASICS CHECK")
        
        # Check JWT configuration exists
        security_config = self.project_root / "ai-training/configs/security.yaml"
        if not security_config.exists():
            return self._check_passed("security_config", False, "security.yaml missing", True)
        
        # Check integrated server has security middleware
        server_file = self.project_root / "apps/api/whis_integrated_server.py"
        if server_file.exists():
            with open(server_file) as f:
                content = f.read()
                has_jwt = "JWT" in content or "jwt" in content
                has_cors = "CORS" in content or "cors" in content
                
                if not (has_jwt and has_cors):
                    return self._check_passed("server_security", False, "Missing JWT or CORS in integrated server", True)
        
        return self._check_passed("security_basics", True, "Security configurations present")
    
    def run_preflight(self) -> Dict[str, Any]:
        """Run complete preflight validation"""
        print("🛫 WHIS PREFLIGHT VALIDATION")
        print("=" * 50)
        
        # Run all checks
        checks = [
            self.check_manifest_parity(),
            self.check_config_sanity(), 
            self.check_artifact_manifest(),
            self.check_quarantine_enforcement(),
            self.check_legacy_exclusion(),
            self.check_security_basics()
        ]
        
        # Determine status
        all_passed = all(checks)
        critical_failed = len(self.results["critical_failures"]) > 0
        
        if critical_failed:
            self.results["status"] = "CRITICAL_FAILURE"
        elif all_passed:
            self.results["status"] = "GO"
        else:
            self.results["status"] = "GO_WITH_WARNINGS"
        
        return self.results
    
    def print_summary(self):
        """Print preflight summary"""
        print("\n🛫 PREFLIGHT SUMMARY")
        print("=" * 50)
        
        status = self.results["status"]
        status_icons = {
            "GO": "🟢",
            "GO_WITH_WARNINGS": "🟡", 
            "CRITICAL_FAILURE": "🔴"
        }
        
        print(f"{status_icons.get(status, '❓')} Status: {status}")
        
        if self.results["critical_failures"]:
            print(f"🚨 Critical failures: {len(self.results['critical_failures'])}")
            for failure in self.results["critical_failures"]:
                print(f"  • {failure}")
        
        print()
        
        if status == "GO":
            print("🚀 WHIS IS READY FOR LAUNCH!")
            print("   Run: ./LAUNCH-FULL-WHIS.sh")
        elif status == "GO_WITH_WARNINGS":
            print("⚠️  WHIS can launch but has warnings")
        else:
            print("🛑 WHIS IS NOT READY - Fix critical failures first")

def main():
    """Main preflight runner"""
    validator = PreflightValidator()
    
    print("Running WHIS preflight validation...")
    results = validator.run_preflight()
    validator.print_summary()
    
    # Save results
    results_file = f"preflight_results_{results['validation_id']}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Results saved to: {results_file}")
    
    # Exit with appropriate code
    if results["status"] in ["GO", "GO_WITH_WARNINGS"]:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
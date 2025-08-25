#!/usr/bin/env python3
"""
Quarantine enforcement for raw data processing.
Prevents direct access to raw data without proper sanitization.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Any

# Quarantined directories that require special handling
QUARANTINE_DIRS = [
    "ai-training/llm/data/external/open-malsec",
    "ai-training/llm/external-models",
    "data/raw",
    "results/experiments"
]

# Patterns that require quarantine processing
SENSITIVE_PATTERNS = [
    r'password["\s]*[:=]["\s]*[^"\s]+',
    r'api[_-]?key["\s]*[:=]["\s]*[^"\s]+',
    r'secret["\s]*[:=]["\s]*[^"\s]+',
    r'token["\s]*[:=]["\s]*[^"\s]+',
    r'-----BEGIN [A-Z ]+-----'
]

def check_quarantine_access(file_path: str) -> bool:
    """Check if file is in quarantine and requires special handling."""
    file_path = Path(file_path).resolve()
    
    for qdir in QUARANTINE_DIRS:
        qdir_path = Path(qdir).resolve()
        try:
            file_path.relative_to(qdir_path)
            return True
        except ValueError:
            continue
    
    return False

def scan_for_sensitive_content(file_path: str) -> List[str]:
    """Scan file for potentially sensitive content."""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for pattern in SENSITIVE_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                violations.append(f"Line {line_num}: {pattern}")
                
    except Exception as e:
        violations.append(f"Scan error: {e}")
        
    return violations

def enforce_quarantine_protocol(operation: str, file_path: str) -> bool:
    """
    Enforce quarantine protocol for file operations.
    
    Args:
        operation: Type of operation (read, write, execute)
        file_path: Path to file being accessed
        
    Returns:
        bool: True if operation is allowed, False if blocked
    """
    
    if not check_quarantine_access(file_path):
        return True  # Not in quarantine, allow normal access
    
    print(f"🔒 QUARANTINE: {file_path} requires special handling")
    
    # Check for sensitive content
    violations = scan_for_sensitive_content(file_path)
    if violations:
        print(f"⚠️  SECURITY VIOLATIONS DETECTED:")
        for violation in violations[:5]:  # Show first 5
            print(f"   {violation}")
        
        if len(violations) > 5:
            print(f"   ... and {len(violations) - 5} more")
            
        response = input("Continue with sanitization? (y/N): ")
        return response.lower() == 'y'
    
    print(f"✅ No security violations detected in {file_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: quarantine-enforcer.py <operation> <file_path>")
        print("Operations: read, write, execute")
        sys.exit(1)
    
    operation = sys.argv[1]
    file_path = sys.argv[2]
    
    if enforce_quarantine_protocol(operation, file_path):
        print(f"✅ ALLOWED: {operation} on {file_path}")
        sys.exit(0)
    else:
        print(f"🚫 BLOCKED: {operation} on {file_path}")
        sys.exit(1)
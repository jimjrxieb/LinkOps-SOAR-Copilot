#!/usr/bin/env python3
"""
📦 Artifact Externalization Script
==================================
Move large artifacts out of git and create manifests with checksums.
"""

import os
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes"""
    return file_path.stat().st_size

def externalize_artifacts():
    """Move artifacts to external storage and create manifests"""
    project_root = Path(__file__).parent.parent
    external_storage = project_root / "external-artifacts"
    external_storage.mkdir(exist_ok=True)
    
    # Patterns to externalize
    patterns = [
        "**/*.safetensors",
        "**/*.bin",
        "**/*.faiss", 
        "**/*.pth",
        "**/venv/**",
        "**/codellama-cache/**",
        "**/checkpoints/**"
    ]
    
    manifests = {}
    total_size = 0
    files_moved = 0
    
    print("📦 Starting artifact externalization...")
    
    for pattern in patterns:
        print(f"🔍 Processing pattern: {pattern}")
        
        for file_path in project_root.rglob(pattern.replace("**", "*")):
            if file_path.is_file() and not str(file_path).startswith(str(external_storage)):
                
                # Skip if already in external storage or is placeholder
                relative_path = file_path.relative_to(project_root)
                if "external-artifacts" in str(relative_path) or str(relative_path).endswith(".externalized"):
                    continue
                
                print(f"📦 Externalizing: {relative_path}")
                
                # Calculate metadata
                file_size = get_file_size(file_path)
                checksum = calculate_checksum(file_path)
                
                # Create external path maintaining structure
                external_file_path = external_storage / relative_path
                external_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.move(str(file_path), str(external_file_path))
                
                # Create manifest entry
                manifests[str(relative_path)] = {
                    "external_path": str(external_file_path.relative_to(project_root)),
                    "size_bytes": file_size,
                    "checksum_sha256": checksum,
                    "externalized_at": datetime.now().isoformat(),
                    "type": file_path.suffix[1:] if file_path.suffix else "unknown"
                }
                
                # Create placeholder file
                placeholder_content = f"""# EXTERNALIZED ARTIFACT
# This file has been moved to external storage for repository hygiene.
# 
# Original file: {relative_path}
# External path: {external_file_path.relative_to(project_root)}
# Size: {file_size:,} bytes
# Checksum: {checksum}
# Externalized: {datetime.now().isoformat()}
#
# To restore: ./scripts/restore-artifacts.py {relative_path}
"""
                
                placeholder_path = file_path.with_suffix(file_path.suffix + ".externalized")
                with open(placeholder_path, 'w') as f:
                    f.write(placeholder_content)
                
                total_size += file_size
                files_moved += 1
    
    # Save manifest
    manifest_path = project_root / "EXTERNAL_ARTIFACTS_MANIFEST.json"
    manifest_data = {
        "metadata": {
            "externalized_at": datetime.now().isoformat(),
            "total_files": files_moved,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "external_storage_path": str(external_storage.relative_to(project_root))
        },
        "artifacts": manifests
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    print(f"\n✅ Externalization complete!")
    print(f"📊 Files moved: {files_moved}")
    print(f"💾 Space saved: {round(total_size / (1024 * 1024), 2)} MB")
    print(f"📋 Manifest: {manifest_path}")
    print(f"🗂️  External storage: {external_storage}")
    
    # Update .gitignore to ignore external storage
    gitignore_path = project_root / ".gitignore"
    gitignore_addition = f"\n# External artifact storage\n{external_storage.name}/\n"
    
    with open(gitignore_path, 'a') as f:
        f.write(gitignore_addition)
    
    print(f"📝 Updated .gitignore to exclude external storage")

if __name__ == "__main__":
    externalize_artifacts()
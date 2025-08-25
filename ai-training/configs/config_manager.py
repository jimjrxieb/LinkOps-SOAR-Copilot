#!/usr/bin/env python3
"""
⚙️ WHIS Configuration Manager
============================
Centralized configuration management with environment-aware defaults,
validation, and hot-reloading capabilities.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from dataclasses import dataclass, field
import logging
from datetime import datetime
import hashlib


@dataclass
class ConfigSource:
    """Configuration source metadata"""
    path: Path
    last_modified: datetime
    checksum: str
    priority: int = 0  # Higher priority overrides lower


class ConfigManager:
    """Centralized configuration management for WHIS SOAR-Copilot"""
    
    def __init__(self, base_path: str = "ai-training/configs", environment: str = None):
        self.base_path = Path(base_path)
        self.environment = environment or os.getenv("WHIS_ENV", "development")
        self.config_cache: Dict[str, Any] = {}
        self.sources: Dict[str, ConfigSource] = {}
        self.watchers: Dict[str, callable] = {}
        
        logging.info(f"⚙️ ConfigManager initialized for environment: {self.environment}")
        
    def _get_config_path(self, config_name: str, environment: str = None) -> Path:
        """Get path for configuration file"""
        env = environment or self.environment
        
        # Try environment-specific config first
        env_path = self.base_path / f"{config_name}.{env}.yaml"
        if env_path.exists():
            return env_path
            
        # Fall back to base config
        base_path = self.base_path / f"{config_name}.yaml"
        if base_path.exists():
            return base_path
            
        # Try JSON format
        json_path = self.base_path / f"{config_name}.json"
        if json_path.exists():
            return json_path
            
        raise FileNotFoundError(f"Configuration '{config_name}' not found in {self.base_path}")
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum for change detection"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            logging.error(f"Failed to load config from {file_path}: {e}")
            return {}
    
    def _resolve_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variables in configuration values"""
        def resolve_value(value):
            if isinstance(value, str):
                # Handle ${VAR} and ${VAR:-default} patterns
                import re
                pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
                
                def replace_var(match):
                    var_name = match.group(1)
                    default_value = match.group(2) if match.group(2) is not None else ''
                    return os.getenv(var_name, default_value)
                
                return re.sub(pattern, replace_var, value)
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            else:
                return value
        
        return resolve_value(config)
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge configuration dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def load(self, config_name: str, refresh: bool = False) -> Dict[str, Any]:
        """Load configuration with caching and environment resolution"""
        cache_key = f"{config_name}:{self.environment}"
        
        # Check cache first
        if not refresh and cache_key in self.config_cache:
            source = self.sources.get(cache_key)
            if source:
                # Check if file has changed
                current_checksum = self._calculate_checksum(source.path)
                if current_checksum == source.checksum:
                    return self.config_cache[cache_key]
        
        try:
            config_path = self._get_config_path(config_name)
            config_data = self._load_file(config_path)
            
            # Load base config if this is environment-specific
            if f".{self.environment}." in config_path.name:
                try:
                    base_path = self._get_config_path(config_name, "base")
                    base_data = self._load_file(base_path)
                    config_data = self._merge_configs(base_data, config_data)
                except FileNotFoundError:
                    pass  # No base config, use environment config as-is
            
            # Resolve environment variables
            config_data = self._resolve_environment_variables(config_data)
            
            # Update cache and source tracking
            checksum = self._calculate_checksum(config_path)
            self.config_cache[cache_key] = config_data
            self.sources[cache_key] = ConfigSource(
                path=config_path,
                last_modified=datetime.fromtimestamp(config_path.stat().st_mtime),
                checksum=checksum
            )
            
            logging.debug(f"📁 Loaded config '{config_name}' from {config_path}")
            return config_data
            
        except Exception as e:
            logging.error(f"Failed to load configuration '{config_name}': {e}")
            # Return cached version if available
            if cache_key in self.config_cache:
                logging.warning(f"Using cached version of '{config_name}'")
                return self.config_cache[cache_key]
            raise
    
    def get(self, config_name: str, path: str, default: Any = None) -> Any:
        """Get specific configuration value using dot notation"""
        config = self.load(config_name)
        
        keys = path.split('.')
        current = config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, config_name: str, path: str, value: Any, persist: bool = False):
        """Set configuration value (in-memory by default, optionally persist)"""
        cache_key = f"{config_name}:{self.environment}"
        config = self.load(config_name)
        
        keys = path.split('.')
        current = config
        
        # Navigate to parent
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set value
        current[keys[-1]] = value
        
        # Update cache
        self.config_cache[cache_key] = config
        
        if persist:
            self.save(config_name, config)
    
    def save(self, config_name: str, config: Dict[str, Any] = None):
        """Save configuration to file"""
        if config is None:
            cache_key = f"{config_name}:{self.environment}"
            config = self.config_cache.get(cache_key)
            if not config:
                raise ValueError(f"No configuration data for '{config_name}'")
        
        try:
            config_path = self._get_config_path(config_name)
        except FileNotFoundError:
            # Create new file
            config_path = self.base_path / f"{config_name}.{self.environment}.yaml"
        
        # Backup existing file
        if config_path.exists():
            backup_path = config_path.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak')
            config_path.rename(backup_path)
        
        # Save configuration
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            if config_path.suffix.lower() == '.json':
                json.dump(config, f, indent=2)
            else:
                yaml.dump(config, f, indent=2, default_flow_style=False)
        
        logging.info(f"💾 Saved config '{config_name}' to {config_path}")
    
    def watch(self, config_name: str, callback: callable):
        """Register callback for configuration changes"""
        key = f"{config_name}:{self.environment}"
        self.watchers[key] = callback
        logging.info(f"👀 Watching config '{config_name}' for changes")
    
    def check_changes(self):
        """Check for configuration file changes and notify watchers"""
        for key, source in self.sources.items():
            try:
                current_checksum = self._calculate_checksum(source.path)
                if current_checksum != source.checksum:
                    config_name = key.split(':')[0]
                    logging.info(f"🔄 Config '{config_name}' changed, reloading...")
                    
                    # Reload configuration
                    new_config = self.load(config_name, refresh=True)
                    
                    # Notify watchers
                    if key in self.watchers:
                        try:
                            self.watchers[key](config_name, new_config)
                        except Exception as e:
                            logging.error(f"Error in config watcher for '{config_name}': {e}")
                            
            except Exception as e:
                logging.error(f"Error checking changes for {source.path}: {e}")
    
    def validate(self, config_name: str, schema: Dict[str, Any]) -> List[str]:
        """Validate configuration against schema"""
        config = self.load(config_name)
        errors = []
        
        def validate_recursive(data, schema_part, path=""):
            for key, expected in schema_part.items():
                current_path = f"{path}.{key}" if path else key
                
                if key not in data:
                    if expected.get("required", False):
                        errors.append(f"Missing required field: {current_path}")
                    continue
                
                value = data[key]
                expected_type = expected.get("type")
                
                if expected_type and not isinstance(value, expected_type):
                    errors.append(f"Type mismatch at {current_path}: expected {expected_type.__name__}, got {type(value).__name__}")
                
                if "values" in expected and value not in expected["values"]:
                    errors.append(f"Invalid value at {current_path}: {value} not in {expected['values']}")
                
                if "nested" in expected and isinstance(value, dict):
                    validate_recursive(value, expected["nested"], current_path)
        
        validate_recursive(config, schema)
        return errors
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded configurations"""
        configs = {}
        for key, config in self.config_cache.items():
            config_name = key.split(':')[0]
            configs[config_name] = config
        return configs
    
    def export_merged_config(self, output_path: str):
        """Export all configurations merged into single file"""
        all_configs = self.get_all_configs()
        
        with open(output_path, 'w') as f:
            yaml.dump(all_configs, f, indent=2, default_flow_style=False)
        
        logging.info(f"📦 Exported merged config to {output_path}")


# Global configuration manager instance
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def init_config_manager(base_path: str = "ai-training/configs", environment: str = None) -> ConfigManager:
    """Initialize global configuration manager"""
    global _global_config_manager
    _global_config_manager = ConfigManager(base_path, environment)
    return _global_config_manager


# Convenience functions
def load_config(name: str) -> Dict[str, Any]:
    """Load configuration using global manager"""
    return get_config_manager().load(name)


def get_config(name: str, path: str, default: Any = None) -> Any:
    """Get configuration value using global manager"""
    return get_config_manager().get(name, path, default)


def set_config(name: str, path: str, value: Any, persist: bool = False):
    """Set configuration value using global manager"""
    return get_config_manager().set(name, path, value, persist)


# Configuration schemas for validation
CONFIG_SCHEMAS = {
    "monitoring": {
        "telemetry": {
            "type": dict,
            "required": True,
            "nested": {
                "service_name": {"type": str, "required": True},
                "environment": {"type": str, "values": ["development", "staging", "production"]}
            }
        },
        "logging": {
            "type": dict,
            "nested": {
                "level": {"type": str, "values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]}
            }
        }
    },
    
    "rag": {
        "embedder": {
            "type": dict,
            "required": True,
            "nested": {
                "model_name": {"type": str, "required": True},
                "device": {"type": str, "values": ["cpu", "cuda", "auto"]}
            }
        }
    },
    
    "model": {
        "base_model": {
            "type": dict,
            "required": True,
            "nested": {
                "name": {"type": str, "required": True},
                "path": {"type": str, "required": True}
            }
        }
    }
}
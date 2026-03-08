"""
Task 1: YAML Configuration Loader
Author: 闫文峰

Loads and parses boundary_patterns.yaml configuration file.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List


class ConfigLoader:
    """
    YAML configuration loader for bug report analyzer.
    
    Loads configuration from YAML file and provides methods to access
    different sections like boundary markers, record types, and interest points.
    """
    
    def __init__(self, config_path: str) -> None:
        """
        Initialize the config loader.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self._config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
    
    @property
    def config_path(self) -> Path:
        """Get the configuration file path."""
        return self._config_path
    
    def load(self) -> Dict[str, Any]:
        """
        Load YAML configuration from file.
        
        Returns:
            Dictionary containing all configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML format is invalid
        """
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        
        with open(self._config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        return self._config
    
    def get_boundary_markers(self) -> Dict[str, Dict]:
        """
        Get boundary marker configurations.
        
        Returns:
            Dictionary mapping marker names to their configurations
        """
        return self._config.get("boundary_markers", {})
    
    def get_record_types(self) -> List[Dict]:
        """
        Get record type configurations.
        
        Returns:
            List of record type dictionaries
        """
        return self._config.get("record_types", [])
    
    def get_interest_points(self) -> List[Dict]:
        """
        Get interest point configurations.
        
        Returns:
            List of interest point dictionaries
        """
        return self._config.get("interest_points", [])
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata from configuration.
        
        Returns:
            Dictionary containing metadata
        """
        return self._config.get("metadata", {})


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Helper function to load YAML configuration.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Dictionary containing all configuration
    """
    loader = ConfigLoader(config_path)
    return loader.load()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python config_loader.py <config_path>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    try:
        config = load_yaml_config(config_path)
        print(f"✓ Config loaded successfully: {config_path}")
        print(f"  Boundary markers: {len(config.get('boundary_markers', {}))}")
        print(f"  Record types: {len(config.get('record_types', []))}")
        print(f"  Interest points: {len(config.get('interest_points', []))}")
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        sys.exit(1)

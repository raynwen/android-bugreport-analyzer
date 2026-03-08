# Test for Task 1: YAML Configuration Loader

import pytest
import os
import sys
import tempfile
import yaml

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_loader import ConfigLoader, load_yaml_config


class TestConfigLoader:
    """Test ConfigLoader class"""

    @pytest.fixture
    def sample_yaml_content(self):
        """Sample YAML content for testing"""
        return {
            "boundary_markers": {
                "equals_separator": {
                    "pattern": r"^={20,}$",
                    "description": "20+ consecutive equals"
                },
                "dash_separator": {
                    "pattern": r"^-{20,}$",
                    "description": "20+ consecutive dashes"
                }
            },
            "record_types": [
                {
                    "name": "dumpsys_normal",
                    "keywords": ["dumpsys", "activity"],
                    "category": "system"
                }
            ],
            "interest_points": [
                {
                    "name": "crash",
                    "keywords": ["crash", "FATAL"],
                    "priority": "HIGH"
                }
            ]
        }

    @pytest.fixture
    def temp_yaml_file(self, sample_yaml_content):
        """Create a temporary YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_yaml_content, f)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_load_existing_config(self, temp_yaml_file):
        """T1.1: Load existing config file"""
        loader = ConfigLoader(temp_yaml_file)
        config = loader.load()
        
        assert config is not None
        assert isinstance(config, dict)

    def test_load_nonexistent_file(self):
        """T1.2: Load non-existent config file"""
        loader = ConfigLoader("nonexistent.yaml")
        
        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_load_invalid_yaml(self):
        """T1.3: Load invalid YAML format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [}")
            temp_path = f.name
        
        try:
            loader = ConfigLoader(temp_path)
            with pytest.raises(yaml.YAMLError):
                loader.load()
        finally:
            os.unlink(temp_path)

    def test_get_boundary_markers(self, temp_yaml_file):
        """T1.4: Get boundary markers configuration"""
        loader = ConfigLoader(temp_yaml_file)
        loader.load()
        
        boundary_markers = loader.get_boundary_markers()
        
        assert boundary_markers is not None
        assert isinstance(boundary_markers, dict)
        assert len(boundary_markers) > 0
        assert "equals_separator" in boundary_markers
        assert "dash_separator" in boundary_markers

    def test_get_record_types(self, temp_yaml_file):
        """T1.5: Get record types configuration"""
        loader = ConfigLoader(temp_yaml_file)
        loader.load()
        
        record_types = loader.get_record_types()
        
        assert record_types is not None
        assert isinstance(record_types, list)
        assert len(record_types) > 0

    def test_get_interest_points(self, temp_yaml_file):
        """Get interest points configuration"""
        loader = ConfigLoader(temp_yaml_file)
        loader.load()
        
        interest_points = loader.get_interest_points()
        
        assert interest_points is not None
        assert isinstance(interest_points, list)
        assert len(interest_points) > 0

    def test_load_yaml_helper_function(self, temp_yaml_file):
        """Test helper function load_yaml_config"""
        config = load_yaml_config(temp_yaml_file)
        
        assert config is not None
        assert "boundary_markers" in config
        assert "record_types" in config

    def test_boundary_marker_has_pattern(self, temp_yaml_file):
        """Verify boundary marker has pattern field"""
        loader = ConfigLoader(temp_yaml_file)
        loader.load()
        
        markers = loader.get_boundary_markers()
        equals_marker = markers["equals_separator"]
        
        assert "pattern" in equals_marker
        assert equals_marker["pattern"] == r"^={20,}$"


class TestConfigLoaderWithRealFile:
    """Test with real boundary_patterns.yaml file"""

    @pytest.fixture
    def real_config_path(self):
        """Path to real config file"""
        return os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "boundary_patterns.yaml"
        )

    def test_load_real_config(self, real_config_path):
        """T1.1: Load real configuration file"""
        if not os.path.exists(real_config_path):
            pytest.skip("Real config file not found")
        
        loader = ConfigLoader(real_config_path)
        config = loader.load()
        
        assert config is not None
        assert "boundary_markers" in config

    def test_real_config_has_required_sections(self, real_config_path):
        """Verify real config has required sections"""
        if not os.path.exists(real_config_path):
            pytest.skip("Real config file not found")
        
        loader = ConfigLoader(real_config_path)
        loader.load()
        
        assert loader.get_boundary_markers()
        assert loader.get_record_types()

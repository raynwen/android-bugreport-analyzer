# Test for Task 10: Query Interface

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.query_interface import QueryInterface


class TestQueryInterface:
    """Test QueryInterface class"""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("normal line\n")
            f.write("ANR occurred\n")
            f.write("crash detected\n")
            f.write("com.example.app run\n")
            f.write("another line\n")
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_config(self):
        """Create a temporary config file"""
        import yaml
        
        config = {
            "record_types": [
                {"name": "anr", "keywords": ["ANR", "Application Not Responding"]},
                {"name": "crash", "keywords": ["crash", "FATAL"]},
            ],
            "interest_points": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)

    def test_query_preset_keyword(self, temp_file, temp_config):
        """T10.1: Query preset keyword"""
        index = {"anr": [2], "crash": [3]}
        
        qi = QueryInterface(temp_file, temp_config)
        qi.preset_index = index
        
        results = qi.query("ANR")
        
        assert len(results) > 0

    def test_query_custom_keyword(self, temp_file, temp_config):
        """T10.2: Query custom keyword"""
        qi = QueryInterface(temp_file, temp_config)
        
        results = qi.query("com.example.app")
        
        assert len(results) > 0

    def test_is_preset(self, temp_file, temp_config):
        """T10.3: Check if keyword is preset"""
        qi = QueryInterface(temp_file, temp_config)
        
        assert qi.is_preset("ANR") == True
        assert qi.is_preset("com.newapp") == False

    def test_fallback_to_custom(self, temp_file, temp_config):
        """T10.4: Fallback to custom query when no index"""
        qi = QueryInterface(temp_file, temp_config)
        qi.preset_index = {}
        
        results = qi.query("ANR")
        
        assert len(results) > 0

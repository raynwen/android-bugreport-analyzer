# Test for Task 11: Integration Tests

import pytest
import os
import sys
import tempfile
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_loader import ConfigLoader
from src.boundary_detector import BoundaryDetector
from src.section_detector import SectionDetector
from src.section_parser import build_section_tree
from src.keyword_extractor import extract_preset_keywords
from src.index_builder import PresetIndexBuilder
from src.query_interface import QueryInterface


class TestIntegration:
    """Integration tests for the complete workflow"""

    @pytest.fixture
    def temp_bugreport(self):
        """Create a temporary bug report file"""
        content = """========================================================
------ MEMORY INFO (/proc/meminfo) ------
MemTotal: 4096 MB
ANR detected in com.example.app
------ 5.234s was the duration of 'MEMORY INFO' ------
------ VIRTUAL MEMORY STATS (/proc/vmstat) ------
pgpgin: 1234
------ 3.100s was the duration of 'VIRTUAL MEMORY STATS' ------
------ ACTIVITY MANAGER ACTIVITIES ------
com.example.app ActivityManager: ANR
crash in system_server
------ 2.500s was the duration of 'ACTIVITY MANAGER ACTIVITIES' ------
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def temp_config(self):
        """Create a temporary config file"""
        config = {
            "boundary_markers": {
                "equals_separator": {"pattern": r"^={20,}.*={20,}$", "level": 1},
                "dash_separator": {"pattern": r"^-+.*-+$", "level": 2},
                "duration_marker_major": {"pattern": r"was the duration of", "level": 0},
            },
            "record_types": [
                {"name": "anr", "keywords": ["ANR"], "category": "critical"},
                {"name": "crash", "keywords": ["crash", "FATAL"], "category": "critical"},
            ],
            "interest_points": [
                {"name": "oom", "keywords": ["OOM", "OutOfMemory"], "priority": "high"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)

    def test_full_workflow(self, temp_bugreport, temp_config):
        """T11.1: Full workflow from config to query"""
        
        config_loader = ConfigLoader(temp_config)
        config = config_loader.load()
        
        assert "boundary_markers" in config
        assert "record_types" in config
        
        boundary_detector = BoundaryDetector(config["boundary_markers"])
        boundaries = boundary_detector.detect_file(temp_bugreport)
        
        assert len(boundaries) > 0
        
        section_detector = SectionDetector(boundaries)
        sections = section_detector.detect()
        
        assert len(sections) > 0
        
        tree = build_section_tree(sections)
        
        assert len(tree) > 0
        
        keywords = extract_preset_keywords(config)
        
        assert "anr" in keywords
        assert "crash" in keywords
        
        builder = PresetIndexBuilder(temp_bugreport, keywords)
        index = builder.build()
        
        assert "anr" in index
        assert "crash" in index
        
        qi = QueryInterface(temp_bugreport, temp_config)
        qi.preset_index = index
        
        results = qi.query("ANR")
        
        assert len(results) > 0
        
        assert qi.is_preset("ANR") == True
        assert qi.is_preset("com.newapp") == False

    def test_query_preset_from_index(self, temp_bugreport, temp_config):
        """T11.2: Query preset keyword uses index"""
        
        config_loader = ConfigLoader(temp_config)
        config = config_loader.load()
        
        keywords = extract_preset_keywords(config)
        
        builder = PresetIndexBuilder(temp_bugreport, keywords)
        index = builder.build()
        
        qi = QueryInterface(temp_bugreport, temp_config)
        qi.preset_index = index
        
        results = qi.query("ANR")
        
        assert len(results) >= 1
        assert any(r.keyword.lower() == "anr" for r in results)

    def test_query_custom_fallback(self, temp_bugreport, temp_config):
        """T11.3: Query custom keyword falls back to full scan"""
        
        qi = QueryInterface(temp_bugreport, temp_config)
        qi.preset_index = {}
        
        results = qi.query("com.example.app")
        
        assert len(results) > 0

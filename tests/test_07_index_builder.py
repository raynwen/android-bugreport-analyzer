# Test for Task 7: Preset Index Builder

import pytest
import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.index_builder import PresetIndexBuilder


class TestPresetIndexBuilder:
    """Test PresetIndexBuilder class"""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("normal line\n")
            f.write("ANR occurred here\n")
            f.write("crash detected\n")
            f.write("OOM error\n")
            f.write("another line\n")
            f.write("ANR again\n")
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)

    def test_build_basic_index(self, temp_file):
        """T7.1: Build basic index"""
        keywords = {"anr", "crash", "oom"}
        
        builder = PresetIndexBuilder(temp_file, keywords)
        index = builder.build()
        
        assert "anr" in index
        assert len(index["anr"]) == 2
        assert "crash" in index
        assert len(index["crash"]) == 1

    def test_case_insensitive(self, temp_file):
        """T7.2: Keywords are case insensitive"""
        keywords = {"anr", "crash"}
        
        builder = PresetIndexBuilder(temp_file, keywords)
        index = builder.build()
        
        assert "anr" in index
        assert "crash" in index

    def test_empty_keywords(self, temp_file):
        """T7.3: Empty keywords returns empty index"""
        keywords = set()
        
        builder = PresetIndexBuilder(temp_file, keywords)
        index = builder.build()
        
        assert index == {}

    def test_save_and_load(self, temp_file):
        """T7.4: Save and load index"""
        keywords = {"anr", "crash"}
        
        builder = PresetIndexBuilder(temp_file, keywords)
        index = builder.build()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_json = f.name
        
        try:
            builder.save(temp_json)
            loaded = PresetIndexBuilder.load(temp_json)
            
            assert loaded == index
        finally:
            os.unlink(temp_json)

    def test_partial_match(self, temp_file):
        """Keywords match partial content"""
        keywords = {"an"}
        
        builder = PresetIndexBuilder(temp_file, keywords)
        index = builder.build()
        
        assert len(index["an"]) >= 2

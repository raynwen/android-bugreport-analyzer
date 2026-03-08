# Test for Task 9: Custom Query

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.custom_query import query_custom


class TestCustomQuery:
    """Test query_custom function"""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("normal line\n")
            f.write("com.example.app activity\n")
            f.write("com.example.app crash\n")
            f.write("com.other.app run\n")
            f.write("another line\n")
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)

    def test_query_existing_keyword(self, temp_file):
        """T9.1: Query existing keyword"""
        results = query_custom("com.example.app", temp_file)
        
        assert len(results) == 2

    def test_query_nonexistent_keyword(self, temp_file):
        """T9.2: Query nonexistent keyword"""
        results = query_custom("nonexistent", temp_file)
        
        assert len(results) == 0

    def test_partial_match(self, temp_file):
        """T9.3: Partial match works"""
        results = query_custom("example", temp_file)
        
        assert len(results) == 2

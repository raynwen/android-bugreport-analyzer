# Test for Task 8: Preset Query

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.preset_query import QueryResult, query_preset


class TestQueryResult:
    """Test QueryResult class"""

    def test_create_result(self):
        """Create QueryResult"""
        result = QueryResult(line_number=10, content="ANR occurred", keyword="anr")
        
        assert result.line_number == 10
        assert result.content == "ANR occurred"
        assert result.keyword == "anr"


class TestQueryPreset:
    """Test query_preset function"""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("normal line\n")
            f.write("ANR occurred\n")
            f.write("crash detected\n")
            f.write("OOM error\n")
            f.write("another line\n")
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)

    def test_query_existing_keyword(self, temp_file):
        """T8.1: Query existing keyword"""
        index = {"anr": [2]}
        
        results = query_preset("anr", index, temp_file)
        
        assert len(results) == 1
        assert results[0].line_number == 2

    def test_query_nonexistent_keyword(self, temp_file):
        """T8.2: Query nonexistent keyword"""
        index = {"anr": [2]}
        
        results = query_preset("crash", index, temp_file)
        
        assert len(results) == 0

    def test_case_insensitive(self, temp_file):
        """T8.3: Query is case insensitive"""
        index = {"anr": [2]}
        
        results = query_preset("ANR", index, temp_file)
        
        assert len(results) == 1

    def test_results_sorted(self, temp_file):
        """T8.4: Results are sorted by line number"""
        index = {"anr": [10, 2, 5]}
        
        results = query_preset("anr", index, temp_file)
        
        line_nums = [r.line_number for r in results]
        assert line_nums == sorted(line_nums)

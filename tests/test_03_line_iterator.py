# Test for Task 3: Line Iterator

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.line_iterator import LineIterator


class TestLineIterator:
    """Test LineIterator class"""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary test file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Line 1 content\n")
            f.write("Line 2 content\n")
            f.write("Line 3 content\n")
            f.write("Line 4 content\n")
            f.write("Line 5 content\n")
            temp_path = f.name
        
        yield temp_path
        os.unlink(temp_path)

    def test_basic_iteration(self, temp_file):
        """T3.1: Basic iteration returns (line_num, content)"""
        iterator = LineIterator(temp_file)
        
        lines = list(iterator)
        
        assert len(lines) == 5
        assert lines[0] == (1, "Line 1 content")
        assert lines[1] == (2, "Line 2 content")

    def test_iteration_with_strip(self, temp_file):
        """Verify newline characters are stripped"""
        iterator = LineIterator(temp_file)
        
        for line_num, line in iterator:
            assert not line.endswith('\n')
            assert not line.endswith('\r')

    def test_iter_lines_range(self, temp_file):
        """T3.2: Iterate specific line range"""
        iterator = LineIterator(temp_file)
        
        lines = list(iterator.iter_lines(2, 4))
        
        assert len(lines) == 3
        assert lines[0] == (2, "Line 2 content")
        assert lines[1] == (3, "Line 3 content")
        assert lines[2] == (4, "Line 4 content")

    def test_iter_lines_out_of_range(self, temp_file):
        """Iterating beyond file bounds should work"""
        iterator = LineIterator(temp_file)
        
        lines = list(iterator.iter_lines(10, 20))
        
        assert len(lines) == 0

    def test_count_lines(self, temp_file):
        """T3.3: Count total lines"""
        iterator = LineIterator(temp_file)
        
        count = iterator.count_lines()
        
        assert count == 5

    def test_empty_file(self):
        """T3.4: Handle empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            iterator = LineIterator(temp_path)
            lines = list(iterator)
            
            assert len(lines) == 0
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """T3.5: File not found raises error"""
        iterator = LineIterator("nonexistent_file.txt")
        
        with pytest.raises(FileNotFoundError):
            list(iterator)

    def test_large_file_no_memory_overflow(self):
        """T3.3: Large file should not load all into memory"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for i in range(10000):
                f.write(f"Line {i} content\n")
            temp_path = f.name
        
        try:
            iterator = LineIterator(temp_path)
            
            first_line = None
            for line_num, line in iterator:
                first_line = (line_num, line)
                break
            
            assert first_line is not None
            assert first_line[0] == 1
        finally:
            os.unlink(temp_path)

    def test_custom_encoding(self):
        """Test with custom encoding"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Unicode content: 你好世界\n")
            temp_path = f.name
        
        try:
            iterator = LineIterator(temp_path, encoding='utf-8')
            lines = list(iterator)
            
            assert "Unicode content: 你好世界" in lines[0][1]
        finally:
            os.unlink(temp_path)


class TestLineIteratorEdgeCases:
    """Test edge cases"""

    def test_file_with_only_newlines(self):
        """File with only newlines"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("\n\n\n")
            temp_path = f.name
        
        try:
            iterator = LineIterator(temp_path)
            lines = list(iterator)
            
            assert len(lines) == 3
        finally:
            os.unlink(temp_path)

    def test_very_long_line(self):
        """Very long single line"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("x" * 10000 + "\n")
            temp_path = f.name
        
        try:
            iterator = LineIterator(temp_path)
            lines = list(iterator)
            
            assert len(lines[0][1]) == 10000
        finally:
            os.unlink(temp_path)

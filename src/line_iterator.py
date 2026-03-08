"""
Task 3: Line Iterator
Author: 闫文峰

Provides streaming line-by-line iteration for large files without loading all into memory.
"""

from typing import Iterator, Tuple, Optional
import os


class LineIterator:
    """
    Stream-based line iterator for large files.
    
    Iterates through a file line by line without loading the entire file
    into memory, making it suitable for processing large bug report files.
    """
    
    def __init__(self, file_path: str, encoding: str = 'utf-8') -> None:
        """
        Initialize the line iterator.
        
        Args:
            file_path: Path to the file to iterate
            encoding: File encoding, default 'utf-8'
        """
        self._file_path = file_path
        self._encoding = encoding
    
    @property
    def file_path(self) -> str:
        """Get the file path."""
        return self._file_path
    
    def __iter__(self) -> Iterator[Tuple[int, str]]:
        """
        Iterate through all lines in the file.
        
        Yields:
            Tuple of (line_number, line_content)
        """
        with open(self._file_path, 'r', encoding=self._encoding, errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                yield line_num, line.rstrip('\n\r')
    
    def iter_lines(self, start: int, end: int) -> Iterator[Tuple[int, str]]:
        """
        Iterate through a specific range of lines.
        
        Args:
            start: Starting line number (1-indexed)
            end: Ending line number (inclusive)
            
        Yields:
            Tuple of (line_number, line_content) within the range
        """
        with open(self._file_path, 'r', encoding=self._encoding, errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if start <= line_num <= end:
                    yield line_num, line.rstrip('\n\r')
                elif line_num > end:
                    break
    
    def count_lines(self) -> int:
        """
        Count total number of lines in the file.
        
        Returns:
            Total line count
        """
        count = 0
        with open(self._file_path, 'r', encoding=self._encoding, errors='ignore') as f:
            for _ in f:
                count += 1
        return count
    
    def read_line(self, line_number: int) -> Optional[str]:
        """
        Read a specific line by number.
        
        Args:
            line_number: Line number to read (1-indexed)
            
        Returns:
            Line content or None if line doesn't exist
        """
        with open(self._file_path, 'r', encoding=self._encoding, errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line_num == line_number:
                    return line.rstrip('\n\r')
                elif line_num > line_number:
                    break
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python line_iterator.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    try:
        iterator = LineIterator(file_path)
        
        print(f"Total lines: {iterator.count_lines()}")
        print("\nFirst 10 lines:")
        
        for line_num, line in iterator:
            if line_num > 10:
                break
            print(f"  {line_num}: {line[:80]}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

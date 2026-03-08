"""
Task 7 Enhanced: Index Builder with Line Offsets
Author: Yan Wenfeng

Build preset keyword index with line byte offsets for O(1) random access.
"""

import json
from typing import Dict, List, Set, Optional
from pathlib import Path


class EnhancedIndexBuilder:
    """
    Build enhanced index with line byte offsets for fast random access.
    
    Index structure:
    {
        "keywords": {
            "anr": [78054, 78123, ...],
            "crash": [77593, ...],
            ...
        },
        "line_offsets": [0, 125, 256, ...]  # byte offset for each line
    }
    """
    
    def __init__(self, file_path: str, keywords: Set[str], max_lines: Optional[int] = None) -> None:
        """
        Initialize the index builder.
        
        Args:
            file_path: Path to bug report file
            keywords: Set of preset keywords to index
            max_lines: Maximum number of lines to process (for testing)
        """
        self._file_path = file_path
        self._keywords = {kw.lower() for kw in keywords}
        self._keyword_index: Dict[str, List[int]] = {kw: [] for kw in self._keywords}
        self._line_offsets: List[int] = []
        self._max_lines = max_lines
    
    def build(self) -> Dict:
        """
        Build the enhanced index.
        
        Uses text mode to ensure line numbers match the section detector.
        However, we need byte offsets for O(1) random access.
        
        Solution: Build a mapping from text-mode line numbers to byte offsets.
        Text mode treats \r, \n, \r\n as line separators.
        
        Returns:
            Dictionary with keywords index and line offsets
        """
        with open(self._file_path, 'rb') as f:
            content = f.read()
        
        total_bytes = len(content)
        line_num = 0
        offset = 0
        
        while offset < total_bytes:
            self._line_offsets.append(offset)
            
            line_end = offset
            while line_end < total_bytes:
                ch = content[line_end:line_end+1]
                if ch == b'\n':
                    line_end += 1
                    break
                elif ch == b'\r':
                    if line_end + 1 < total_bytes and content[line_end+1:line_end+2] == b'\n':
                        line_end += 2
                    else:
                        line_end += 1
                    break
                line_end += 1
            
            line_bytes = content[offset:line_end]
            
            try:
                line = line_bytes.decode('utf-8', errors='ignore')
            except:
                line = ''
            
            line_lower = line.lower()
            for kw in self._keywords:
                if kw in line_lower:
                    self._keyword_index[kw].append(line_num + 1)
            
            line_num += 1
            offset = line_end
            
            if self._max_lines and line_num >= self._max_lines:
                break
        
        return {
            'keywords': self._keyword_index,
            'line_offsets': self._line_offsets,
            'total_lines': line_num
        }
    
    def save(self, output_path: str) -> None:
        """
        Save the index to a JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        index = self.build()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index, f)
    
    @staticmethod
    def load(index_path: str) -> Dict:
        """
        Load index from JSON file.
        
        Args:
            index_path: Path to index JSON file
            
        Returns:
            Index dictionary
        """
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)


class EnhancedPresetQuery:
    """
    Fast preset query using line offsets for O(1) random access.
    """
    
    def __init__(self, file_path: str, index: Dict) -> None:
        """
        Initialize the query engine.
        
        Args:
            file_path: Path to bug report file
            index: Pre-built enhanced index
        """
        self._file_path = file_path
        self._keywords_index = index.get('keywords', {})
        self._line_offsets = index.get('line_offsets', [])
    
    def query(self, keyword: str) -> List[Dict]:
        """
        Query for a keyword using line offsets.
        
        Args:
            keyword: Keyword to search
            
        Returns:
            List of results with line_number and content
        """
        keyword_lower = keyword.lower()
        
        if keyword_lower not in self._keywords_index:
            return []
        
        line_nums = self._keywords_index[keyword_lower]
        results = []
        
        with open(self._file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num in line_nums:
                if 1 <= line_num <= len(self._line_offsets):
                    offset = self._line_offsets[line_num - 1]
                    f.seek(offset)
                    content = f.readline().rstrip('\n\r')
                    results.append({
                        'line_number': line_num,
                        'content': content,
                        'keyword': keyword
                    })
        
        return results


if __name__ == "__main__":
    import sys
    import time
    
    if len(sys.argv) < 3:
        print("Usage: python enhanced_index.py <file_path> <output_path> [keywords...]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_path = sys.argv[2]
    keywords = set(sys.argv[3:]) if len(sys.argv) > 3 else {'anr', 'crash', 'error'}
    
    print(f"Building enhanced index for {file_path}...")
    start = time.time()
    
    builder = EnhancedIndexBuilder(file_path, keywords)
    builder.save(output_path)
    
    elapsed = time.time() - start
    print(f"Done in {elapsed:.2f}s")
    print(f"Index saved to {output_path}")

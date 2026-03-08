"""
Task 10: Query Interface
Author: 闫文峰

Unified query interface with preset/custom keyword detection.
"""

import json
from typing import List, Dict, Optional, Set

from src.config_loader import ConfigLoader
from src.keyword_extractor import extract_preset_keywords
from src.preset_query import query_preset, QueryResult
from src.custom_query import query_custom


class QueryInterface:
    """
    Unified query interface for bug report analysis.
    
    Automatically determines whether to use preset index or custom scan
    based on whether the keyword is defined in the YAML configuration.
    """
    
    def __init__(
        self, 
        file_path: str, 
        config_path: str,
        index_path: Optional[str] = None
    ) -> None:
        """
        Initialize the query interface.
        
        Args:
            file_path: Path to bug report file
            config_path: Path to YAML configuration
            index_path: Optional path to preset index file
        """
        self._file_path = file_path
        self._config = ConfigLoader(config_path).load()
        self._preset_keywords = extract_preset_keywords(self._config)
        
        if index_path:
            with open(index_path, 'r') as f:
                self._preset_index: Dict[str, List[int]] = json.load(f)
        else:
            self._preset_index = {}
    
    @property
    def file_path(self) -> str:
        """Get the file path."""
        return self._file_path
    
    @property
    def preset_keywords(self) -> Set[str]:
        """Get preset keywords."""
        return self._preset_keywords
    
    @property
    def preset_index(self) -> Dict[str, List[int]]:
        """Get preset index."""
        return self._preset_index
    
    @preset_index.setter
    def preset_index(self, value: Dict[str, List[int]]) -> None:
        """Set preset index."""
        self._preset_index = value
    
    def is_preset(self, keyword: str) -> bool:
        """
        Check if keyword is a preset keyword.
        
        Args:
            keyword: Keyword to check
            
        Returns:
            True if keyword is in YAML configuration
        """
        return keyword.lower() in self._preset_keywords
    
    def query(self, keyword: str) -> List[QueryResult]:
        """
        Query for a keyword.
        
        Automatically determines whether to use preset index or custom scan.
        
        Args:
            keyword: Keyword to search
            
        Returns:
            List of QueryResult objects
        """
        keyword_lower = keyword.lower()
        
        if keyword_lower in self._preset_keywords:
            if keyword_lower in self._preset_index:
                return query_preset(keyword, self._preset_index, self._file_path)
            else:
                return query_custom(keyword, self._file_path)
        else:
            return query_custom(keyword, self._file_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python query_interface.py <keyword> <file_path> [config_path] [index_path]")
        sys.exit(1)
    
    keyword = sys.argv[1]
    file_path = sys.argv[2]
    config_path = sys.argv[3] if len(sys.argv) > 3 else "boundary_patterns.yaml"
    index_path = sys.argv[4] if len(sys.argv) > 4 else None
    
    qi = QueryInterface(file_path, config_path, index_path)
    
    print(f"Keyword '{keyword}' is preset: {qi.is_preset(keyword)}")
    
    results = qi.query(keyword)
    
    print(f"\n✓ Found {len(results)} matches:\n")
    
    for result in results[:10]:
        print(f"  L{result.line_number}: {result.content[:80]}")
    
    if len(results) > 10:
        print(f"\n  ... and {len(results) - 10} more")

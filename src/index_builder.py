"""
Task 7: Preset Index Builder
Author: 闫文峰

Builds line number indexes for preset keywords.
"""

import json
from typing import Dict, List, Set
from collections import defaultdict

from src.line_iterator import LineIterator


class PresetIndexBuilder:
    """
    Builds line number indexes for preset keywords.
    
    Scans through the file once and creates an index mapping
    keywords to the line numbers where they appear.
    """
    
    def __init__(self, file_path: str, keywords: Set[str]) -> None:
        """
        Initialize the index builder.
        
        Args:
            file_path: Path to the bug report file
            keywords: Set of keywords to index
        """
        self._file_path = file_path
        self._keywords = keywords
        self._index: Dict[str, List[int]] = {}
    
    @property
    def file_path(self) -> str:
        """Get the file path."""
        return self._file_path
    
    @property
    def keywords(self) -> Set[str]:
        """Get the keywords."""
        return self._keywords
    
    def build(self) -> Dict[str, List[int]]:
        """
        Build the index.
        
        Returns:
            Dictionary mapping keyword -> list of line numbers
        """
        self._index = defaultdict(list)
        
        iterator = LineIterator(self._file_path)
        
        for line_num, line in iterator:
            line_lower = line.lower()
            
            for keyword in self._keywords:
                if keyword in line_lower:
                    self._index[keyword].append(line_num)
        
        return dict(self._index)
    
    def save(self, output_path: str) -> None:
        """
        Save index to JSON file.
        
        Args:
            output_path: Path to output file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dict(self._index), f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def load(input_path: str) -> Dict[str, List[int]]:
        """
        Load index from JSON file.
        
        Args:
            input_path: Path to index file
            
        Returns:
            Dictionary mapping keyword -> list of line numbers
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)


if __name__ == "__main__":
    import sys
    from src.keyword_extractor import extract_preset_keywords
    from src.config_loader import load_yaml_config
    
    if len(sys.argv) < 2:
        print("Usage: python index_builder.py <file_path> [config_path] [output_path]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else "boundary_patterns.yaml"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "preset_index.json"
    
    config = load_yaml_config(config_path)
    keywords = extract_preset_keywords(config)
    
    print(f"Building index for {len(keywords)} keywords...")
    
    builder = PresetIndexBuilder(file_path, keywords)
    index = builder.build()
    
    builder.save(output_path)
    
    print(f"✓ Index built with {len(index)} keywords")
    print(f"✓ Saved to {output_path}")

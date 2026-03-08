"""
Task 2: Boundary Separator Detection
Author: 闫文峰

Detects boundary separators in bug report files using regex patterns.
"""

import re
from typing import Dict, List, Tuple


class BoundaryDetector:
    """
    Detects boundary separators in bug report files.
    
    Uses regex patterns from configuration to identify section boundaries,
    duration markers, and other structural elements.
    """
    
    def __init__(self, boundary_config: Dict[str, Dict]) -> None:
        """
        Initialize the boundary detector.
        
        Args:
            boundary_config: Dictionary mapping marker names to their configurations
        """
        self._patterns: Dict[str, re.Pattern] = {}
        
        for name, config in boundary_config.items():
            pattern_str = config.get("pattern", "")
            if pattern_str:
                self._patterns[name] = re.compile(pattern_str)
    
    @property
    def patterns(self) -> Dict[str, re.Pattern]:
        """Get compiled regex patterns."""
        return self._patterns
    
    def detect(self, line: str) -> List[str]:
        """
        Detect if a line matches any boundary separator.
        
        Args:
            line: Line content to check
            
        Returns:
            List of matched boundary types
        """
        if not line:
            return []
        
        line = line.strip()
        if not line:
            return []
        
        matched = []
        
        for name, pattern in self._patterns.items():
            if pattern.match(line):
                matched.append(name)
        
        return matched
    
    def detect_file(self, file_path: str) -> List[Tuple[int, str, List[str]]]:
        """
        Detect all boundary separators in a file.
        
        Args:
            file the bug report file
            
_path: Path to        Returns:
            List of tuples: (line_number, line_content, matched_types)
        """
        results: List[Tuple[int, str, List[str]]] = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n\r')
                matches = self.detect(line)
                
                if matches:
                    results.append((line_num, line, matches))
        
        return results
    
    def detect_iter(self, lines: List[str]) -> List[Tuple[int, str, List[str]]]:
        """
        Detect boundary separators from a list of lines.
        
        Args:
            lines: List of lines to check
            
        Returns:
            List of tuples: (line_number, line_content, matched_types)
        """
        results: List[Tuple[int, str, List[str]]] = []
        
        for line_num, line in enumerate(lines, 1):
            matches = self.detect(line)
            
            if matches:
                results.append((line_num, line, matches))
        
        return results


def create_detector_from_config(config_path: str) -> BoundaryDetector:
    """
    Create a BoundaryDetector from a config file.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Configured BoundaryDetector instance
    """
    from src.config_loader import ConfigLoader
    
    loader = ConfigLoader(config_path)
    config = loader.load()
    
    return BoundaryDetector(loader.get_boundary_markers())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python boundary_detector.py <file_path> [config_path]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else "boundary_patterns.yaml"
    
    try:
        detector = create_detector_from_config(config_path)
        results = detector.detect_file(file_path)
        
        print(f"✓ Found {len(results)} boundary separators")
        
        for line_num, line, matches in results[:10]:
            print(f"  Line {line_num}: {matches} - {line[:50]}")
        
        if len(results) > 10:
            print(f"  ... and {len(results) - 10} more")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

"""
Subsection Detector
Author: Yan Wenfeng

Detects Level 2 subsections within dumpsys sections.
Handles patterns like "ACTIVITY MANAGER MARs", "ACTIVITY MANAGER BROADCAST STATE", etc.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Subsection:
    """
    Represents a subsection within a main section.
    
    Attributes:
        name: Subsection name
        start_line: Starting line number
        end_line: Ending line number
        pattern: Pattern that matched this subsection
        priority: Priority level from config
        category: Category from config
        parent_section: Name of parent section
    """
    name: str
    start_line: int
    end_line: int
    pattern: str
    priority: str = "MEDIUM"
    category: str = "unknown"
    parent_section: str = ""
    
    def __repr__(self) -> str:
        return f"Subsection({self.name}, L{self.start_line}-{self.end_line})"


class SubsectionDetector:
    """
    Detects subsections within dumpsys sections.
    
    Uses subsection patterns from YAML configuration to identify
    Level 2 sections like "ACTIVITY MANAGER MARs", "ACTIVITY MANAGER BROADCAST STATE", etc.
    """
    
    def __init__(self, subsection_config: List[Dict]) -> None:
        """
        Initialize the subsection detector.
        
        Args:
            subsection_config: List of subsection configurations from YAML
        """
        self._patterns: List[Tuple[str, re.Pattern, Dict]] = []
        
        for subsection in subsection_config:
            pattern_str = subsection.get("pattern", "")
            if pattern_str:
                compiled = re.compile(re.escape(pattern_str), re.IGNORECASE)
                self._patterns.append((
                    subsection.get("name", ""),
                    compiled,
                    {
                        "priority": subsection.get("priority", "MEDIUM"),
                        "category": subsection.get("category", "unknown"),
                        "original_pattern": pattern_str
                    }
                ))
    
    def detect_in_range(
        self, 
        file_path: str, 
        start_line: int, 
        end_line: int,
        parent_section: str = ""
    ) -> List[Subsection]:
        """
        Detect subsections within a line range.
        
        Args:
            file_path: Path to bug report file
            start_line: Start line of parent section
            end_line: End line of parent section
            parent_section: Name of parent section
            
        Returns:
            List of detected Subsection objects
        """
        subsections: List[Subsection] = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line_num < start_line:
                    continue
                if line_num > end_line:
                    break
                
                line = line.rstrip('\n\r')
                
                for name, pattern, meta in self._patterns:
                    if pattern.search(line):
                        subsections.append(Subsection(
                            name=name or meta["original_pattern"],
                            start_line=line_num,
                            end_line=0,
                            pattern=meta["original_pattern"],
                            priority=meta["priority"],
                            category=meta["category"],
                            parent_section=parent_section
                        ))
                        break
        
        for i, sub in enumerate(subsections):
            if i + 1 < len(subsections):
                sub.end_line = subsections[i + 1].start_line - 1
            else:
                sub.end_line = end_line
        
        return subsections
    
    def detect_all(
        self, 
        file_path: str, 
        sections: List[Dict]
    ) -> List[Subsection]:
        """
        Detect subsections in all sections that have subsection config.
        
        Args:
            file_path: Path to bug report file
            sections: List of main sections with subsection configs
            
        Returns:
            List of all detected Subsection objects
        """
        all_subsections: List[Subsection] = []
        
        for section in sections:
            if "subsections" in section:
                detector = SubsectionDetector(section["subsections"])
                subs = detector.detect_in_range(
                    file_path,
                    section.get("start_line", 0),
                    section.get("end_line", 0),
                    section.get("name", "")
                )
                all_subsections.extend(subs)
        
        return all_subsections


def extract_subsections_from_config(config: Dict) -> List[Dict]:
    """
    Extract all subsection configurations from YAML config.
    
    Args:
        config: Loaded YAML configuration
        
    Returns:
        List of subsection configurations
    """
    subsections = []
    
    record_types = config.get("record_types", {})
    
    if isinstance(record_types, dict):
        for name, rt_config in record_types.items():
            if isinstance(rt_config, dict) and "subsections" in rt_config:
                for sub in rt_config["subsections"]:
                    sub["parent_record_type"] = name
                    subsections.append(sub)
    
    return subsections


def detect_subsections_from_file(
    file_path: str, 
    config: Dict,
    start_line: int = 0,
    end_line: int = 0
) -> List[Subsection]:
    """
    Convenience function to detect subsections from a file.
    
    Args:
        file_path: Path to bug report file
        config: Loaded YAML configuration
        start_line: Optional start line (0 = from beginning)
        end_line: Optional end line (0 = to end)
        
    Returns:
        List of detected Subsection objects
    """
    if end_line == 0:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                pass
            end_line = line_num if 'line_num' in dir() else 10000000
    
    subsections_config = extract_subsections_from_config(config)
    detector = SubsectionDetector(subsections_config)
    
    return detector.detect_in_range(file_path, start_line, end_line)


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python subsection_detector.py <file_path> [config_path]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else "boundary_patterns.yaml"
    
    try:
        from src.config_loader import ConfigLoader
        
        loader = ConfigLoader(config_path)
        config = loader.load()
        
        print("Detecting subsections...")
        
        subsections = detect_subsections_from_file(file_path, config)
        
        print(f"\n[OK] Found {len(subsections)} subsections\n")
        
        for sub in subsections[:30]:
            print(f"  L{sub.start_line}-{sub.end_line}: {sub.name} [{sub.priority}]")
        
        if len(subsections) > 30:
            print(f"\n  ... and {len(subsections) - 30} more")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

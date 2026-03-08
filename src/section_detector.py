"""
Task 4: Section Detector (Enhanced with Subsection Support)
Author: Yan Wenfeng

Detects and marks section boundaries in bug report files.
Supports both Level 1 (main sections) and Level 2 (subsections) detection.
"""

import re
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class Section:
    """
    Represents a section in the bug report.
    
    Attributes:
        name: Section name
        start_line: Starting line number
        end_line: Ending line number
        section_type: Type of boundary marker
        level: Hierarchical level (1=root, 2=chapter, 3=subsection)
        priority: Priority level
        category: Category
    """
    name: str
    start_line: int
    end_line: int
    section_type: str
    level: int = 1
    priority: str = "MEDIUM"
    category: str = "unknown"
    
    def __repr__(self) -> str:
        return f"Section({self.name}, L{self.start_line}-{self.end_line})"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "section_type": self.section_type,
            "level": self.level,
            "priority": self.priority,
            "category": self.category
        }


class SectionDetector:
    """
    Detects sections in bug report files based on boundary markers.
    
    Uses boundary detection results to identify section start/end positions
    and extract section names and hierarchy levels.
    """
    
    def __init__(self, boundary_results: List[Tuple[int, str, List[str]]]) -> None:
        """
        Initialize the section detector.
        
        Args:
            boundary_results: List of (line_number, line_content, matched_types)
        """
        self._boundaries = boundary_results
    
    def detect(self) -> List[Section]:
        """
        Detect all sections from boundary results.
        
        Returns:
            List of Section objects with start/end lines and metadata
        """
        sections: List[Section] = []
        
        for i, (line_num, line_content, match_types) in enumerate(self._boundaries):
            if self._is_start_marker(match_types):
                section = self._parse_section(line_num, line_content, match_types)
                if section:
                    sections.append(section)
        
        for i, section in enumerate(sections):
            if i + 1 < len(sections):
                section.end_line = sections[i + 1].start_line - 1
            else:
                section.end_line = 0
        
        return sections
    
    def _is_start_marker(self, match_types: List[str]) -> bool:
        """Check if matched types indicate a section start (not an end marker)"""
        for marker_type in match_types:
            if "duration_marker" in marker_type:
                return False
        return True
    
    def _parse_section(self, line_num: int, line_content: str, 
                      match_types: List[str]) -> Optional[Section]:
        """Parse a boundary line into a Section object"""
        name = self._extract_name(line_content, match_types)
        
        if not name:
            return None
        
        level = self._get_level(line_content, match_types)
        
        return Section(
            name=name,
            start_line=line_num,
            end_line=0,
            section_type=match_types[0] if match_types else "unknown",
            level=level
        )
    
    def _extract_name(self, line: str, match_types: List[str]) -> str:
        """Extract section name from boundary line"""
        line = line.strip()
        
        if "equals_separator" in match_types:
            return "HEADER"
        
        if "dash_separator" in match_types:
            match = re.match(r"^------\s+(.+?)\s+------$", line)
            if match:
                return match.group(1).strip()
            
            match = re.match(r"^------\s+(.+)\s*$", line)
            if match:
                name = match.group(1).strip()
                name = re.sub(r"\s*\(.*?\)\s*$", "", name)
                return name
        
        if "equals_with_text" in match_types:
            match = re.match(r"^=+\s+(.+?)\s+=+$", line)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _get_level(self, line: str, match_types: List[str]) -> int:
        """Determine section hierarchy level"""
        if "equals_separator" in match_types:
            return 1
        
        if "equals_with_text" in match_types:
            return 1
        
        if "dash_separator" in match_types:
            return 2
        
        return 1


class SubsectionDetector:
    """
    Detects Level 2 subsections within main sections.
    
    Uses subsection patterns from YAML configuration to identify
    sections like "ACTIVITY MANAGER MARs", "ACTIVITY MANAGER BROADCAST STATE", etc.
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
                    subsection.get("name", pattern_str),
                    compiled,
                    {
                        "priority": subsection.get("priority", "MEDIUM"),
                        "category": subsection.get("category", "unknown"),
                        "original_pattern": pattern_str
                    }
                ))
    
    def detect_in_file(
        self, 
        file_path: str, 
        start_line: int = 0, 
        end_line: int = 0,
        parent_section: str = ""
    ) -> List[Section]:
        """
        Detect subsections within a file or line range.
        
        Args:
            file_path: Path to bug report file
            start_line: Start line (0 = from beginning)
            end_line: End line (0 = to end)
            parent_section: Name of parent section
            
        Returns:
            List of Section objects (level=3 for subsections)
        """
        subsections: List[Section] = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if start_line > 0 and line_num < start_line:
                    continue
                if end_line > 0 and line_num > end_line:
                    break
                
                line = line.rstrip('\n\r')
                
                for name, pattern, meta in self._patterns:
                    if pattern.search(line):
                        subsections.append(Section(
                            name=name,
                            start_line=line_num,
                            end_line=0,
                            section_type="subsection",
                            level=3,
                            priority=meta["priority"],
                            category=meta["category"]
                        ))
                        break
        
        for i, sub in enumerate(subsections):
            if i + 1 < len(subsections):
                sub.end_line = subsections[i + 1].start_line - 1
            elif end_line > 0:
                sub.end_line = end_line
        
        return subsections


def extract_subsections_config(config: Dict) -> List[Dict]:
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
                    sub_copy = dict(sub)
                    sub_copy["parent_record_type"] = name
                    subsections.append(sub_copy)
    
    return subsections


def detect_all_sections(
    file_path: str, 
    boundary_config: Dict,
    subsection_config: List[Dict]
) -> List[Section]:
    """
    Detect all sections (Level 1 + Level 2) from a file.
    
    Args:
        file_path: Path to bug report file
        boundary_config: Boundary marker configuration
        subsection_config: Subsection configuration list
        
    Returns:
        List of all Section objects (main sections + subsections)
    """
    from src.boundary_detector import BoundaryDetector
    
    detector = BoundaryDetector(boundary_config)
    boundaries = detector.detect_file(file_path)
    
    section_detector = SectionDetector(boundaries)
    main_sections = section_detector.detect()
    
    subsection_detector = SubsectionDetector(subsection_config)
    subsections = subsection_detector.detect_in_file(file_path)
    
    all_sections = main_sections + subsections
    all_sections.sort(key=lambda s: s.start_line)
    
    return all_sections


def detect_sections_from_file(file_path: str, boundary_config: Dict) -> List[Section]:
    """
    Convenience function to detect sections from a file.
    
    Args:
        file_path: Path to bug report file
        boundary_config: Boundary marker configuration
        
    Returns:
        List of detected sections
    """
    from src.boundary_detector import BoundaryDetector
    
    detector = BoundaryDetector(boundary_config)
    boundaries = detector.detect_file(file_path)
    
    section_detector = SectionDetector(boundaries)
    return section_detector.detect()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python section_detector.py <file_path> [config_path]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else "boundary_patterns.yaml"
    
    try:
        from src.config_loader import ConfigLoader
        
        loader = ConfigLoader(config_path)
        config = loader.load()
        
        subsection_config = extract_subsections_config(config)
        
        print("Detecting all sections (Level 1 + Level 2)...")
        
        all_sections = detect_all_sections(
            file_path, 
            loader.get_boundary_markers(),
            subsection_config
        )
        
        print(f"\n[OK] Found {len(all_sections)} total sections\n")
        
        level1_count = sum(1 for s in all_sections if s.level <= 2)
        level3_count = sum(1 for s in all_sections if s.level == 3)
        
        print(f"  Level 1-2 (main sections): {level1_count}")
        print(f"  Level 3 (subsections): {level3_count}")
        
        print("\nFirst 30 sections:")
        for section in all_sections[:30]:
            indent = "  " * (section.level - 1)
            print(f"{indent}L{section.start_line}-{section.end_line}: {section.name} [{section.priority}]")
        
        if len(all_sections) > 30:
            print(f"\n  ... and {len(all_sections) - 30} more")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

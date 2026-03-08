# Test for Task 4: Section Detector

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.section_detector import Section, SectionDetector


class TestSection:
    """Test Section dataclass"""

    def test_section_creation(self):
        """Create a Section object"""
        section = Section(
            name="MEMORY INFO",
            start_line=10,
            end_line=20,
            section_type="dash_separator",
            level=2
        )
        
        assert section.name == "MEMORY INFO"
        assert section.start_line == 10
        assert section.end_line == 20
        assert section.section_type == "dash_separator"
        assert section.level == 2

    def test_section_repr(self):
        """Test Section __repr__"""
        section = Section("TEST", 1, 10, "type", 1)
        
        assert "TEST" in repr(section)
        assert "1-10" in repr(section)


class TestSectionDetector:
    """Test SectionDetector class"""

    def test_detect_sections_basic(self):
        """T4.1: Detect basic sections"""
        boundary_results = [
            (1, "=====================", ["equals_separator"]),
            (10, "------ MEMORY INFO ------", ["dash_separator"]),
            (20, "------ 5.234s was the duration of 'MEMORY INFO'", ["duration_marker_major"]),
            (30, "------ VIRTUAL MEMORY STATS ------", ["dash_separator"]),
            (40, "------ 3.100s was the duration of 'VIRTUAL MEMORY STATS'", ["duration_marker_major"]),
        ]
        
        detector = SectionDetector(boundary_results)
        sections = detector.detect()
        
        assert len(sections) >= 2
        assert sections[0].name == "HEADER"
        assert sections[0].start_line == 1
        assert sections[1].name == "MEMORY INFO"
        assert sections[1].start_line == 10
        assert sections[1].end_line == 29

    def test_section_level_detection(self):
        """T4.2: Detect section levels"""
        boundary_results = [
            (1, "==============================================", ["equals_separator"]),
            (10, "------ MEMORY INFO ------", ["dash_separator"]),
            (20, "------ 5.234s was the duration of", ["duration_marker_major"]),
        ]
        
        detector = SectionDetector(boundary_results)
        sections = detector.detect()
        
        assert sections[0].level == 1
        assert sections[1].level == 2

    def test_empty_boundaries(self):
        """T4.3: Handle empty boundary results"""
        detector = SectionDetector([])
        sections = detector.detect()
        
        assert sections == []

    def test_extract_section_name_dash(self):
        """Extract name from dash separator"""
        boundary_results = [
            (10, "------ MEMORY INFO ------", ["dash_separator"]),
        ]
        
        detector = SectionDetector(boundary_results)
        sections = detector.detect()
        
        assert len(sections) > 0
        assert sections[0].name == "MEMORY INFO"

    def test_extract_section_name_dumpsys(self):
        """Extract name from dumpsys section"""
        boundary_results = [
            (10, "------ MEMORY INFO (/proc/meminfo) ------", ["dash_separator"]),
        ]
        
        detector = SectionDetector(boundary_results)
        sections = detector.detect()
        
        assert len(sections) > 0
        assert "MEMORY INFO" in sections[0].name


class TestSectionDetectorWithRealData:
    """Test with realistic boundary data"""

    def test_detect_with_real_patterns(self):
        """T4.4: Detect sections with real bugreport patterns"""
        boundary_results = [
            (1, "========================================================", ["equals_separator"]),
            (5, "------ MEMORY INFO (/proc/meminfo) ------", ["dash_separator"]),
            (15, "------ 5.234s was the duration of 'MEMORY INFO'", ["duration_marker_major"]),
            (20, "------ VIRTUAL MEMORY STATS (/proc/vmstat) ------", ["dash_separator"]),
            (30, "------ 3.100s was the duration of 'VIRTUAL MEMORY STATS'", ["duration_marker_major"]),
            (35, "------ BINDER FAILED TRANSACTION LOG ------", ["dash_separator"]),
            (45, "------ 0.500s was the duration of 'BINDER FAILED TRANSACTION LOG'", ["duration_marker_major"]),
        ]
        
        detector = SectionDetector(boundary_results)
        sections = detector.detect()
        
        assert len(sections) == 4
        assert sections[0].name == "HEADER"
        assert "MEMORY INFO" in sections[1].name
        assert "VIRTUAL MEMORY" in sections[2].name
        assert "BINDER FAILED" in sections[3].name
        
        assert sections[1].end_line == 19
        assert sections[2].end_line == 34
        assert sections[3].end_line == 0

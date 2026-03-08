# Test for Task 2: Boundary Separator Detection

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.boundary_detector import BoundaryDetector


class TestBoundaryDetector:
    """Test BoundaryDetector class"""

    @pytest.fixture
    def sample_boundary_config(self):
        """Sample boundary configuration (matching real YAML patterns)"""
        return {
            "equals_separator": {
                "pattern": r"^={20,}$",
                "description": "Pure equals separator"
            },
            "equals_with_text": {
                "pattern": r"^=+ .+ =+$",
                "description": "Equals with text in middle"
            },
            "dash_separator": {
                "pattern": r"^------ .+ ------$",
                "description": "Dashes with text in middle"
            },
            "duration_marker_major": {
                "pattern": r"^------ \d+\.\d+s was the duration of",
                "description": "Duration marker (major sections)"
            },
            "duration_marker_dumpsys": {
                "pattern": r"^---------+ \d+\.\d+s was the duration of dumpsys",
                "description": "Duration marker (dumpsys sections)"
            }
        }

    def test_detect_equals_separator(self, sample_boundary_config):
        """T2.1: Detect equals separator (pure equals, no text)"""
        detector = BoundaryDetector(sample_boundary_config)
        
        line = "====================="
        matches = detector.detect(line)
        
        assert "equals_separator" in matches

    def test_detect_equals_separator_with_text(self, sample_boundary_config):
        """T2.1: Detect equals separator with text (real bugreport format)"""
        detector = BoundaryDetector(sample_boundary_config)
        
        line = "===================== dump state: starting ===================="
        matches = detector.detect(line)
        
        assert "equals_with_text" in matches

    def test_detect_dash_separator(self, sample_boundary_config):
        """T2.2: Detect dash separator (matching real pattern)"""
        detector = BoundaryDetector(sample_boundary_config)
        
        line = "------ MEMORY INFO ------"
        matches = detector.detect(line)
        
        assert "dash_separator" in matches

    def test_detect_duration_marker_major(self, sample_boundary_config):
        """T2.3: Detect duration marker (major)"""
        detector = BoundaryDetector(sample_boundary_config)
        
        line = "------ 5.234s was the duration of 'dumpsys activity'"
        matches = detector.detect(line)
        
        assert "duration_marker_major" in matches

    def test_detect_duration_marker_dumpsys(self, sample_boundary_config):
        """T2.3: Detect duration marker (dumpsys)"""
        detector = BoundaryDetector(sample_boundary_config)
        
        line = "--------- 0.123s was the duration of dumpsys"
        matches = detector.detect(line)
        
        assert "duration_marker_dumpsys" in matches

    def test_non_boundary_line(self, sample_boundary_config):
        """T2.4: Non-boundary line returns empty"""
        detector = BoundaryDetector(sample_boundary_config)
        
        line = "This is a normal content line"
        matches = detector.detect(line)
        
        assert matches == []

    def test_empty_line(self, sample_boundary_config):
        """T2.5: Empty line returns empty"""
        detector = BoundaryDetector(sample_boundary_config)
        
        matches = detector.detect("")
        
        assert matches == []

    def test_whitespace_line(self, sample_boundary_config):
        """T2.5: Whitespace-only line returns empty"""
        detector = BoundaryDetector(sample_boundary_config)
        
        matches = detector.detect("   ")
        
        assert matches == []

    def test_detect_file(self, sample_boundary_config):
        """Test detect_file method"""
        detector = BoundaryDetector(sample_boundary_config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("normal line 1\n")
            f.write("===================== dump state: starting ====================\n")
            f.write("normal line 2\n")
            f.write("------ MEMORY INFO ------\n")
            f.write("normal line 3\n")
            temp_path = f.name
        
        try:
            results = detector.detect_file(temp_path)
            
            assert len(results) >= 2
            line_nums = [r[0] for r in results]
            assert 2 in line_nums  # equals separator
            assert 4 in line_nums  # dash separator
        finally:
            os.unlink(temp_path)

    def test_strip_line_before_match(self, sample_boundary_config):
        """Verify line is stripped before matching"""
        detector = BoundaryDetector(sample_boundary_config)
        
        line = "   ====================   "
        matches = detector.detect(line)
        
        assert "equals_separator" in matches


class TestBoundaryDetectorWithRealConfig:
    """Test with real boundary_patterns.yaml"""

    @pytest.fixture
    def real_config_path(self):
        return os.path.join(
            os.path.dirname(__file__),
            "..",
            "boundary_patterns.yaml"
        )

    def test_load_real_boundaries(self, real_config_path):
        """T2.1: Load real boundary configuration"""
        if not os.path.exists(real_config_path):
            pytest.skip("Real config not found")
        
        from src.config_loader import ConfigLoader
        loader = ConfigLoader(real_config_path)
        config = loader.load()
        
        boundary_config = loader.get_boundary_markers()
        
        assert boundary_config is not None
        assert len(boundary_config) > 0

    def test_detect_real_patterns(self, real_config_path):
        """Test detection with real patterns"""
        if not os.path.exists(real_config_path):
            pytest.skip("Real config not found")
        
        from src.config_loader import ConfigLoader
        loader = ConfigLoader(real_config_path)
        loader.load()
        
        detector = BoundaryDetector(loader.get_boundary_markers())
        
        test_lines = [
            "========================================================",
            "------ MEMORY INFO ------",
            "------ 5.234s was the duration of 'dumpsys activity'",
        ]
        
        results = []
        for line in test_lines:
            matches = detector.detect(line)
            results.append((line, matches))
        
        assert len(results[0][1]) > 0, f"Failed to detect: {test_lines[0]}"
        assert len(results[1][1]) > 0, f"Failed to detect: {test_lines[1]}"
        assert len(results[2][1]) > 0, f"Failed to detect: {test_lines[2]}"

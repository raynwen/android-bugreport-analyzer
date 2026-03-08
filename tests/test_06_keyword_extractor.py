# Test for Task 6: Keyword Extractor

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.keyword_extractor import extract_preset_keywords, build_keyword_mapping


class TestExtractPresetKeywords:
    """Test extract_preset_keywords function"""

    def test_extract_from_record_types(self):
        """T6.1: Extract keywords from record_types"""
        config = {
            "record_types": [
                {"name": "anr", "keywords": ["ANR", "Application Not Responding"]},
                {"name": "crash", "keywords": ["crash", "FATAL"]},
            ]
        }
        
        keywords = extract_preset_keywords(config)
        
        assert "anr" in keywords
        assert "crash" in keywords

    def test_extract_from_subsections(self):
        """T6.2: Extract keywords from subsections"""
        config = {
            "record_types": [
                {
                    "name": "dumpsys",
                    "keywords": ["dumpsys"],
                    "subsections": [
                        {"name": "broadcasts", "keywords": ["broadcast", "BROADCAST STATE"]}
                    ]
                }
            ]
        }
        
        keywords = extract_preset_keywords(config)
        
        assert "broadcast" in keywords

    def test_extract_from_interest_points(self):
        """T6.3: Extract keywords from interest_points"""
        config = {
            "interest_points": [
                {"name": "oom", "keywords": ["OOM", "OutOfMemory"]},
                {"name": "binder_error", "keywords": ["binder error"]}
            ]
        }
        
        keywords = extract_preset_keywords(config)
        
        assert "oom" in keywords
        assert "binder error" in keywords

    def test_empty_config(self):
        """T6.4: Empty config returns empty set"""
        keywords = extract_preset_keywords({})
        
        assert keywords == set()

    def test_case_insensitive(self):
        """Keywords are lowercased"""
        config = {
            "record_types": [
                {"name": "anr", "keywords": ["ANR", "Anr"]}
            ]
        }
        
        keywords = extract_preset_keywords(config)
        
        assert "anr" in keywords
        assert len(keywords) == 1


class TestBuildKeywordMapping:
    """Test build_keyword_mapping function"""

    def test_map_record_types(self):
        """Map keywords to record types"""
        config = {
            "record_types": [
                {
                    "name": "anr",
                    "keywords": ["ANR"],
                    "category": "critical"
                }
            ]
        }
        
        mapping = build_keyword_mapping(config)
        
        assert "anr" in mapping
        assert mapping["anr"]["type"] == "record_type"
        assert mapping["anr"]["name"] == "anr"

    def test_map_subsections(self):
        """Map keywords to subsections"""
        config = {
            "record_types": [
                {
                    "name": "activity",
                    "keywords": ["activity"],
                    "subsections": [
                        {
                            "name": "broadcasts",
                            "keywords": ["broadcast"],
                            "category": "normal"
                        }
                    ]
                }
            ]
        }
        
        mapping = build_keyword_mapping(config)
        
        assert "broadcast" in mapping
        assert mapping["broadcast"]["type"] == "subsection"
        assert mapping["broadcast"]["name"] == "broadcasts"

"""
Android Bug Report Analyzer
Android Bug Report 全流程分析系统
"""

from pathlib import Path

SKILL_PATH = Path(__file__).parent

__version__ = "1.1.0"
__all__ = [
    "bugreport_extractor",
    "bugreport_parser", 
    "bugreport_analyzer",
    "bugreport_coordinator"
]

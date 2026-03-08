# Test for Task 5: Section Parser

import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.section_parser import SectionTree, build_section_tree
from src.section_detector import Section


class TestSectionTree:
    """Test SectionTree class"""

    def test_create_tree_node(self):
        """Create a SectionTree node"""
        section = Section("TEST", 1, 10, "type", 1)
        tree = SectionTree(section)
        
        assert tree.section.name == "TEST"
        assert tree.children == []

    def test_add_child(self):
        """Add child to tree"""
        parent_section = Section("Parent", 1, 20, "type", 1)
        child_section = Section("Child", 5, 10, "type", 2)
        
        parent = SectionTree(parent_section)
        child = SectionTree(child_section)
        parent.children.append(child)
        
        assert len(parent.children) == 1
        assert parent.children[0].section.name == "Child"


class TestBuildSectionTree:
    """Test build_section_tree function"""

    def test_build_flat_tree(self):
        """Build tree with no hierarchy"""
        sections = [
            Section("Header", 1, 10, "equals", 1),
            Section("Section A", 11, 20, "dash", 1),
            Section("Section B", 21, 30, "dash", 1),
        ]
        
        tree = build_section_tree(sections)
        
        assert len(tree) == 3
        assert tree[0].section.name == "Header"
        assert tree[1].section.name == "Section A"

    def test_build_hierarchical_tree(self):
        """Build tree with hierarchy"""
        sections = [
            Section("Header", 1, 5, "equals", 1),
            Section("Chapter 1", 6, 20, "dash", 2),
            Section("Subsection 1.1", 10, 15, "dash", 3),
            Section("Subsection 1.2", 16, 19, "dash", 3),
            Section("Chapter 2", 21, 30, "dash", 2),
        ]
        
        tree = build_section_tree(sections)
        
        assert len(tree) == 1
        assert tree[0].section.name == "Header"
        assert len(tree[0].children) == 2
        assert tree[0].children[0].section.name == "Chapter 1"
        assert tree[0].children[1].section.name == "Chapter 2"
        assert len(tree[0].children[0].children) == 2

    def test_empty_sections(self):
        """Empty sections returns empty tree"""
        tree = build_section_tree([])
        
        assert tree == []

    def test_single_section(self):
        """Single section returns single node"""
        sections = [Section("Header", 1, 10, "equals", 1)]
        
        tree = build_section_tree(sections)
        
        assert len(tree) == 1
        assert tree[0].section.name == "Header"

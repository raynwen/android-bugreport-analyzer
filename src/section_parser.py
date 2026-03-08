"""
Task 5: Section Parser
Author: 闫文峰

Parses sections into hierarchical tree structure.
"""

from typing import List, Optional
from dataclasses import dataclass, field

from src.section_detector import Section


@dataclass
class SectionTree:
    """
    Represents a section node in the hierarchical tree.
    
    Attributes:
        section: The Section object
        children: List of child SectionTree nodes
        parent: Optional parent SectionTree node
    """
    section: Section
    children: List['SectionTree'] = field(default_factory=list)
    parent: Optional['SectionTree'] = None
    
    def __repr__(self) -> str:
        return f"SectionTree({self.section.name}, {len(self.children)} children)"


def build_section_tree(sections: List[Section]) -> List[SectionTree]:
    """
    Build a hierarchical tree from flat section list.
    
    Args:
        sections: List of Section objects
        
    Returns:
        List of root SectionTree nodes with children attached
    """
    if not sections:
        return []
    
    roots: List[SectionTree] = []
    stack: List[SectionTree] = []
    
    for section in sections:
        node = SectionTree(section)
        
        while stack and stack[-1].section.level >= section.level:
            stack.pop()
        
        if stack:
            node.parent = stack[-1]
            stack[-1].children.append(node)
        else:
            roots.append(node)
        
        stack.append(node)
    
    return roots


def get_all_sections(tree: List[SectionTree]) -> List[Section]:
    """
    Flatten tree back to section list.
    
    Args:
        tree: List of root SectionTree nodes
        
    Returns:
        Flat list of all sections
    """
    result = []
    
    def traverse(node: SectionTree):
        result.append(node.section)
        for child in node.children:
            traverse(child)
    
    for root in tree:
        traverse(root)
    
    return result


if __name__ == "__main__":
    from src.section_detector import Section
    
    sections = [
        Section("Header", 1, 10, "equals", 1),
        Section("Chapter 1", 11, 30, "dash", 2),
        Section("Section 1.1", 15, 20, "dash", 3),
        Section("Section 1.2", 21, 29, "dash", 3),
        Section("Chapter 2", 31, 50, "dash", 2),
    ]
    
    tree = build_section_tree(sections)
    
    print(f"✓ Built tree with {len(tree)} root nodes")
    
    def print_tree(nodes: List[SectionTree], indent: int = 0):
        for node in nodes:
            print("  " * indent + f"├── {node.section.name} (L{node.section.start_line}-{node.section.end_line})")
            print_tree(node.children, indent + 1)
    
    print_tree(tree)

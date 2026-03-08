"""
Task 8: Preset Query
Author: 闫文峰

Query preset index for keyword matches.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from src.line_iterator import LineIterator


@dataclass
class QueryResult:
    """
    Represents a query result.
    
    Attributes:
        line_number: Line number where match was found
        content: Line content
        keyword: Keyword that was searched
    """
    line_number: int
    content: str
    keyword: str
    
    def __repr__(self) -> str:
        return f"QueryResult(L{self.line_number}: {self.content[:50]}...)"


def query_preset(
    keyword: str, 
    index: Dict[str, List[int]], 
    file_path: str
) -> List[QueryResult]:
    """
    Query preset index for a keyword.
    
    Args:
        keyword: Keyword to search
        index: Pre-built index mapping keywords to line numbers
        file_path: Path to bug report file
        
    Returns:
        List of QueryResult objects
    """
    keyword_lower = keyword.lower()
    
    if keyword_lower not in index:
        return []
    
    line_nums = index[keyword_lower]
    
    if not line_nums:
        return []
    
    line_nums_set = set(line_nums)
    lines: Dict[int, str] = {}
    
    iterator = LineIterator(file_path)
    for line_num, line in iterator:
        if line_num in line_nums_set:
            lines[line_num] = line
        
        if len(lines) >= len(line_nums):
            break
    
    results = []
    for line_num in sorted(line_nums):
        if line_num in lines:
            results.append(QueryResult(
                line_number=line_num,
                content=lines[line_num],
                keyword=keyword
            ))
    
    return results


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 3:
        print("Usage: python preset_query.py <keyword> <index_file> <bugreport_file>")
        sys.exit(1)
    
    keyword = sys.argv[1]
    index_path = sys.argv[2]
    file_path = sys.argv[3]
    
    with open(index_path, 'r') as f:
        index = json.load(f)
    
    results = query_preset(keyword, index, file_path)
    
    print(f"✓ Found {len(results)} matches for '{keyword}':\n")
    
    for result in results[:10]:
        print(f"  L{result.line_number}: {result.content[:80]}")
    
    if len(results) > 10:
        print(f"\n  ... and {len(results) - 10} more")

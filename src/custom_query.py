"""
Task 9: Custom Query
Author: 闫文峰

Scans file for custom keywords (not in preset index).
"""

from typing import List

from src.line_iterator import LineIterator
from src.preset_query import QueryResult


def query_custom(keyword: str, file_path: str) -> List[QueryResult]:
    """
    Scan file for custom keyword (not in preset index).
    
    Args:
        keyword: Keyword to search
        file_path: Path to bug report file
        
    Returns:
        List of QueryResult objects
    """
    results: List[QueryResult] = []
    keyword_lower = keyword.lower()
    
    iterator = LineIterator(file_path)
    
    for line_num, line in iterator:
        if keyword_lower in line.lower():
            results.append(QueryResult(
                line_number=line_num,
                content=line,
                keyword=keyword
            ))
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python custom_query.py <keyword> <bugreport_file>")
        sys.exit(1)
    
    keyword = sys.argv[1]
    file_path = sys.argv[2]
    
    results = query_custom(keyword, file_path)
    
    print(f"✓ Found {len(results)} matches for '{keyword}':\n")
    
    for result in results[:10]:
        print(f"  L{result.line_number}: {result.content[:80]}")
    
    if len(results) > 10:
        print(f"\n  ... and {len(results) - 10} more")

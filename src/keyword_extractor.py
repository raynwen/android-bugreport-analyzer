"""
Task 6: Keyword Extractor
Author: 闫文峰

Extracts preset keywords from YAML configuration.
"""

from typing import Dict, List, Set, Any


def extract_preset_keywords(config: Dict[str, Any]) -> Set[str]:
    """
    Extract all preset keywords from YAML configuration.
    
    Args:
        config: YAML configuration dictionary
        
    Returns:
        Set of lowercase keywords
    """
    keywords: Set[str] = set()
    
    # Extract from keywords section (new format)
    keywords_section = config.get("keywords", {})
    if isinstance(keywords_section, dict):
        for category, kw_list in keywords_section.items():
            if isinstance(kw_list, list):
                for kw in kw_list:
                    keywords.add(kw.lower())
    
    # Extract from record_types section
    record_types = config.get("record_types", {})
    
    if isinstance(record_types, dict):
        for type_name, record_type in record_types.items():
            if isinstance(record_type, dict):
                for kw in record_type.get("keywords", []):
                    keywords.add(kw.lower())
                
                for subsection in record_type.get("subsections", []):
                    for kw in subsection.get("keywords", []):
                        keywords.add(kw.lower())
    elif isinstance(record_types, list):
        for record_type in record_types:
            if isinstance(record_type, dict):
                for kw in record_type.get("keywords", []):
                    keywords.add(kw.lower())
                
                for subsection in record_type.get("subsections", []):
                    for kw in subsection.get("keywords", []):
                        keywords.add(kw.lower())
    
    # Extract from interest_points section
    for point in config.get("interest_points", []):
        for kw in point.get("keywords", []):
            keywords.add(kw.lower())
    
    return keywords


def build_keyword_mapping(config: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Build mapping from keywords to their types.
    
    Args:
        config: YAML configuration dictionary
        
    Returns:
        Dictionary mapping keyword -> {type, name, category}
    """
    mapping: Dict[str, Dict[str, str]] = {}
    
    for record_type in config.get("record_types", []):
        type_name = record_type.get("name", "")
        
        for kw in record_type.get("keywords", []):
            kw_lower = kw.lower()
            mapping[kw_lower] = {
                "type": "record_type",
                "name": type_name,
                "category": record_type.get("category", "")
            }
        
        for subsection in record_type.get("subsections", []):
            sub_name = subsection.get("name", "")
            
            for kw in subsection.get("keywords", []):
                kw_lower = kw.lower()
                mapping[kw_lower] = {
                    "type": "subsection",
                    "name": sub_name,
                    "parent": type_name,
                    "category": subsection.get("category", "")
                }
    
    for point in config.get("interest_points", []):
        point_name = point.get("name", "")
        
        for kw in point.get("keywords", []):
            kw_lower = kw.lower()
            mapping[kw_lower] = {
                "type": "interest_point",
                "name": point_name,
                "priority": point.get("priority", "")
            }
    
    return mapping


if __name__ == "__main__":
    import sys
    from src.config_loader import load_yaml_config
    
    if len(sys.argv) < 2:
        print("Usage: python keyword_extractor.py <config_path>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    
    config = load_yaml_config(config_path)
    keywords = extract_preset_keywords(config)
    mapping = build_keyword_mapping(config)
    
    print(f"✓ Extracted {len(keywords)} preset keywords")
    print(f"✓ Built mapping for {len(mapping)} keywords")

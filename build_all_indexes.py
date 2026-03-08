"""Build All Indexes - 构建所有索引

生成 sections.json 和 enhanced_index.json

Usage:
    python build_all_indexes.py <output_dir>

Example:
    python build_all_indexes.py J:\Trae\extracted_log_v2\log\dumpState_F9660ZCS6AYKF_202512301000
"""

import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.boundary_detector import BoundaryDetector
from src.section_detector import SectionDetector
from src.enhanced_index import EnhancedIndexBuilder
from src.keyword_extractor import extract_preset_keywords


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_all_indexes.py <output_dir>")
        sys.exit(1)

    output_dir = sys.argv[1]
    config_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(output_dir, 'dumpstate.txt')

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print("=" * 60)
    print("Building All Indexes")
    print("=" * 60)
    print(f"File: {file_path}")

    file_size = os.path.getsize(file_path) / (1024 * 1024)
    print(f"File size: {file_size:.2f} MB")

    print("\n[Step 1] Load configuration...")
    boundary_config_path = os.path.join(config_dir, 'boundary_patterns.yaml')
    
    from src.config_loader import load_yaml_config
    full_config = load_yaml_config(boundary_config_path)
    boundary_config = full_config.get('boundary_markers', {})
    record_types = full_config.get('record_types', {})
    print(f"  Boundary markers: {len(boundary_config)}")
    print(f"  Record types: {len(record_types)}")

    print("\n[Step 2] Detect boundaries...")
    start_time = time.time()
    detector = BoundaryDetector(boundary_config)
    boundaries = detector.detect_file(file_path)
    elapsed = time.time() - start_time
    print(f"  Found {len(boundaries)} boundaries in {elapsed:.2f}s")
    
    if len(boundaries) > 100:
        print(f"  (First 5: L{boundaries[0][0]}, L{boundaries[1][0]}, L{boundaries[2][0]}, L{boundaries[3][0]}, L{boundaries[4][0]})")

    print("\n[Step 3] Detect sections...")
    start_time = time.time()
    section_detector = SectionDetector(boundaries)
    sections = section_detector.detect()
    elapsed = time.time() - start_time
    print(f"  Found {len(sections)} sections in {elapsed:.2f}s")

    sections_path = os.path.join(output_dir, 'sections.json')
    sections_dicts = [section.to_dict() for section in sections]
    with open(sections_path, 'w', encoding='utf-8') as f:
        json.dump(sections_dicts, f, ensure_ascii=False, indent=2)
    print(f"  Saved to: {sections_path}")

    print("\n[Step 4] Extract preset keywords...")
    keywords = extract_preset_keywords(full_config)
    print(f"  Found {len(keywords)} preset keywords")

    print("\n[Step 5] Build enhanced index...")
    start_time = time.time()
    index_builder = EnhancedIndexBuilder(file_path, keywords)
    index = index_builder.build()
    elapsed = time.time() - start_time
    print(f"  Total lines: {index['total_lines']:,}")
    print(f"  Time: {elapsed:.2f}s")

    enhanced_index_path = os.path.join(output_dir, 'enhanced_index.json')
    with open(enhanced_index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f"  Saved to: {enhanced_index_path}")

    print("\n" + "=" * 60)
    print("Index build completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()

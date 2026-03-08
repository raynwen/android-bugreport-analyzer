"""Query Engine - 统一查询引擎

整合预设索引和自定义索引，提供统一的查询接口。

Author: 闫文峰
Version: 1.0
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple


class QueryEngine:
    """统一查询引擎

    负责:
    - 加载预设索引 (enhanced_index.json)
    - 加载自定义索引 (custom_index.json)
    - 执行查询并合并结果
    """

    def __init__(self, output_dir: str, config_dir: str):
        """初始化查询引擎

        Args:
            output_dir: 输出目录路径
            config_dir: 配置目录路径
        """
        self.output_dir = output_dir
        self.config_dir = config_dir

        self.enhanced_index_path = os.path.join(output_dir, 'enhanced_index.json')
        self.custom_index_path = os.path.join(output_dir, 'custom_index.json')
        self.sections_path = os.path.join(output_dir, 'sections.json')

        self._enhanced_index = None
        self._custom_index = None
        self._sections = None

    def load_indexes(self) -> Dict[str, Any]:
        """加载所有索引

        Returns:
            索引加载状态
        """
        status = {
            'enhanced_index': False,
            'custom_index': False,
            'sections': False
        }

        if os.path.exists(self.enhanced_index_path):
            with open(self.enhanced_index_path, 'r', encoding='utf-8') as f:
                self._enhanced_index = json.load(f)
            status['enhanced_index'] = True

        if os.path.exists(self.custom_index_path):
            with open(self.custom_index_path, 'r', encoding='utf-8') as f:
                self._custom_index = json.load(f)
            status['custom_index'] = True

        if os.path.exists(self.sections_path):
            with open(self.sections_path, 'r', encoding='utf-8') as f:
                self._sections = json.load(f)
            status['sections'] = True

        return status

    def query(self, keyword: str, use_custom: bool = True, use_preset: bool = True) -> Dict[str, Any]:
        """执行查询

        Args:
            keyword: 查询关键词
            use_custom: 是否使用自定义索引
            use_preset: 是否使用预设索引

        Returns:
            查询结果
        """
        results = {
            'keyword': keyword,
            'sources': [],
            'total_matches': 0,
            'matches': []
        }

        if use_custom and self._custom_index:
            custom_results = self._query_custom_index(keyword)
            if custom_results:
                results['sources'].append('custom_index')
                results['matches'].extend(custom_results)
                results['total_matches'] += len(custom_results)

        if use_preset and self._enhanced_index:
            preset_results = self._query_preset_index(keyword)
            if preset_results:
                results['sources'].append('enhanced_index')
                results['matches'].extend(preset_results)
                results['total_matches'] += len(preset_results)

        return results

    def _query_preset_index(self, keyword: str) -> List[Dict[str, Any]]:
        """查询预设索引

        Args:
            keyword: 关键词

        Returns:
            匹配结果列表
        """
        keywords_index = self._enhanced_index.get('keywords', {})
        keyword_lower = keyword.lower()

        if keyword_lower not in keywords_index:
            return []

        line_nums = keywords_index[keyword_lower]
        return [{'line_number': ln, 'source': 'preset'} for ln in line_nums]

    def _query_custom_index(self, keyword: str) -> List[Dict[str, Any]]:
        """查询自定义索引

        Args:
            keyword: 关键词

        Returns:
            匹配结果列表
        """
        if not self._custom_index:
            return []

        queries = self._custom_index.get('queries', [])
        keyword_lower = keyword.lower()

        results = []
        for query in queries:
            query_type = query.get('type', 'keyword')
            pattern = query.get('pattern', '')

            if query_type == 'keyword':
                if keyword_lower == pattern.lower():
                    line_nums = query.get('line_numbers', [])
                    results.extend([{
                        'line_number': ln,
                        'source': 'custom',
                        'query_name': query.get('name', '')
                    } for ln in line_nums])

            elif query_type == 'regex':
                import re
                try:
                    if re.search(pattern, keyword, re.IGNORECASE):
                        line_nums = query.get('line_numbers', [])
                        results.extend([{
                            'line_number': ln,
                            'source': 'custom',
                            'query_name': query.get('name', '')
                        } for ln in line_nums])
                except re.error:
                    pass

        return results

    def query_by_line_numbers(
        self,
        line_numbers: List[int],
        file_path: str,
        line_offsets: List[int],
        context_before: int = 5,
        context_after: int = 5
    ) -> List[Dict[str, Any]]:
        """根据行号列表提取内容和上下文

        Args:
            line_numbers: 行号列表
            file_path: 文件路径
            line_offsets: 行偏移列表
            context_before: 上下文前行数
            context_after: 上下文后行数

        Returns:
            带上下文的结果列表
        """
        results = []
        total_lines = len(line_offsets)

        with open(file_path, 'rb') as f:
            for line_num in line_numbers:
                result = {
                    'line_number': line_num,
                    'content': '',
                    'context': {
                        'before': [],
                        'after': []
                    }
                }

                before_start = max(1, line_num - context_before)
                for i in range(before_start, line_num):
                    if i < len(line_offsets):
                        offset = line_offsets[i - 1]
                        f.seek(offset)
                        line = f.readline().decode('utf-8', errors='ignore').rstrip()
                        result['context']['before'].append({
                            'line_number': i,
                            'content': line
                        })

                if line_num <= len(line_offsets):
                    offset = line_offsets[line_num - 1]
                    f.seek(offset)
                    result['content'] = f.readline().decode('utf-8', errors='ignore').rstrip()

                after_end = min(total_lines, line_num + context_after)
                for i in range(line_num + 1, after_end + 1):
                    if i <= len(line_offsets):
                        offset = line_offsets[i - 1]
                        f.seek(offset)
                        line = f.readline().decode('utf-8', errors='ignore').rstrip()
                        result['context']['after'].append({
                            'line_number': i,
                            'content': line
                        })

                results.append(result)

        return results

    def get_line_offsets(self) -> List[int]:
        """获取行偏移列表

        Returns:
            行偏移列表
        """
        if self._enhanced_index:
            return self._enhanced_index.get('line_offsets', [])
        return []

    def get_sections(self) -> List[Dict[str, Any]]:
        """获取章节列表

        Returns:
            章节列表
        """
        return self._sections or []


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python query_engine.py <output_dir> <keyword>")
        sys.exit(1)

    output_dir = sys.argv[1]
    keyword = sys.argv[2]

    engine = QueryEngine(output_dir, '')
    status = engine.load_indexes()

    print(f"Index status: {status}")

    results = engine.query(keyword)
    print(f"Total matches: {results['total_matches']}")
    print(f"Sources: {results['sources']}")

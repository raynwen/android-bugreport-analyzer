"""Custom Index Manager - 自定义索引管理器

管理用户自定义查询的索引创建和查询。

Author: 闫文峰
Version: 1.0
"""

import os
import re
import json
import time
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


class CustomIndexManager:
    """自定义索引管理器

    负责:
    - 加载全局配置 query_config.yaml
    - 管理 custom_queries.yaml (用户查询配置)
    - 生成 custom_index.json (自定义索引)
    - 执行自定义查询
    """

    def __init__(self, output_dir: str, config_dir: str):
        """初始化自定义索引管理器

        Args:
            output_dir: 输出目录路径 (存放索引和结果)
            config_dir: 配置文件目录路径 (存放 query_config.yaml)
        """
        self.output_dir = output_dir
        self.config_dir = config_dir
        self.query_config_path = os.path.join(config_dir, 'query_config.yaml')
        self.custom_queries_path = os.path.join(output_dir, 'custom_queries.yaml')
        self.custom_index_path = os.path.join(output_dir, 'custom_index.json')
        self.query_results_dir = os.path.join(output_dir, 'query_results')
        self._query_config = None

    def load_query_config(self) -> Dict[str, Any]:
        """加载全局查询配置

        Returns:
            查询配置字典
        """
        if self._query_config is not None:
            return self._query_config

        if os.path.exists(self.query_config_path):
            with open(self.query_config_path, 'r', encoding='utf-8') as f:
                self._query_config = yaml.safe_load(f)
        else:
            self._query_config = self._get_default_config()

        return self._query_config

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置

        Returns:
            默认配置字典
        """
        return {
            'version': '1.0',
            'output': {
                'context_lines_before': 5,
                'context_lines_after': 5,
                'pagination': {
                    'enabled': True,
                    'max_tokens_per_file': 32000,
                    'encoding': 'cl100k_base'
                }
            },
            'priority_order': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
            'index': {
                'rebuild_on_new_query': True,
                'keep_history': False
            }
        }

    def save_custom_queries(self, queries: List[Dict[str, Any]]) -> None:
        """保存用户查询配置

        Args:
            queries: 查询配置列表
        """
        config = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'queries': queries
        }

        with open(self.custom_queries_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    def load_custom_queries(self) -> Optional[List[Dict[str, Any]]]:
        """加载用户查询配置

        Returns:
            查询配置列表，如果不存在返回 None
        """
        if not os.path.exists(self.custom_queries_path):
            return None

        with open(self.custom_queries_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config.get('queries', [])

    def clear_custom_index(self) -> None:
        """清除自定义索引"""
        if os.path.exists(self.custom_index_path):
            os.remove(self.custom_index_path)

    def clear_query_results(self) -> None:
        """清除查询结果"""
        if os.path.exists(self.query_results_dir):
            import shutil
            shutil.rmtree(self.query_results_dir)

    def rebuild_custom_index(
        self,
        file_path: str,
        sections: List[Dict[str, Any]],
        line_offsets: List[int]
    ) -> Dict[str, Any]:
        """重建自定义索引

        Args:
            file_path: 原始文件路径
            sections: 章节列表
            line_offsets: 行偏移列表

        Returns:
            索引结果字典
        """
        queries = self.load_custom_queries()
        if not queries:
            return {'queries': [], 'total_matches': 0}

        enabled_queries = [q for q in queries if q.get('enabled', True)]

        index_data = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'queries': []
        }

        total_matches = 0
        start_time = time.time()

        for query in enabled_queries:
            query_result = self._build_query_index(
                query, file_path, sections, line_offsets
            )
            if query_result:
                index_data['queries'].append(query_result)
                total_matches += query_result.get('match_count', 0)

        index_data['total_matches'] = total_matches
        index_data['elapsed_time'] = time.time() - start_time

        with open(self.custom_index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        return index_data

    def _build_query_index(
        self,
        query: Dict[str, Any],
        file_path: str,
        sections: List[Dict[str, Any]],
        line_offsets: List[int]
    ) -> Optional[Dict[str, Any]]:
        """为单个查询构建索引

        Args:
            query: 查询配置
            sections: 章节列表
            line_offsets: 行偏移列表

        Returns:
            查询索引结果
        """
        query_type = query.get('type', 'keyword')
        pattern = query.get('pattern', '')
        query_name = query.get('name', 'unknown')

        if not pattern:
            return None

        match_func = self._get_match_function(query_type, pattern)
        if not match_func:
            return None

        line_numbers = []
        try:
            with open(file_path, 'rb') as f:
                for line_num in range(1, len(line_offsets) + 1):
                    offset = line_offsets[line_num - 1]
                    f.seek(offset)
                    line_bytes = f.readline()
                    try:
                        line = line_bytes.decode('utf-8', errors='ignore')
                    except Exception:
                        line = ''

                    if match_func(line):
                        line_numbers.append(line_num)
        except Exception as e:
            print(f'Error scanning file for {query_name}: {e}')
            return None

        return {
            'name': query_name,
            'type': query_type,
            'pattern': pattern,
            'priority': query.get('priority', 'MEDIUM'),
            'description': query.get('description', ''),
            'match_count': len(line_numbers),
            'line_numbers': line_numbers
        }

    def _get_match_function(self, query_type: str, pattern: str):
        """获取匹配函数

        Args:
            query_type: 查询类型 (keyword/regex/section)
            pattern: 匹配模式

        Returns:
            匹配函数
        """
        if query_type == 'keyword':
            pattern_lower = pattern.lower()
            return lambda line: pattern_lower in line.lower()

        elif query_type == 'regex':
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                return lambda line: compiled.search(line) is not None
            except re.error:
                print(f'Invalid regex pattern: {pattern}')
                return None

        elif query_type == 'section':
            return lambda line: False

        return None

    def query_by_custom_index(
        self,
        query_name: str,
        file_path: str,
        line_offsets: List[int],
        context_lines_before: int = 5,
        context_lines_after: int = 5
    ) -> List[Dict[str, Any]]:
        """使用自定义索引查询

        Args:
            query_name: 查询名称
            file_path: 文件路径
            line_offsets: 行偏移列表
            context_lines_before: 上下文前行数
            context_lines_after: 上下文后行数

        Returns:
            查询结果列表
        """
        if not os.path.exists(self.custom_index_path):
            return []

        with open(self.custom_index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        query_result = None
        for q in index_data.get('queries', []):
            if q.get('name') == query_name:
                query_result = q
                break

        if not query_result:
            return []

        line_numbers = query_result.get('line_numbers', [])
        return self._extract_context(
            file_path, line_offsets, line_numbers,
            context_lines_before, context_lines_after
        )

    def _extract_context(
        self,
        file_path: str,
        line_offsets: List[int],
        line_numbers: List[int],
        context_lines_before: int,
        context_lines_after: int
    ) -> List[Dict[str, Any]]:
        """提取上下文

        Args:
            file_path: 文件路径
            line_offsets: 行偏移列表
            line_numbers: 匹配行号列表
            context_lines_before: 上下文前行数
            context_lines_after: 上下文后行数

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

                before_start = max(1, line_num - context_lines_before)
                for i in range(before_start, line_num):
                    offset = line_offsets[i - 1]
                    f.seek(offset)
                    line = f.readline().decode('utf-8', errors='ignore').rstrip()
                    result['context']['before'].append({
                        'line_number': i,
                        'content': line
                    })

                offset = line_offsets[line_num - 1]
                f.seek(offset)
                result['content'] = f.readline().decode('utf-8', errors='ignore').rstrip()

                after_end = min(total_lines, line_num + context_lines_after)
                for i in range(line_num + 1, after_end + 1):
                    offset = line_offsets[i - 1]
                    f.seek(offset)
                    line = f.readline().decode('utf-8', errors='ignore').rstrip()
                    result['context']['after'].append({
                        'line_number': i,
                        'content': line
                    })

                results.append(result)

        return results

"""Query Result Writer - 分页结果写入器

负责将查询结果分页并写入文件。

Author: 闫文峰
Version: 1.0
"""

import os
import json
import math
from datetime import datetime
from typing import Dict, List, Any, Optional


class QueryResultWriter:
    """分页结果写入器

    负责:
    - 将查询结果按分页配置写入文件
    - 生成 result.json 和 context/part_*.json
    - 生成 metadata.json 元信息
    """

    def __init__(self, output_dir: str):
        """初始化分页结果写入器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = output_dir
        self.query_results_dir = os.path.join(output_dir, 'query_results')

    def write_results(
        self,
        query_name: str,
        query_config: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """写入查询结果

        Args:
            query_name: 查询名称
            query_config: 查询配置
            results: 查询结果列表

        Returns:
            写入结果统计
        """
        query_dir = os.path.join(self.query_results_dir, query_name)
        context_dir = os.path.join(query_dir, 'context')

        os.makedirs(context_dir, exist_ok=True)

        output_config = query_config.get('output', {})
        pagination = output_config.get('pagination', {})
        context_lines_before = output_config.get('context_lines_before', 5)
        context_lines_after = output_config.get('context_lines_after', 5)

        if pagination.get('enabled', True):
            max_tokens = pagination.get('max_tokens_per_file', 32000)
            return self._write_paginated_results(
                query_dir, context_dir, results,
                query_name, query_config,
                max_tokens, context_lines_before, context_lines_after
            )
        else:
            return self._write_single_result(
                query_dir, context_dir, results,
                query_name, query_config, context_lines_before, context_lines_after
            )

    def _write_paginated_results(
        self,
        query_dir: str,
        context_dir: str,
        results: List[Dict[str, Any]],
        query_name: str,
        query_config: Dict[str, Any],
        max_tokens: int,
        context_lines_before: int,
        context_lines_after: int
    ) -> Dict[str, Any]:
        """分页写入结果

        Args:
            query_dir: 查询目录
            context_dir: 上下文目录
            results: 查询结果
            query_name: 查询名称
            query_config: 查询配置
            max_tokens: 每页最大 tokens
            context_lines_before: 上下文前行数
            context_lines_after: 上下文后行数

        Returns:
            写入统计
        """
        estimated_tokens_per_result = self._estimate_tokens_per_result(
            context_lines_before, context_lines_after
        )

        max_results_per_page = max(1, max_tokens // estimated_tokens_per_result)

        total_results = len(results)
        total_pages = math.ceil(total_results / max_results_per_page)

        all_line_numbers = []

        for page_num in range(1, total_pages + 1):
            start_idx = (page_num - 1) * max_results_per_page
            end_idx = min(start_idx + max_results_per_page, total_results)
            page_results = results[start_idx:end_idx]

            part_file = f'part_{page_num}.json'
            part_path = os.path.join(context_dir, part_file)

            part_data = {
                'query': query_name,
                'pagination': {
                    'total_parts': total_pages,
                    'current_part': page_num,
                    'results_in_part': len(page_results)
                },
                'results': page_results
            }

            with open(part_path, 'w', encoding='utf-8') as f:
                json.dump(part_data, f, ensure_ascii=False, indent=2)

            for r in page_results:
                all_line_numbers.append(r.get('line_number', 0))

        metadata = {
            'query_name': query_name,
            'query_config': query_config,
            'total_results': total_results,
            'total_pages': total_pages,
            'results_per_page': max_results_per_page,
            'created_at': datetime.now().isoformat(),
            'files': {
                'result.json': '主结果文件 (汇总)',
                'context': {
                    'part_1.json': f'第 1 页 (最多 {max_results_per_page} 条)',
                    'part_2.json': f'第 2 页 (最多 {max_results_per_page} 条)',
                    '...': f'共 {total_pages} 页'
                }
            }
        }

        metadata_path = os.path.join(query_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        summary = {
            'query_name': query_name,
            'total_results': total_results,
            'total_pages': total_pages,
            'results_per_page': max_results_per_page,
            'context_dir': context_dir,
            'files_created': total_pages + 2
        }

        result_json = {
            'query': query_name,
            'type': query_config.get('type', 'keyword'),
            'total_matches': total_results,
            'pagination': {
                'total_parts': total_pages,
                'results_per_part': max_results_per_page
            },
            'summary': {
                'total_results': total_results,
                'total_pages': total_pages,
                'context_lines_before': context_lines_before,
                'context_lines_after': context_lines_after
            },
            'line_numbers': all_line_numbers[:100]
        }

        result_json_path = os.path.join(query_dir, 'result.json')
        with open(result_json_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)

        return summary

    def _write_single_result(
        self,
        query_dir: str,
        context_dir: str,
        results: List[Dict[str, Any]],
        query_name: str,
        query_config: Dict[str, Any],
        context_lines_before: int,
        context_lines_after: int
    ) -> Dict[str, Any]:
        """不分页写入结果

        Args:
            query_dir: 查询目录
            context_dir: 上下文目录
            results: 查询结果
            query_name: 查询名称
            query_config: 查询配置
            context_lines_before: 上下文前行数
            context_lines_after: 上下文后行数

        Returns:
            写入统计
        """
        result_json_path = os.path.join(query_dir, 'result.json')

        result_json = {
            'query': query_name,
            'type': query_config.get('type', 'keyword'),
            'total_matches': len(results),
            'results': results
        }

        with open(result_json_path, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)

        metadata = {
            'query_name': query_name,
            'query_config': query_config,
            'total_results': len(results),
            'created_at': datetime.now().isoformat(),
            'files': {
                'result.json': '完整结果'
            }
        }

        metadata_path = os.path.join(query_dir, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return {
            'query_name': query_name,
            'total_results': len(results),
            'total_pages': 1,
            'files_created': 2
        }

    def _estimate_tokens_per_result(
        self,
        context_lines_before: int,
        context_lines_after: int
    ) -> int:
        """估算每个结果占用的 tokens 数量

        Args:
            context_lines_before: 上下文前行数
            context_lines_after: 上下文后行数

        Returns:
            估算的 tokens 数量
        """
        avg_chars_per_line = 100
        total_lines = 1 + context_lines_before + context_lines_after
        avg_chars = total_lines * avg_chars_per_line

        tokens = math.ceil(avg_chars / 4)

        return max(tokens, 10)

    def read_result(self, query_name: str) -> Optional[Dict[str, Any]]:
        """读取查询结果

        Args:
            query_name: 查询名称

        Returns:
            查询结果，如果不存在返回 None
        """
        result_path = os.path.join(
            self.query_results_dir, query_name, 'result.json'
        )

        if not os.path.exists(result_path):
            return None

        with open(result_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_queries(self) -> List[str]:
        """列出所有查询结果

        Returns:
            查询名称列表
        """
        if not os.path.exists(self.query_results_dir):
            return []

        return [
            d for d in os.listdir(self.query_results_dir)
            if os.path.isdir(os.path.join(self.query_results_dir, d))
        ]

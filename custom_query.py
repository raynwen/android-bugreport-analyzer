"""Custom Query - 自定义查询脚本

按照设计文档第12章完整执行所有步骤:
1. 准备输出目录
2. 生成配置文件 (custom_queries.yaml)
3. 清除旧索引
4. 重建自定义索引 (custom_index.json)
5. 执行查询（提取上下文）
6. 分页保存结果

Usage:
    # 单个查询
    python custom_query.py <output_dir> --name "query_name" --pattern "pattern" --type keyword
    
    # 多个查询（JSON配置文件）
    python custom_query.py <output_dir> --config queries.json
    
    # 交互式输入
    python custom_query.py <output_dir> --interactive

Example:
    # 查询微信冻结
    python custom_query.py J:\Trae\extracted_log_v2\log\dumpState_F9660ZCS6AYKF_202512301000 \
        --name "query_wechat_freeze" \
        --pattern "com.tencent.mm.*freeze" \
        --type regex \
        --priority CRITICAL \
        --description "查询微信冻结问题"
"""

import os
import sys
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.custom_index_manager import CustomIndexManager
from src.query_result_writer import QueryResultWriter
from src.query_engine import QueryEngine


def parse_args():
    parser = argparse.ArgumentParser(
        description='自定义查询脚本 - 完整执行所有步骤',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('output_dir', help='输出目录路径')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--name', help='查询名称（单个查询模式）')
    group.add_argument('--config', help='查询配置文件路径（JSON格式）')
    group.add_argument('--interactive', action='store_true', help='交互式输入模式')
    
    parser.add_argument('--pattern', help='匹配模式（单个查询模式）')
    parser.add_argument('--type', choices=['keyword', 'regex', 'section'],
                       default='keyword', help='查询类型（默认: keyword）')
    parser.add_argument('--priority', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
                       default='HIGH', help='优先级（默认: HIGH）')
    parser.add_argument('--description', default='', help='查询描述')
    parser.add_argument('--context-before', type=int, default=5,
                       help='上下文前行数（默认: 5）')
    parser.add_argument('--context-after', type=int, default=5,
                       help='上下文后行数（默认: 5）')
    parser.add_argument('--keep-history', action='store_true',
                       help='保留历史查询结果')
    
    return parser.parse_args()


def validate_single_query(args):
    if not args.pattern:
        print("错误: 单个查询模式需要 --pattern 参数")
        sys.exit(1)
    
    return [{
        'name': args.name,
        'type': args.type,
        'pattern': args.pattern,
        'priority': args.priority,
        'description': args.description,
        'enabled': True
    }]


def load_queries_from_config(config_path):
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    queries = config.get('queries', [])
    if not queries:
        print("错误: 配置文件中没有查询定义")
        sys.exit(1)
    
    return queries


def interactive_input():
    print("\n" + "=" * 60)
    print("交互式查询配置")
    print("=" * 60)
    
    queries = []
    
    while True:
        print(f"\n--- 查询 #{len(queries) + 1} ---")
        
        name = input("查询名称 (例如: query_wechat_freeze): ").strip()
        if not name:
            print("错误: 查询名称不能为空")
            continue
        
        query_type = input("查询类型 (keyword/regex/section) [keyword]: ").strip()
        if not query_type:
            query_type = 'keyword'
        elif query_type not in ['keyword', 'regex', 'section']:
            print("错误: 查询类型必须是 keyword, regex 或 section")
            continue
        
        pattern = input("匹配模式: ").strip()
        if not pattern:
            print("错误: 匹配模式不能为空")
            continue
        
        priority = input("优先级 (CRITICAL/HIGH/MEDIUM/LOW) [HIGH]: ").strip()
        if not priority:
            priority = 'HIGH'
        elif priority not in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            print("错误: 优先级必须是 CRITICAL, HIGH, MEDIUM 或 LOW")
            continue
        
        description = input("查询描述: ").strip()
        
        queries.append({
            'name': name,
            'type': query_type,
            'pattern': pattern,
            'priority': priority,
            'description': description,
            'enabled': True
        })
        
        more = input("\n添加更多查询? (y/n) [n]: ").strip().lower()
        if more != 'y':
            break
    
    return queries


def main():
    args = parse_args()
    
    output_dir = args.output_dir
    config_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(output_dir, 'dumpstate.txt')
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("自定义查询系统 - 完整流程执行")
    print("=" * 80)
    
    print(f"\n输出目录: {output_dir}")
    print(f"原始文件: {file_path}")
    
    if args.name:
        print(f"查询模式: 单个查询")
        queries = validate_single_query(args)
    elif args.config:
        print(f"查询模式: 配置文件 ({args.config})")
        queries = load_queries_from_config(args.config)
    else:
        print(f"查询模式: 交互式输入")
        queries = interactive_input()
    
    print(f"\n查询数量: {len(queries)}")
    for q in queries:
        print(f"  - {q['name']}: {q['pattern']} ({q['type']}, {q['priority']})")
    
    print("\n" + "=" * 80)
    print("[步骤1] 准备输出目录")
    print("=" * 80)
    
    query_results_dir = os.path.join(output_dir, 'query_results')
    os.makedirs(query_results_dir, exist_ok=True)
    print(f"✓ 创建目录: {query_results_dir}")
    
    print("\n" + "=" * 80)
    print("[步骤2] 生成配置文件 (custom_queries.yaml)")
    print("=" * 80)
    
    custom_mgr = CustomIndexManager(output_dir, config_dir)
    custom_mgr.save_custom_queries(queries)
    print(f"✓ 保存到: {custom_mgr.custom_queries_path}")
    
    print("\n" + "=" * 80)
    print("[步骤3] 清除旧索引")
    print("=" * 80)
    
    if not args.keep_history:
        custom_mgr.clear_custom_index()
        print(f"✓ 已清除: {custom_mgr.custom_index_path}")
    else:
        print("✓ 保留历史索引 (--keep-history)")
    
    print("\n" + "=" * 80)
    print("[步骤4] 重建自定义索引 (custom_index.json)")
    print("=" * 80)
    
    engine = QueryEngine(output_dir, config_dir)
    status = engine.load_indexes()
    
    print(f"Enhanced index: {'OK' if status['enhanced_index'] else 'NOT FOUND'}")
    print(f"Sections: {'OK' if status['sections'] else 'NOT FOUND'}")
    
    if not status['enhanced_index'] or not status['sections']:
        print("\n错误: 缺少必要索引，请先运行 build_all_indexes.py")
        sys.exit(1)
    
    total_lines = engine._enhanced_index.get('total_lines', 0)
    print(f"Total lines: {total_lines:,}")
    
    line_offsets = engine._enhanced_index.get('line_offsets', [])
    if not line_offsets:
        print("\n错误: 缺少行偏移数据")
        sys.exit(1)
    
    print("\n开始扫描文件...")
    start_time = datetime.now()
    
    custom_index = custom_mgr.rebuild_custom_index(
        file_path,
        engine._sections,
        line_offsets
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"\n✓ 索引构建完成")
    print(f"  总匹配数: {custom_index.get('total_matches', 0):,}")
    print(f"  耗时: {elapsed:.2f}s")
    print(f"  保存到: {custom_mgr.custom_index_path}")
    
    for q in custom_index.get('queries', []):
        print(f"    - {q['name']}: {q.get('match_count', 0):,} 匹配")
    
    print("\n" + "=" * 80)
    print("[步骤5] 执行查询（提取上下文）")
    print("=" * 80)
    
    print(f"上下文配置: 前 {args.context_before} 行, 后 {args.context_after} 行")
    
    all_results = {}
    for query in queries:
        query_name = query['name']
        print(f"\n处理查询: {query_name}")
        
        results = custom_mgr.query_by_custom_index(
            query_name,
            file_path,
            line_offsets,
            context_lines_before=args.context_before,
            context_lines_after=args.context_after
        )
        
        all_results[query_name] = results
        print(f"  ✓ 提取 {len(results)} 条结果")
    
    print("\n" + "=" * 80)
    print("[步骤6] 分页保存结果")
    print("=" * 80)
    
    writer = QueryResultWriter(output_dir)
    
    for query_name, results in all_results.items():
        if not results:
            print(f"\n{query_name}: 无匹配结果，跳过")
            continue
        
        query_config = {
            'type': next((q['type'] for q in queries if q['name'] == query_name), 'keyword'),
            'output': {
                'context_lines_before': args.context_before,
                'context_lines_after': args.context_after,
                'pagination': {
                    'enabled': True,
                    'max_tokens_per_file': 32000,
                    'encoding': 'cl100k_base'
                }
            }
        }
        
        write_result = writer.write_results(
            query_name,
            query_config,
            results
        )
        
        print(f"\n{query_name}:")
        print(f"  ✓ 总结果数: {write_result['total_results']}")
        print(f"  ✓ 总页数: {write_result['total_pages']}")
        print(f"  ✓ 每页结果数: {write_result['results_per_page']}")
        print(f"  ✓ 创建文件数: {write_result['files_created']}")
        print(f"  ✓ 输出目录: {os.path.join(query_results_dir, query_name)}")
    
    print("\n" + "=" * 80)
    print("查询完成！")
    print("=" * 80)
    
    print("\n生成的文件:")
    print(f"  - {custom_mgr.custom_queries_path}")
    print(f"  - {custom_mgr.custom_index_path}")
    
    for query_name in all_results.keys():
        query_dir = os.path.join(query_results_dir, query_name)
        if os.path.exists(query_dir):
            print(f"  - {query_dir}/")
            for item in sorted(os.listdir(query_dir)):
                item_path = os.path.join(query_dir, item)
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    print(f"      {item} ({size:,} 字节)")
                else:
                    print(f"      {item}/")


if __name__ == '__main__':
    main()

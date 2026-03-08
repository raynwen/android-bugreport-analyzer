"""CLI - 统一命令行入口

提供统一的命令行入口，整合所有功能模块：
- build: 构建索引
- query: 执行查询
- analyze: 完整分析流程（build + query）
- interactive: 交互式模式

Usage:
    python cli.py build <output_dir>
    python cli.py query <output_dir> --pattern "xxx" --type keyword
    python cli.py analyze <output_dir> --pattern "xxx"
    python cli.py interactive

Author: 闫文峰
Version: 1.0
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class CLIError(Exception):
    """CLI 错误基类"""
    pass


class IndexNotFoundError(CLIError):
    """索引不存在错误"""
    
    def __init__(self, output_dir):
        super().__init__(f"索引不存在: {output_dir}")
        self.suggestion = "请先运行: python cli.py build <output_dir>"


class InvalidPatternError(CLIError):
    """无效模式错误"""
    
    def __init__(self, pattern, error):
        super().__init__(f"无效的正则表达式: {pattern}")
        self.original_error = error


class CLI:
    """统一命令行接口"""
    
    def __init__(self):
        self.config_dir = os.path.dirname(os.path.abspath(__file__))
    
    def build(self, args):
        """构建索引
        
        Args:
            args: 命令行参数
        """
        output_dir = args.output_dir
        file_path = os.path.join(output_dir, 'dumpstate.txt')
        
        if not os.path.exists(file_path):
            print(f"错误: 文件不存在: {file_path}")
            sys.exit(1)
        
        enhanced_index_path = os.path.join(output_dir, 'enhanced_index.json')
        sections_path = os.path.join(output_dir, 'sections.json')
        
        if os.path.exists(enhanced_index_path) and os.path.exists(sections_path):
            if not args.force:
                print("索引已存在，跳过构建。使用 --force 强制重建。")
                return
            print("强制重建索引...")
        
        print("=" * 80)
        print("构建索引")
        print("=" * 80)
        print(f"输出目录: {output_dir}")
        
        build_script = os.path.join(self.config_dir, 'build_all_indexes.py')
        
        if not os.path.exists(build_script):
            print(f"错误: 构建脚本不存在: {build_script}")
            sys.exit(1)
        
        cmd = [sys.executable, build_script, output_dir]
        
        result = subprocess.run(cmd, cwd=self.config_dir)
        
        if result.returncode != 0:
            print(f"错误: 构建索引失败")
            sys.exit(1)
        
        print("\n" + "=" * 80)
        print("索引构建完成!")
        print("=" * 80)
    
    def query(self, args):
        """执行查询
        
        Args:
            args: 命令行参数
        """
        output_dir = args.output_dir
        
        enhanced_index_path = os.path.join(output_dir, 'enhanced_index.json')
        sections_path = os.path.join(output_dir, 'sections.json')
        
        if args.auto_build:
            if not os.path.exists(enhanced_index_path) or not os.path.exists(sections_path):
                print("索引不存在，自动构建...")
                build_args = argparse.Namespace(
                    output_dir=output_dir,
                    force=False
                )
                self.build(build_args)
        else:
            if not os.path.exists(enhanced_index_path):
                raise IndexNotFoundError(output_dir)
        
        print("=" * 80)
        print("执行查询")
        print("=" * 80)
        
        query_script = os.path.join(self.config_dir, 'custom_query.py')
        
        if not os.path.exists(query_script):
            print(f"错误: 查询脚本不存在: {query_script}")
            sys.exit(1)
        
        cmd = [sys.executable, query_script, output_dir]
        
        if args.config:
            cmd.extend(['--config', args.config])
        elif args.interactive:
            cmd.append('--interactive')
        else:
            if not args.pattern:
                print("错误: 需要指定 --pattern 或 --config 或 --interactive")
                sys.exit(1)
            
            if args.name:
                cmd.extend(['--name', args.name])
            cmd.extend(['--pattern', args.pattern])
            cmd.extend(['--type', args.type])
            cmd.extend(['--priority', args.priority])
            if args.description:
                cmd.extend(['--description', args.description])
        
        cmd.extend(['--context-before', str(args.context_before)])
        cmd.extend(['--context-after', str(args.context_after)])
        
        if args.keep_history:
            cmd.append('--keep-history')
        
        result = subprocess.run(cmd, cwd=self.config_dir)
        
        if result.returncode != 0:
            print(f"错误: 查询执行失败")
            sys.exit(1)
    
    def analyze(self, args):
        """完整分析流程（build + query）
        
        Args:
            args: 命令行参数
        """
        output_dir = args.output_dir
        
        print("=" * 80)
        print("完整分析流程")
        print("=" * 80)
        print(f"输出目录: {output_dir}")
        
        enhanced_index_path = os.path.join(output_dir, 'enhanced_index.json')
        
        if os.path.exists(enhanced_index_path):
            print("\n索引已存在，跳过构建。")
        else:
            print("\n索引不存在，开始构建...")
            build_args = argparse.Namespace(
                output_dir=output_dir,
                force=False
            )
            self.build(build_args)
        
        print("\n开始执行查询...")
        
        query_name = args.name
        if not query_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            query_name = f"query_{timestamp}"
        
        query_args = argparse.Namespace(
            output_dir=output_dir,
            name=query_name,
            pattern=args.pattern,
            type=args.type,
            priority=args.priority,
            description=args.description,
            config=args.config,
            interactive=False,
            context_before=args.context_before,
            context_after=args.context_after,
            keep_history=args.keep_history,
            auto_build=False
        )
        self.query(query_args)
        
        print("\n" + "=" * 80)
        print("分析完成!")
        print("=" * 80)
    
    def interactive(self, args):
        """交互式模式
        
        Args:
            args: 命令行参数
        """
        print("=" * 80)
        print("Android Bug Report Analyzer - 交互式模式")
        print("=" * 80)
        
        print("\n请选择操作:")
        print("  1. 构建索引 (build)")
        print("  2. 执行查询 (query)")
        print("  3. 完整分析 (analyze)")
        print("  0. 退出")
        
        choice = input("\n请输入选项 (0-3): ").strip()
        
        if choice == '0':
            print("再见!")
            return
        
        output_dir = input("请输入输出目录路径: ").strip()
        if not output_dir:
            print("错误: 输出目录不能为空")
            return
        
        if not os.path.isdir(output_dir):
            print(f"错误: 目录不存在: {output_dir}")
            return
        
        if choice == '1':
            force = input("强制重建索引? (y/n) [n]: ").strip().lower() == 'y'
            build_args = argparse.Namespace(
                output_dir=output_dir,
                force=force
            )
            self.build(build_args)
        
        elif choice == '2':
            print("\n请选择查询模式:")
            print("  1. 单个查询")
            print("  2. 配置文件")
            print("  3. 交互式输入")
            
            query_choice = input("请输入选项 (1-3): ").strip()
            
            if query_choice == '1':
                name = input("查询名称 (例如: query_wechat_freeze): ").strip()
                pattern = input("匹配模式: ").strip()
                query_type = input("查询类型 (keyword/regex/section) [keyword]: ").strip() or 'keyword'
                priority = input("优先级 (CRITICAL/HIGH/MEDIUM/LOW) [HIGH]: ").strip() or 'HIGH'
                description = input("查询描述: ").strip()
                
                query_args = argparse.Namespace(
                    output_dir=output_dir,
                    name=name if name else None,
                    pattern=pattern,
                    type=query_type,
                    priority=priority,
                    description=description,
                    config=None,
                    interactive=False,
                    context_before=5,
                    context_after=5,
                    keep_history=False,
                    auto_build=True
                )
            
            elif query_choice == '2':
                config_path = input("请输入配置文件路径: ").strip()
                query_args = argparse.Namespace(
                    output_dir=output_dir,
                    name=None,
                    pattern=None,
                    type='keyword',
                    priority='HIGH',
                    description='',
                    config=config_path,
                    interactive=False,
                    context_before=5,
                    context_after=5,
                    keep_history=False,
                    auto_build=True
                )
            
            elif query_choice == '3':
                query_args = argparse.Namespace(
                    output_dir=output_dir,
                    name=None,
                    pattern=None,
                    type='keyword',
                    priority='HIGH',
                    description='',
                    config=None,
                    interactive=True,
                    context_before=5,
                    context_after=5,
                    keep_history=False,
                    auto_build=True
                )
            else:
                print("无效选项")
                return
            
            self.query(query_args)
        
        elif choice == '3':
            pattern = input("匹配模式: ").strip()
            query_type = input("查询类型 (keyword/regex/section) [keyword]: ").strip() or 'keyword'
            priority = input("优先级 (CRITICAL/HIGH/MEDIUM/LOW) [HIGH]: ").strip() or 'HIGH'
            description = input("查询描述: ").strip()
            
            analyze_args = argparse.Namespace(
                output_dir=output_dir,
                name=None,
                pattern=pattern,
                type=query_type,
                priority=priority,
                description=description,
                config=None,
                context_before=5,
                context_after=5,
                keep_history=False
            )
            self.analyze(analyze_args)
        
        else:
            print("无效选项")


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='Android Bug Report Analyzer - 统一命令行入口',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    build_parser = subparsers.add_parser('build', help='构建索引')
    build_parser.add_argument('output_dir', help='输出目录路径')
    build_parser.add_argument('--force', action='store_true', help='强制重建索引')
    
    query_parser = subparsers.add_parser('query', help='执行查询')
    query_parser.add_argument('output_dir', help='输出目录路径')
    
    query_group = query_parser.add_mutually_exclusive_group()
    query_group.add_argument('--name', help='查询名称（单个查询模式）')
    query_group.add_argument('--config', help='查询配置文件路径（JSON格式）')
    query_group.add_argument('--interactive', action='store_true', help='交互式输入模式')
    
    query_parser.add_argument('--pattern', help='匹配模式')
    query_parser.add_argument('--type', choices=['keyword', 'regex', 'section'],
                             default='keyword', help='查询类型（默认: keyword）')
    query_parser.add_argument('--priority', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
                             default='HIGH', help='优先级（默认: HIGH）')
    query_parser.add_argument('--description', default='', help='查询描述')
    query_parser.add_argument('--context-before', type=int, default=5,
                             help='上下文前行数（默认: 5）')
    query_parser.add_argument('--context-after', type=int, default=5,
                             help='上下文后行数（默认: 5）')
    query_parser.add_argument('--keep-history', action='store_true',
                             help='保留历史查询结果')
    query_parser.add_argument('--auto-build', action='store_true',
                             help='自动构建缺失的索引')
    
    analyze_parser = subparsers.add_parser('analyze', help='完整分析流程（build + query）')
    analyze_parser.add_argument('output_dir', help='输出目录路径')
    analyze_parser.add_argument('--name', help='查询名称')
    analyze_parser.add_argument('--pattern', help='匹配模式')
    analyze_parser.add_argument('--type', choices=['keyword', 'regex', 'section'],
                               default='keyword', help='查询类型（默认: keyword）')
    analyze_parser.add_argument('--priority', choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
                               default='HIGH', help='优先级（默认: HIGH）')
    analyze_parser.add_argument('--description', default='', help='查询描述')
    analyze_parser.add_argument('--config', help='查询配置文件路径（JSON格式）')
    analyze_parser.add_argument('--context-before', type=int, default=5,
                               help='上下文前行数（默认: 5）')
    analyze_parser.add_argument('--context-after', type=int, default=5,
                               help='上下文后行数（默认: 5）')
    analyze_parser.add_argument('--keep-history', action='store_true',
                               help='保留历史查询结果')
    
    interactive_parser = subparsers.add_parser('interactive', help='交互式模式')
    
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = CLI()
    
    try:
        if args.command == 'build':
            cli.build(args)
        elif args.command == 'query':
            cli.query(args)
        elif args.command == 'analyze':
            cli.analyze(args)
        elif args.command == 'interactive':
            cli.interactive(args)
    except CLIError as e:
        print(f"\n错误: {e}")
        if hasattr(e, 'suggestion'):
            print(f"建议: {e.suggestion}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(1)


if __name__ == '__main__':
    main()

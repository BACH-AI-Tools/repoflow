#!/usr/bin/env python3
"""
克隆GitHub仓库并发布到EMCP的命令行工具

用法:
    python clone_and_publish.py <github_url> [--prefix PREFIX] [--output OUTPUT_DIR]

示例:
    python clone_and_publish.py https://github.com/user/awesome-mcp
    python clone_and_publish.py https://github.com/user/awesome-mcp --prefix bachai
    python clone_and_publish.py https://github.com/user/awesome-mcp --output ./repos
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.workflow_executor import WorkflowExecutor
from src.unified_config_manager import UnifiedConfigManager


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="克隆GitHub仓库并发布到EMCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  克隆并发布（使用默认前缀 bachai）:
    python clone_and_publish.py https://github.com/user/awesome-mcp
  
  使用自定义前缀:
    python clone_and_publish.py https://github.com/user/awesome-mcp --prefix myprefix
  
  指定输出目录:
    python clone_and_publish.py https://github.com/user/awesome-mcp --output ./my_repos
  
  完整示例:
    python clone_and_publish.py https://github.com/user/awesome-mcp --prefix bachai --output ./repos

注意事项:
  1. 确保已配置 config.json 文件（GitHub Token、EMCP账号等）
  2. 源仓库必须是一个有效的 Python 或 Node.js 项目
  3. 包名会自动添加前缀以避免冲突
  4. 首次推送后会自动触发 GitHub Actions 进行打包发布
  5. 上游必须有允许再发布的开源许可证；会保留原 LICENSE，并写入 UPSTREAM.md 和 README 署名
        """
    )
    
    parser.add_argument(
        'github_url',
        help='要克隆的GitHub仓库URL（例如: https://github.com/user/repo）'
    )
    
    parser.add_argument(
        '--prefix',
        default='bachai',
        help='包名前缀（默认: bachai）'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='输出目录（可选，默认使用临时目录）'
    )
    
    parser.add_argument(
        '--no-tests',
        action='store_true',
        help='跳过测试步骤'
    )
    
    parser.add_argument(
        '--accept-license',
        action='store_true',
        help='上游许可证无法自动识别时，人工确认允许再发布后继续'
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("🚀 RepoFlow - 克隆和发布工具")
    print("="*70)
    print(f"📋 配置:")
    print(f"  🔗 源仓库: {args.github_url}")
    print(f"  🏷️  包名前缀: {args.prefix}")
    if args.output:
        print(f"  📁 输出目录: {args.output}")
    if args.no_tests:
        print(f"  🧪 跳过测试: 是")
    print()
    
    # 加载配置
    try:
        config_mgr = UnifiedConfigManager()
        config = config_mgr.load_config()
        
        # 检查必要的配置
        if not config.get("github", {}).get("token"):
            print("❌ 错误: 未配置 GitHub Token")
            print("💡 请在 config.json 中配置 github.token")
            sys.exit(1)
        
        if not config.get("github", {}).get("org_name"):
            print("❌ 错误: 未配置 GitHub 组织名称")
            print("💡 请在 config.json 中配置 github.org_name")
            sys.exit(1)
        
        print("✅ 配置加载成功")
        print(f"  📦 目标组织: {config['github']['org_name']}")
        print()
        
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        print("💡 请确保 config.json 文件存在且格式正确")
        sys.exit(1)
    
    # 创建工作流执行器
    executor = WorkflowExecutor(config_mgr)
    
    # 执行克隆和发布工作流程
    try:
        result = executor.workflow_clone_and_publish(
            github_url=args.github_url,
            prefix=args.prefix,
            output_dir=args.output,
            accept_unknown_license=args.accept_license
        )
        
        # 显示结果
        print("\n" + "="*70)
        if result['success']:
            print("✅ 工作流程执行成功！")
            print("="*70)
            print(f"\n📊 执行结果:")
            print(f"  📦 包名: {result.get('package_name', 'N/A')}")
            print(f"  🔗 GitHub仓库: {result.get('github_repo_url', 'N/A')}")
            if result.get('template_id'):
                print(f"  🆔 EMCP模板ID: {result['template_id']}")
            print(f"\n✅ 完成步骤 ({len(result['steps_completed'])} 个):")
            for step in result['steps_completed']:
                print(f"    ✓ {step}")
            
            if result.get('errors'):
                print(f"\n⚠️  警告 ({len(result['errors'])} 个):")
                for error in result['errors']:
                    print(f"    • {error}")
            
            print("\n🎉 恭喜！包已成功克隆、修改并发布到EMCP平台")
            sys.exit(0)
        else:
            print("❌ 工作流程执行失败")
            print("="*70)
            print(f"\n错误: {result.get('error', '未知错误')}")
            print(f"\n已完成步骤:")
            for step in result['steps_completed']:
                print(f"  ✓ {step}")
            
            if result.get('error_trace'):
                print(f"\n详细错误信息:")
                print(result['error_trace'])
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        sys.exit(130)
    except Exception as e:
        import traceback
        print(f"\n❌ 执行失败: {e}")
        print("\n详细错误:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()






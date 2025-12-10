#!/usr/bin/env python3
"""
批量发布文件夹中的所有 MCP 项目

功能：
1. 扫描指定文件夹中的所有子文件夹
2. 对每个项目执行发布流程：GitHub + EMCP
3. 只发布到 EMCP，不执行测试（避免服务器压力）
4. 记录已处理的项目，支持断点续传

用法：
    python batch_publish_folder.py E:\\1\\generated_mcps
    python batch_publish_folder.py E:\\1\\generated_mcps --limit 5
    python batch_publish_folder.py E:\\1\\generated_mcps --skip-github  # 只发布到EMCP
    python batch_publish_folder.py E:\\1\\generated_mcps --continue  # 从上次中断处继续
    python batch_publish_folder.py E:\\1\\generated_mcps --api-key YOUR_KEY  # 指定默认API Key
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.unified_config_manager import UnifiedConfigManager
from src.workflow_executor import WorkflowExecutor

# 进度记录文件
PROGRESS_FILE = Path("outputs/batch_publish_progress.json")
REPORT_FILE = Path("outputs/batch_publish_report.json")


class BatchFolderPublisher:
    """批量文件夹发布器"""
    
    def __init__(self, source_folder: str, prefix: str = "bachai", default_api_key: str = ""):
        self.source_folder = Path(source_folder)
        self.prefix = prefix
        self.config_mgr = UnifiedConfigManager()
        self.default_api_key = default_api_key  # 默认 API Key（用于 RapidAPI 等）
        
        # 进度记录
        self.progress: Dict[str, dict] = {}
        self._load_progress()
        
        # 统计
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # 失败项目列表
        self.failed_projects: List[dict] = []
    
    def _load_progress(self):
        """加载进度记录"""
        try:
            if PROGRESS_FILE.exists():
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    self.progress = json.load(f)
                print(f"📋 已加载进度记录: {len(self.progress)} 个项目")
        except Exception as e:
            print(f"⚠️ 加载进度记录失败: {e}")
            self.progress = {}
    
    def _save_progress(self, project_name: str, status: str, details: dict = None):
        """保存进度记录"""
        try:
            PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.progress[project_name] = {
                "status": status,
                "updated_at": datetime.now().isoformat(),
                "details": details or {}
            }
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存进度记录失败: {e}")
    
    def _save_report(self):
        """保存最终报告"""
        try:
            REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
            report = {
                "source_folder": str(self.source_folder),
                "generated_at": datetime.now().isoformat(),
                "stats": self.stats,
                "failed_projects": self.failed_projects
            }
            with open(REPORT_FILE, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📄 报告已保存: {REPORT_FILE}")
        except Exception as e:
            print(f"⚠️ 保存报告失败: {e}")
    
    def is_already_processed(self, project_name: str) -> bool:
        """检查项目是否已处理过"""
        if project_name not in self.progress:
            return False
        return self.progress[project_name].get("status") == "success"
    
    def get_project_folders(self) -> List[Path]:
        """获取所有项目文件夹"""
        if not self.source_folder.exists():
            print(f"❌ 文件夹不存在: {self.source_folder}")
            return []
        
        projects = []
        for item in self.source_folder.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 检查是否是有效的 Python 项目
                if (item / "pyproject.toml").exists() or (item / "setup.py").exists():
                    projects.append(item)
                # 检查是否是有效的 Node.js 项目
                elif (item / "package.json").exists():
                    projects.append(item)
        
        # 按名称排序
        projects.sort(key=lambda p: p.name)
        return projects
    
    def publish_single_project(
        self, 
        project_path: Path, 
        skip_github: bool = False
    ) -> Dict:
        """
        发布单个项目
        
        Args:
            project_path: 项目路径
            skip_github: 是否跳过 GitHub（只发布到 EMCP）
        
        Returns:
            发布结果
        """
        project_name = project_path.name
        result = {
            "project_name": project_name,
            "project_path": str(project_path),
            "success": False,
            "steps_completed": [],
            "error": None
        }
        
        print(f"\n{'='*70}")
        print(f"📦 发布项目: {project_name}")
        print(f"{'='*70}")
        print(f"📁 路径: {project_path}")
        
        try:
            # 创建执行器
            executor = WorkflowExecutor(self.config_mgr)
            
            # 检测项目信息
            from src.project_detector import ProjectDetector
            detector = ProjectDetector(project_path)
            project_info = detector.detect()
            
            # 生成新包名（添加前缀，避免重复）
            original_name = project_info.get('package_name', project_name)
            
            # ⭐ 清理原始包名中已有的前缀（避免 bachai-bach-xxx 这种情况）
            clean_name = original_name.lower().replace('_', '-')
            # 移除已有的 bach-、bachai-、bach_ 前缀
            for old_prefix in ['bach-', 'bachai-', 'bach_', 'bachai_']:
                if clean_name.startswith(old_prefix):
                    clean_name = clean_name[len(old_prefix):]
            
            new_package_name = f"{self.prefix}-{clean_name}"
            
            # 设置项目信息
            executor.project_path = project_path
            executor.package_name = new_package_name
            executor.repo_name = new_package_name
            executor.package_type = project_info.get('type', 'python').lower()
            executor.version = project_info.get('version', '1.0.0')
            executor.org_name = self.config_mgr.load_config().get('github', {}).get('org_name', 'BACH-AI-Tools')
            
            # ⭐ 直接设置 API_KEY 环境变量（这些 RapidAPI MCP 只需要 API_KEY）
            # 不使用检测器，因为它会误检测 README 中的 HOST/PORT 等词
            executor.env_vars_config = []
            
            if self.default_api_key:
                print(f"   🔧 配置 API_KEY 环境变量: {self.default_api_key[:20]}...")
                executor.env_vars_config = [{
                    'name': 'API_KEY',
                    'description': 'RapidAPI Key',
                    'required': True,
                    'example': self.default_api_key  # 这个值会被用作 default_value
                }]
            else:
                print(f"   ⚠️ 未提供 API Key，跳过环境变量配置")
            
            print(f"📦 原始包名: {original_name}")
            print(f"📦 新包名: {new_package_name}")
            print(f"🔧 项目类型: {executor.package_type}")
            print(f"🏷️ 版本: {executor.version}")
            
            # ===== GitHub 发布流程 =====
            if not skip_github:
                # 1. 扫描敏感信息
                print(f"\n📋 步骤 1: 扫描敏感信息...")
                executor.step_scan_project()
                result['steps_completed'].append('scan')
                
                # 2. 创建 GitHub 仓库
                print(f"\n📋 步骤 2: 创建 GitHub 仓库...")
                executor.step_create_repo()
                result['steps_completed'].append('create_repo')
                result['github_repo_url'] = executor.github_repo_url
                
                # 3. 生成 Pipeline
                print(f"\n📋 步骤 3: 生成 CI/CD Pipeline...")
                executor.step_generate_pipeline()
                result['steps_completed'].append('generate_pipeline')
                
                # 4. 推送代码
                print(f"\n📋 步骤 4: 推送代码到 GitHub...")
                executor.step_push_code()
                result['steps_completed'].append('push_code')
                
                # 5. 触发发布
                print(f"\n📋 步骤 5: 触发发布并等待...")
                executor.step_trigger_publish()
                result['steps_completed'].append('trigger_publish')
            
            # ===== EMCP 发布流程 =====
            # 6. 获取包信息
            print(f"\n📋 步骤 6: 获取包信息...")
            executor.step_fetch_package()
            result['steps_completed'].append('fetch_package')
            
            # 7. AI 生成模板
            print(f"\n📋 步骤 7: AI 生成模板...")
            executor.step_ai_generate()
            result['steps_completed'].append('ai_generate')
            
            # 8. 生成 Logo
            print(f"\n📋 步骤 8: 生成 Logo...")
            try:
                executor.step_generate_logo()
                result['steps_completed'].append('generate_logo')
            except Exception as e:
                print(f"   ⚠️ Logo 生成失败: {e}")
            
            # 9. 发布到 EMCP
            print(f"\n📋 步骤 9: 发布到 EMCP...")
            executor.step_publish_emcp()
            result['steps_completed'].append('publish_emcp')
            result['template_id'] = executor.template_id
            
            # ⭐ 跳过测试步骤（避免 EMCP 服务器压力过大）
            # 测试会启动 MCP Server，批量处理时会导致服务器资源不足
            print(f"\n✅ 发布完成，跳过测试步骤（批量模式）")
            
            result['success'] = True
            result['package_name'] = new_package_name
            
            print(f"\n✅ 项目发布成功: {new_package_name}")
            
        except Exception as e:
            import traceback
            result['success'] = False
            result['error'] = str(e)
            result['error_trace'] = traceback.format_exc()
            
            print(f"\n❌ 项目发布失败: {project_name}")
            print(f"   错误: {e}")
            
            # ⭐ 如果是网络问题，提供额外提示
            error_str = str(e).lower()
            if 'connect' in error_str or 'timeout' in error_str or 'network' in error_str:
                print(f"   💡 这看起来是网络连接问题")
                print(f"   💡 使用 --continue 可以从失败处继续")
        
        return result
    
    def run(
        self, 
        limit: int = None, 
        skip_github: bool = False,
        continue_from_last: bool = False,
        delay_seconds: int = 5
    ):
        """
        运行批量发布（发布到 EMCP 后结束，不执行测试）
        
        Args:
            limit: 限制处理数量
            skip_github: 是否跳过 GitHub
            continue_from_last: 是否从上次中断处继续
            delay_seconds: 每个项目之间的延迟秒数
        """
        print("\n" + "="*70)
        print("🚀 批量发布 MCP 项目（发布模式，不测试）")
        print("="*70)
        print(f"📁 源文件夹: {self.source_folder}")
        print(f"🏷️ 包名前缀: {self.prefix}")
        print(f"⏭️ 跳过 GitHub: {'是' if skip_github else '否'}")
        print(f"🔄 断点续传: {'是' if continue_from_last else '否'}")
        
        # 获取所有项目
        projects = self.get_project_folders()
        
        if not projects:
            print(f"\n❌ 未找到有效项目")
            return
        
        print(f"\n📋 找到 {len(projects)} 个项目")
        
        # 过滤已处理的项目
        if continue_from_last:
            projects = [p for p in projects if not self.is_already_processed(p.name)]
            print(f"   (排除已处理项目后: {len(projects)} 个)")
        
        # 应用限制
        if limit and limit > 0:
            projects = projects[:limit]
            print(f"   (限制处理前 {limit} 个)")
        
        self.stats["total"] = len(projects)
        
        # 逐个处理
        for i, project_path in enumerate(projects, 1):
            project_name = project_path.name
            
            print(f"\n\n{'#'*70}")
            print(f"# [{i}/{len(projects)}] {project_name}")
            print(f"{'#'*70}")
            
            # 检查是否已处理
            if continue_from_last and self.is_already_processed(project_name):
                print(f"⏭️ 已处理过，跳过")
                self.stats["skipped"] += 1
                continue
            
            # 发布项目
            result = self.publish_single_project(
                project_path,
                skip_github=skip_github
            )
            
            # 更新统计和进度
            if result['success']:
                self.stats["success"] += 1
                self._save_progress(project_name, "success", {
                    "package_name": result.get('package_name'),
                    "template_id": result.get('template_id'),
                    "github_repo_url": result.get('github_repo_url')
                })
            else:
                self.stats["failed"] += 1
                self.failed_projects.append({
                    "project_name": project_name,
                    "error": result.get('error'),
                    "steps_completed": result.get('steps_completed', [])
                })
                self._save_progress(project_name, "failed", {
                    "error": result.get('error')
                })
            
            # 延迟（避免请求过快）
            if i < len(projects):
                print(f"\n⏳ 等待 {delay_seconds} 秒后处理下一个项目...")
                time.sleep(delay_seconds)
        
        # 保存报告
        self._save_report()
        
        # 打印统计
        print("\n" + "="*70)
        print("📊 批量发布统计")
        print("="*70)
        print(f"   总数: {self.stats['total']}")
        print(f"   成功: {self.stats['success']}")
        print(f"   失败: {self.stats['failed']}")
        print(f"   跳过: {self.stats['skipped']}")
        
        if self.failed_projects:
            print(f"\n❌ 失败项目列表:")
            for item in self.failed_projects:
                print(f"   - {item['project_name']}: {item['error']}")
        
        print("="*70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量发布 MCP 项目到 GitHub 和 EMCP（只发布，不测试）')
    parser.add_argument('folder', help='包含 MCP 项目的文件夹路径')
    parser.add_argument('--prefix', default='bachai', help='包名前缀 (默认: bachai)')
    parser.add_argument('--limit', type=int, default=None, help='限制处理数量')
    parser.add_argument('--skip-github', action='store_true', help='跳过 GitHub 发布（只发布到 EMCP）')
    parser.add_argument('--continue', dest='continue_from_last', action='store_true', 
                       help='从上次中断处继续')
    parser.add_argument('--delay', type=int, default=5, help='每个项目之间的延迟秒数 (默认: 5)')
    parser.add_argument('--clear-progress', action='store_true', help='清除进度记录')
    parser.add_argument('--api-key', type=str, default='', help='默认 API Key（用于 RapidAPI 等服务）')
    
    args = parser.parse_args()
    
    # 清除进度记录
    if args.clear_progress:
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
            print(f"✅ 已清除进度记录: {PROGRESS_FILE}")
        return
    
    # 运行批量发布
    publisher = BatchFolderPublisher(args.folder, args.prefix, args.api_key)
    publisher.run(
        limit=args.limit,
        skip_github=args.skip_github,
        continue_from_last=args.continue_from_last,
        delay_seconds=args.delay
    )


if __name__ == '__main__':
    main()


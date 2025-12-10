#!/usr/bin/env python3
"""
批量发布脚本 - 自动发布多个 MCP 项目
运行方式: python batch_publish.py <目录路径>
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 设置 UTF-8 编码
if sys.platform == 'win32':
    if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from src.unified_config_manager import UnifiedConfigManager
from src.workflow_executor import WorkflowExecutor
from src.project_detector import ProjectDetector


# 默认 API Key - 用于批量发布时自动配置环境变量
DEFAULT_API_KEY = "c73d0eb842msh082900adbe7d22cp15a3e0jsn8156d94adb0d"


class BatchPublisher:
    """批量发布器"""
    
    def __init__(self, projects_dir: str):
        self.projects_dir = Path(projects_dir)
        self.config_mgr = UnifiedConfigManager()
        
        # 发布结果记录
        self.results: Dict[str, Dict] = {}
        self.failed_projects: List[str] = []
        self.success_projects: List[str] = []
        self.skipped_projects: List[str] = []
        
        # 报告文件路径
        self.report_file = Path("batch_publish_report.json")
        self.failed_file = Path("failed_projects.json")
        
    def discover_projects(self) -> List[Path]:
        """发现所有可发布的项目"""
        projects = []
        
        if not self.projects_dir.exists():
            print(f"❌ 目录不存在: {self.projects_dir}")
            return projects
        
        for item in self.projects_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 检查是否有有效的项目文件
                has_pyproject = (item / "pyproject.toml").exists()
                has_package_json = (item / "package.json").exists()
                has_setup_py = (item / "setup.py").exists()
                
                if has_pyproject or has_package_json or has_setup_py:
                    projects.append(item)
                    print(f"  ✓ 发现项目: {item.name}")
                else:
                    print(f"  ⊘ 跳过: {item.name} (无项目配置文件)")
        
        return projects
    
    def publish_project(self, project_path: Path) -> Dict:
        """发布单个项目"""
        project_name = project_path.name
        result = {
            'project': project_name,
            'path': str(project_path),
            'success': False,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration': 0,
            'steps_completed': [],
            'error': None,
            'github_url': None,
            'template_id': None
        }
        
        print(f"\n{'#'*70}")
        print(f"📦 开始发布: {project_name}")
        print(f"📁 路径: {project_path}")
        print(f"{'#'*70}")
        
        start_time = time.time()
        
        try:
            # 检测项目信息
            detector = ProjectDetector(str(project_path))
            project_info = detector.detect()
            
            project_type = project_info.get('type', 'unknown')
            version = project_info.get('version', '1.0.0')
            
            print(f"🔧 项目类型: {project_type}")
            print(f"🏷️ 版本: {version}")
            
            # 创建执行器
            executor = WorkflowExecutor(self.config_mgr)
            
            # 设置项目信息
            executor.set_project_info(
                project_path=str(project_path),
                repo_name=project_name,
                version=version
            )
            
            # 设置包类型
            executor.package_type = project_type
            executor.package_name = project_name
            
            # 进度回调
            def progress_callback(progress):
                print(f"   📊 进度: {progress}%")
            executor.set_progress_callback(progress_callback)
            
            # ===== GitHub 发布流程 =====
            print(f"\n{'='*50}")
            print(f"📤 阶段 1: GitHub 发布")
            print(f"{'='*50}")
            
            # 1. 扫描项目
            print(f"\n🔍 步骤 1/5: 扫描项目...")
            executor.step_scan_project()
            result['steps_completed'].append('scan')
            
            # 2. 创建仓库
            print(f"\n📦 步骤 2/5: 创建 GitHub 仓库...")
            executor.step_create_repo()
            result['steps_completed'].append('create_repo')
            result['github_url'] = executor.github_repo_url
            
            # 3. 生成 Pipeline
            print(f"\n⚙️ 步骤 3/5: 生成 CI/CD Pipeline...")
            executor.step_generate_pipeline()
            result['steps_completed'].append('generate_pipeline')
            
            # 4. 推送代码
            print(f"\n📤 步骤 4/5: 推送代码...")
            executor.step_push_code()
            result['steps_completed'].append('push_code')
            
            # 5. 触发发布
            print(f"\n🚀 步骤 5/5: 触发发布...")
            executor.step_trigger_publish()
            result['steps_completed'].append('trigger_publish')
            
            # ===== EMCP 发布流程 =====
            print(f"\n{'='*50}")
            print(f"🌐 阶段 2: EMCP 发布")
            print(f"{'='*50}")
            
            # 6. 获取包信息
            print(f"\n📋 步骤 1/4: 获取包信息...")
            executor.step_fetch_package()
            result['steps_completed'].append('fetch_package')
            
            # 7. AI 生成模板 - 预先配置环境变量，避免弹窗
            print(f"\n🤖 步骤 2/4: AI 生成模板...")
            # 预设环境变量配置，使用默认 API Key
            executor.env_vars_config = [
                {
                    'name': 'API_KEY',
                    'description': 'API 密钥',
                    'example': DEFAULT_API_KEY,
                    'required': True
                }
            ]
            print(f"   📋 自动配置 API_KEY: {DEFAULT_API_KEY[:20]}...")
            executor.step_ai_generate()
            result['steps_completed'].append('ai_generate')
            
            # 8. 生成 Logo
            print(f"\n🎨 步骤 3/4: 生成 Logo...")
            try:
                executor.step_generate_logo()
                result['steps_completed'].append('generate_logo')
            except Exception as e:
                print(f"   ⚠️ Logo 生成失败: {e}")
            
            # 9. 发布到 EMCP
            print(f"\n🌐 步骤 4/4: 发布到 EMCP...")
            executor.step_publish_emcp()
            result['steps_completed'].append('publish_emcp')
            result['template_id'] = executor.template_id
            
            # ===== 测试流程 (可选) =====
            print(f"\n{'='*50}")
            print(f"🧪 阶段 3: 测试 (可选)")
            print(f"{'='*50}")
            
            # 10. MCP 测试
            print(f"\n🧪 步骤 1/3: MCP 测试...")
            try:
                executor.step_test_mcp()
                result['steps_completed'].append('test_mcp')
            except Exception as e:
                print(f"   ⚠️ MCP 测试失败: {e}")
            
            # 11. Agent 测试
            print(f"\n🤖 步骤 2/3: Agent 测试...")
            try:
                executor.step_test_agent()
                result['steps_completed'].append('test_agent')
            except Exception as e:
                print(f"   ⚠️ Agent 测试失败: {e}")
            
            # 12. 对话测试
            print(f"\n💬 步骤 3/3: 对话测试...")
            try:
                executor.step_test_chat()
                result['steps_completed'].append('test_chat')
            except Exception as e:
                print(f"   ⚠️ 对话测试失败: {e}")
            
            # 成功
            result['success'] = True
            self.success_projects.append(project_name)
            
            print(f"\n✅ 项目 {project_name} 发布成功!")
            
        except Exception as e:
            result['error'] = str(e)
            self.failed_projects.append(project_name)
            
            print(f"\n❌ 项目 {project_name} 发布失败!")
            print(f"   错误: {e}")
            
            import traceback
            result['error_trace'] = traceback.format_exc()
        
        # 记录时间
        end_time = time.time()
        result['end_time'] = datetime.now().isoformat()
        result['duration'] = round(end_time - start_time, 2)
        
        print(f"\n⏱️ 耗时: {result['duration']} 秒")
        print(f"📋 完成步骤: {', '.join(result['steps_completed'])}")
        
        return result
    
    def run(self, skip_existing: bool = True, max_projects: Optional[int] = None):
        """运行批量发布"""
        print(f"\n{'='*70}")
        print(f"🏭 MCP 工厂 - 批量发布")
        print(f"{'='*70}")
        print(f"📁 项目目录: {self.projects_dir}")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 发现项目
        print(f"\n🔍 扫描项目目录...")
        projects = self.discover_projects()
        
        if not projects:
            print(f"\n❌ 未发现任何可发布的项目")
            return
        
        print(f"\n📊 发现 {len(projects)} 个项目")
        
        # 限制发布数量
        if max_projects:
            projects = projects[:max_projects]
            print(f"   限制发布数量: {max_projects}")
        
        # 加载之前的失败记录
        previously_failed = self._load_failed_projects()
        if previously_failed:
            print(f"\n📋 之前失败的项目: {len(previously_failed)} 个")
            for name in previously_failed:
                print(f"   • {name}")
        
        # 开始发布
        total = len(projects)
        for i, project in enumerate(projects, 1):
            project_name = project.name
            
            print(f"\n{'='*70}")
            print(f"📦 [{i}/{total}] {project_name}")
            print(f"{'='*70}")
            
            # 检查是否已经成功发布过
            if skip_existing and self._check_already_published(project_name):
                print(f"⏭️ 跳过: 已发布")
                self.skipped_projects.append(project_name)
                continue
            
            # 发布项目
            result = self.publish_project(project)
            self.results[project_name] = result
            
            # 保存中间结果
            self._save_results()
            
            # 短暂休息，避免 API 限流
            if i < total:
                print(f"\n⏳ 等待 3 秒后继续...")
                time.sleep(3)
        
        # 最终报告
        self._print_summary()
        self._save_results()
    
    def _check_already_published(self, project_name: str) -> bool:
        """检查项目是否已经成功发布"""
        # 可以扩展：检查 GitHub、EMCP 等
        return False
    
    def _load_failed_projects(self) -> List[str]:
        """加载之前失败的项目列表"""
        if self.failed_file.exists():
            try:
                with open(self.failed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('failed_projects', [])
            except:
                pass
        return []
    
    def _save_results(self):
        """保存结果"""
        # 保存完整报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'projects_dir': str(self.projects_dir),
            'total_projects': len(self.results),
            'success_count': len(self.success_projects),
            'failed_count': len(self.failed_projects),
            'skipped_count': len(self.skipped_projects),
            'success_projects': self.success_projects,
            'failed_projects': self.failed_projects,
            'skipped_projects': self.skipped_projects,
            'details': self.results
        }
        
        with open(self.report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 保存失败项目列表（方便下次重试）
        failed_data = {
            'generated_at': datetime.now().isoformat(),
            'failed_projects': self.failed_projects,
            'details': {
                name: {
                    'path': self.results[name]['path'],
                    'error': self.results[name].get('error'),
                    'steps_completed': self.results[name].get('steps_completed', [])
                }
                for name in self.failed_projects
                if name in self.results
            }
        }
        
        with open(self.failed_file, 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, ensure_ascii=False, indent=2)
    
    def _print_summary(self):
        """打印汇总报告"""
        print(f"\n{'='*70}")
        print(f"📊 批量发布汇总报告")
        print(f"{'='*70}")
        print(f"📁 项目目录: {self.projects_dir}")
        print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"")
        print(f"📈 统计:")
        print(f"   总项目数: {len(self.results) + len(self.skipped_projects)}")
        print(f"   ✅ 成功: {len(self.success_projects)}")
        print(f"   ❌ 失败: {len(self.failed_projects)}")
        print(f"   ⏭️ 跳过: {len(self.skipped_projects)}")
        
        if self.success_projects:
            print(f"\n✅ 成功的项目:")
            for name in self.success_projects:
                result = self.results.get(name, {})
                github_url = result.get('github_url', 'N/A')
                template_id = result.get('template_id', 'N/A')
                print(f"   • {name}")
                print(f"     GitHub: {github_url}")
                if template_id:
                    print(f"     模板ID: {template_id}")
        
        if self.failed_projects:
            print(f"\n❌ 失败的项目:")
            for name in self.failed_projects:
                result = self.results.get(name, {})
                error = result.get('error', '未知错误')
                steps = result.get('steps_completed', [])
                print(f"   • {name}")
                print(f"     错误: {error}")
                print(f"     已完成步骤: {', '.join(steps) if steps else '无'}")
        
        print(f"\n📄 报告文件:")
        print(f"   完整报告: {self.report_file.absolute()}")
        print(f"   失败列表: {self.failed_file.absolute()}")
        print(f"{'='*70}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP 工厂 - 批量发布脚本')
    parser.add_argument('dir', nargs='?', default=r"E:\code\APItoMCP\generated_mcps",
                       help='项目目录路径')
    parser.add_argument('-n', '--max', type=int, default=None,
                       help='最大发布数量')
    parser.add_argument('-y', '--yes', action='store_true',
                       help='跳过确认，自动开始')
    parser.add_argument('--retry-failed', action='store_true',
                       help='只重试之前失败的项目')
    
    args = parser.parse_args()
    
    projects_dir = args.dir
    max_projects = args.max
    auto_confirm = args.yes
    
    print(f"🏭 MCP 工厂 - 批量发布脚本")
    print(f"📁 目录: {projects_dir}")
    if max_projects:
        print(f"📊 限制: 最多 {max_projects} 个项目")
    
    # 确认开始
    if not auto_confirm:
        print(f"\n⚠️ 即将开始批量发布，这可能需要较长时间")
        response = input("是否继续? [y/N]: ").strip().lower()
        
        if response != 'y':
            print("已取消")
            return
    
    # 运行批量发布
    publisher = BatchPublisher(projects_dir)
    publisher.run(skip_existing=True, max_projects=max_projects)


if __name__ == "__main__":
    main()


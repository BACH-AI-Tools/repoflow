#!/usr/bin/env python3
"""
批量 MCP 工厂 - 批量执行完整的 MCP 发布流程
"""

import sys
import os
from pathlib import Path
from typing import List, Dict
import time
from datetime import datetime
import json
import re

# 尝试导入 tomllib (Python 3.11+) 或 tomli (旧版本)
try:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib
        except ImportError:
            tomllib = None
except:
    tomllib = None

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.unified_config_manager import UnifiedConfigManager
from src.workflow_executor import WorkflowExecutor
from src.project_detector import ProjectDetector


class BatchMCPFactory:
    """批量 MCP 工厂"""
    
    def __init__(self, projects_dir: str):
        """
        初始化批量处理器
        
        Args:
            projects_dir: MCP 项目所在的文件夹路径
        """
        self.projects_dir = Path(projects_dir)
        self.config_mgr = UnifiedConfigManager()
        self.projects = []
        self.results = []
        
    def scan_projects(self) -> List[Dict]:
        """扫描所有 MCP 项目"""
        print(f"\n{'='*70}")
        print(f"📂 扫描项目目录")
        print(f"{'='*70}")
        print(f"路径: {self.projects_dir}")
        
        if not self.projects_dir.exists():
            print(f"❌ 目录不存在: {self.projects_dir}")
            return []
        
        self.projects = []
        
        # 遍历所有子目录
        for item in self.projects_dir.iterdir():
            if not item.is_dir():
                continue
            
            # 跳过隐藏目录和特殊目录
            if item.name.startswith('.') or item.name in ['node_modules', '__pycache__', 'venv', 'dist', 'build', 'outputs']:
                continue
            
            # 检测项目类型
            try:
                # 直接检查项目文件，不完全依赖 ProjectDetector
                has_pyproject = (item / 'pyproject.toml').exists()
                has_setup_py = (item / 'setup.py').exists()
                has_package_json = (item / 'package.json').exists()
                
                # 判断项目类型
                project_type = None
                package_name = item.name
                version = '1.0.0'
                description = ''
                
                if has_pyproject or has_setup_py:
                    project_type = 'python'
                    # 尝试从 pyproject.toml 读取信息
                    if has_pyproject:
                        try:
                            if tomllib:
                                with open(item / 'pyproject.toml', 'rb') as f:
                                    data = tomllib.load(f)
                                    package_name = data.get('project', {}).get('name', item.name)
                                    version = data.get('project', {}).get('version', '1.0.0')
                                    description = data.get('project', {}).get('description', '')
                            else:
                                # 如果 tomllib 不可用，使用简单的文本解析
                                with open(item / 'pyproject.toml', 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                                    if name_match:
                                        package_name = name_match.group(1)
                                    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                                    if version_match:
                                        version = version_match.group(1)
                                    desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
                                    if desc_match:
                                        description = desc_match.group(1)
                        except Exception as parse_error:
                            print(f"      解析 pyproject.toml 时出错: {parse_error}")
                            pass
                
                elif has_package_json:
                    project_type = 'node.js'
                    # 尝试从 package.json 读取信息
                    try:
                        with open(item / 'package.json', 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            package_name = data.get('name', item.name)
                            version = data.get('version', '1.0.0')
                            description = data.get('description', '')
                    except Exception as parse_error:
                        print(f"      解析 package.json 时出错: {parse_error}")
                        pass
                
                if project_type:
                    project_data = {
                        'path': item,
                        'name': item.name,
                        'type': project_type,
                        'package_name': package_name,
                        'version': version,
                        'description': description,
                    }
                    self.projects.append(project_data)
                    print(f"  ✅ 发现项目: {item.name} ({project_type}) - {package_name}")
                else:
                    print(f"  ⚠️ 跳过 {item.name}: 不是有效的 MCP 项目")
                    
            except Exception as e:
                print(f"  ⚠️ 跳过 {item.name}: {e}")
                import traceback
                print(f"      详细错误: {traceback.format_exc()}")
        
        print(f"\n✅ 找到 {len(self.projects)} 个 MCP 项目")
        return self.projects
    
    def list_projects(self):
        """列出所有项目"""
        if not self.projects:
            print("⚠️ 没有找到项目，请先运行 scan_projects()")
            return
        
        print(f"\n{'='*70}")
        print(f"📋 MCP 项目列表")
        print(f"{'='*70}")
        
        for i, proj in enumerate(self.projects, 1):
            print(f"\n{i}. {proj['name']}")
            print(f"   路径: {proj['path']}")
            print(f"   类型: {proj['type']}")
            print(f"   包名: {proj['package_name']}")
            print(f"   版本: {proj['version']}")
            if proj['description']:
                desc = proj['description'][:60] + '...' if len(proj['description']) > 60 else proj['description']
                print(f"   描述: {desc}")
        
        print(f"\n{'='*70}")
    
    def process_project(self, project: Dict, index: int, total: int) -> Dict:
        """
        处理单个项目 - 执行完整的 MCP 工厂流程
        
        Args:
            project: 项目信息
            index: 当前项目索引（从 1 开始）
            total: 总项目数
            
        Returns:
            Dict: 处理结果
        """
        print(f"\n{'='*70}")
        print(f"🏭 处理项目 [{index}/{total}]")
        print(f"{'='*70}")
        print(f"项目: {project['name']}")
        print(f"路径: {project['path']}")
        print(f"类型: {project['type']}")
        print(f"{'='*70}")
        
        result = {
            'project_name': project['name'],
            'success': False,
            'start_time': datetime.now(),
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # 创建工作流执行器
            executor = WorkflowExecutor(self.config_mgr)
            
            # 保存正确的包名（用于后续验证）
            correct_package_name = project['package_name']
            
            # 设置项目信息
            executor.set_project_info(
                project_path=str(project['path']),
                repo_name=correct_package_name,
                version=project['version']
            )
            
            # 强制设置包名
            executor.package_name = correct_package_name
            
            # 辅助函数：确保包名正确
            def ensure_package_name():
                if executor.package_name != correct_package_name:
                    print(f"   🔧 恢复包名: {correct_package_name}")
                    executor.package_name = correct_package_name
            
            # ===== 步骤 1: 扫描项目 =====
            print(f"\n▶️ 步骤 1/12: 扫描项目")
            executor.step_scan_project()
            result['steps_completed'].append('扫描项目')
            ensure_package_name()
            
            # ===== 步骤 2: 创建 GitHub 仓库 =====
            print(f"\n▶️ 步骤 2/12: 创建 GitHub 仓库")
            executor.step_create_repo()
            result['steps_completed'].append('创建 GitHub 仓库')
            result['github_url'] = executor.github_repo_url
            
            # ===== 步骤 3: 生成 CI/CD Pipeline =====
            print(f"\n▶️ 步骤 3/12: 生成 CI/CD Pipeline")
            executor.step_generate_pipeline()
            result['steps_completed'].append('生成 Pipeline')
            
            # ===== 步骤 4: 推送代码 =====
            print(f"\n▶️ 步骤 4/12: 推送代码到 GitHub")
            executor.step_push_code()
            result['steps_completed'].append('推送代码')
            
            # ===== 步骤 5: 触发发布 =====
            print(f"\n▶️ 步骤 5/12: 触发发布并等待完成")
            executor.step_trigger_publish()
            result['steps_completed'].append('触发发布')
            
            # ===== 步骤 6: 获取包信息 =====
            print(f"\n▶️ 步骤 6/12: 获取包信息")
            # 在批量模式下，直接使用扫描时获取的包名（带 bach- 前缀）
            print(f"📦 使用批量扫描的包名: {correct_package_name}")
            executor.package_name = correct_package_name
            
            # 仍然调用 step_fetch_package() 来提取命令
            executor.step_fetch_package()
            
            # 强制确保使用正确的包名
            ensure_package_name()
            result['steps_completed'].append('获取包信息')
            result['package_name'] = executor.package_name
            print(f"✅ 最终包名: {executor.package_name}")
            
            # ===== 步骤 7: AI 生成模板 =====
            print(f"\n▶️ 步骤 7/12: AI 生成模板")
            try:
                # 在批量模式下，自动配置环境变量（不弹出对话框）
                print(f"💡 批量模式：自动配置环境变量")
                
                # 检测项目中的环境变量
                from src.env_var_detector import EnvVarDetector
                detector = EnvVarDetector()
                env_vars = detector.detect_from_project(executor.project_path)
                
                # 自动填充常见的环境变量
                auto_filled_vars = []
                for var in env_vars:
                    var_name = var['name']
                    var_config = {
                        'name': var_name,
                        'description': var.get('description', var_name),
                        'required': var.get('required', False),
                        'example': ''
                    }
                    
                    # 自动填充已知的环境变量
                    if var_name == 'API_KEY':
                        var_config['example'] = os.environ.get('API_KEY', '')
                        var_config['description'] = 'API 密钥'
                        print(f"   ✅ 自动填充: API_KEY")
                    elif var_name == 'HOST':
                        var_config['example'] = 'api.example.com'
                        var_config['description'] = '服务主机地址'
                        print(f"   ✅ 自动填充: HOST")
                    elif 'API' in var_name:
                        var_config['example'] = 'your-api-key-here'
                        var_config['description'] = f'{var_name} 配置'
                        print(f"   ✅ 自动填充: {var_name}")
                    else:
                        var_config['example'] = 'your-value-here'
                        print(f"   ℹ️  占位符: {var_name}")
                    
                    auto_filled_vars.append(var_config)
                
                # 将自动配置的环境变量设置到 executor
                executor.env_vars_config = auto_filled_vars
                print(f"   已配置 {len(auto_filled_vars)} 个环境变量")
                
                # 初始化 AI Generator（如果配置了的话）
                try:
                    ai_config = self.config_mgr.load_config().get("azure_openai", {})
                    if ai_config.get("endpoint") and ai_config.get("api_key"):
                        from src.ai_generator import AITemplateGenerator
                        executor.ai_generator = AITemplateGenerator(
                            azure_endpoint=ai_config['endpoint'],
                            api_key=ai_config['api_key'],
                            api_version=ai_config.get('api_version', '2024-02-15-preview'),
                            deployment_name=ai_config['deployment_name']
                        )
                        print(f"   🤖 AI Generator 已初始化")
                except Exception as ai_error:
                    print(f"   ℹ️ 未配置 AI（将使用简化版简介）: {ai_error}")
                
                # 执行 AI 生成（不会弹出对话框）
                executor.step_ai_generate()
                result['steps_completed'].append('AI 生成模板')
                # 确保包名正确
                ensure_package_name()
            except Exception as e:
                print(f"⚠️ AI 生成失败（继续流程）: {e}")
                result['errors'].append(f"AI 生成: {e}")
            
            # ===== 步骤 8: 生成 Logo =====
            print(f"\n▶️ 步骤 8/12: 生成 Logo")
            try:
                executor.step_generate_logo()
                result['steps_completed'].append('生成 Logo')
                if hasattr(executor, 'logo_url'):
                    result['logo_url'] = executor.logo_url
                # 确保包名正确
                ensure_package_name()
            except Exception as e:
                print(f"⚠️ Logo 生成失败（继续流程）: {e}")
                result['errors'].append(f"Logo 生成: {e}")
            
            # ===== 步骤 9: 发布到 EMCP =====
            print(f"\n▶️ 步骤 9/12: 发布到 EMCP")
            print(f"📦 发布前包名: {executor.package_name}")
            executor.step_publish_emcp()
            print(f"📦 发布后包名: {executor.package_name}")
            result['steps_completed'].append('发布到 EMCP')
            result['template_id'] = executor.template_id
            
            # 强制确保包名正确
            ensure_package_name()
            
            # ===== 步骤 10: MCP 测试 =====
            print(f"\n▶️ 步骤 10/12: MCP 测试")
            print(f"📦 测试前确认包名: {executor.package_name}")
            try:
                executor.step_test_mcp()
                result['steps_completed'].append('MCP 测试')
            except Exception as e:
                print(f"⚠️ MCP 测试失败（继续流程）: {e}")
                result['errors'].append(f"MCP 测试: {e}")
            
            # ===== 步骤 11: Agent 测试 =====
            print(f"\n▶️ 步骤 11/12: Agent 测试")
            try:
                executor.step_test_agent()
                result['steps_completed'].append('Agent 测试')
                if hasattr(executor, 'agent_id'):
                    result['agent_id'] = executor.agent_id
            except Exception as e:
                print(f"⚠️ Agent 测试失败（继续流程）: {e}")
                result['errors'].append(f"Agent 测试: {e}")
            
            # ===== 步骤 12: SignalR 对话测试 =====
            print(f"\n▶️ 步骤 12/12: SignalR 对话测试")
            try:
                executor.step_test_chat()
                result['steps_completed'].append('SignalR 对话测试')
            except Exception as e:
                print(f"⚠️ SignalR 测试失败（继续流程）: {e}")
                result['errors'].append(f"SignalR 测试: {e}")
            
            # ===== 完成 =====
            result['success'] = True
            result['end_time'] = datetime.now()
            result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
            
            print(f"\n{'='*70}")
            print(f"✅ 项目处理完成: {project['name']}")
            print(f"{'='*70}")
            print(f"📦 包名: {result.get('package_name', 'N/A')}")
            print(f"🔗 GitHub: {result.get('github_url', 'N/A')}")
            print(f"🆔 模板ID: {result.get('template_id', 'N/A')}")
            print(f"⏱️ 耗时: {result['duration']:.1f} 秒")
            print(f"✅ 完成步骤: {len(result['steps_completed'])}/12")
            if result['errors']:
                print(f"⚠️ 警告: {len(result['errors'])} 个")
            print(f"{'='*70}")
            
        except Exception as e:
            import traceback
            result['success'] = False
            result['error'] = str(e)
            result['error_trace'] = traceback.format_exc()
            result['end_time'] = datetime.now()
            result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
            
            print(f"\n{'='*70}")
            print(f"❌ 项目处理失败: {project['name']}")
            print(f"{'='*70}")
            print(f"错误: {str(e)}")
            print(f"完成步骤: {len(result['steps_completed'])}/12")
            print(f"⏱️ 耗时: {result['duration']:.1f} 秒")
            print(f"\n详细错误:")
            print(traceback.format_exc())
            print(f"{'='*70}")
        
        return result
    
    def process_all(self, project_indices: List[int] = None):
        """
        批量处理所有项目
        
        Args:
            project_indices: 要处理的项目索引列表（从 1 开始），None 表示处理所有项目
        """
        if not self.projects:
            print("❌ 没有项目可处理，请先运行 scan_projects()")
            return
        
        # 确定要处理的项目
        if project_indices:
            projects_to_process = [self.projects[i-1] for i in project_indices if 0 < i <= len(self.projects)]
        else:
            projects_to_process = self.projects
        
        total = len(projects_to_process)
        
        print(f"\n{'='*70}")
        print(f"🏭 批量 MCP 工厂")
        print(f"{'='*70}")
        print(f"总项目数: {total}")
        print(f"环境变量 API_KEY: {'已配置' if os.environ.get('API_KEY') else '未配置'}")
        print(f"{'='*70}")
        
        # 开始处理
        start_time = datetime.now()
        self.results = []
        
        for i, project in enumerate(projects_to_process, 1):
            result = self.process_project(project, i, total)
            self.results.append(result)
            
            # 项目之间休息一下，避免 API 限流
            if i < total:
                print(f"\n⏸️ 休息 5 秒后处理下一个项目...")
                time.sleep(5)
        
        # 显示总结
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        self.print_summary(total_duration)
    
    def print_summary(self, total_duration: float):
        """打印处理总结"""
        print(f"\n{'='*70}")
        print(f"📊 批量处理总结")
        print(f"{'='*70}")
        
        total = len(self.results)
        success = sum(1 for r in self.results if r['success'])
        failed = total - success
        
        print(f"\n总项目数: {total}")
        print(f"  ✅ 成功: {success}")
        print(f"  ❌ 失败: {failed}")
        print(f"  📈 成功率: {success/total*100:.1f}%")
        print(f"  ⏱️ 总耗时: {total_duration:.1f} 秒 ({total_duration/60:.1f} 分钟)")
        
        if total > 0:
            avg_duration = total_duration / total
            print(f"  ⚡ 平均耗时: {avg_duration:.1f} 秒/项目")
        
        # 成功的项目
        if success > 0:
            print(f"\n✅ 成功的项目:")
            for r in self.results:
                if r['success']:
                    print(f"\n  • {r['project_name']}")
                    print(f"    包名: {r.get('package_name', 'N/A')}")
                    print(f"    GitHub: {r.get('github_url', 'N/A')}")
                    print(f"    模板ID: {r.get('template_id', 'N/A')}")
                    print(f"    耗时: {r['duration']:.1f}秒")
                    print(f"    完成: {len(r['steps_completed'])}/12 步骤")
                    if r.get('errors'):
                        print(f"    警告: {len(r['errors'])} 个")
        
        # 失败的项目
        if failed > 0:
            print(f"\n❌ 失败的项目:")
            for r in self.results:
                if not r['success']:
                    print(f"\n  • {r['project_name']}")
                    print(f"    错误: {r.get('error', 'Unknown')}")
                    print(f"    完成: {len(r['steps_completed'])}/12 步骤")
        
        # 保存结果到文件
        self.save_results()
        
        print(f"\n{'='*70}")
    
    def save_results(self):
        """保存处理结果到文件"""
        import json
        
        output_dir = Path("outputs/batch_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"batch_result_{timestamp}.json"
        
        # 准备数据（转换 Path 和 datetime 对象）
        results_data = []
        for r in self.results:
            result_dict = {
                'project_name': r['project_name'],
                'success': r['success'],
                'start_time': r['start_time'].isoformat(),
                'end_time': r['end_time'].isoformat() if 'end_time' in r else None,
                'duration': r.get('duration', 0),
                'steps_completed': r['steps_completed'],
                'package_name': r.get('package_name'),
                'github_url': r.get('github_url'),
                'template_id': r.get('template_id'),
                'logo_url': r.get('logo_url'),
                'agent_id': r.get('agent_id'),
                'errors': r.get('errors', []),
                'error': r.get('error'),
            }
            results_data.append(result_dict)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 结果已保存: {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='批量 MCP 工厂 - 批量执行完整的 MCP 发布流程')
    parser.add_argument('projects_dir', help='MCP 项目所在的文件夹路径')
    parser.add_argument('--projects', type=str, help='要处理的项目编号，用逗号分隔 (例如: 1,3,5)')
    
    args = parser.parse_args()
    
    # 创建批量处理器
    factory = BatchMCPFactory(args.projects_dir)
    
    # 扫描项目
    factory.scan_projects()
    
    if not factory.projects:
        print("❌ 没有找到任何 MCP 项目")
        return
    
    # 列出项目
    factory.list_projects()
    
    # 解析项目索引
    project_indices = None
    if args.projects:
        project_indices = [int(x.strip()) for x in args.projects.split(',')]
    
    # 确认
    print(f"\n⚠️ 即将开始批量处理，这会执行完整的 MCP 工厂流程：")
    print(f"   1. 扫描项目")
    print(f"   2. 创建 GitHub 仓库")
    print(f"   3. 生成 CI/CD Pipeline")
    print(f"   4. 推送代码")
    print(f"   5. 触发发布并等待完成")
    print(f"   6. 获取包信息")
    print(f"   7. AI 生成模板")
    print(f"   8. 生成 Logo")
    print(f"   9. 发布到 EMCP")
    print(f"  10. MCP 测试")
    print(f"  11. Agent 测试")
    print(f"  12. SignalR 对话测试")
    
    if project_indices:
        print(f"\n将处理项目: {project_indices}")
    else:
        print(f"\n将处理所有 {len(factory.projects)} 个项目")
    
    response = input("\n确认继续? (y/n): ").strip().lower()
    if response != 'y':
        print("❌ 已取消")
        return
    
    # 开始处理
    factory.process_all(project_indices)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # 交互模式
        print("=" * 70)
        print("🏭 批量 MCP 工厂")
        print("=" * 70)
        
        projects_dir = input("\n请输入 MCP 项目文件夹路径: ").strip()
        
        if not projects_dir:
            print("❌ 路径不能为空")
            sys.exit(1)
        
        factory = BatchMCPFactory(projects_dir)
        factory.scan_projects()
        
        if not factory.projects:
            print("❌ 没有找到任何 MCP 项目")
            sys.exit(1)
        
        factory.list_projects()
        
        print(f"\n⚠️ 即将开始批量处理 {len(factory.projects)} 个项目")
        print(f"这会执行完整的 MCP 工厂流程（12个步骤）")
        
        response = input("\n处理所有项目? (y/n): ").strip().lower()
        
        project_indices = None
        if response != 'y':
            indices_str = input("请输入项目编号，用逗号分隔 (例如: 1,3,5): ").strip()
            if indices_str:
                project_indices = [int(x.strip()) for x in indices_str.split(',')]
        
        confirm = input("\n确认继续? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ 已取消")
            sys.exit(0)
        
        factory.process_all(project_indices)
    else:
        # 命令行模式
        main()


"""
MCP发布模块
整合GitHub、PyPI、EMCP发布功能
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加repoflow路径
repoflow_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repoflow_path))
sys.path.insert(0, str(repoflow_path / 'src'))

try:
    from src.github_manager import GitHubManager
    from src.pypi_manager import PyPIManager
    from src.emcp_manager import EMCPManager
    from src.mcp_tester import MCPTester
    REPOFLOW_AVAILABLE = True
except ImportError:
    REPOFLOW_AVAILABLE = False


def publish_to_github_org(
    project_path: str,
    org_name: str = 'BACH-AI-Tools',
    private: bool = False,
    add_workflows: bool = True
) -> Dict[str, Any]:
    """
    发布项目到GitHub组织
    
    Args:
        project_path: 项目路径
        org_name: 组织名称
        private: 是否私有仓库
        add_workflows: 是否添加CI/CD工作流
    
    Returns:
        发布结果
    """
    try:
        if REPOFLOW_AVAILABLE:
            manager = GitHubManager()
            result = manager.publish_to_org(
                project_path=project_path,
                org_name=org_name,
                private=private,
                add_workflows=add_workflows
            )
            return {
                'success': True,
                'repo_url': result.get('html_url', ''),
                'message': f'成功发布到 {org_name}'
            }
        else:
            # 使用命令行方式
            project = Path(project_path)
            repo_name = project.name
            
            # 初始化git
            subprocess.run(['git', 'init'], cwd=project_path, check=True)
            subprocess.run(['git', 'add', '.'], cwd=project_path, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=project_path, check=True)
            
            # 创建远程仓库（需要gh cli）
            visibility = '--private' if private else '--public'
            subprocess.run([
                'gh', 'repo', 'create', f'{org_name}/{repo_name}',
                visibility, '--source', '.', '--push'
            ], cwd=project_path, check=True)
            
            return {
                'success': True,
                'repo_url': f'https://github.com/{org_name}/{repo_name}',
                'message': f'成功发布到 {org_name}/{repo_name}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def publish_to_pypi_registry(
    project_path: str,
    test_pypi: bool = True
) -> Dict[str, Any]:
    """
    发布项目到PyPI
    
    Args:
        project_path: 项目路径
        test_pypi: 是否发布到TestPyPI
    
    Returns:
        发布结果
    """
    try:
        project = Path(project_path)
        
        # 构建包
        subprocess.run([
            sys.executable, '-m', 'build'
        ], cwd=project_path, check=True)
        
        # 上传
        target = 'testpypi' if test_pypi else 'pypi'
        repo_url = 'https://test.pypi.org/legacy/' if test_pypi else 'https://upload.pypi.org/legacy/'
        
        subprocess.run([
            sys.executable, '-m', 'twine', 'upload',
            '--repository-url', repo_url,
            'dist/*'
        ], cwd=project_path, check=True)
        
        package_name = project.name
        
        return {
            'success': True,
            'target': target,
            'package_name': package_name,
            'message': f'成功发布到 {target}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def publish_to_emcp_platform(
    project_path: str,
    generate_logo: bool = True,
    test_after: bool = True
) -> Dict[str, Any]:
    """
    发布项目到EMCP平台
    
    Args:
        project_path: 项目路径
        generate_logo: 是否生成Logo
        test_after: 发布后是否测试
    
    Returns:
        发布结果
    """
    try:
        if REPOFLOW_AVAILABLE:
            manager = EMCPManager()
            result = manager.publish(
                project_path=project_path,
                generate_logo=generate_logo,
                test_after=test_after
            )
            return {
                'success': True,
                'emcp_id': result.get('id', ''),
                'message': '成功发布到EMCP平台'
            }
        else:
            return {
                'success': False,
                'error': 'EMCP管理器不可用，请确保repoflow模块正确配置'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def batch_publish_mcps(
    projects: List[str],
    targets: List[str] = ['github', 'pypi', 'emcp'],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    批量发布MCP项目
    
    Args:
        projects: 项目路径列表
        targets: 发布目标列表
        config: 配置选项
    
    Returns:
        批量发布结果
    """
    config = config or {}
    results = {
        'total': len(projects),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for project_path in projects:
        project_result = {
            'path': project_path,
            'name': Path(project_path).name,
            'targets': {}
        }
        
        try:
            # GitHub发布
            if 'github' in targets:
                github_result = publish_to_github_org(
                    project_path,
                    org_name=config.get('github_org', 'BACH-AI-Tools'),
                    private=config.get('github_private', False)
                )
                project_result['targets']['github'] = github_result
            
            # PyPI发布
            if 'pypi' in targets:
                pypi_result = publish_to_pypi_registry(
                    project_path,
                    test_pypi=config.get('test_pypi', True)
                )
                project_result['targets']['pypi'] = pypi_result
            
            # EMCP发布
            if 'emcp' in targets:
                emcp_result = publish_to_emcp_platform(
                    project_path,
                    generate_logo=config.get('emcp_logo', True),
                    test_after=config.get('emcp_test', True)
                )
                project_result['targets']['emcp'] = emcp_result
            
            # 统计成功/失败
            all_success = all(
                t.get('success', False) 
                for t in project_result['targets'].values()
            )
            if all_success:
                results['success'] += 1
            else:
                results['failed'] += 1
                
        except Exception as e:
            project_result['error'] = str(e)
            results['failed'] += 1
        
        results['details'].append(project_result)
    
    return results


def test_online_mcp(
    platform: str,
    url: str = None,
    package_name: str = None
) -> Dict[str, Any]:
    """
    线上测试MCP（平台验证）
    
    Args:
        platform: 平台名称 (emcp/lobehub/mcpso)
        url: 平台URL
        package_name: 包名
    
    Returns:
        测试结果
    """
    try:
        if platform == 'emcp':
            # EMCP平台测试
            if REPOFLOW_AVAILABLE:
                manager = EMCPManager()
                result = manager.test_online(package_name or url)
                return {
                    'success': result.get('passed', False),
                    'platform': 'emcp',
                    'tests': result.get('tests', []),
                    'message': 'EMCP线上测试完成'
                }
            else:
                # 基本连通性测试
                import requests
                if url:
                    response = requests.get(url, timeout=10)
                    return {
                        'success': response.status_code == 200,
                        'platform': 'emcp',
                        'message': f'EMCP连通性测试: {response.status_code}'
                    }
        
        elif platform == 'lobehub':
            # LobeHub平台验证
            import requests
            test_url = f'https://lobehub.com/plugins/{package_name}' if package_name else url
            if test_url:
                response = requests.get(test_url, timeout=10)
                return {
                    'success': response.status_code == 200,
                    'platform': 'lobehub',
                    'message': f'LobeHub验证: {"通过" if response.status_code == 200 else "失败"}'
                }
        
        elif platform == 'mcpso':
            # mcp.so平台验证
            import requests
            test_url = f'https://mcp.so/server/{package_name}' if package_name else url
            if test_url:
                response = requests.get(test_url, timeout=10)
                return {
                    'success': response.status_code == 200,
                    'platform': 'mcpso',
                    'message': f'mcp.so验证: {"通过" if response.status_code == 200 else "失败"}'
                }
        
        return {
            'success': False,
            'error': f'不支持的平台: {platform}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'platform': platform,
            'error': str(e)
        }


def test_mcp_server(project_path: str) -> Dict[str, Any]:
    """
    测试MCP服务器
    
    Args:
        project_path: 项目路径
    
    Returns:
        测试结果
    """
    try:
        if REPOFLOW_AVAILABLE:
            tester = MCPTester()
            result = tester.test(project_path)
            return {
                'success': result.get('all_passed', False),
                'tests': result.get('tests', []),
                'message': '测试完成'
            }
        else:
            # 基本测试
            project = Path(project_path)
            
            # 检查必要文件
            required_files = ['server.py', 'pyproject.toml']
            missing = [f for f in required_files if not (project / f).exists()]
            
            if missing:
                return {
                    'success': False,
                    'error': f'缺少必要文件: {", ".join(missing)}'
                }
            
            # 语法检查
            server_file = project / 'server.py'
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(server_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f'语法错误: {result.stderr}'
                }
            
            return {
                'success': True,
                'message': '基本测试通过'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


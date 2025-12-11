"""
项目管理模块
列出和管理MCP项目
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError


def list_mcp_projects(base_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    列出本地MCP项目
    
    Args:
        base_dir: 基础目录，默认为generated_mcps
    
    Returns:
        项目列表
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.parent / 'generated_mcps'
    else:
        base_dir = Path(base_dir)
    
    projects = []
    
    if not base_dir.exists():
        return projects
    
    for item in base_dir.iterdir():
        if item.is_dir():
            project_info = {
                'name': item.name,
                'path': str(item),
                'type': 'unknown',
                'version': None,
                'language': None
            }
            
            # 检查项目类型
            if (item / 'pyproject.toml').exists():
                project_info['language'] = 'Python'
                # 尝试读取版本
                try:
                    import tomllib
                    with open(item / 'pyproject.toml', 'rb') as f:
                        data = tomllib.load(f)
                        project_info['version'] = data.get('project', {}).get('version')
                except:
                    pass
                    
            elif (item / 'package.json').exists():
                project_info['language'] = 'TypeScript/JavaScript'
                try:
                    with open(item / 'package.json', 'r') as f:
                        data = json.load(f)
                        project_info['version'] = data.get('version')
                except:
                    pass
            
            # 检查是否是MCP
            if (item / 'server.py').exists() or (item / 'src' / 'index.ts').exists():
                project_info['type'] = 'mcp'
            
            projects.append(project_info)
    
    return projects


def list_github_org_repos(org_name: str = 'BACH-AI-Tools') -> List[Dict[str, Any]]:
    """
    列出GitHub组织的仓库
    
    Args:
        org_name: 组织名称
    
    Returns:
        仓库列表
    """
    repos = []
    page = 1
    per_page = 100
    
    try:
        while True:
            api_url = f"https://api.github.com/orgs/{org_name}/repos?page={page}&per_page={per_page}"
            req = Request(api_url, headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "MCP-Factory"
            })
            
            try:
                with urlopen(req, timeout=30) as response:
                    data = json.loads(response.read().decode())
                    
                    if not data:
                        break
                    
                    for repo in data:
                        repos.append({
                            'name': repo['name'],
                            'url': repo['html_url'],
                            'description': repo.get('description', ''),
                            'language': repo.get('language'),
                            'stars': repo.get('stargazers_count', 0),
                            'updated_at': repo.get('updated_at'),
                            'topics': repo.get('topics', [])
                        })
                    
                    if len(data) < per_page:
                        break
                    
                    page += 1
                    
            except URLError as e:
                break
                
    except Exception as e:
        pass
    
    return repos


def get_project_info(project_path: str) -> Dict[str, Any]:
    """
    获取项目详细信息
    
    Args:
        project_path: 项目路径
    
    Returns:
        项目信息
    """
    project = Path(project_path)
    
    if not project.exists():
        return {'error': '项目不存在'}
    
    info = {
        'name': project.name,
        'path': str(project),
        'files': [],
        'type': 'unknown',
        'language': None,
        'version': None,
        'dependencies': []
    }
    
    # 列出文件
    for item in project.rglob('*'):
        if item.is_file() and not any(p in str(item) for p in ['__pycache__', '.git', 'node_modules']):
            info['files'].append(str(item.relative_to(project)))
    
    # Python项目
    pyproject = project / 'pyproject.toml'
    if pyproject.exists():
        info['language'] = 'Python'
        try:
            import tomllib
            with open(pyproject, 'rb') as f:
                data = tomllib.load(f)
                info['version'] = data.get('project', {}).get('version')
                info['dependencies'] = data.get('project', {}).get('dependencies', [])
        except:
            pass
    
    # Node.js项目
    package_json = project / 'package.json'
    if package_json.exists():
        info['language'] = 'TypeScript/JavaScript'
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
                info['version'] = data.get('version')
                info['dependencies'] = list(data.get('dependencies', {}).keys())
        except:
            pass
    
    # 检查是否是MCP
    if (project / 'server.py').exists():
        info['type'] = 'mcp-python'
    elif (project / 'src' / 'index.ts').exists():
        info['type'] = 'mcp-typescript'
    
    return info


def get_stats() -> Dict[str, Any]:
    """
    获取统计信息
    
    Returns:
        统计数据
    """
    projects = list_mcp_projects()
    
    # 从日志文件读取更多统计
    stats = {
        'apis': len([p for p in projects if p.get('type') == 'mcp']),
        'published': 0,
        'platforms': 0,
        'tests': 0
    }
    
    # 尝试读取发布日志
    try:
        log_path = Path(__file__).parent.parent.parent / 'outputs' / 'batch_publish_report.json'
        if log_path.exists():
            with open(log_path, 'r') as f:
                data = json.load(f)
                stats['published'] = data.get('success_count', 0)
    except:
        pass
    
    # 读取平台提交日志
    try:
        lobehub_log = Path(__file__).parent.parent / 'outputs' / 'lobehub_submit_log.json'
        if lobehub_log.exists():
            with open(lobehub_log, 'r') as f:
                data = json.load(f)
                stats['platforms'] += len(data.get('submitted', []))
    except:
        pass
    
    return stats





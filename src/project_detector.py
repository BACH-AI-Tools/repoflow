"""MCP 项目检测器"""

from pathlib import Path
from typing import Dict
import json
import re


class ProjectDetector:
    """检测项目类型和信息"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
    
    def detect(self) -> Dict:
        """
        检测项目信息
        
        Returns:
            {
                'type': 'pypi' | 'npm' | 'docker' | 'unknown',
                'name': str,  # 项目名称
                'package_name': str,  # 包名称
                'version': str,
                'description': str
            }
        """
        result = {
            'type': 'unknown',
            'name': '',
            'package_name': '',
            'version': '1.0.0',
            'description': ''
        }
        
        # 检测 PyPI 项目
        if (self.project_path / 'setup.py').exists() or (self.project_path / 'pyproject.toml').exists():
            result['type'] = 'Python'
            detected = self._detect_pypi()
            result.update(detected)
            # name 用于仓库名，package_name 用于包名
            if detected.get('package_name'):
                result['name'] = detected['package_name']
        
        # 检测 NPM 项目
        elif (self.project_path / 'package.json').exists():
            result['type'] = 'Node.js'
            detected = self._detect_npm()
            result.update(detected)
            if detected.get('package_name'):
                result['name'] = detected['package_name']
        
        # 检测 Docker 项目
        elif (self.project_path / 'Dockerfile').exists():
            result['type'] = 'Docker'
            detected = self._detect_docker()
            result.update(detected)
            if detected.get('package_name'):
                result['name'] = detected['package_name']
        
        # 如果还没有名称，使用文件夹名
        if not result.get('name'):
            result['name'] = self.project_path.name
        
        # 读取 README
        readme_path = self.project_path / 'README.md'
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text(encoding='utf-8')
                # 提取第一段作为描述
                lines = [l.strip() for l in readme_content.split('\n') if l.strip() and not l.startswith('#')]
                if lines:
                    result['description'] = lines[0][:500]
            except:
                pass
        
        return result
    
    def _detect_pypi(self) -> Dict:
        """检测 PyPI 项目信息"""
        info = {}
        
        # 从 setup.py 读取
        setup_py = self.project_path / 'setup.py'
        if setup_py.exists():
            try:
                content = setup_py.read_text(encoding='utf-8')
                # 提取包名
                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    info['package_name'] = match.group(1)
                # 提取版本
                match = re.search(r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content)
                if match:
                    info['version'] = match.group(1)
            except:
                pass
        
        # 从 pyproject.toml 读取
        pyproject = self.project_path / 'pyproject.toml'
        if pyproject.exists() and not info.get('package_name'):
            try:
                content = pyproject.read_text(encoding='utf-8')
                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    info['package_name'] = match.group(1)
                match = re.search(r'version\s*=\s*["\']v?(\d+\.\d+\.\d+)["\']', content)
                if match:
                    info['version'] = match.group(1)
            except:
                pass
        
        return info
    
    def _detect_npm(self) -> Dict:
        """检测 NPM 项目信息"""
        info = {}
        
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(encoding='utf-8'))
                info['package_name'] = data.get('name', '')
                info['version'] = data.get('version', '1.0.0')
                info['description'] = data.get('description', '')
            except:
                pass
        
        return info
    
    def _detect_docker(self) -> Dict:
        """检测 Docker 项目信息"""
        info = {}
        
        # 从项目名称推断
        info['package_name'] = f"bachstudio/{self.project_path.name.lower()}"
        info['version'] = '1.0.0'
        
        return info


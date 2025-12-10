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
        
        # 读取完整 README
        readme_path = self.project_path / 'README.md'
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text(encoding='utf-8')
                
                # 保存完整 README
                result['readme'] = readme_content
                
                # 智能提取简短描述
                lines = [l.strip() for l in readme_content.split('\n') if l.strip() and not l.startswith('#')]
                if lines:
                    # 找到第一个有实际内容的段落
                    for line in lines:
                        if len(line) > 20 and not line.startswith('```'):
                            result['description'] = line[:500]
                            break
                
                # 提取命令（从 README 中）
                command = self._extract_command_from_readme(readme_content)
                if command:
                    result['command'] = command
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
    
    def _extract_command_from_readme(self, readme_content: str) -> str:
        """
        从 README 中提取安装/运行命令
        
        Args:
            readme_content: README 文件内容
            
        Returns:
            提取到的命令，如果没找到返回空字符串
        """
        import re
        
        # 查找代码块中的 uvx 或 npx 命令
        # 匹配 ```bash 或 ```shell 或 ``` 后面的命令
        code_blocks = re.findall(r'```(?:bash|shell|sh)?\n(.*?)```', readme_content, re.DOTALL)
        
        for block in code_blocks:
            lines = block.strip().split('\n')
            for line in lines:
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 移除行首的 $ 符号
                if line.startswith('$ '):
                    line = line[2:]
                
                # 查找 uvx 命令
                if line.startswith('uvx '):
                    return line
                
                # 查找 npx 命令
                if line.startswith('npx '):
                    return line
        
        # 如果代码块中没找到，尝试在普通文本中查找
        # 查找行内代码 `uvx ...` 或 `npx ...`
        inline_commands = re.findall(r'`((?:uvx|npx)\s+[^`]+)`', readme_content)
        if inline_commands:
            return inline_commands[0]
        
        return ""


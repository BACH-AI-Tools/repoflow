"""PyPI 发布管理模块"""

import subprocess
from pathlib import Path
from typing import Optional
import shutil


class PyPIManager:
    """管理 PyPI 构建和发布操作"""
    
    def __init__(self, project_path: Path):
        """
        初始化 PyPI Manager
        
        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)
    
    def check_tools_installed(self) -> dict:
        """检查所需工具是否已安装"""
        tools = {
            'build': shutil.which('python') is not None,
            'twine': shutil.which('twine') is not None
        }
        return tools
    
    def install_tools(self) -> bool:
        """
        安装构建和发布工具
        
        Returns:
            bool: 是否成功
        """
        try:
            result = subprocess.run(
                ['pip', 'install', 'build', 'twine'],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception as e:
            raise Exception(f"安装工具失败: {str(e)}")
    
    def clean_dist(self) -> bool:
        """
        清理旧的构建文件
        
        Returns:
            bool: 是否成功
        """
        try:
            dist_dir = self.project_path / 'dist'
            build_dir = self.project_path / 'build'
            egg_dir = self.project_path / f"{self.project_path.name}.egg-info"
            
            for dir_path in [dist_dir, build_dir, egg_dir]:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
            
            return True
        except Exception as e:
            raise Exception(f"清理失败: {str(e)}")
    
    def build_package(self) -> bool:
        """
        构建 Python 包
        
        Returns:
            bool: 是否成功
        """
        try:
            # 检查是否有 setup.py 或 pyproject.toml
            has_setup = (self.project_path / 'setup.py').exists()
            has_pyproject = (self.project_path / 'pyproject.toml').exists()
            
            if not has_setup and not has_pyproject:
                raise Exception("找不到 setup.py 或 pyproject.toml")
            
            # 使用 python -m build
            result = subprocess.run(
                ['python', '-m', 'build'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"构建失败: {result.stderr}")
            
            return True
            
        except Exception as e:
            raise Exception(f"包构建失败: {str(e)}")
    
    def upload_to_pypi(self, token: str, test: bool = False) -> bool:
        """
        上传包到 PyPI
        
        Args:
            token: PyPI API Token
            test: 是否上传到 Test PyPI
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查 dist 目录
            dist_dir = self.project_path / 'dist'
            if not dist_dir.exists() or not list(dist_dir.glob('*')):
                raise Exception("dist 目录为空，请先构建包")
            
            # 准备上传命令
            repository_url = (
                'https://test.pypi.org/legacy/' if test 
                else 'https://upload.pypi.org/legacy/'
            )
            
            # 使用 twine 上传
            result = subprocess.run(
                [
                    'twine', 'upload',
                    '--repository-url', repository_url,
                    '--username', '__token__',
                    '--password', token,
                    '--non-interactive',
                    str(dist_dir / '*')
                ],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                shell=True  # 需要 shell 来展开通配符
            )
            
            if result.returncode != 0:
                raise Exception(f"上传失败: {result.stderr}")
            
            return True
            
        except Exception as e:
            raise Exception(f"PyPI 上传失败: {str(e)}")
    
    def build_and_upload(
        self,
        token: str,
        test: bool = False,
        clean: bool = True
    ) -> bool:
        """
        构建并上传包（完整流程）
        
        Args:
            token: PyPI API Token
            test: 是否上传到 Test PyPI
            clean: 是否先清理旧文件
            
        Returns:
            bool: 是否成功
        """
        # 清理旧文件
        if clean:
            self.clean_dist()
        
        # 构建包
        self.build_package()
        
        # 上传到 PyPI
        self.upload_to_pypi(token, test)
        
        return True
    
    def get_package_info(self) -> dict:
        """
        获取包信息
        
        Returns:
            dict: 包信息
        """
        info = {
            'name': None,
            'version': None,
            'has_setup': False,
            'has_pyproject': False
        }
        
        try:
            # 检查 setup.py
            setup_py = self.project_path / 'setup.py'
            if setup_py.exists():
                info['has_setup'] = True
                # 尝试从 setup.py 提取信息（简单解析）
                content = setup_py.read_text(encoding='utf-8')
                if 'name=' in content:
                    import re
                    name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if name_match:
                        info['name'] = name_match.group(1)
                if 'version=' in content:
                    import re
                    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                    if version_match:
                        info['version'] = version_match.group(1)
            
            # 检查 pyproject.toml
            pyproject = self.project_path / 'pyproject.toml'
            if pyproject.exists():
                info['has_pyproject'] = True
                content = pyproject.read_text(encoding='utf-8')
                if 'name =' in content:
                    import re
                    name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if name_match:
                        info['name'] = name_match.group(1)
                if 'version =' in content:
                    import re
                    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                    if version_match:
                        info['version'] = version_match.group(1)
            
            return info
            
        except Exception:
            return info


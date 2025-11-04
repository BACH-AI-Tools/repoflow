"""Docker 构建和推送管理模块"""

import subprocess
from pathlib import Path
from typing import Optional


class DockerManager:
    """管理 Docker 构建和推送操作"""
    
    def __init__(self, project_path: Path):
        """
        初始化 Docker Manager
        
        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)
    
    def check_docker_installed(self) -> bool:
        """检查 Docker 是否已安装"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def build_image(self, image_name: str, tag: str = 'latest', dockerfile: str = 'Dockerfile') -> bool:
        """
        构建 Docker 镜像
        
        Args:
            image_name: 镜像名称 (例如: username/repo)
            tag: 镜像标签
            dockerfile: Dockerfile 路径
            
        Returns:
            bool: 是否成功
        """
        try:
            full_image = f"{image_name}:{tag}"
            
            # 检查 Dockerfile 是否存在
            dockerfile_path = self.project_path / dockerfile
            if not dockerfile_path.exists():
                raise FileNotFoundError(f"Dockerfile 不存在: {dockerfile_path}")
            
            # 构建镜像
            cmd = [
                'docker', 'build',
                '-t', full_image,
                '-f', str(dockerfile_path),
                str(self.project_path)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"构建失败: {result.stderr}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Docker 构建失败: {str(e)}")
    
    def login(self, username: str, password: str, registry: str = 'docker.io') -> bool:
        """
        登录到 Docker Registry
        
        Args:
            username: 用户名
            password: 密码/Token
            registry: Registry 地址
            
        Returns:
            bool: 是否成功
        """
        try:
            # 使用 --password-stdin 以安全方式传递密码
            process = subprocess.Popen(
                ['docker', 'login', registry, '-u', username, '--password-stdin'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=password)
            
            if process.returncode != 0:
                raise Exception(f"登录失败: {stderr}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Docker 登录失败: {str(e)}")
    
    def push_image(self, image_name: str, tag: str = 'latest') -> bool:
        """
        推送 Docker 镜像到 Registry
        
        Args:
            image_name: 镜像名称 (例如: username/repo)
            tag: 镜像标签
            
        Returns:
            bool: 是否成功
        """
        try:
            full_image = f"{image_name}:{tag}"
            
            result = subprocess.run(
                ['docker', 'push', full_image],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"推送失败: {result.stderr}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Docker 推送失败: {str(e)}")
    
    def build_and_push(
        self,
        image_name: str,
        tag: str = 'latest',
        username: Optional[str] = None,
        password: Optional[str] = None,
        registry: str = 'docker.io'
    ) -> bool:
        """
        构建并推送 Docker 镜像（完整流程）
        
        Args:
            image_name: 镜像名称 (例如: username/repo)
            tag: 镜像标签
            username: Docker Hub 用户名
            password: Docker Hub 密码/Token
            registry: Registry 地址
            
        Returns:
            bool: 是否成功
        """
        # 登录（如果提供了凭据）
        if username and password:
            self.login(username, password, registry)
        
        # 构建镜像
        self.build_image(image_name, tag)
        
        # 推送镜像
        self.push_image(image_name, tag)
        
        return True
    
    def get_image_info(self, image_name: str, tag: str = 'latest') -> dict:
        """
        获取镜像信息
        
        Args:
            image_name: 镜像名称
            tag: 镜像标签
            
        Returns:
            dict: 镜像信息
        """
        try:
            full_image = f"{image_name}:{tag}"
            
            result = subprocess.run(
                ['docker', 'image', 'inspect', full_image],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {}
            
            import json
            return json.loads(result.stdout)[0] if result.stdout else {}
            
        except Exception:
            return {}


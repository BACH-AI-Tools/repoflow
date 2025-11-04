"""GitHub 仓库管理模块"""

from github import Github, GithubException
from typing import Optional, Dict, Tuple
from base64 import b64encode
from nacl import encoding, public


class GitHubManager:
    """管理 GitHub 仓库操作"""
    
    def __init__(self, token: str):
        """
        初始化 GitHub Manager
        
        Args:
            token: GitHub Personal Access Token
        """
        self.github = Github(token)
        self.user = self.github.get_user()
    
    def create_repository(self, org_name: str, repo_name: str, 
                         description: str = "", private: bool = False) -> Tuple[str, bool]:
        """
        在指定组织下创建新仓库，如果已存在则返回已存在仓库的URL
        
        Args:
            org_name: 组织名称
            repo_name: 仓库名称
            description: 仓库描述
            private: 是否为私有仓库
            
        Returns:
            (仓库的 Git URL, 是否为新创建)
        """
        try:
            org = self.github.get_organization(org_name)
            
            # 先检查仓库是否已存在
            try:
                existing_repo = org.get_repo(repo_name)
                # 仓库已存在
                return (existing_repo.clone_url, False)
            except GithubException:
                # 仓库不存在，创建新仓库
                pass
            
            # 创建新仓库
            repo = org.create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=False
            )
            return (repo.clone_url, True)
            
        except GithubException as e:
            error_msg = str(e)
            if '404' in error_msg or 'Not Found' in error_msg:
                raise Exception(f"组织 '{org_name}' 不存在，请检查组织名称是否正确")
            elif '403' in error_msg or 'Forbidden' in error_msg:
                raise Exception(f"无权限访问组织 '{org_name}'，请确保：\n1. Token 有组织权限\n2. 你是组织成员")
            else:
                raise Exception(f"创建仓库失败: {e.data.get('message', str(e))}")
    
    def repository_exists(self, org_name: str, repo_name: str) -> bool:
        """
        检查仓库是否存在
        
        Args:
            org_name: 组织名称
            repo_name: 仓库名称
            
        Returns:
            仓库是否存在
        """
        try:
            try:
                org = self.github.get_organization(org_name)
                org.get_repo(repo_name)
            except:
                self.user.get_repo(repo_name)
            return True
        except:
            return False
    
    def delete_repository(self, org_name: str, repo_name: str):
        """
        删除仓库（谨慎使用）
        
        Args:
            org_name: 组织名称
            repo_name: 仓库名称
        """
        try:
            org = self.github.get_organization(org_name)
            repo = org.get_repo(repo_name)
        except:
            repo = self.user.get_repo(repo_name)
        
        repo.delete()
    
    def _encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """
        使用仓库的公钥加密 Secret 值
        
        Args:
            public_key: 仓库的公钥
            secret_value: 要加密的值
            
        Returns:
            加密后的 base64 字符串
        """
        # 使用 NaCl 库加密 Secret
        public_key_obj = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder)
        sealed_box = public.SealedBox(public_key_obj)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return b64encode(encrypted).decode("utf-8")
    
    def set_repository_secret(self, org_name: str, repo_name: str, 
                             secret_name: str, secret_value: str) -> bool:
        """
        设置仓库的 Secret（用于 GitHub Actions）
        
        Args:
            org_name: 组织名称
            repo_name: 仓库名称
            secret_name: Secret 名称（如 DOCKERHUB_USERNAME）
            secret_value: Secret 值
            
        Returns:
            是否成功
        """
        try:
            # 获取仓库
            try:
                org = self.github.get_organization(org_name)
                repo = org.get_repo(repo_name)
            except:
                repo = self.user.get_repo(repo_name)
            
            # 使用 PyGithub 的内置方法创建 Secret（自动加密）
            # secret_type 默认为 "actions"
            repo.create_secret(secret_name, secret_value)
            
            return True
            
        except GithubException as e:
            raise Exception(f"设置 Secret 失败: {e.data.get('message', str(e))}")
    
    def set_multiple_secrets(self, org_name: str, repo_name: str, 
                            secrets: Dict[str, str]) -> Dict[str, bool]:
        """
        批量设置多个 Secrets
        
        Args:
            org_name: 组织名称
            repo_name: 仓库名称
            secrets: Secret 字典 {name: value}
            
        Returns:
            结果字典 {name: success}
        """
        results = {}
        for name, value in secrets.items():
            try:
                self.set_repository_secret(org_name, repo_name, name, value)
                results[name] = True
            except Exception as e:
                results[name] = False
                print(f"设置 {name} 失败: {str(e)}")
        
        return results


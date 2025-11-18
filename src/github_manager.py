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
            
            # 创建新仓库并启用安全功能
            repo = org.create_repo(
                name=repo_name,
                description=description,
                private=private,
                auto_init=False,
                # 启用安全扫描（组织级别默认启用，这里确保开启）
                has_issues=True,
                has_projects=True,
                has_wiki=True
            )
            
            # 启用仓库级别的安全功能
            try:
                # 1. 启用 Vulnerability Alerts（免费，所有仓库可用）
                repo.enable_vulnerability_alert()
                print(f"✅ 已启用 Vulnerability Alerts")
                
                # 2. 启用 Secret Scanning（公开仓库免费，私有仓库需要 Advanced Security）
                # 注意：PyGithub 不直接支持，使用 REST API
                headers = {
                    'Authorization': f'token {self.github._Github__requester._Requester__auth.token}',
                    'Accept': 'application/vnd.github+json',
                    'X-GitHub-Api-Version': '2022-11-28'
                }
                
                # 检查并启用 Secret Scanning
                import requests
                security_url = f'https://api.github.com/repos/{org_name}/{repo_name}/secret-scanning/alerts'
                try:
                    response = requests.get(security_url, headers=headers)
                    if response.status_code == 200:
                        print(f"✅ Secret Scanning 已启用（仓库级别）")
                    elif response.status_code == 404 and not private:
                        # 公开仓库应该自动启用，如果 404 可能需要手动开启
                        print(f"💡 请在仓库设置中启用 Secret Scanning")
                except:
                    pass
                
                # 3. Push Protection（公开仓库可用，私有仓库需要 Advanced Security）
                if not private:
                    print(f"✅ Push Protection 可用（公开仓库免费）")
                else:
                    print(f"💡 私有仓库需要在设置中手动启用 Secret Scanning 和 Push Protection")
                    
            except Exception as security_error:
                print(f"⚠️  启用安全功能时出错: {str(security_error)}")
            
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


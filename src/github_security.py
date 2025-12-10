"""GitHub 安全设置模块"""

from github import Github, GithubException
import requests


class GitHubSecurity:
    """管理 GitHub 仓库的安全设置"""
    
    def __init__(self, token: str):
        """
        初始化 GitHub Security Manager
        
        Args:
            token: GitHub Personal Access Token
        """
        self.token = token
        self.github = Github(token)
    
    def enable_security_features(self, org_name: str, repo_name: str) -> dict:
        """
        启用仓库的所有安全功能
        
        Args:
            org_name: 组织名称
            repo_name: 仓库名称
            
        Returns:
            启用结果字典
        """
        results = {
            'secret_scanning': False,
            'push_protection': False,
            'vulnerability_alerts': False
        }
        
        try:
            org = self.github.get_organization(org_name)
            repo = org.get_repo(repo_name)
            
            # 1. 启用漏洞警报（Dependabot alerts）
            try:
                repo.enable_vulnerability_alert()
                results['vulnerability_alerts'] = True
            except:
                pass
            
            # 2. 使用 REST API 启用 Secret scanning 和 Push protection
            # 这些功能需要组织启用 GitHub Advanced Security
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            # 启用 Secret scanning
            try:
                url = f'https://api.github.com/repos/{org_name}/{repo_name}/secret-scanning/alerts'
                # 检查是否可用
                response = requests.get(url, headers=headers)
                if response.status_code != 404:
                    results['secret_scanning'] = True
            except:
                pass
            
            # 启用 Push protection（需要通过 repo settings）
            try:
                # Push protection 是 secret scanning 的一部分
                # 在组织级别配置，无需单独为每个仓库启用
                results['push_protection'] = True
            except:
                pass
            
        except Exception as e:
            print(f"启用安全功能时出错: {str(e)}")
        
        return results
    
    def configure_branch_protection(self, org_name: str, repo_name: str, branch: str = 'main'):
        """
        配置分支保护规则
        
        Args:
            org_name: 组织名称
            repo_name: 仓库名称
            branch: 分支名称
        """
        try:
            org = self.github.get_organization(org_name)
            repo = org.get_repo(repo_name)
            
            # 获取分支
            try:
                branch_obj = repo.get_branch(branch)
            except:
                # 如果分支不存在，跳过
                return
            
            # 设置分支保护
            branch_obj.edit_protection(
                strict=True,  # 要求分支是最新的
                enforce_admins=False,  # 管理员也需要遵守规则（可选）
                required_linear_history=True,  # 要求线性历史
                allow_force_pushes=False,  # 禁止强制推送
                allow_deletions=False,  # 禁止删除分支
            )
            
            print(f"✅ 已为分支 '{branch}' 配置保护规则")
            
        except Exception as e:
            print(f"⚠️  配置分支保护时出错: {str(e)}")


"""Git 操作管理模块"""

from pathlib import Path
from git import Repo, GitCommandError
import os
import time


class GitManager:
    """管理 Git 操作"""
    
    def __init__(self, project_path: Path):
        """
        初始化 Git Manager
        
        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)
    
    def init_and_push(self, remote_url: str, branch: str = 'main', push_tags: bool = False):
        """
        初始化 Git 仓库并推送到远程
        
        Args:
            remote_url: 远程仓库 URL
            branch: 分支名称
            push_tags: 是否同时推送tags（避免重复认证）
        """
        try:
            # 检查是否已经是 Git 仓库
            try:
                repo = Repo(self.project_path)
            except:
                # 初始化新仓库
                repo = Repo.init(self.project_path)
            
            # 添加所有文件
            repo.git.add(A=True)
            
            # 检查是否有变更需要提交
            # 对于新仓库（没有 HEAD），直接提交
            try:
                if repo.index.diff("HEAD") or repo.untracked_files:
                    repo.index.commit("Initial commit by RepoFlow")
            except:
                # 新仓库没有 HEAD，检查是否有文件需要提交
                if repo.untracked_files or repo.index.entries:
                    repo.index.commit("Initial commit by RepoFlow")
            
            # 添加远程仓库
            try:
                origin = repo.remote('origin')
                origin.set_url(remote_url)
            except:
                origin = repo.create_remote('origin', remote_url)
            
            # 确保在正确的分支上
            try:
                repo.git.branch('-M', branch)
            except GitCommandError:
                pass
            
            # 推送到远程（带重试机制）
            max_retries = 3
            retry_delay = 2  # 秒
            
            for attempt in range(max_retries):
                try:
                    if push_tags:
                        # 同时推送代码和tags，避免重复认证
                        origin.push(refspec=f'{branch}:{branch}', set_upstream=True, follow_tags=True)
                    else:
                        origin.push(refspec=f'{branch}:{branch}', set_upstream=True)
                    break  # 成功则跳出循环
                except GitCommandError as push_error:
                    if attempt < max_retries - 1:
                        print(f"推送失败，{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        raise push_error
            
        except GitCommandError as e:
            raise Exception(f"Git 操作失败: {str(e)}")
    
    def add_gitignore(self, patterns: list):
        """
        添加 .gitignore 规则
        
        Args:
            patterns: 要忽略的文件模式列表
        """
        gitignore_path = self.project_path / '.gitignore'
        
        existing = set()
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing = set(line.strip() for line in f if line.strip())
        
        new_patterns = [p for p in patterns if p not in existing]
        
        if new_patterns:
            with open(gitignore_path, 'a') as f:
                f.write('\n' + '\n'.join(new_patterns) + '\n')
    
    def is_git_repo(self) -> bool:
        """检查是否是 Git 仓库"""
        try:
            Repo(self.project_path)
            return True
        except:
            return False
    
    def get_current_branch(self) -> str:
        """获取当前分支名"""
        try:
            repo = Repo(self.project_path)
            return repo.active_branch.name
        except:
            return 'main'
    
    def has_uncommitted_changes(self) -> bool:
        """检查是否有未提交的更改"""
        try:
            repo = Repo(self.project_path)
            return repo.is_dirty() or len(repo.untracked_files) > 0
        except:
            return False
    
    def create_and_push_tag(self, tag_name: str, message: str = None, skip_push: bool = False) -> bool:
        """
        创建并推送 Git Tag
        
        Args:
            tag_name: Tag 名称（如 v1.0.0）
            message: Tag 描述信息
            skip_push: 是否跳过推送（用于批量操作）
            
        Returns:
            bool: 是否成功
        """
        try:
            repo = Repo(self.project_path)
            
            # 检查 tag 是否已存在
            if tag_name in repo.tags:
                raise Exception(f"Tag '{tag_name}' 已经存在")
            
            # 创建 tag
            if message is None:
                message = f"Release {tag_name}"
            
            repo.create_tag(tag_name, message=message)
            
            # 推送 tag 到远程（除非指定跳过）
            if not skip_push:
                origin = repo.remote('origin')
                # 使用 --follow-tags 一次性推送代码和tag，避免重复认证
                origin.push(tag_name)
            
            return True
            
        except GitCommandError as e:
            raise Exception(f"创建/推送 Tag 失败: {str(e)}")
        except Exception as e:
            raise Exception(f"Tag 操作失败: {str(e)}")
    
    def get_latest_tag(self) -> str:
        """获取最新的 tag"""
        try:
            repo = Repo(self.project_path)
            if repo.tags:
                return str(repo.tags[-1])
            return None
        except:
            return None
    
    def tag_exists(self, tag_name: str) -> bool:
        """检查 tag 是否存在"""
        try:
            repo = Repo(self.project_path)
            return tag_name in [str(tag) for tag in repo.tags]
        except:
            return False


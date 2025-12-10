#!/usr/bin/env python3
"""
批量配置 SonarQube 扫描
一次性完成：
1. 在组织级别设置 Secrets（SONAR_TOKEN, SONAR_HOST_URL）
2. 批量给仓库添加 GitHub Actions 工作流文件
3. 提交代码后自动触发 SonarQube 分析
"""

import os
import sys
import json
import base64
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.unified_config_manager import UnifiedConfigManager

# 尝试导入 nacl 用于加密
try:
    from nacl import encoding, public
    HAS_NACL = True
except ImportError:
    HAS_NACL = False
    print("⚠️  警告: nacl 未安装，将尝试其他方式")


class BatchSonarSetup:
    """批量配置 SonarQube 扫描"""
    
    # GitHub Actions 工作流模板
    WORKFLOW_TEMPLATE = '''name: SonarQube Analysis

on:
  workflow_dispatch:  # 支持手动触发
  push:
    branches:
      - main
      - master
      - develop
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sonarqube:
    name: SonarQube Scan
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Shallow clones should be disabled for a better relevancy of analysis

      - name: SonarQube Scan
        uses: SonarSource/sonarqube-scan-action@v3
        env:
          SONAR_TOKEN: ${{{{ secrets.SONAR_TOKEN }}}}
          SONAR_HOST_URL: ${{{{ secrets.SONAR_HOST_URL }}}}
        with:
          args: >
            -Dsonar.projectKey={project_key}
            -Dsonar.projectName={project_name}

      # Optional: Fail the build if Quality Gate fails
      # - name: SonarQube Quality Gate check
      #   uses: SonarSource/sonarqube-quality-gate-action@master
      #   timeout-minutes: 5
      #   env:
      #     SONAR_TOKEN: ${{{{ secrets.SONAR_TOKEN }}}}
'''

    def __init__(self):
        self.config_mgr = UnifiedConfigManager()
        self.config = self.config_mgr.load_config()
        
        # GitHub 配置
        self.github_token = self.config.get("github", {}).get("token", "")
        self.github_org = self.config.get("github", {}).get("org_name", "BACH-AI-Tools")
        
        # SonarQube 配置
        sonar_config = self.config_mgr.get_sonarqube_config()
        self.sonar_url = sonar_config.get("base_url", "https://sonar.kaleido.guru")
        self.sonar_token = sonar_config.get("token", "")
        
        # API 请求头
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        # 统计
        self.stats = {
            "total_repos": 0,
            "workflow_added": 0,
            "workflow_exists": 0,
            "workflow_failed": 0,
            "details": []
        }
    
    def _encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """使用仓库的公钥加密 Secret"""
        if not HAS_NACL:
            raise Exception("nacl 库未安装，请运行: pip install pynacl")
        
        public_key_obj = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder)
        sealed_box = public.SealedBox(public_key_obj)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")
    
    def setup_org_secrets(self) -> bool:
        """
        在组织级别设置 Secrets
        这样所有仓库都可以使用，不需要每个仓库单独配置
        """
        print(f"\n{'='*70}")
        print(f"🔐 配置组织级别 Secrets")
        print(f"{'='*70}")
        print(f"📦 组织: {self.github_org}")
        
        if not self.sonar_token:
            print("❌ 未配置 SonarQube Token")
            return False
        
        secrets_to_set = {
            "SONAR_TOKEN": self.sonar_token,
            "SONAR_HOST_URL": self.sonar_url
        }
        
        success = True
        
        for secret_name, secret_value in secrets_to_set.items():
            try:
                # 获取组织的公钥
                pub_key_url = f"https://api.github.com/orgs/{self.github_org}/actions/secrets/public-key"
                response = requests.get(pub_key_url, headers=self.headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"❌ 获取公钥失败: {response.status_code}")
                    print(f"   可能原因: 没有组织管理员权限")
                    success = False
                    continue
                
                pub_key_data = response.json()
                public_key = pub_key_data["key"]
                key_id = pub_key_data["key_id"]
                
                # 加密 Secret
                encrypted_value = self._encrypt_secret(public_key, secret_value)
                
                # 设置组织 Secret（对所有仓库可见）
                secret_url = f"https://api.github.com/orgs/{self.github_org}/actions/secrets/{secret_name}"
                payload = {
                    "encrypted_value": encrypted_value,
                    "key_id": key_id,
                    "visibility": "all"  # 对组织内所有仓库可见
                }
                
                response = requests.put(secret_url, headers=self.headers, json=payload, timeout=30)
                
                if response.status_code in [201, 204]:
                    print(f"✅ {secret_name} 设置成功")
                else:
                    print(f"❌ {secret_name} 设置失败: {response.status_code}")
                    print(f"   {response.text}")
                    success = False
                    
            except Exception as e:
                print(f"❌ 设置 {secret_name} 时出错: {e}")
                success = False
        
        return success
    
    def get_org_repos(self, include_archived: bool = False) -> List[Dict]:
        """获取组织下的所有仓库"""
        print(f"\n📦 获取 {self.github_org} 组织的仓库列表...")
        
        repos = []
        page = 1
        per_page = 100
        
        while True:
            try:
                response = requests.get(
                    f"https://api.github.com/orgs/{self.github_org}/repos",
                    headers=self.headers,
                    params={
                        "page": page,
                        "per_page": per_page,
                        "type": "all"
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ 获取仓库列表失败: {response.status_code}")
                    break
                
                data = response.json()
                if not data:
                    break
                
                for repo in data:
                    if repo.get("archived") and not include_archived:
                        continue
                    
                    repos.append({
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "default_branch": repo.get("default_branch", "main"),
                        "language": repo.get("language"),
                        "private": repo.get("private", False)
                    })
                
                page += 1
                
            except Exception as e:
                print(f"❌ 获取仓库列表错误: {e}")
                break
        
        print(f"✅ 找到 {len(repos)} 个仓库")
        return repos
    
    def check_workflow_exists(self, repo_name: str) -> Tuple[bool, Optional[str]]:
        """
        检查仓库是否已有 SonarQube 工作流
        返回: (是否存在, 文件SHA)
        """
        workflow_paths = [
            ".github/workflows/sonar.yml",
            ".github/workflows/sonarqube.yml", 
            ".github/workflows/sonar-scan.yml",
            ".github/workflows/build.yml"  # 可能包含 sonar 配置
        ]
        
        for path in workflow_paths:
            try:
                url = f"https://api.github.com/repos/{self.github_org}/{repo_name}/contents/{path}"
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    if "sonar" in content.lower() or "SONAR" in content:
                        return True, data.get("sha")
            except:
                pass
        
        return False, None
    
    def get_sonar_project_key(self, repo_name: str) -> str:
        """
        获取 SonarQube 项目 key
        GitHub App 导入的项目 key 格式通常是: org_repo_uuid
        我们尝试查询 SonarQube 获取正确的 key
        """
        try:
            # 搜索 SonarQube 中的项目
            search_url = f"{self.sonar_url}/api/projects/search"
            params = {"q": repo_name}
            auth = (self.sonar_token, "")
            
            response = requests.get(search_url, params=params, auth=auth, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", [])
                
                # 查找匹配的项目
                for comp in components:
                    if repo_name in comp.get("key", "") or repo_name in comp.get("name", ""):
                        return comp["key"]
        except:
            pass
        
        # 如果找不到，使用组织名_仓库名格式
        return f"{self.github_org}_{repo_name}"
    
    def add_workflow_to_repo(self, repo: Dict, dry_run: bool = False, force_update: bool = False) -> Dict:
        """给仓库添加 SonarQube 工作流"""
        repo_name = repo["name"]
        result = {
            "repo": repo_name,
            "success": False,
            "action": None,
            "error": None
        }
        
        try:
            # 检查是否已有 workflow
            exists, sha = self.check_workflow_exists(repo_name)
            
            # 如果存在且不强制更新，跳过
            if exists and not force_update:
                result["action"] = "skipped"
                result["success"] = True
                result["error"] = "已存在 SonarQube 工作流"
                return result
            
            # 获取正确的 SonarQube project key
            project_key = self.get_sonar_project_key(repo_name)
            
            # 生成 workflow 内容
            workflow_content = self.WORKFLOW_TEMPLATE.format(
                project_key=project_key,
                project_name=repo_name
            )
            
            if dry_run:
                result["action"] = "dry_run"
                result["success"] = True
                result["project_key"] = project_key
                return result
            
            # 获取已存在文件的 SHA（更新时需要）
            workflow_path = ".github/workflows/sonar.yml"
            url = f"https://api.github.com/repos/{self.github_org}/{repo_name}/contents/{workflow_path}"
            
            file_sha = None
            if exists:
                try:
                    response = requests.get(url, headers=self.headers, timeout=30)
                    if response.status_code == 200:
                        file_sha = response.json().get("sha")
                except:
                    pass
            
            payload = {
                "message": "Update SonarQube analysis workflow (add manual trigger)" if exists else "Add SonarQube analysis workflow",
                "content": base64.b64encode(workflow_content.encode()).decode(),
                "branch": repo["default_branch"]
            }
            
            # 如果文件已存在，需要提供 SHA
            if file_sha:
                payload["sha"] = file_sha
            
            response = requests.put(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code in [200, 201]:
                result["action"] = "updated" if exists else "created"
                result["success"] = True
                result["project_key"] = project_key
            else:
                result["action"] = "failed"
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                
        except Exception as e:
            result["action"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def run_batch_setup(self, 
                        repos_filter: List[str] = None,
                        skip_repos: List[str] = None,
                        dry_run: bool = False,
                        skip_secrets: bool = False,
                        force_update: bool = False,
                        max_workers: int = 5) -> Dict:
        """
        批量配置 SonarQube 扫描
        
        Args:
            repos_filter: 只处理这些仓库
            skip_repos: 跳过这些仓库
            dry_run: 只预览，不实际操作
            skip_secrets: 跳过设置组织 secrets
            force_update: 强制更新已存在的 workflow 文件
            max_workers: 并发数
        """
        print(f"\n{'='*70}")
        print(f"🚀 批量配置 SonarQube 扫描")
        print(f"{'='*70}")
        print(f"📦 组织: {self.github_org}")
        print(f"🌐 SonarQube: {self.sonar_url}")
        print(f"🔧 模式: {'预览' if dry_run else '执行'}")
        
        # 1. 设置组织级别 Secrets
        if not skip_secrets and not dry_run:
            if not self.setup_org_secrets():
                print("\n⚠️  组织 Secrets 设置失败，继续添加 workflow...")
        elif dry_run:
            print("\n📋 [预览] 将设置组织 Secrets:")
            print(f"   - SONAR_TOKEN: {self.sonar_token[:10]}...")
            print(f"   - SONAR_HOST_URL: {self.sonar_url}")
        
        # 2. 获取仓库列表
        repos = self.get_org_repos()
        
        if not repos:
            print("❌ 未找到仓库")
            return self.stats
        
        # 过滤仓库
        if repos_filter:
            repos = [r for r in repos if r["name"] in repos_filter]
            print(f"📋 过滤后: {len(repos)} 个仓库")
        
        if skip_repos:
            repos = [r for r in repos if r["name"] not in skip_repos]
            print(f"📋 跳过后: {len(repos)} 个仓库")
        
        self.stats["total_repos"] = len(repos)
        
        # 3. 批量添加 workflow
        print(f"\n{'='*70}")
        print(f"📝 添加 GitHub Actions 工作流")
        print(f"{'='*70}\n")
        
        for i, repo in enumerate(repos, 1):
            repo_name = repo["name"]
            print(f"[{i}/{len(repos)}] 📦 {repo_name}", end=" ... ")
            
            result = self.add_workflow_to_repo(repo, dry_run, force_update)
            self.stats["details"].append(result)
            
            if result["success"]:
                if result["action"] == "created":
                    self.stats["workflow_added"] += 1
                    print(f"✅ 已添加")
                elif result["action"] == "updated":
                    self.stats["workflow_added"] += 1
                    print(f"🔄 已更新")
                elif result["action"] == "skipped":
                    self.stats["workflow_exists"] += 1
                    print(f"⏭️  已存在")
                elif result["action"] == "dry_run":
                    print(f"📋 预览 (project_key: {result.get('project_key', 'N/A')})")
            else:
                self.stats["workflow_failed"] += 1
                print(f"❌ 失败: {result.get('error', '未知错误')[:50]}")
        
        # 4. 打印统计
        self._print_summary(dry_run)
        
        # 5. 生成报告
        if not dry_run:
            self._generate_report()
        
        return self.stats
    
    def _print_summary(self, dry_run: bool = False):
        """打印统计摘要"""
        print(f"\n{'='*70}")
        print(f"📊 {'预览' if dry_run else '配置'}统计")
        print(f"{'='*70}")
        print(f"总仓库数: {self.stats['total_repos']}")
        print(f"✅ 新增 workflow: {self.stats['workflow_added']}")
        print(f"⏭️  已有 workflow: {self.stats['workflow_exists']}")
        print(f"❌ 失败: {self.stats['workflow_failed']}")
        
        if not dry_run and self.stats['workflow_added'] > 0:
            print(f"\n🎉 配置完成！")
            print(f"   新添加的仓库将在下次 push 时自动触发 SonarQube 扫描")
            print(f"\n💡 要立即触发扫描，可以：")
            print(f"   1. 在仓库中做一个小改动并 push")
            print(f"   2. 或者在 GitHub Actions 页面手动触发 workflow")
    
    def _generate_report(self):
        """生成报告"""
        report_dir = Path("outputs/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 报告
        json_file = report_dir / f"sonar_setup_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        print(f"\n📄 报告已保存: {json_file}")
    
    def trigger_initial_scan(self, repo_name: str) -> bool:
        """
        触发仓库的首次扫描
        通过创建一个空提交来触发 workflow
        """
        try:
            # 获取仓库的默认分支的最新 commit
            ref_url = f"https://api.github.com/repos/{self.github_org}/{repo_name}/git/refs/heads/main"
            response = requests.get(ref_url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                # 尝试 master 分支
                ref_url = f"https://api.github.com/repos/{self.github_org}/{repo_name}/git/refs/heads/master"
                response = requests.get(ref_url, headers=self.headers, timeout=30)
            
            if response.status_code != 200:
                return False
            
            # 手动触发 workflow
            dispatch_url = f"https://api.github.com/repos/{self.github_org}/{repo_name}/actions/workflows/sonar.yml/dispatches"
            payload = {"ref": "main"}
            
            response = requests.post(dispatch_url, headers=self.headers, json=payload, timeout=30)
            return response.status_code in [204, 200]
            
        except:
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量配置 SonarQube 扫描（组织 Secrets + GitHub Actions）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 预览模式（不实际操作）
  python batch_setup_sonar.py --dry-run
  
  # 执行配置（设置 secrets + 添加 workflow）
  python batch_setup_sonar.py
  
  # 只处理指定仓库
  python batch_setup_sonar.py -r repo1 repo2 repo3
  
  # 跳过某些仓库
  python batch_setup_sonar.py -s old-repo archived-repo
  
  # 跳过设置组织 secrets（如果已配置）
  python batch_setup_sonar.py --skip-secrets
        """
    )
    
    parser.add_argument(
        "--org", "-o",
        help="GitHub 组织名称（默认从配置读取）"
    )
    parser.add_argument(
        "--repos", "-r",
        nargs="+",
        help="只处理指定的仓库（空格分隔）"
    )
    parser.add_argument(
        "--skip", "-s",
        nargs="+",
        help="跳过指定的仓库（空格分隔）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式，不实际操作"
    )
    parser.add_argument(
        "--skip-secrets",
        action="store_true",
        help="跳过设置组织级别 Secrets"
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="强制更新已存在的 workflow 文件（会触发新的扫描）"
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="只列出仓库，不执行任何操作"
    )
    
    args = parser.parse_args()
    
    setup = BatchSonarSetup()
    
    if args.org:
        setup.github_org = args.org
    
    if args.list_only:
        repos = setup.get_org_repos()
        print(f"\n📋 仓库列表 ({len(repos)} 个):")
        for i, repo in enumerate(repos, 1):
            lang = repo.get("language", "未知")
            print(f"  {i}. {repo['name']} ({lang})")
        return
    
    # 执行批量配置
    setup.run_batch_setup(
        repos_filter=args.repos,
        skip_repos=args.skip,
        dry_run=args.dry_run,
        skip_secrets=args.skip_secrets,
        force_update=args.force_update
    )


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
批量 SonarQube 扫描脚本
将 GitHub 组织下的所有仓库提交到 SonarQube 进行代码质量分析
"""

import os
import sys
import json
import shutil
import subprocess
import tempfile
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.sonar_scanner import SonarScanner
from src.unified_config_manager import UnifiedConfigManager


class BatchSonarScanner:
    """批量 SonarQube 扫描器"""
    
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
        
        # 初始化 SonarQube 扫描器
        self.scanner = SonarScanner(self.sonar_url, self.sonar_token)
        
        # 工作目录
        self.work_dir = Path(tempfile.gettempdir()) / "sonar_batch_scan"
        
        # 统计信息
        self.stats = {
            "total": 0,
            "scanned": 0,
            "failed": 0,
            "skipped": 0,
            "results": []
        }
    
    def get_github_repos(self, org_name: str = None, 
                         include_private: bool = True,
                         include_archived: bool = False) -> List[Dict]:
        """
        获取 GitHub 组织下的所有仓库
        
        Args:
            org_name: 组织名称
            include_private: 是否包含私有仓库
            include_archived: 是否包含已归档仓库
            
        Returns:
            仓库列表
        """
        if org_name is None:
            org_name = self.github_org
        
        if not self.github_token:
            print("❌ 未配置 GitHub Token")
            return []
        
        print(f"\n📦 获取 {org_name} 组织的仓库列表...")
        
        repos = []
        page = 1
        per_page = 100
        
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        while True:
            try:
                response = requests.get(
                    f"https://api.github.com/orgs/{org_name}/repos",
                    headers=headers,
                    params={
                        "page": page,
                        "per_page": per_page,
                        "type": "all"
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ 获取仓库列表失败: {response.status_code}")
                    print(f"   {response.text}")
                    break
                
                data = response.json()
                if not data:
                    break
                
                for repo in data:
                    # 过滤条件
                    if repo.get("archived") and not include_archived:
                        continue
                    if repo.get("private") and not include_private:
                        continue
                    
                    repos.append({
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "clone_url": repo["clone_url"],
                        "ssh_url": repo["ssh_url"],
                        "html_url": repo["html_url"],
                        "default_branch": repo.get("default_branch", "main"),
                        "language": repo.get("language"),
                        "size": repo.get("size", 0),
                        "private": repo.get("private", False),
                        "archived": repo.get("archived", False),
                        "description": repo.get("description", "")
                    })
                
                page += 1
                
            except Exception as e:
                print(f"❌ 获取仓库列表错误: {e}")
                break
        
        print(f"✅ 找到 {len(repos)} 个仓库")
        return repos
    
    def clone_repo(self, repo: Dict, target_dir: Path) -> bool:
        """
        克隆仓库
        
        Args:
            repo: 仓库信息
            target_dir: 目标目录
            
        Returns:
            是否成功
        """
        repo_name = repo["name"]
        clone_url = repo["clone_url"]
        
        # 如果使用 token，修改 clone URL
        if self.github_token:
            clone_url = clone_url.replace(
                "https://github.com/",
                f"https://{self.github_token}@github.com/"
            )
        
        repo_dir = target_dir / repo_name
        
        if repo_dir.exists():
            # 已存在，尝试更新
            try:
                subprocess.run(
                    ["git", "pull"],
                    cwd=str(repo_dir),
                    capture_output=True,
                    timeout=120
                )
                return True
            except:
                # 删除重新克隆
                shutil.rmtree(repo_dir, ignore_errors=True)
        
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(repo_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"   ❌ 克隆失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ❌ 克隆超时")
            return False
        except Exception as e:
            print(f"   ❌ 克隆错误: {e}")
            return False
    
    def scan_repo(self, repo: Dict, repo_dir: Path) -> Dict:
        """
        扫描单个仓库
        
        Args:
            repo: 仓库信息
            repo_dir: 仓库目录
            
        Returns:
            扫描结果
        """
        repo_name = repo["name"]
        project_key = repo_name
        
        result = {
            "repo": repo_name,
            "success": False,
            "project_key": project_key,
            "quality_gate": None,
            "measures": None,
            "error": None,
            "url": self.scanner.get_project_url(project_key)
        }
        
        try:
            # 确保项目存在
            project = self.scanner.get_project(project_key)
            if not project:
                print(f"   📦 创建 SonarQube 项目...")
                project = self.scanner.create_project(project_key, repo_name)
            
            # 检查 sonar-scanner 是否安装
            if not self.scanner.check_scanner_installed():
                result["error"] = "SonarScanner 未安装"
                return result
            
            # 生成配置文件
            self.scanner.create_sonar_properties_file(repo_dir, project_key, repo_name)
            
            # 运行扫描
            print(f"   🔍 运行扫描...")
            scan_result = subprocess.run(
                ["sonar-scanner"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if scan_result.returncode != 0:
                result["error"] = scan_result.stderr[:500] if scan_result.stderr else "扫描失败"
                return result
            
            print(f"   ✅ 扫描任务已提交")
            result["success"] = True
            
            # 等待一会儿让结果处理
            import time
            time.sleep(5)
            
            # 获取结果
            status = self.scanner.get_project_status(project_key)
            if status:
                result["quality_gate"] = status.get("status", "UNKNOWN")
            
            measures = self.scanner.get_project_measures(project_key)
            if measures:
                result["measures"] = measures
            
        except subprocess.TimeoutExpired:
            result["error"] = "扫描超时"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def run_batch_scan(self, 
                       org_name: str = None,
                       repos_filter: List[str] = None,
                       skip_repos: List[str] = None,
                       max_workers: int = 1,
                       cleanup: bool = True) -> Dict:
        """
        批量扫描组织下的仓库
        
        Args:
            org_name: 组织名称
            repos_filter: 只扫描这些仓库（为空则扫描全部）
            skip_repos: 跳过这些仓库
            max_workers: 并发数（建议设为 1，避免 SonarQube 过载）
            cleanup: 扫描后是否清理临时文件
            
        Returns:
            扫描统计结果
        """
        if org_name is None:
            org_name = self.github_org
        
        if skip_repos is None:
            skip_repos = []
        
        print(f"\n{'='*70}")
        print(f"🚀 批量 SonarQube 扫描")
        print(f"{'='*70}")
        print(f"📦 组织: {org_name}")
        print(f"🌐 SonarQube: {self.sonar_url}")
        
        # 测试 SonarQube 连接
        if not self.scanner.test_connection():
            print(f"❌ 无法连接到 SonarQube 服务器")
            return self.stats
        
        # 检查 sonar-scanner
        if not self.scanner.check_scanner_installed():
            print(f"\n❌ SonarScanner 未安装！")
            print(f"请先安装 SonarScanner:")
            print(f"  Windows: choco install sonarscanner-cli")
            print(f"  Mac: brew install sonar-scanner")
            print(f"  或从官网下载: https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/")
            return self.stats
        
        # 获取仓库列表
        repos = self.get_github_repos(org_name)
        
        if not repos:
            print(f"❌ 未找到仓库")
            return self.stats
        
        # 过滤仓库
        if repos_filter:
            repos = [r for r in repos if r["name"] in repos_filter]
            print(f"📋 过滤后: {len(repos)} 个仓库")
        
        if skip_repos:
            repos = [r for r in repos if r["name"] not in skip_repos]
            print(f"📋 跳过后: {len(repos)} 个仓库")
        
        self.stats["total"] = len(repos)
        
        # 创建工作目录
        self.work_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 工作目录: {self.work_dir}")
        
        # 开始扫描
        print(f"\n{'='*70}")
        print(f"开始扫描 {len(repos)} 个仓库")
        print(f"{'='*70}\n")
        
        for i, repo in enumerate(repos, 1):
            repo_name = repo["name"]
            print(f"\n[{i}/{len(repos)}] 📦 {repo_name}")
            print(f"   语言: {repo.get('language', '未知')}")
            print(f"   大小: {repo.get('size', 0)} KB")
            
            # 克隆仓库
            print(f"   📥 克隆仓库...")
            if not self.clone_repo(repo, self.work_dir):
                self.stats["failed"] += 1
                self.stats["results"].append({
                    "repo": repo_name,
                    "success": False,
                    "error": "克隆失败"
                })
                continue
            
            repo_dir = self.work_dir / repo_name
            
            # 扫描仓库
            result = self.scan_repo(repo, repo_dir)
            self.stats["results"].append(result)
            
            if result["success"]:
                self.stats["scanned"] += 1
                gate = result.get("quality_gate", "UNKNOWN")
                if gate == "OK":
                    print(f"   ✅ 质量门禁: 通过")
                elif gate == "ERROR":
                    print(f"   ❌ 质量门禁: 未通过")
                else:
                    print(f"   ⚠️ 质量门禁: {gate}")
            else:
                self.stats["failed"] += 1
                print(f"   ❌ 扫描失败: {result.get('error', '未知错误')}")
        
        # 清理
        if cleanup:
            print(f"\n🧹 清理临时文件...")
            try:
                shutil.rmtree(self.work_dir, ignore_errors=True)
            except:
                pass
        
        # 打印统计
        self._print_summary()
        
        # 生成报告
        self._generate_report()
        
        return self.stats
    
    def _print_summary(self):
        """打印扫描统计摘要"""
        print(f"\n{'='*70}")
        print(f"📊 扫描统计")
        print(f"{'='*70}")
        print(f"总仓库数: {self.stats['total']}")
        print(f"成功扫描: {self.stats['scanned']}")
        print(f"扫描失败: {self.stats['failed']}")
        print(f"跳过: {self.stats['skipped']}")
        
        # 按质量门禁状态分组
        passed = sum(1 for r in self.stats["results"] 
                    if r.get("quality_gate") == "OK")
        failed_gate = sum(1 for r in self.stats["results"] 
                         if r.get("quality_gate") == "ERROR")
        
        if self.stats["scanned"] > 0:
            print(f"\n质量门禁统计:")
            print(f"  ✅ 通过: {passed}")
            print(f"  ❌ 未通过: {failed_gate}")
            print(f"  ⚠️ 其他: {self.stats['scanned'] - passed - failed_gate}")
    
    def _generate_report(self):
        """生成扫描报告"""
        report_dir = Path("outputs/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 报告
        json_file = report_dir / f"batch_sonar_scan_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        print(f"\n📄 JSON 报告: {json_file}")
        
        # HTML 报告
        html_file = report_dir / f"batch_sonar_scan_{timestamp}.html"
        html_content = self._generate_html_report()
        html_file.write_text(html_content, encoding='utf-8')
        print(f"📄 HTML 报告: {html_file}")
    
    def _generate_html_report(self) -> str:
        """生成 HTML 报告"""
        
        # 生成仓库行
        rows_html = ""
        for result in self.stats["results"]:
            repo = result.get("repo", "未知")
            success = result.get("success", False)
            gate = result.get("quality_gate", "N/A")
            error = result.get("error", "")
            url = result.get("url", "#")
            
            measures = result.get("measures", {})
            bugs = measures.get("bugs", "N/A")
            vulns = measures.get("vulnerabilities", "N/A")
            smells = measures.get("code_smells", "N/A")
            
            status_icon = "✅" if success else "❌"
            gate_class = "gate-ok" if gate == "OK" else "gate-error" if gate == "ERROR" else "gate-unknown"
            
            rows_html += f"""
            <tr>
                <td>{status_icon} {repo}</td>
                <td class="{gate_class}">{gate}</td>
                <td>{bugs}</td>
                <td>{vulns}</td>
                <td>{smells}</td>
                <td>{error[:50] + '...' if len(error) > 50 else error}</td>
                <td><a href="{url}" target="_blank">查看</a></td>
            </tr>
            """
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>批量 SonarQube 扫描报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #4361ee 0%, #3f37c9 100%);
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(67, 97, 238, 0.3);
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            color: #4361ee;
        }}
        .stat-label {{ opacity: 0.7; font-size: 14px; margin-top: 5px; }}
        .table-container {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            overflow-x: auto;
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }}
        th {{ background: rgba(67, 97, 238, 0.2); }}
        .gate-ok {{ color: #28a745; font-weight: bold; }}
        .gate-error {{ color: #dc3545; font-weight: bold; }}
        .gate-unknown {{ color: #ffc107; }}
        a {{ color: #4361ee; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .timestamp {{ text-align: center; opacity: 0.5; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 批量 SonarQube 扫描报告</h1>
            <p>组织: {self.github_org}</p>
            <p>服务器: {self.sonar_url}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{self.stats['total']}</div>
                <div class="stat-label">总仓库数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #28a745;">{self.stats['scanned']}</div>
                <div class="stat-label">成功扫描</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #dc3545;">{self.stats['failed']}</div>
                <div class="stat-label">扫描失败</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #28a745;">{sum(1 for r in self.stats['results'] if r.get('quality_gate') == 'OK')}</div>
                <div class="stat-label">门禁通过</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #dc3545;">{sum(1 for r in self.stats['results'] if r.get('quality_gate') == 'ERROR')}</div>
                <div class="stat-label">门禁未通过</div>
            </div>
        </div>
        
        <div class="table-container">
            <h2 style="margin-bottom: 15px;">📋 扫描详情</h2>
            <table>
                <thead>
                    <tr>
                        <th>仓库</th>
                        <th>质量门禁</th>
                        <th>Bug</th>
                        <th>漏洞</th>
                        <th>代码异味</th>
                        <th>错误信息</th>
                        <th>链接</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        
        <div class="timestamp">
            报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>
"""
        return html


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量将 GitHub 组织仓库提交到 SonarQube 扫描"
    )
    parser.add_argument(
        "--org", "-o",
        help="GitHub 组织名称（默认从配置读取）"
    )
    parser.add_argument(
        "--repos", "-r",
        nargs="+",
        help="只扫描指定的仓库（空格分隔）"
    )
    parser.add_argument(
        "--skip", "-s",
        nargs="+",
        help="跳过指定的仓库（空格分隔）"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="扫描后不清理临时文件"
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="只列出仓库，不执行扫描"
    )
    
    args = parser.parse_args()
    
    scanner = BatchSonarScanner()
    
    if args.list_only:
        # 只列出仓库
        repos = scanner.get_github_repos(args.org)
        print(f"\n📋 仓库列表:")
        for i, repo in enumerate(repos, 1):
            lang = repo.get("language", "未知")
            size = repo.get("size", 0)
            print(f"  {i}. {repo['name']} ({lang}, {size}KB)")
        return
    
    # 执行批量扫描
    scanner.run_batch_scan(
        org_name=args.org,
        repos_filter=args.repos,
        skip_repos=args.skip,
        cleanup=not args.no_cleanup
    )


if __name__ == "__main__":
    main()












#!/usr/bin/env python3
"""
SonarQube 代码质量扫描模块
提供与 SonarQube 服务器的集成功能
"""

import os
import subprocess
import requests
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class SonarScanner:
    """SonarQube 代码质量扫描器"""
    
    def __init__(self, base_url: str, token: str):
        """
        初始化 SonarQube 扫描器
        
        Args:
            base_url: SonarQube 服务器地址，如 https://sonar.kaleido.guru
            token: SonarQube API Token（Global Analysis Token）
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.auth = (token, '')  # Token 作为用户名，密码为空
        
    # ===== API 方法 =====
    
    def test_connection(self) -> bool:
        """
        测试与 SonarQube 服务器的连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/system/status",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SonarQube 连接成功")
                print(f"   版本: {data.get('version', '未知')}")
                print(f"   状态: {data.get('status', '未知')}")
                return True
            else:
                print(f"❌ SonarQube 连接失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ SonarQube 连接错误: {e}")
            return False
    
    def get_project(self, project_key: str) -> Optional[Dict]:
        """
        获取项目信息
        
        Args:
            project_key: 项目键名
            
        Returns:
            项目信息字典，如果不存在返回 None
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/projects/search",
                params={"projects": project_key},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", [])
                if components:
                    return components[0]
            return None
        except Exception as e:
            print(f"⚠️ 获取项目失败: {e}")
            return None
    
    def create_project(self, project_key: str, project_name: str) -> Optional[Dict]:
        """
        创建新项目
        
        Args:
            project_key: 项目键名（唯一标识）
            project_name: 项目显示名称
            
        Returns:
            创建结果字典
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/projects/create",
                data={
                    "project": project_key,
                    "name": project_name
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 项目创建成功: {project_key}")
                return data.get("project")
            elif response.status_code == 400:
                # 项目可能已存在
                error = response.json()
                if "already exists" in str(error).lower():
                    print(f"ℹ️ 项目已存在: {project_key}")
                    return self.get_project(project_key)
                print(f"❌ 创建项目失败: {error}")
                return None
            else:
                print(f"❌ 创建项目失败: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 创建项目错误: {e}")
            return None
    
    def get_project_status(self, project_key: str) -> Optional[Dict]:
        """
        获取项目质量门禁状态
        
        Args:
            project_key: 项目键名
            
        Returns:
            质量门禁状态字典
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/qualitygates/project_status",
                params={"projectKey": project_key},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("projectStatus")
            return None
        except Exception as e:
            print(f"⚠️ 获取项目状态失败: {e}")
            return None
    
    def get_project_measures(self, project_key: str, 
                            metrics: List[str] = None) -> Optional[Dict]:
        """
        获取项目度量指标
        
        Args:
            project_key: 项目键名
            metrics: 指标列表，默认获取常用指标
            
        Returns:
            度量指标字典
        """
        if metrics is None:
            metrics = [
                "bugs", "vulnerabilities", "code_smells",
                "coverage", "duplicated_lines_density",
                "ncloc", "sqale_rating", "reliability_rating",
                "security_rating", "sqale_index"
            ]
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/measures/component",
                params={
                    "component": project_key,
                    "metricKeys": ",".join(metrics)
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                component = data.get("component", {})
                measures = component.get("measures", [])
                
                # 转换为字典格式
                result = {}
                for measure in measures:
                    result[measure["metric"]] = measure.get("value", "N/A")
                return result
            return None
        except Exception as e:
            print(f"⚠️ 获取项目度量失败: {e}")
            return None
    
    def get_project_issues(self, project_key: str, 
                          severities: str = None,
                          types: str = None,
                          page_size: int = 100) -> Optional[Dict]:
        """
        获取项目问题列表
        
        Args:
            project_key: 项目键名
            severities: 严重级别（BLOCKER,CRITICAL,MAJOR,MINOR,INFO）
            types: 问题类型（BUG,VULNERABILITY,CODE_SMELL）
            page_size: 每页数量
            
        Returns:
            问题列表字典
        """
        try:
            params = {
                "componentKeys": project_key,
                "ps": page_size
            }
            if severities:
                params["severities"] = severities
            if types:
                params["types"] = types
            
            response = self.session.get(
                f"{self.base_url}/api/issues/search",
                params=params,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"⚠️ 获取项目问题失败: {e}")
            return None
    
    # ===== 扫描方法 =====
    
    def generate_sonar_properties(self, project_path: Path, 
                                  project_key: str,
                                  project_name: str = None,
                                  sources: str = ".",
                                  exclusions: str = None) -> str:
        """
        生成 sonar-project.properties 文件内容
        
        Args:
            project_path: 项目路径
            project_key: 项目键名
            project_name: 项目名称
            sources: 源代码目录
            exclusions: 排除的文件/目录
            
        Returns:
            properties 文件内容
        """
        if project_name is None:
            project_name = project_key
        
        if exclusions is None:
            exclusions = ",".join([
                "**/node_modules/**",
                "**/__pycache__/**",
                "**/venv/**",
                "**/env/**",
                "**/.git/**",
                "**/dist/**",
                "**/build/**",
                "**/*.min.js",
                "**/*.bundle.js",
                "**/coverage/**",
                "**/.pytest_cache/**",
                "**/.mypy_cache/**"
            ])
        
        content = f"""# SonarQube 项目配置
# 由 RepoFlow 自动生成

sonar.projectKey={project_key}
sonar.projectName={project_name}
sonar.projectVersion=1.0

# 源代码目录
sonar.sources={sources}

# 排除的文件和目录
sonar.exclusions={exclusions}

# 编码
sonar.sourceEncoding=UTF-8

# SonarQube 服务器
sonar.host.url={self.base_url}
sonar.token={self.token}
"""
        return content
    
    def create_sonar_properties_file(self, project_path: Path,
                                     project_key: str,
                                     project_name: str = None) -> Path:
        """
        在项目目录创建 sonar-project.properties 文件
        
        Args:
            project_path: 项目路径
            project_key: 项目键名
            project_name: 项目名称
            
        Returns:
            生成的文件路径
        """
        properties_content = self.generate_sonar_properties(
            project_path, project_key, project_name
        )
        
        properties_file = project_path / "sonar-project.properties"
        properties_file.write_text(properties_content, encoding='utf-8')
        
        print(f"📝 已生成 sonar-project.properties")
        return properties_file
    
    def check_scanner_installed(self) -> bool:
        """
        检查 sonar-scanner 是否已安装
        
        Returns:
            bool: 是否已安装
        """
        try:
            result = subprocess.run(
                ["sonar-scanner", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ SonarScanner 已安装")
                # 提取版本信息
                for line in result.stdout.split('\n'):
                    if 'SonarScanner' in line:
                        print(f"   {line.strip()}")
                        break
                return True
            return False
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"⚠️ 检查 SonarScanner 时出错: {e}")
            return False
    
    def run_scan(self, project_path: Path, 
                 project_key: str,
                 wait_for_result: bool = True,
                 timeout: int = 300) -> Dict[str, Any]:
        """
        运行 SonarQube 扫描
        
        Args:
            project_path: 项目路径
            project_key: 项目键名
            wait_for_result: 是否等待扫描结果
            timeout: 等待超时时间（秒）
            
        Returns:
            扫描结果字典
        """
        result = {
            "success": False,
            "project_key": project_key,
            "scan_started": False,
            "quality_gate": None,
            "measures": None,
            "issues_summary": None,
            "error": None
        }
        
        # 检查 sonar-scanner 是否安装
        if not self.check_scanner_installed():
            result["error"] = "SonarScanner 未安装"
            print(f"❌ SonarScanner 未安装")
            print(f"💡 请安装 SonarScanner:")
            print(f"   Windows: choco install sonarscanner-cli")
            print(f"   Mac: brew install sonar-scanner")
            print(f"   Linux: 下载并添加到 PATH")
            return result
        
        # 确保项目存在
        project = self.get_project(project_key)
        if not project:
            print(f"📦 创建 SonarQube 项目: {project_key}")
            project = self.create_project(project_key, project_key)
            if not project:
                result["error"] = "无法创建项目"
                return result
        
        # 生成配置文件
        self.create_sonar_properties_file(project_path, project_key)
        
        # 运行扫描
        print(f"\n🔍 开始 SonarQube 扫描...")
        print(f"   项目: {project_key}")
        print(f"   路径: {project_path}")
        
        try:
            scan_result = subprocess.run(
                ["sonar-scanner"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if scan_result.returncode == 0:
                print(f"✅ 扫描任务已提交")
                result["scan_started"] = True
            else:
                print(f"❌ 扫描失败")
                print(f"   错误: {scan_result.stderr}")
                result["error"] = scan_result.stderr
                return result
                
        except subprocess.TimeoutExpired:
            result["error"] = f"扫描超时（{timeout}秒）"
            print(f"❌ 扫描超时")
            return result
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 扫描错误: {e}")
            return result
        
        # 等待扫描结果
        if wait_for_result:
            print(f"\n⏳ 等待扫描结果...")
            max_wait = 120  # 最多等待 2 分钟
            check_interval = 10
            elapsed = 0
            
            while elapsed < max_wait:
                time.sleep(check_interval)
                elapsed += check_interval
                
                # 检查质量门禁状态
                status = self.get_project_status(project_key)
                if status:
                    result["quality_gate"] = status
                    gate_status = status.get("status", "UNKNOWN")
                    
                    if gate_status == "OK":
                        print(f"✅ 质量门禁: 通过")
                    elif gate_status == "ERROR":
                        print(f"❌ 质量门禁: 未通过")
                    else:
                        print(f"⚠️ 质量门禁: {gate_status}")
                    
                    break
                
                print(f"   等待中... ({elapsed}/{max_wait}秒)")
            
            # 获取度量指标
            measures = self.get_project_measures(project_key)
            if measures:
                result["measures"] = measures
                self._print_measures(measures)
            
            # 获取问题摘要
            issues = self.get_project_issues(project_key)
            if issues:
                result["issues_summary"] = {
                    "total": issues.get("total", 0),
                    "bugs": sum(1 for i in issues.get("issues", []) if i.get("type") == "BUG"),
                    "vulnerabilities": sum(1 for i in issues.get("issues", []) if i.get("type") == "VULNERABILITY"),
                    "code_smells": sum(1 for i in issues.get("issues", []) if i.get("type") == "CODE_SMELL")
                }
        
        result["success"] = True
        return result
    
    def _print_measures(self, measures: Dict):
        """打印度量指标"""
        print(f"\n📊 代码度量指标:")
        
        # 代码行数
        if "ncloc" in measures:
            print(f"   代码行数: {measures['ncloc']}")
        
        # 问题数量
        if "bugs" in measures:
            print(f"   Bug: {measures['bugs']}")
        if "vulnerabilities" in measures:
            print(f"   漏洞: {measures['vulnerabilities']}")
        if "code_smells" in measures:
            print(f"   代码异味: {measures['code_smells']}")
        
        # 覆盖率
        if "coverage" in measures:
            print(f"   测试覆盖率: {measures['coverage']}%")
        
        # 重复率
        if "duplicated_lines_density" in measures:
            print(f"   重复代码: {measures['duplicated_lines_density']}%")
        
        # 评级
        rating_map = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}
        
        if "reliability_rating" in measures:
            rating = rating_map.get(measures['reliability_rating'], measures['reliability_rating'])
            print(f"   可靠性评级: {rating}")
        
        if "security_rating" in measures:
            rating = rating_map.get(measures['security_rating'], measures['security_rating'])
            print(f"   安全性评级: {rating}")
        
        if "sqale_rating" in measures:
            rating = rating_map.get(measures['sqale_rating'], measures['sqale_rating'])
            print(f"   可维护性评级: {rating}")
    
    # ===== 仅检查模式（不运行扫描）=====
    
    def check_existing_project(self, project_key: str) -> Dict[str, Any]:
        """
        检查已存在项目的质量状态（不运行新扫描）
        
        Args:
            project_key: 项目键名
            
        Returns:
            项目状态字典
        """
        result = {
            "exists": False,
            "project_key": project_key,
            "quality_gate": None,
            "measures": None,
            "last_analysis": None,
            "issues_summary": None
        }
        
        # 检查项目是否存在
        project = self.get_project(project_key)
        if not project:
            print(f"ℹ️ 项目不存在: {project_key}")
            return result
        
        result["exists"] = True
        result["last_analysis"] = project.get("lastAnalysisDate")
        
        print(f"📦 项目: {project.get('name', project_key)}")
        if result["last_analysis"]:
            print(f"   最后分析: {result['last_analysis']}")
        
        # 获取质量门禁状态
        status = self.get_project_status(project_key)
        if status:
            result["quality_gate"] = status
            gate_status = status.get("status", "UNKNOWN")
            
            if gate_status == "OK":
                print(f"✅ 质量门禁: 通过")
            elif gate_status == "ERROR":
                print(f"❌ 质量门禁: 未通过")
            else:
                print(f"⚠️ 质量门禁: {gate_status}")
        
        # 获取度量指标
        measures = self.get_project_measures(project_key)
        if measures:
            result["measures"] = measures
            self._print_measures(measures)
        
        # 获取问题摘要
        issues = self.get_project_issues(project_key)
        if issues:
            result["issues_summary"] = {
                "total": issues.get("total", 0),
                "bugs": sum(1 for i in issues.get("issues", []) if i.get("type") == "BUG"),
                "vulnerabilities": sum(1 for i in issues.get("issues", []) if i.get("type") == "VULNERABILITY"),
                "code_smells": sum(1 for i in issues.get("issues", []) if i.get("type") == "CODE_SMELL")
            }
        
        return result
    
    def get_project_url(self, project_key: str) -> str:
        """
        获取项目在 SonarQube 中的 URL
        
        Args:
            project_key: 项目键名
            
        Returns:
            项目 URL
        """
        return f"{self.base_url}/dashboard?id={project_key}"
    
    # ===== 报告生成 =====
    
    def generate_scan_report(self, project_key: str, 
                            output_dir: Path = None) -> Optional[Path]:
        """
        生成扫描报告 HTML 文件
        
        Args:
            project_key: 项目键名
            output_dir: 输出目录
            
        Returns:
            报告文件路径
        """
        if output_dir is None:
            output_dir = Path("outputs/reports")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取项目数据
        project = self.get_project(project_key)
        status = self.get_project_status(project_key)
        measures = self.get_project_measures(project_key)
        issues = self.get_project_issues(project_key, page_size=50)
        
        if not project:
            print(f"❌ 项目不存在: {project_key}")
            return None
        
        # 生成 HTML 报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"sonar_report_{project_key}_{timestamp}.html"
        
        html_content = self._generate_html_report(
            project_key, project, status, measures, issues
        )
        
        report_file.write_text(html_content, encoding='utf-8')
        print(f"📄 报告已生成: {report_file}")
        
        return report_file
    
    def _generate_html_report(self, project_key: str, project: Dict,
                             status: Dict, measures: Dict, 
                             issues: Dict) -> str:
        """生成 HTML 报告内容"""
        
        gate_status = status.get("status", "UNKNOWN") if status else "UNKNOWN"
        gate_color = "#28a745" if gate_status == "OK" else "#dc3545"
        
        # 评级映射
        rating_map = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}
        
        def get_rating(key):
            if measures and key in measures:
                return rating_map.get(measures[key], measures[key])
            return "N/A"
        
        def get_measure(key, default="N/A"):
            if measures and key in measures:
                return measures[key]
            return default
        
        # 问题列表 HTML
        issues_html = ""
        if issues and issues.get("issues"):
            for issue in issues.get("issues", [])[:20]:  # 只显示前 20 个
                severity = issue.get("severity", "UNKNOWN")
                severity_color = {
                    "BLOCKER": "#dc3545",
                    "CRITICAL": "#dc3545", 
                    "MAJOR": "#fd7e14",
                    "MINOR": "#ffc107",
                    "INFO": "#17a2b8"
                }.get(severity, "#6c757d")
                
                issues_html += f"""
                <tr>
                    <td><span style="color: {severity_color}; font-weight: bold;">{severity}</span></td>
                    <td>{issue.get("type", "UNKNOWN")}</td>
                    <td>{issue.get("message", "")[:100]}</td>
                    <td>{issue.get("component", "").split(":")[-1]}</td>
                    <td>{issue.get("line", "")}</td>
                </tr>
                """
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SonarQube 扫描报告 - {project_key}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #4361ee 0%, #3f37c9 100%);
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(67, 97, 238, 0.3);
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.8; }}
        .quality-gate {{
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 18px;
            background: {gate_color};
            color: white;
            margin-top: 15px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #4361ee;
            margin-bottom: 5px;
        }}
        .metric-label {{ opacity: 0.7; font-size: 14px; }}
        .rating {{ 
            display: inline-block;
            width: 40px;
            height: 40px;
            line-height: 40px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 20px;
        }}
        .rating-A {{ background: #28a745; color: white; }}
        .rating-B {{ background: #9acd32; color: white; }}
        .rating-C {{ background: #ffc107; color: black; }}
        .rating-D {{ background: #fd7e14; color: white; }}
        .rating-E {{ background: #dc3545; color: white; }}
        .section {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .section h2 {{
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        th {{ background: rgba(67, 97, 238, 0.2); }}
        .link {{
            color: #4361ee;
            text-decoration: none;
        }}
        .link:hover {{ text-decoration: underline; }}
        .timestamp {{
            text-align: center;
            opacity: 0.5;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 SonarQube 扫描报告</h1>
            <p>项目: {project.get("name", project_key)}</p>
            <p>最后分析: {project.get("lastAnalysisDate", "未知")}</p>
            <div class="quality-gate">
                质量门禁: {gate_status}
            </div>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{get_measure("ncloc", "0")}</div>
                <div class="metric-label">代码行数</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{get_measure("bugs", "0")}</div>
                <div class="metric-label">Bug</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{get_measure("vulnerabilities", "0")}</div>
                <div class="metric-label">漏洞</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{get_measure("code_smells", "0")}</div>
                <div class="metric-label">代码异味</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{get_measure("coverage", "0")}%</div>
                <div class="metric-label">测试覆盖率</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{get_measure("duplicated_lines_density", "0")}%</div>
                <div class="metric-label">重复代码</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 质量评级</h2>
            <div class="metrics">
                <div class="metric-card">
                    <div class="rating rating-{get_rating('reliability_rating')}">{get_rating("reliability_rating")}</div>
                    <div class="metric-label">可靠性</div>
                </div>
                <div class="metric-card">
                    <div class="rating rating-{get_rating('security_rating')}">{get_rating("security_rating")}</div>
                    <div class="metric-label">安全性</div>
                </div>
                <div class="metric-card">
                    <div class="rating rating-{get_rating('sqale_rating')}">{get_rating("sqale_rating")}</div>
                    <div class="metric-label">可维护性</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🐛 问题列表 (前20个)</h2>
            <table>
                <thead>
                    <tr>
                        <th>严重级别</th>
                        <th>类型</th>
                        <th>消息</th>
                        <th>文件</th>
                        <th>行号</th>
                    </tr>
                </thead>
                <tbody>
                    {issues_html if issues_html else '<tr><td colspan="5" style="text-align:center;">暂无问题</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🔗 链接</h2>
            <p><a class="link" href="{self.get_project_url(project_key)}" target="_blank">
                在 SonarQube 中查看完整报告 →
            </a></p>
        </div>
        
        <div class="timestamp">
            报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
</body>
</html>
"""
        return html









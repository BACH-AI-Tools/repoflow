#!/usr/bin/env python3
"""
工作流执行器 - 真实执行所有步骤
"""

from pathlib import Path
from typing import Dict, Any, Optional
import sys

from src.github_manager import GitHubManager
from src.git_manager import GitManager
from src.secret_scanner import SecretScanner
from src.pipeline_generator import PipelineGenerator
from src.emcp_manager import EMCPManager
from src.package_fetcher import PackageFetcher
from src.ai_generator import AITemplateGenerator
from src.jimeng_api_generator import JimengAPIGenerator
from src.mcp_tester import MCPTester
from src.agent_tester import AgentTester
from src.signalr_chat_tester import SignalRChatTester
from src.unified_config_manager import UnifiedConfigManager
from src.repo_cloner import RepoCloner
from src.sonar_scanner import SonarScanner


class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self, config_mgr: UnifiedConfigManager):
        self.config_mgr = config_mgr
        self.config = config_mgr.load_config()
        
        # 项目信息
        self.project_path = None
        self.repo_name = None
        self.version = None
        self.org_name = None
        
        # 运行时数据
        self.github_repo_url = None
        self.package_name = None
        self.package_type = None  # 添加 package_type 属性
        self.package_command = None  # 从 README 提取的命令
        self.template_id = None
        self.env_vars_config = []  # 环境变量配置
        
        # 管理器实例（复用）
        self.emcp_manager = None
        self.agent_id = None  # Agent ID
        self.agent_publish_id = None  # Agent发布ID
        
        # 进度回调
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def update_progress(self, progress: int):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(progress)
        
    def set_project_info(self, project_path: str, repo_name: str, version: str):
        """设置项目信息"""
        self.project_path = Path(project_path)
        self.repo_name = repo_name
        self.version = version
        self.org_name = self.config.get("github", {}).get("org_name", "BACH-AI-Tools")
    
    # ===== GitHub 发布流程 =====
    
    def step_scan_project(self):
        """扫描项目"""
        print(f"\n{'='*60}")
        print(f"步骤: 扫描项目")
        print(f"{'='*60}")
        
        scanner = SecretScanner()
        print(f"📁 扫描路径: {self.project_path}")
        
        # 确保传入 Path 对象
        scan_path = Path(self.project_path) if not isinstance(self.project_path, Path) else self.project_path
        secrets = scanner.scan_directory(scan_path)
        
        if secrets:
            print(f"❌ 发现 {len(secrets)} 个敏感信息！")
            for secret in secrets:
                print(f"  - {secret['type']} 在 {secret['file']}")
            raise Exception("发现敏感信息，请删除后重试")
        
        print(f"✅ 未发现敏感信息")
        print(f"✅ 扫描完成\n")
    
    def step_sonar_scan(self, run_scan: bool = False):
        """
        SonarQube 代码质量扫描
        
        Args:
            run_scan: 是否运行完整扫描（需要安装 sonar-scanner）
                     False = 只检查已有项目的质量状态
                     True = 运行完整扫描并上传结果
        """
        print(f"\n{'='*60}")
        print(f"步骤: SonarQube 代码质量扫描")
        print(f"{'='*60}")
        
        # 获取 SonarQube 配置
        sonar_config = self.config_mgr.get_sonarqube_config()
        
        if not sonar_config.get("enabled", True):
            print(f"ℹ️ SonarQube 扫描已禁用，跳过")
            return
        
        if not sonar_config.get("token"):
            print(f"⚠️ 未配置 SonarQube Token，跳过扫描")
            print(f"💡 请在设置中配置 SonarQube Token")
            return
        
        base_url = sonar_config.get("base_url", "https://sonar.kaleido.guru")
        token = sonar_config.get("token")
        
        print(f"🌐 SonarQube 服务器: {base_url}")
        
        # 初始化扫描器
        scanner = SonarScanner(base_url, token)
        
        # 测试连接
        if not scanner.test_connection():
            print(f"⚠️ 无法连接到 SonarQube 服务器，跳过扫描")
            return
        
        # 生成项目键名（使用包名或仓库名）
        project_key = self.package_name or self.repo_name
        if not project_key:
            print(f"⚠️ 无法确定项目键名，跳过扫描")
            return
        
        # 清理项目键名（只保留字母、数字、横杠、下划线）
        import re
        project_key = re.sub(r'[^a-zA-Z0-9\-_]', '-', project_key)
        
        print(f"📦 项目键名: {project_key}")
        
        if run_scan:
            # 运行完整扫描
            print(f"\n🔍 运行完整 SonarQube 扫描...")
            result = scanner.run_scan(
                self.project_path,
                project_key,
                wait_for_result=True
            )
            
            if result.get("success"):
                print(f"✅ SonarQube 扫描完成")
                
                # 检查质量门禁
                quality_gate = result.get("quality_gate", {})
                gate_status = quality_gate.get("status", "UNKNOWN")
                
                if gate_status == "ERROR":
                    print(f"⚠️ 质量门禁未通过，但继续流程")
                    # 不抛出异常，只是警告
                
                # 生成报告
                try:
                    report_path = scanner.generate_scan_report(project_key)
                    if report_path:
                        print(f"📄 扫描报告: {report_path}")
                except Exception as e:
                    print(f"⚠️ 生成报告失败: {e}")
            else:
                print(f"⚠️ SonarQube 扫描失败: {result.get('error', '未知错误')}")
                print(f"ℹ️ 继续执行后续步骤")
        else:
            # 只检查已有项目状态
            print(f"\n🔍 检查 SonarQube 项目状态...")
            result = scanner.check_existing_project(project_key)
            
            if result.get("exists"):
                print(f"✅ 项目在 SonarQube 中存在")
                
                # 检查质量门禁
                quality_gate = result.get("quality_gate", {})
                gate_status = quality_gate.get("status", "UNKNOWN")
                
                if gate_status == "ERROR":
                    print(f"⚠️ 质量门禁未通过")
                elif gate_status == "OK":
                    print(f"✅ 质量门禁已通过")
            else:
                print(f"ℹ️ 项目尚未在 SonarQube 中分析")
                print(f"💡 可以在 GitHub Actions 中配置 SonarQube 扫描")
        
        # 显示项目链接
        project_url = scanner.get_project_url(project_key)
        print(f"🔗 SonarQube 项目: {project_url}")
        
        print(f"✅ 步骤完成\n")
    
    def step_create_repo(self):
        """创建GitHub仓库"""
        print(f"\n{'='*60}")
        print(f"步骤: 创建 GitHub 仓库")
        print(f"{'='*60}")
        
        github_token = self.config.get("github", {}).get("token", "")
        if not github_token:
            raise Exception("未配置 GitHub Token")
        
        print(f"🔗 组织: {self.org_name}")
        print(f"📦 仓库: {self.repo_name}")
        print(f"🌐 连接 GitHub API...")
        
        github_mgr = GitHubManager(github_token)
        
        print(f"📝 创建仓库...")
        repo_url, is_new = github_mgr.create_repository(
            org_name=self.org_name,
            repo_name=self.repo_name,
            description=f"{self.repo_name} - 由 MCP工厂自动创建",
            private=False
        )
        
        self.github_repo_url = repo_url
        
        if is_new:
            print(f"✅ 仓库创建成功")
        else:
            print(f"ℹ️ 仓库已存在")
        
        print(f"🔗 仓库地址: {repo_url}")
        print(f"✅ 步骤完成\n")
    
    def step_generate_pipeline(self):
        """生成CI/CD Pipeline"""
        print(f"\n{'='*60}")
        print(f"步骤: 生成 CI/CD Pipeline")
        print(f"{'='*60}")
        
        from src.project_detector import ProjectDetector
        
        # 检测项目类型
        project_path_str = str(self.project_path)
        detector = ProjectDetector(project_path_str)
        info = detector.detect()
        project_type = info.get("type", "unknown").lower()
        
        # 保存项目类型
        self.package_type = project_type
        
        print(f"🔍 项目类型: {project_type}")
        
        # 获取 GitHub 组织名称
        config = self.config_mgr.load_config()
        org_name = config.get('github', {}).get('organization', 'BACH-AI-Tools')
        
        # 创建生成器（传入组织名称用于 SonarQube project key）
        generator = PipelineGenerator(org_name=org_name)
        
        # 根据类型生成（同时会生成 SonarQube workflow）
        if project_type == "python":
            print(f"📝 生成 PyPI 发布工作流...")
            generator.generate('pypi', Path(self.project_path))
        elif project_type == "node.js":
            print(f"📝 生成 NPM 发布工作流...")
            generator.generate('npm', Path(self.project_path))
        else:
            print(f"⚠️ 未知项目类型，跳过 Pipeline 生成")
            # 即使未知类型，也生成 SonarQube workflow
            generator._generate_sonar_pipeline(Path(self.project_path))
        
        print(f"✅ Pipeline 文件已生成到: .github/workflows/")
        print(f"   - 发布 workflow (pypi/npm)")
        print(f"   - SonarQube 扫描 workflow")
        print(f"✅ 步骤完成\n")
    
    def step_push_code(self):
        """推送代码到GitHub"""
        print(f"\n{'='*60}")
        print(f"步骤: 推送代码到 GitHub")
        print(f"{'='*60}")
        
        if not self.github_repo_url:
            raise Exception("未找到 GitHub 仓库 URL")
        
        github_token = self.config.get("github", {}).get("token", "")
        
        print(f"📁 项目路径: {self.project_path}")
        print(f"🔗 远程地址: {self.github_repo_url}")
        print(f"🏷️ 版本标签: v{self.version}")
        
        git_mgr = GitManager(self.project_path, github_token)
        
        print(f"📤 初始化并推送...")
        git_mgr.init_and_push(self.github_repo_url, push_tags=False)
        
        print(f"✅ 代码推送成功")
        print(f"✅ 步骤完成\n")
    
    def step_trigger_publish(self):
        """触发发布（创建Tag）并等待完成"""
        print(f"\n{'='*60}")
        print(f"步骤: 触发发布并等待完成")
        print(f"{'='*60}")
        
        print(f"🏷️ 检查版本标签: v{self.version}")
        
        git_mgr = GitManager(self.project_path, self.config.get("github", {}).get("token", ""))
        
        tag_exists = False
        try:
            print(f"📤 推送标签到 GitHub...")
            git_mgr.create_and_push_tag(f"v{self.version}", f"Release v{self.version}")
            
            print(f"✅ 标签推送成功")
            print(f"🚀 GitHub Actions 已触发")
        except Exception as e:
            if "已经存在" in str(e) or "already exists" in str(e).lower():
                print(f"ℹ️ 标签 v{self.version} 已存在")
                print(f"ℹ️ GitHub Actions 可能已经运行过")
                tag_exists = True
            else:
                raise
        
        # 等待包发布
        if not tag_exists:
            print(f"\n⏳ 等待包发布到仓库...")
            print(f"💡 GitHub Actions 通常需要 2-3 分钟")
            print(f"📊 进度: https://github.com/{self.org_name}/{self.repo_name}/actions")
            
            import time
            import requests
            
            max_wait = 180  # 最多等3分钟
            check_interval = 15
            elapsed = 0
            package_found = False
            
            while elapsed < max_wait:
                try:
                    # 检查包是否已发布
                    if self.package_type and self.package_type.lower() == 'node.js':
                        url = f"https://registry.npmjs.org/{self.package_name}"
                    else:
                        url = f"https://pypi.org/pypi/{self.package_name}/json"
                    
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        print(f"\n✅ 包已成功发布！")
                        package_found = True
                        break
                    
                    print(f"   ⏳ 等待中... ({elapsed}秒/{max_wait}秒)")
                except:
                    pass
                
                time.sleep(check_interval)
                elapsed += check_interval
            
            if not package_found:
                print(f"\n⚠️ 警告: 包在 {max_wait} 秒内未发布")
                print(f"")
                print(f"可能原因：")
                print(f"  • GitHub Actions 执行失败（依赖缺失、构建错误等）")
                print(f"  • 网络问题或发布时间较长")
                print(f"")
                print(f"请检查：")
                print(f"  🔗 {f'https://github.com/{self.org_name}/{self.repo_name}/actions'}")
                print(f"")
                print(f"⛔ 停止后续流程")
                print(f"💡 修复问题后，可以只运行 EMCP 发布部分")
                raise Exception(f"包未发布，停止流程以避免无效操作")
        
        print(f"✅ 步骤完成\n")
    
    def _wait_for_package_published(self, max_wait_seconds: int = 60) -> bool:
        """
        等待包发布到包源
        
        Args:
            max_wait_seconds: 最大等待时间（秒），默认 60 秒
        
        Returns:
            bool: 包是否已发布
        """
        import time
        from src.package_fetcher import PackageFetcher
        
        fetcher = PackageFetcher()
        check_interval = 10  # 每 10 秒检查一次
        elapsed = 0
        attempt = 1
        
        while elapsed < max_wait_seconds:
            print(f"   🔍 检查第 {attempt} 次...")
            
            # 根据包类型检查
            result = None
            if self.package_type in ['pypi', 'python']:
                result = fetcher.fetch_pypi(self.package_name)
            elif self.package_type in ['npm', 'node.js', 'node']:
                result = fetcher.fetch_npm(self.package_name)
            elif self.package_type == 'docker':
                result = fetcher.fetch_docker(self.package_name)
            
            # 检查是否找到包
            if result and result.get('type') != 'unknown':
                print(f"   ✅ 包已发布到 {self.package_type}")
                if result.get('info'):
                    version = result['info'].get('version', '未知')
                    print(f"   📌 版本: {version}")
                return True
            
            # 未找到，等待后重试
            if elapsed + check_interval < max_wait_seconds:
                remaining = max_wait_seconds - elapsed
                wait_time = min(check_interval, remaining)
                print(f"   ⏳ 包未发布，等待 {wait_time} 秒后重试... (剩余 {remaining} 秒)")
                time.sleep(wait_time)
                elapsed += wait_time
                attempt += 1
            else:
                break
        
        print(f"   ❌ 超时：等待 {max_wait_seconds} 秒后包仍未发布")
        return False
    
    def _generate_command_by_type(self) -> str:
        """根据项目类型生成启动命令"""
        # 优先使用从 README 提取的命令
        if self.package_command:
            return self.package_command
        
        # 如果没有提取到命令，自动生成
        if self.package_type and self.package_type.lower() == 'node.js':
            return f"npx {self.package_name}"
        else:
            # Python 包：使用 uvx --from 格式
            # 包名用横杠，模块名用下划线
            module_name = self.package_name.replace('-', '_')
            # 使用实际版本号
            version = self.version if self.version else "1.0.0"
            return f"uvx --from {self.package_name}@{version} {module_name}"
    
    def _get_package_type_code(self) -> int:
        """获取包类型代码"""
        if self.package_type and self.package_type.lower() == 'node.js':
            return 1  # NPM
        else:
            return 2  # PyPI
    
    def _generate_route_prefix(self) -> str:
        """生成合法的路由前缀"""
        import re
        # 从包名提取，移除作用域前缀
        name = self.package_name.split('/')[-1] if '/' in self.package_name else self.package_name
        # 移除 bachai- 和 bach- 前缀
        name = name.replace('bachai-', '').replace('bachai', '').replace('bach-', '').replace('bach', '')
        # 只保留字母和数字
        name = re.sub(r'[^a-z0-9]', '', name.lower())
        # 如果以数字开头，添加前缀
        if name and name[0].isdigit():
            name = 'mcp' + name
        # 限制长度
        if len(name) > 10:
            name = name[:10]
        # 如果为空，使用默认值
        if not name:
            name = 'mcp'
        return name
    
    # ===== EMCP 发布流程 =====
    
    def step_fetch_package(self):
        """获取包信息"""
        print(f"\n{'='*60}")
        print(f"步骤: 获取包信息")
        print(f"{'='*60}")
        
        # 使用 ProjectDetector 读取真实的包名和命令
        from src.project_detector import ProjectDetector
        detector = ProjectDetector(self.project_path)
        project_info = detector.detect()
        
        # ⭐ 包名管理逻辑
        # 优先级：已设置的包名 > 仓库名 > ProjectDetector 检测结果
        
        detected_package_name = project_info.get('package_name')
        
        print(f"\n🔍 包名检测:")
        print(f"   当前包名: {getattr(self, 'package_name', 'None')}")
        print(f"   仓库名: {getattr(self, 'repo_name', 'None')}")
        print(f"   ProjectDetector 检测: {detected_package_name}")
        
        # 如果已经有包名（从克隆流程或外部设置），优先使用它
        if hasattr(self, 'package_name') and self.package_name:
            print(f"📦 使用已设置的包名: {self.package_name} ✓")
            # 不要覆盖！即使 ProjectDetector 检测到不同的值
        elif hasattr(self, 'repo_name') and self.repo_name:
            # 如果有仓库名，使用仓库名（通常是修改后的正确包名）
            self.package_name = self.repo_name
            print(f"📦 使用仓库名作为包名: {self.package_name}")
        elif detected_package_name:
            # 最后才使用 ProjectDetector 检测的包名
            self.package_name = detected_package_name
            print(f"📦 使用检测到的包名: {self.package_name}")
        else:
            # 如果都没有，报错
            raise Exception("无法确定包名")
        
        # 从 README 提取命令
        detected_command = project_info.get('command')
        if detected_command:
            self.package_command = detected_command
            print(f"🔧 从 README 提取命令: {self.package_command}")
        else:
            print(f"ℹ️ README 中未找到命令，将自动生成")
        
        print(f"🔧 项目类型: {self.package_type}")
        print(f"✅ 步骤完成\n")
    
    def _filter_readme_for_emcp(self, readme_content: str, ai_generator=None, language='zh-cn') -> str:
        """
        过滤 README 内容，优化为 EMCP 描述格式
        
        保留：
        1. 项目标题（去掉多语言链接）
        2. 简介（用 AI 生成简短版本，不提技术细节）
        3. 工具列表（保持原语言）
        
        过滤掉：EMCP 引流、多语言切换文字、安装、运行、配置、开发等章节
        
        Args:
            readme_content: 原始 README 内容（已经是对应语言的内容）
            ai_generator: AI 生成器（可选，用于生成简介）
            language: 语言代码（zh-cn, zh-tw, en）
            
        Returns:
            str: 过滤后的内容（保持原语言）
        """
        import re
        
        # 去掉多语言切换文字
        readme_content = re.sub(r'\[?English\]?\(.*?\)?\s*\|\s*\[?简体中文\]?\(.*?\)?\s*\|\s*\[?繁體中文\]?\(.*?\)?', '', readme_content)
        readme_content = re.sub(r'\[?English\]?\s*\|\s*\[?简体中文\]?\s*\|\s*\[?繁體中文\]?', '', readme_content)
        readme_content = re.sub(r'English\s*\|\s*\[简体中文\]\(.*?\)\s*\|\s*\[繁體中文\]\(.*?\)', '', readme_content)
        
        # 将内容按章节分割
        sections = {}
        current_section = 'header'
        current_content = []
        
        lines = readme_content.split('\n')
        
        for line in lines:
            # 检测二级标题
            heading_match = re.match(r'^##\s+(.+)$', line)
            
            if heading_match:
                # 保存上一个章节
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # 开始新章节
                title = heading_match.group(1).strip()
                current_section = title
                current_content = [line]
            else:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        # 需要排除的章节关键词（多语言）
        exclude_keywords = [
            '使用 EMCP 平台', 'Quick Start with EMCP', '使用 EMCP 平臺',  # EMCP 引流
            '安装', 'Installation', '安裝',  # 安装
            '运行', 'Running', '運行', 'Run',  # 运行
            '配置', 'Configuration', '配置',  # 配置
            '开发', 'Development', '開發',  # 开发
            'Claude Desktop',  # Claude Desktop 配置
            '技术栈', 'Tech Stack', 'Technology Stack', '技術棧',  # 技术栈
        ]
        
        # 构建新的 README
        result_parts = []
        
        # 1. 保留标题（去掉多语言链接）
        if 'header' in sections:
            header = sections['header'].strip()
            # 去掉标题中的多语言链接
            header = re.sub(r'\[English\]\(.*?\)', '', header)
            header = re.sub(r'\[简体中文\]\(.*?\)', '', header)
            header = re.sub(r'\[繁體中文\]\(.*?\)', '', header)
            header = header.replace('English |', '').replace('| 简体中文', '').replace('| 繁體中文', '').strip()
            # 清理多余的分隔符
            header = re.sub(r'\s*\|\s*$', '', header)
            header = re.sub(r'^\s*\|\s*', '', header)
            if header:
                result_parts.append(header)
        
        # 2. 遍历所有章节，只保留需要的
        for section_key, section_content in sections.items():
            if section_key == 'header':
                continue
            
            # 检查是否需要排除
            should_exclude = False
            for keyword in exclude_keywords:
                if keyword in section_key:
                    should_exclude = True
                    break
            
            if should_exclude:
                continue
            
            # 保留简介和工具列表章节
            is_intro = any(kw in section_key for kw in ['简介', 'Introduction', '簡介', '介绍', 'Overview'])
            is_tools = any(kw in section_key for kw in ['可用工具', 'Available Tools', '工具'])
            
            if is_intro:
                # 简介章节：用 AI 优化
                intro_lines = section_content.split('\n')[1:]  # 跳过标题行
                intro_text = '\n'.join(intro_lines).strip()
                
                # 去掉技术细节
                intro_text = re.sub(r'使用\s*\[?FastMCP\]?\(.*?\)\s*自动生成.*?。', '', intro_text, flags=re.IGNORECASE)
                intro_text = re.sub(r'This is an automatically generated.*?using\s*\[?FastMCP\]?\(.*?\).*?\.', '', intro_text, flags=re.IGNORECASE)
                intro_text = re.sub(r'這是一個使用\s*\[?FastMCP\]?\(.*?\)\s*自動生成.*?。', '', intro_text, flags=re.IGNORECASE)
                intro_text = re.sub(r'FastMCP', '', intro_text, flags=re.IGNORECASE)
                
                # 如果有 AI，生成简短版本
                if ai_generator and hasattr(ai_generator, 'client'):
                    try:
                        print(f"   🤖 使用 AI 生成简短简介 ({language})...")
                        
                        # 根据语言设置提示词
                        if language == 'en':
                            system_prompt = """You are a technical documentation expert. Write a clear, practical introduction (150-200 words) that explains:
1. What this MCP server does (main functionality)
2. What APIs/services it provides access to
3. What users can do with it (practical use cases)
4. Key features or capabilities

Do NOT mention:
- 'FastMCP' or any framework names
- 'automatically generated'
- Technical implementation details
- Installation or setup instructions

Focus on VALUE and FUNCTIONALITY. Write in a way that helps users understand if this tool is useful for them.
Output only the introduction text, no explanations."""
                            intro_title = "## Introduction"
                        elif language == 'zh-tw':
                            system_prompt = """你是技術文檔專家。請撰寫清晰、實用的簡介（150-200字），說明：
1. 這個 MCP 伺服器做什麼（主要功能）
2. 它提供哪些 API/服務的存取
3. 使用者可以用它做什麼（實際用途）
4. 關鍵特性或能力

不要提及：
- 「FastMCP」或任何框架名稱
- 「自動生成」
- 技術實作細節
- 安裝或設定說明

聚焦於價值和功能。用能幫助使用者了解這個工具是否有用的方式撰寫。
只輸出簡介文字，不要額外說明。"""
                            intro_title = "## 簡介"
                        else:
                            system_prompt = """你是技术文档专家。请撰写清晰、实用的简介（150-200字），说明：
1. 这个 MCP 服务器做什么（主要功能）
2. 它提供哪些 API/服务的访问
3. 用户可以用它做什么（实际用途）
4. 关键特性或能力

不要提及：
- 「FastMCP」或任何框架名称
- 「自动生成」
- 技术实现细节
- 安装或设置说明

聚焦于价值和功能。用能帮助用户了解这个工具是否有用的方式撰写。
只输出简介文字，不要额外说明。"""
                            intro_title = "## 简介"
                        
                        messages = [
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": intro_text[:800]
                            }
                        ]
                        
                        response = ai_generator.client.chat.completions.create(
                            model=ai_generator.deployment_name,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=300
                        )
                        
                        ai_intro = response.choices[0].message.content.strip()
                        result_parts.append(f"{intro_title}\n\n{ai_intro}")
                        print(f"   ✅ AI 生成简介: {len(ai_intro)} 字符")
                    except Exception as e:
                        print(f"   ⚠️ AI 生成失败，使用原文: {e}")
                        # 降级：使用原文（已去掉技术细节）
                        short_intro = intro_text[:150] + ('...' if len(intro_text) > 150 else '')
                        result_parts.append(f"## 简介\n\n{short_intro}")
                else:
                    # 没有 AI：使用原文（已去掉技术细节）
                    short_intro = intro_text[:150] + ('...' if len(intro_text) > 150 else '')
                    result_parts.append(f"## 简介\n\n{short_intro}")
            
            elif is_tools:
                # 工具列表章节：直接保留（保持原语言）
                result_parts.append(section_content)
        
        # 组合结果
        result = '\n\n'.join(result_parts)
        
        # 清理多余空行
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        # 限制总长度
        max_length = 3000
        if len(result) > max_length:
            result = result[:max_length] + '\n\n...'
        
        return result.strip()
    
    def _load_multilang_readmes(self):
        """
        加载多语言 README 文件
        优先查找 mcp 文件夹中的 README 文件
        
        Returns:
            dict: 包含三种语言描述的字典，如果找到则跳过 AI 生成
        """
        mcp_dir = self.project_path / "mcp"
        
        # README 文件映射
        readme_files = {
            "description_zh_cn": ["readme.md", "README.md", "README_ZH-CN.md"],
            "description_en": ["README_EN.md", "README-EN.md"],
            "description_zh_tw": ["README_ZH-TW.md", "README-ZH-TW.md"]
        }
        
        loaded_content = {}
        
        # 优先从 mcp 文件夹读取
        if mcp_dir.exists():
            print(f"📁 找到 mcp 文件夹")
            for key, filenames in readme_files.items():
                for filename in filenames:
                    file_path = mcp_dir / filename
                    if file_path.exists():
                        try:
                            content = file_path.read_text(encoding='utf-8')
                            # 过滤 README 内容（传入 AI generator 和语言）
                            ai_gen = getattr(self, 'ai_generator', None)
                            
                            # 根据 key 确定语言
                            lang = 'zh-cn'
                            if 'zh_tw' in key or 'ZH-TW' in filename:
                                lang = 'zh-tw'
                            elif 'en' in key or 'EN' in filename:
                                lang = 'en'
                            
                            filtered_content = self._filter_readme_for_emcp(content, ai_gen, lang)
                            loaded_content[key] = filtered_content
                            print(f"   ✅ 读取 {filename} ({lang}): {len(content)} 字符 → 过滤后 {len(filtered_content)} 字符")
                            break
                        except Exception as e:
                            print(f"   ⚠️ 读取 {filename} 失败: {e}")
        
        # 如果 mcp 文件夹不存在或文件不全，从项目根目录读取
        if len(loaded_content) < 3:
            print(f"📁 从项目根目录查找 README 文件")
            for key, filenames in readme_files.items():
                if key in loaded_content:
                    continue
                for filename in filenames:
                    file_path = self.project_path / filename
                    if file_path.exists():
                        try:
                            content = file_path.read_text(encoding='utf-8')
                            # 过滤 README 内容（传入 AI generator 和语言）
                            ai_gen = getattr(self, 'ai_generator', None)
                            
                            # 根据 key 确定语言
                            lang = 'zh-cn'
                            if 'zh_tw' in key or 'ZH-TW' in filename:
                                lang = 'zh-tw'
                            elif 'en' in key or 'EN' in filename:
                                lang = 'en'
                            
                            filtered_content = self._filter_readme_for_emcp(content, ai_gen, lang)
                            loaded_content[key] = filtered_content
                            print(f"   ✅ 读取 {filename} ({lang}): {len(content)} 字符 → 过滤后 {len(filtered_content)} 字符")
                            break
                        except Exception as e:
                            print(f"   ⚠️ 读取 {filename} 失败: {e}")
        
        # 如果至少找到了简体中文 README，返回加载的内容
        if "description_zh_cn" in loaded_content:
            # 如果缺少繁体或英文，使用简体中文作为备用
            if "description_zh_tw" not in loaded_content:
                loaded_content["description_zh_tw"] = loaded_content["description_zh_cn"]
                print(f"   ℹ️ 未找到繁体 README，使用简体版本")
            if "description_en" not in loaded_content:
                loaded_content["description_en"] = loaded_content["description_zh_cn"]
                print(f"   ℹ️ 未找到英文 README，使用简体版本")
            
            # 添加名称（从 README 第一行提取或使用包名）
            for lang_key, desc_key in [
                ("name_zh_cn", "description_zh_cn"),
                ("name_zh_tw", "description_zh_tw"),
                ("name_en", "description_en")
            ]:
                if desc_key in loaded_content:
                    # 尝试从 README 第一行提取标题
                    lines = loaded_content[desc_key].split('\n')
                    title = None
                    for line in lines:
                        line = line.strip()
                        if line.startswith('#'):
                            title = line.lstrip('#').strip()
                            break
                    loaded_content[lang_key] = title if title else self.package_name
            
            print(f"✅ 成功加载 {len([k for k in loaded_content.keys() if k.startswith('description_')])} 个语言的 README 文件")
            return loaded_content
        
        return None
    
    def step_ai_generate(self):
        """AI生成模板 - 学习批量脚本的方式，正确生成 summary 和 description"""
        print(f"\n{'='*60}")
        print(f"步骤: AI 生成模板")
        print(f"{'='*60}")
        
        # 检测环境变量配置需求（如果还没有配置）
        if not hasattr(self, 'env_vars_config') or not self.env_vars_config:
            print(f"\n🔍 检测环境变量配置...")
            from src.env_var_detector import EnvVarDetector
            detector = EnvVarDetector()
            env_vars = detector.detect_from_project(self.project_path)
            
            if env_vars:
                print(f"   发现 {len(env_vars)} 个环境变量需要配置")
                for var in env_vars:
                    required_text = "必需" if var['required'] else "可选"
                    print(f"   - {var['name']}: {var['description']} ({required_text})")
                
                # 弹出对话框让用户确认/修改
                print(f"\n💡 请在弹出的对话框中填写环境变量说明...")
                
                from src.env_var_dialog import EnvVarDialog
                import tkinter as tk
                
                root = self.parent if hasattr(self, 'parent') else tk._default_root
                dialog = EnvVarDialog(root, env_vars, self.package_name)
                configured_vars = dialog.show()
                
                if not configured_vars:
                    print(f"❌ 用户取消了环境变量配置")
                    raise Exception("必须配置环境变量才能发布到 EMCP")
                
                self.env_vars_config = configured_vars
                print(f"✅ 用户已配置 {len(configured_vars)} 个环境变量")
            else:
                print(f"   ✅ 未检测到需要配置的环境变量")
                self.env_vars_config = []
        else:
            print(f"\n✅ 使用预配置的环境变量 ({len(self.env_vars_config)} 个)")
        
        ai_config = self.config.get("azure_openai", {})
        
        if not ai_config.get("endpoint") or not ai_config.get("api_key"):
            print(f"\n⚠️ 未配置 Azure OpenAI，使用基础生成器")
            self.template_data = {
                "name_zh_cn": self.package_name,
                "name_zh_tw": self.package_name,
                "name_en": self.package_name,
                "summary_zh_cn": f"{self.package_name} MCP服务器",
                "summary_zh_tw": f"{self.package_name} MCP伺服器",
                "summary_en": f"{self.package_name} MCP Server",
                "description_zh_cn": f"{self.package_name} 是一个功能强大的 MCP 服务器",
                "description_zh_tw": f"{self.package_name} 是一個功能強大的 MCP 伺服器",
                "description_en": f"{self.package_name} is a powerful MCP Server"
            }
            print(f"✅ 使用基础模板")
            print(f"✅ 步骤完成\n")
            return
        
        print(f"🤖 Azure OpenAI Endpoint: {ai_config['endpoint']}")
        print(f"🤖 Deployment: {ai_config['deployment_name']}")
        
        try:
            # 初始化并登录EMCP
            emcp_config = self.config_mgr.get_emcp_config()
            if not self.emcp_manager:
                self.emcp_manager = EMCPManager()
                self.emcp_manager.base_url = emcp_config.get('base_url', 'https://sit-emcp.kaleido.guru')
            
            # 确保已登录
            if emcp_config.get("phone_number") and not self.emcp_manager.session_key:
                print(f"🔐 登录 EMCP...")
                try:
                    user_info = self.emcp_manager.login(
                        emcp_config['phone_number'],
                        emcp_config['validation_code'],
                        fallback_token=emcp_config.get('fallback_token')
                    )
                    print(f"✅ EMCP 登录成功: {user_info.get('user_name', 'Unknown')}")
                except Exception as e:
                    print(f"⚠️ EMCP 登录失败: {e}")
            
            # ⭐ 获取 EMCP 分类列表（学习批量脚本的做法）
            print(f"\n📋 获取 EMCP 分类列表...")
            category_map = {}
            category_text = ""
            try:
                categories = self.emcp_manager.get_all_template_categories()
                if categories:
                    print(f"   ✅ 获取到 {len(categories)} 个分类")
                    category_text = "可选的分类列表：\n"
                    for cat in categories:
                        cat_id = (cat.get('templateCategoryId') or 
                                 cat.get('template_category_id') or 
                                 cat.get('id'))
                        # 从多语言数据中提取名称
                        cat_name_data = cat.get('name', [])
                        if isinstance(cat_name_data, list):
                            for item in cat_name_data:
                                if isinstance(item, dict) and item.get('type') == 1:
                                    cat_name = item.get('content', '')
                                    break
                            else:
                                cat_name = str(cat_name_data)
                        else:
                            cat_name = str(cat_name_data)
                        
                        if cat_id:
                            category_map[str(cat_id)] = cat_name
                            category_text += f"- ID: {cat_id}, 名称: {cat_name}\n"
                            print(f"      - {cat_id}: {cat_name}")
            except Exception as e:
                print(f"   ⚠️ 获取分类失败: {e}")
            
            # 初始化 AI 生成器
            ai_gen = AITemplateGenerator(
                azure_endpoint=ai_config['endpoint'],
                api_key=ai_config['api_key'],
                api_version=ai_config.get('api_version', '2024-02-15-preview'),
                deployment_name=ai_config['deployment_name'],
                emcp_manager=self.emcp_manager
            )
            
            self.ai_generator = ai_gen
            
            # 从本地项目读取完整信息
            from src.project_detector import ProjectDetector
            detector = ProjectDetector(self.project_path)
            project_info = detector.detect()
            
            # 获取 README 内容
            readme_content = project_info.get('readme', '')
            
            # 如果没有 README，尝试从文件读取
            if not readme_content:
                readme_paths = [
                    self.project_path / "mcp" / "README.md",
                    self.project_path / "README.md",
                    self.project_path / "readme.md"
                ]
                for readme_path in readme_paths:
                    if readme_path.exists():
                        try:
                            readme_content = readme_path.read_text(encoding='utf-8')
                            print(f"   📄 从 {readme_path.name} 读取: {len(readme_content)} 字符")
                            break
                        except Exception as e:
                            print(f"   ⚠️ 读取 {readme_path.name} 失败: {e}")
            
            # 构建包信息（包含完整 README）
            package_info = {
                "package_name": self.package_name,
                "type": self.package_type,
                "info": {
                    "name": project_info.get('name', self.package_name),
                    "version": project_info.get('version', '1.0.0'),
                    "summary": project_info.get('description', f"{self.package_name} MCP Server"),
                    "description": readme_content,
                    "readme": readme_content,
                    "author": "BACH Studio"
                }
            }
            
            print(f"\n📝 README 内容: {len(readme_content)} 字符")
            print(f"🤖 调用 AI 生成模板信息...")
            print(f"   ⭐ 生成简洁的 summary（20-50字）")
            print(f"   ⭐ 生成完整的 description（200-400字）")
            print(f"   ⭐ 智能选择分类")
            
            # ⭐ 调用 AI 生成器，传入分类列表（学习批量脚本的做法）
            result = ai_gen.generate_template_info(
                package_info, 
                self.package_type or "mcp",
                category_text if category_text else None  # ⭐ 传入分类列表
            )
            
            self.template_data = result
            
            print(f"\n✅ AI 生成完成")
            print(f"  📛 名称: {result.get('name_zh_cn', '')}")
            print(f"  📝 简介: {result.get('summary_zh_cn', '')[:60]}...")
            print(f"  📄 描述: {len(result.get('description_zh_cn', ''))} 字符")
            print(f"  🏷️ 分类: {result.get('category_id', '')}")
            
        except Exception as e:
            import traceback
            print(f"⚠️ AI 生成失败: {str(e)}")
            print(f"   {traceback.format_exc()}")
            print(f"⚠️ 使用基础模板")
            self.template_data = {
                "name_zh_cn": self.package_name,
                "name_zh_tw": self.package_name,
                "name_en": self.package_name,
                "summary_zh_cn": f"{self.package_name} MCP服务器",
                "summary_zh_tw": f"{self.package_name} MCP伺服器",
                "summary_en": f"{self.package_name} MCP Server",
                "description_zh_cn": f"{self.package_name} 是一个功能强大的 MCP 服务器",
                "description_zh_tw": f"{self.package_name} 是一個功能強大的 MCP 伺服器",
                "description_en": f"{self.package_name} is a powerful MCP Server"
            }
        
        print(f"✅ 步骤完成\n")
    
    def step_generate_logo(self):
        """生成Logo - 使用即梦 API 方式"""
        print(f"\n{'='*60}")
        print(f"步骤: 生成 Logo (使用即梦 API)")
        print(f"{'='*60}")
        
        jimeng_config = self.config_mgr.get_jimeng_config()
        
        if not jimeng_config.get("enabled", True):
            print(f"⚠️ 即梦 Logo 生成未启用，使用默认 Logo")
            self.logo_url = "https://emcp.kaleido.guru/logo/default-mcp-logo.png"
            return
        
        # 获取即梦 API 密钥
        access_key = jimeng_config.get("access_key", "")
        secret_key = jimeng_config.get("secret_key", "")
        
        if not access_key or not secret_key:
            print(f"⚠️ 即梦 API 密钥未配置")
            print(f"   请在设置中配置 Access Key 和 Secret Key")
            print(f"   使用默认 Logo")
            self.logo_url = "https://emcp.kaleido.guru/logo/default-mcp-logo.png"
            print(f"✅ 步骤完成\n")
            return
        
        try:
            # 初始化即梦 API 客户端
            print(f"🔧 初始化即梦 API 客户端...")
            jimeng_api = JimengAPIGenerator(access_key, secret_key)
            
            # 准备 Logo 描述
            logo_description = None
            
            # 优先使用已生成的 EMCP 描述（更准确）
            if hasattr(self, 'template_data') and self.template_data:
                desc_zh = self.template_data.get('description_zh_cn', '')
                if desc_zh:
                    logo_description = desc_zh
                    print(f"   📝 使用 MCP 模板描述: {len(logo_description)} 字符")
            
            # 如果没有 EMCP 描述，从 README 读取
            if not logo_description and hasattr(self, 'project_path') and self.project_path:
                try:
                    readme_path = self.project_path / "mcp" / "README.md"
                    if not readme_path.exists():
                        readme_path = self.project_path / "README.md"
                    if not readme_path.exists():
                        readme_path = self.project_path / "readme.md"
                    if readme_path.exists():
                        logo_description = readme_path.read_text(encoding='utf-8')
                        print(f"   📝 从 README 读取: {len(logo_description)} 字符")
                except Exception as e:
                    print(f"   ⚠️ 读取 README 失败: {e}")
            
            # 最后的降级：使用包名
            if not logo_description:
                logo_description = f"{self.package_name} - MCP Server for {self.package_type or 'software'} package"
                print(f"   📝 使用默认描述")
            
            # 使用即梦 API 生成 Logo
            print(f"\n🎨 调用即梦 API 生成 Logo...")
            result = jimeng_api.generate_logo_for_mcp(
                description=logo_description,
                mcp_name=self.package_name
            )
            
            if not result.get('success') or not result.get('image_url'):
                print(f"⚠️ Logo 生成失败: {result.get('error', '未知错误')}")
                print(f"   使用默认 Logo")
                self.logo_url = "https://emcp.kaleido.guru/logo/default-mcp-logo.png"
            else:
                jimeng_image_url = result['image_url']
                print(f"✅ 即梦 API 生成成功")
                print(f"   原始 URL: {jimeng_image_url[:80]}...")
                
                # 下载并保存到本地
                print(f"\n💾 下载并保存 Logo...")
                local_file = self._save_logo_locally(jimeng_image_url, self.package_name)
                if local_file:
                    print(f"✅ 本地文件: {local_file}")
                
                # 上传到 EMCP
                print(f"\n⬆️ 上传到 EMCP...")
                emcp_config = self.config_mgr.get_emcp_config()
                emcp_base_url = emcp_config.get("base_url", "https://sit-emcp.kaleido.guru")
                
                session_token = None
                if hasattr(self, 'emcp_manager') and self.emcp_manager and hasattr(self.emcp_manager, 'session_key'):
                    session_token = self.emcp_manager.session_key
                
                emcp_logo_url = self._upload_logo_to_emcp(jimeng_image_url, emcp_base_url, session_token)
                
                if emcp_logo_url:
                    self.logo_url = emcp_logo_url
                    print(f"✅ EMCP URL: {emcp_logo_url}")
                else:
                    self.logo_url = jimeng_image_url
                    print(f"⚠️ EMCP 上传失败，使用即梦 URL")
                
                print(f"✅ Logo URL: {self.logo_url}")
                
        except Exception as e:
            print(f"❌ Logo 生成出错: {e}")
            import traceback
            print(f"   {traceback.format_exc()}")
            print(f"   使用默认 Logo")
            self.logo_url = "https://emcp.kaleido.guru/logo/default-mcp-logo.png"
        
        print(f"✅ 步骤完成\n")
    
    def _save_logo_locally(self, image_url: str, package_name: str):
        """保存 Logo 到本地文件"""
        import requests
        import re
        
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            # 确保 outputs/logos 目录存在
            logos_dir = Path("outputs/logos")
            logos_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理文件名中的非法字符
            safe_name = re.sub(r'[/\\:*?"<>|@]', '_', package_name)
            filename = logos_dir / f"logo_{safe_name}.png"
            
            with open(filename, 'wb') as f:
                f.write(image_data)
            
            print(f"   ✅ 已保存到: {filename.absolute()}")
            print(f"   📦 文件大小: {len(image_data):,} 字节")
            
            return str(filename)
            
        except Exception as e:
            print(f"   ❌ 保存失败: {e}")
            return None
    
    def _upload_logo_to_emcp(self, image_url: str, base_url: str, session_token: str = None):
        """下载图片并上传到 EMCP"""
        import requests
        
        try:
            # 步骤 1: 从即梦 URL 下载图片
            print(f"   ⬇️ 下载图片...")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            print(f"   ✅ 下载完成: {len(image_data):,} 字节")
            
            # 步骤 2: 构建文件流并上传到 EMCP
            upload_url = f"{base_url}/api/proxyStorage/NoAuth/upload_file"
            
            files = {
                'file': ('logo.png', image_data, 'image/png')
            }
            
            headers = {}
            if session_token:
                headers['token'] = session_token
            
            print(f"   📤 上传到 EMCP...")
            response = requests.post(upload_url, files=files, headers=headers, timeout=30)
            
            # 检查 401 错误并尝试自动登录重试
            if response.status_code == 401:
                print(f"   ⚠️ Token 已过期，尝试重新登录...")
                
                emcp_config = self.config_mgr.get_emcp_config()
                if emcp_config.get("phone_number"):
                    login_url = f"{base_url}/api/Login/login"
                    login_data = {
                        "phone_number": emcp_config['phone_number'],
                        "validation_code": emcp_config['validation_code']
                    }
                    
                    login_resp = requests.post(login_url, json=login_data, timeout=30)
                    if login_resp.status_code == 200:
                        login_result = login_resp.json()
                        if login_result.get('err_code') == 0:
                            new_token = login_result['body']['session_key']
                            print(f"   ✅ 重新登录成功")
                            
                            # 重试上传
                            headers['token'] = new_token
                            response = requests.post(upload_url, files={
                                'file': ('logo.png', image_data, 'image/png')
                            }, headers=headers, timeout=30)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('err_code') == 0:
                logo_url = data.get('body', {}).get('fileUrl')
                print(f"   ✅ 上传成功")
                return logo_url
            else:
                print(f"   ❌ 上传失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"   ❌ 上传错误: {e}")
            return None
    
    def step_publish_emcp(self):
        """发布到EMCP"""
        print(f"\n{'='*60}")
        print(f"步骤: 发布到 EMCP")
        print(f"{'='*60}")
        
        # 使用 get_emcp_config() 自动生成今日验证码
        emcp_config = self.config_mgr.get_emcp_config()
        
        if not emcp_config.get("phone_number"):
            print(f"⚠️ 未配置 EMCP 账号，跳过 EMCP 发布")
            return
        
        print(f"🌐 EMCP 平台: {emcp_config['base_url']}")
        print(f"📱 手机号: {emcp_config['phone_number']}")
        print(f"📦 包名: {self.package_name}")
        
        try:
            # 初始化EMCP管理器（只初始化一次，后续复用）
            if not self.emcp_manager:
                self.emcp_manager = EMCPManager()
                self.emcp_manager.base_url = emcp_config['base_url']
            
            emcp_mgr = self.emcp_manager
            
            # 登录EMCP（只登录一次）
            if not emcp_mgr.session_key:
                print(f"🔐 登录 EMCP 平台...")
                phone = emcp_config['phone_number']
                code = emcp_config['validation_code']
                print(f"📱 手机号: {phone}")
                print(f"🔑 验证码: {code}")
                
                # 获取备用 token（如果有）
                fallback_token = emcp_config.get('fallback_token', 'd303fc3a-ff8c-422f-afb8-6fc02d685ee2')
                
                user_info = emcp_mgr.login(phone, code, fallback_token=fallback_token)
                
                print(f"✅ 登录成功")
                print(f"👤 用户: {user_info.get('user_name', 'Unknown')}")
                print(f"🆔 用户ID: {user_info.get('uid')}")
                print(f"🔑 Session: {emcp_mgr.session_key[:20]}...")
            else:
                print(f"ℹ️ 复用已有EMCP登录")
                print(f"👤 用户: {emcp_mgr.user_info.get('user_name', 'Unknown')}")
            
            # 准备模板数据
            if not hasattr(self, 'template_data'):
                self.template_data = {
                    "name_zh_cn": self.package_name,
                    "name_zh_tw": self.package_name,
                    "name_en": self.package_name,
                    "summary_zh_cn": f"{self.package_name} MCP服务器",  # ✅ 摘要字段
                    "summary_zh_tw": f"{self.package_name} MCP伺服器",
                    "summary_en": f"{self.package_name} MCP Server",
                    "description_zh_cn": f"{self.package_name} 是一个功能强大的 MCP 服务器",  # ✅ 描述字段
                    "description_zh_tw": f"{self.package_name} 是一個功能強大的 MCP 伺服器",
                    "description_en": f"{self.package_name} is a powerful MCP Server"
                }
            
            print(f"\n📝 获取EMCP平台配置...")
            
            # 获取 Logo URL - 优先使用生成的Logo，否则使用默认
            # 1. 首先检查 self.logo_url（从 step_generate_logo 设置）
            # 2. 其次检查 template_data 中的 logo_url
            # 3. 最后使用默认 logo
            logo_url = None
            if hasattr(self, 'logo_url') and self.logo_url:
                logo_url = self.logo_url
                print(f"🖼️ 使用生成的Logo: {logo_url[:80]}...")
            elif self.template_data.get("logo_url"):
                logo_url = self.template_data.get("logo_url")
                print(f"🖼️ 使用模板中的Logo: {logo_url}")
            else:
                logo_url = "https://emcp.kaleido.guru/logo/default-mcp-logo.png"
                print(f"🖼️ 使用默认Logo: {logo_url}")
            
            # ⭐ 获取模板分类ID - 优先使用 AI 生成的分类
            print(f"📋 获取模板分类...")
            template_category_id = None
            
            # 优先使用 AI 生成的分类 ID
            if hasattr(self, 'template_data') and self.template_data.get('category_id'):
                template_category_id = str(self.template_data.get('category_id'))
                print(f"✓ 使用 AI 选择的分类 ID: {template_category_id}")
            
            # 如果没有 AI 分类，使用默认分类
            if not template_category_id:
                try:
                    categories = emcp_mgr.get_all_template_categories()
                    if categories and len(categories) > 0:
                        first_category = categories[0]
                        template_category_id = (first_category.get('templateCategoryId') or
                                               first_category.get('template_category_id') or
                                               first_category.get('id') or "1")
                        print(f"✓ 使用默认分类 ID: {template_category_id}")
                    else:
                        template_category_id = "1"
                        print(f"ℹ️ 未获取到分类，使用默认ID: {template_category_id}")
                except Exception as e:
                    template_category_id = "1"
                    print(f"ℹ️ 获取分类失败: {str(e)}，使用默认ID: {template_category_id}")
            
            print(f"\n📝 构建模板数据...")
            
            # 构建 args 参数（包含环境变量配置）
            args_list = []
            
            # 添加环境变量配置 - 修复字段格式
            if hasattr(self, 'env_vars_config') and self.env_vars_config:
                print(f"   📋 添加 {len(self.env_vars_config)} 个环境变量到配置")
                for env_var in self.env_vars_config:
                    # 获取默认值
                    default_val = env_var.get('example', '')
                    
                    # 使用正确的API格式
                    arg_item = {
                        "arg_name": env_var['name'],  # ✅ 使用 arg_name
                        "default_value": default_val,  # ✅ 使用 default_value
                        "description": emcp_mgr.make_multi_lang(
                            env_var.get('description', env_var['name']),
                            env_var.get('description', env_var['name']),
                            env_var.get('description', env_var['name'])
                        ),
                        "auth_method_id": "",
                        "type": 2,  # ✅ 2 = custom_value（数字类型）
                        "paramter_type": 1,  # ✅ 1 = StartupParameter
                        "input_source": 1,  # ✅ 1 = AdminInput
                        "showDefault": False,
                        "oauth_authorized": False,
                        "r": env_var.get('required', False)  # ✅ 添加必需的 r 字段
                    }
                    args_list.append(arg_item)
                    # ⭐ 打印包括默认值
                    val_display = f"{default_val[:20]}..." if default_val and len(default_val) > 20 else default_val
                    print(f"     • {env_var['name']}: {env_var['description']} = {val_display}")
            else:
                print(f"   ℹ️ 无需环境变量配置")
            
            # 使用build_template_data构建完整数据
            full_template_data = emcp_mgr.build_template_data(
                name=self.template_data.get("name_zh_cn", self.package_name),
                summary=self.template_data.get("summary_zh_cn", f"{self.package_name} MCP服务器"),  # ✅ 使用摘要字段
                description=self.template_data.get("description_zh_cn", f"{self.package_name} MCP服务器"),  # ✅ 使用描述字段
                logo_url=logo_url,  # 使用AI生成的Logo或默认Logo
                template_category_id=template_category_id,  # 使用获取的分类ID
                template_source_id=self.package_name,  # 使用包名作为来源ID
                command=self._generate_command_by_type(),  # 根据类型生成命令
                route_prefix=self._generate_route_prefix(),  # 生成合法的路由前缀
                package_type=self._get_package_type_code(),  # 根据类型获取代码
                args=args_list,  # ✅ 添加环境变量配置
                name_en=self.template_data.get("name_en", self.package_name),
                summary_en=self.template_data.get("summary_en", f"{self.package_name} MCP Server"),  # ✅ 使用摘要字段
                description_en=self.template_data.get("description_en", f"{self.package_name} MCP Server"),  # ✅ 使用描述字段
                name_tw=self.template_data.get("name_zh_tw", self.package_name),
                summary_tw=self.template_data.get("summary_zh_tw", f"{self.package_name} MCP伺服器"),  # ✅ 使用摘要字段
                description_tw=self.template_data.get("description_zh_tw", f"{self.package_name} MCP伺服器")  # ✅ 使用描述字段
            )
            
            print(f"📦 包名: {self.package_name}")
            print(f"🔧 命令: {self._generate_command_by_type()}")
            print(f"🛤️ 路由: {self._generate_route_prefix()}")
            
            # 发布或更新模板
            print(f"\n🚀 调用 EMCP API...")
            operation, result = emcp_mgr.create_or_update_mcp_template(
                template_source_id=self.package_name,
                template_data=full_template_data
            )
            
            print(f"\n📥 API 响应:")
            print(f"  操作类型: {operation}")
            print(f"  Result 类型: {type(result)}")
            print(f"  Result 内容: {result}")
            
            # create_mcp_template 直接返回 body 字典，不是完整响应
            # 所以 result 就是 body，里面有 templateId
            if result:
                # result 直接就是 body
                self.template_id = (result.get('templateId') or 
                                  result.get('template_id') or 
                                  result.get('id'))
                
                if self.template_id:
                    print(f"✅ {operation.upper()} 成功！")
                    print(f"🆔 模板ID: {self.template_id}")
                    print(f"🔗 可在EMCP平台查看模板")
                else:
                    print(f"⚠️ 未找到模板ID")
                    print(f"  返回数据: {result}")
                    raise Exception("EMCP发布失败: 未获取到模板ID")
            else:
                print(f"⚠️ 未获取到响应")
                raise Exception("EMCP API无响应")
                
        except Exception as e:
            import traceback
            print(f"\n{'!'*60}")
            print(f"❌ EMCP 发布异常")
            print(f"{'!'*60}")
            print(f"错误信息: {str(e)}")
            print(f"\n完整错误堆栈:")
            print(traceback.format_exc())
            print(f"{'!'*60}\n")
            raise  # 抛出异常，停止后续执行
        
        print(f"✅ 步骤完成\n")
    
    # ===== 测试流程 =====
    
    def step_test_mcp(self):
        """MCP测试"""
        print(f"\n{'='*60}")
        print(f"步骤: MCP 测试")
        print(f"{'='*60}")
        
        if not self.template_id:
            print(f"⚠️ 未找到模板ID，跳过 MCP 测试")
            return
        
        print(f"🆔 模板ID: {self.template_id}")
        
        try:
            # 复用EMCP管理器
            if not self.emcp_manager or not self.emcp_manager.session_key:
                print(f"⚠️ EMCP未登录，跳过MCP测试")
                return
            
            # ⭐ 步骤 0: 检查包是否已发布到包源
            print(f"\n📦 步骤 0: 检查包是否已发布到包源...")
            print(f"   包名: {self.package_name}")
            print(f"   包类型: {self.package_type}")
            print(f"   仓库名: {self.repo_name}")
            
            # ⚠️ 如果包名和仓库名不一致，发出警告
            if hasattr(self, 'repo_name') and self.package_name != self.repo_name:
                print(f"   ⚠️ 警告：包名与仓库名不一致！")
                print(f"      这可能导致查询错误的包")
            
            if not self._wait_for_package_published(max_wait_seconds=60):
                print(f"\n❌ 包未发布到包源，无法启动 MCP 服务器")
                print(f"💡 可能的原因：")
                print(f"   1. GitHub Actions 还在运行中")
                print(f"   2. 发布过程出现错误")
                print(f"   3. 包名不正确")
                print(f"\n⏸️ 终止测试流程")
                raise Exception(f"包 {self.package_name} 未发布到 {self.package_type} 包源，无法测试")
            
            print(f"✅ 包已发布，可以开始测试")
            print(f"\n🧪 开始测试 MCP 工具...")
            
            emcp_mgr = self.emcp_manager
            user_id = emcp_mgr.user_info.get('uid', 51)
            
            print(f"ℹ️ 复用EMCP登录")
            print(f"👤 用户ID: {user_id}")
            
            # 创建测试器
            tester = MCPTester(emcp_mgr, None)  # 暂不传AI
            
            print(f"🔗 连接MCP服务...")
            print(f"📋 获取工具列表...")
            print(f"🧪 测试每个工具...")
            
            # 执行测试
            report = tester.test_template(self.template_id, user_id)
            
            # 生成报告
            report_file = f"mcp_test_report_{self.template_id[:8]}.html"
            tester.generate_test_report_html(report, report_file)
            
            # ⭐ 测试完成后关闭 MCP Server（释放服务器资源）
            print(f"\n🔌 关闭 MCP Server（释放资源）...")
            try:
                self._close_mcp_server(self.template_id)
                print(f"   ✅ MCP Server 已关闭")
            except Exception as e:
                print(f"   ⚠️ 关闭 MCP Server 失败: {e}")
            
            # 检查是否成功（特别是 Server 是否启动）
            if report.get('error') and 'MCP Server 启动失败' in str(report.get('error')):
                print(f"\n⛔ MCP Server 启动失败!")
                print(f"📊 测试报告: {report_file}")
                print(f"\n💡 请修复以下问题后再继续：")
                print(f"   1. 确认包已成功发布到 npm/pypi")
                print(f"   2. 确认包名正确（当前: {self.package_name}）")
                print(f"   3. 检查 GitHub Actions 构建日志")
                print(f"\n⏸️ 停止后续流程（Agent测试/对话测试）")
                raise Exception("MCP Server 启动失败，停止后续流程")
            
            print(f"✅ MCP 测试完成")
            print(f"📊 测试报告: {report_file}")
            
            if report.get('tools_report'):
                tools_report = report['tools_report']
                print(f"  总工具数: {tools_report.get('total_tools', 0)}")
                print(f"  通过: {tools_report.get('passed_tools', 0)}")
                print(f"  失败: {tools_report.get('failed_tools', 0)}")
                print(f"  成功率: {tools_report.get('success_rate', 0):.1f}%")
                
                if tools_report.get('edgeone_url'):
                    print(f"🌐 公开链接: {tools_report['edgeone_url']}")
            else:
                print(f"⚠️ 未获取到工具测试结果")
            
        except Exception as e:
            print(f"⚠️ MCP 测试失败: {str(e)}")
            # 如果是 Server 启动失败，重新抛出异常以停止后续流程
            if "MCP Server 启动失败" in str(e) or "停止后续流程" in str(e):
                raise
            print(f"ℹ️ 跳过测试，继续执行")
        
        print(f"✅ 步骤完成\n")
    
    def _close_mcp_server(self, template_id: str) -> bool:
        """
        关闭 MCP Server（删除启动的 server 实例，释放服务器资源）
        
        步骤：
        1. 查询 template 下的所有 server
        2. 逐个删除 server
        3. 将模板状态改为 1（关闭状态）
        
        Args:
            template_id: 模板 ID
        
        Returns:
            是否成功
        """
        import requests
        
        if not self.emcp_manager or not self.emcp_manager.session_key:
            print(f"   ⚠️ 未登录 EMCP，无法关闭 Server")
            return False
        
        base_url = self.emcp_manager.base_url
        headers = {
            'token': self.emcp_manager.session_key,
            'language': 'ch_cn',
            'Content-Type': 'application/json'
        }
        
        try:
            # ===== 步骤 1: 查询 template 下的所有 server =====
            print(f"   🔍 查询 template 下的 server 列表...")
            query_url = f"{base_url}/api/Service/query_mcp_server"
            query_data = {
                "page_index": 1,
                "page_size": 100,
                "name": "",
                "template_category_id": "",
                "server_ids": [],
                "template_ids": [template_id]
            }
            
            response = requests.post(query_url, json=query_data, headers=headers, timeout=30)
            data = response.json()
            
            if data.get('err_code') != 0:
                print(f"   ⚠️ 查询 server 列表失败: {data.get('err_message')}")
                return False
            
            # 获取 server 列表
            servers = data.get('body', {}).get('data', [])
            total_servers = len(servers)
            
            if total_servers == 0:
                print(f"   ℹ️ 该 template 下没有运行中的 server")
            else:
                print(f"   📋 发现 {total_servers} 个 server")
                
                # ===== 步骤 2: 逐个删除 server =====
                deleted_count = 0
                for server in servers:
                    server_id = server.get('serverId') or server.get('server_id') or server.get('id')
                    server_name = server.get('name', 'Unknown')
                    
                    if not server_id:
                        print(f"      ⚠️ 跳过无效 server（无 ID）")
                        continue
                    
                    print(f"      🗑️ 删除 server: {server_name} ({server_id[:8]}...)")
                    
                    delete_url = f"{base_url}/api/UserProfile/delete_all_user_profile_info/{server_id}"
                    
                    try:
                        del_response = requests.delete(delete_url, headers=headers, timeout=30)
                        del_data = del_response.json()
                        
                        if del_data.get('err_code') == 0:
                            deleted_count += 1
                            print(f"         ✅ 删除成功")
                        else:
                            print(f"         ⚠️ 删除失败: {del_data.get('err_message')}")
                    except Exception as e:
                        print(f"         ⚠️ 删除请求失败: {e}")
                
                print(f"   ✅ 已删除 {deleted_count}/{total_servers} 个 server")
            
            # ===== 步骤 3: 将模板状态改为 1（关闭状态） =====
            print(f"   🔒 更新模板状态为关闭...")
            publish_url = f"{base_url}/api/Template/publish_mcp_template/{template_id}/1"
            
            pub_response = requests.put(publish_url, headers=headers, timeout=30)
            pub_data = pub_response.json()
            
            if pub_data.get('err_code') == 0:
                print(f"   ✅ 模板状态已更新为关闭")
                return True
            else:
                print(f"   ⚠️ 更新模板状态失败: {pub_data.get('err_message')}")
                return False
                
        except Exception as e:
            print(f"   ⚠️ 关闭 MCP Server 失败: {e}")
            return False
    
    def step_test_agent(self):
        """Agent测试"""
        print(f"\n{'='*60}")
        print(f"步骤: Agent 测试")
        print(f"{'='*60}")
        
        if not self.template_id:
            print(f"⚠️ 未找到模板ID，跳过 Agent 测试")
            return
        
        # 使用 get_agent_config() 自动生成今日验证码
        agent_config = self.config_mgr.get_agent_config()
        
        if not agent_config.get("phone_number"):
            print(f"⚠️ 未配置 Agent 账号，跳过 Agent 测试")
            return
        
        print(f"🆔 模板ID: {self.template_id}")
        print(f"🤖 开始 Agent 测试...")
        
        try:
            # 复用EMCP管理器（不要重新登录！）
            if not self.emcp_manager or not self.emcp_manager.session_key:
                print(f"⚠️ EMCP未登录，跳过Agent测试")
                return
            
            print(f"ℹ️ 复用EMCP登录")
            
            # 创建Agent测试器（传入已登录的emcp_manager）
            tester = AgentTester(
                emcp_manager=self.emcp_manager,
                ai_generator=None  # 暂不传AI
            )
            
            # 设置Agent平台URL
            # 使用 get_agent_config() 自动生成今日验证码
            agent_config = self.config_mgr.get_agent_config()
            tester.agent_client.base_url = agent_config['base_url']
            
            print(f"🔐 登录 Agent 平台...")
            tester.agent_client.login(agent_config['phone_number'], agent_config['validation_code'])
            
            print(f"✅ 登录成功")
            print(f"🤖 创建测试 Agent...")
            print(f"🔗 绑定 MCP...")
            print(f"💬 开始对话测试...")
            
            # 执行完整测试
            report = tester.test_agent_integration(
                template_id=self.template_id,
                mcp_name=self.package_name,
                mcp_description=f"{self.package_name} MCP Server"
            )
            
            # 保存Agent信息供聊天测试使用
            if report and report.get('success'):
                self.agent_id = report.get('agent_id')
                self.agent_publish_id = report.get('publish_id')
                agent_url = report.get('agent_url', '')
                
                print(f"✅ Agent 创建和发布完成")
                print(f"🆔 Agent ID: {self.agent_id}")
                print(f"📋 发布 ID: {self.agent_publish_id}")
                print(f"🔗 Agent链接: {agent_url}")
                print(f"ℹ️ 可用于后续对话测试")
            else:
                print(f"⚠️ Agent测试未成功，无法进行对话测试")
            
        except Exception as e:
            print(f"⚠️ Agent 测试失败: {str(e)}")
            print(f"ℹ️ 跳过测试，继续执行")
        
        print(f"✅ 步骤完成\n")
    
    def step_test_chat(self):
        """SignalR对话测试"""
        print(f"\n{'='*60}")
        print(f"步骤: SignalR 对话测试")
        print(f"{'='*60}")
        
        if not self.agent_id or not self.template_id:
            print(f"⚠️ 未找到Agent ID或模板ID，跳过对话测试")
            print(f"   Agent ID: {self.agent_id}")
            print(f"   模板ID: {self.template_id}")
            return
        
        # 使用 get_agent_config() 自动生成今日验证码
        agent_config = self.config_mgr.get_agent_config()
        
        if not agent_config.get("phone_number"):
            print(f"⚠️ 未配置 Agent 账号，跳过对话测试")
            return
        
        print(f"🆔 Agent ID: {self.agent_id}")
        print(f"🆔 模板ID: {self.template_id}")
        print(f"💬 开始 SignalR 对话测试...")
        print(f"ℹ️ 这将创建会话并测试所有工具...")
        
        try:
            # 复用已有的EMCP manager
            if not self.emcp_manager or not self.emcp_manager.session_key:
                print(f"⚠️ EMCP未登录，跳过对话测试")
                return
            
            from src.agent_tester import AgentPlatformClient, AgentTesterLogger
            
            # 设置日志
            AgentTesterLogger.set_log_function(print)
            
            print(f"ℹ️ 复用EMCP登录")
            
            # 创建Agent客户端
            # 使用 get_agent_config() 自动生成今日验证码
            agent_config = self.config_mgr.get_agent_config()
            agent_client = AgentPlatformClient()
            agent_client.base_url = agent_config['base_url']
            
            print(f"🔐 登录 Agent 平台...")
            agent_client.login(agent_config['phone_number'], agent_config['validation_code'])
            
            print(f"✅ 登录成功")
            print(f"📋 获取/创建工作区...")
            
            workspace_id = agent_client.create_or_get_workspace("MCP 工厂")
            print(f"   工作区ID: {workspace_id}")
            
            print(f"💬 创建测试会话...")
            conv_name = f"{self.package_name} 自动测试"
            conversation_id = agent_client.create_conversation(
                agent_id=self.agent_id,
                workspace_id=workspace_id,
                conversation_name=conv_name
            )
            print(f"   会话ID: {conversation_id}")
            
            print(f"📋 获取 Agent 技能...")
            plugin_ids = agent_client.get_agent_skills(self.agent_id)
            print(f"   插件ID: {plugin_ids}")
            
            # 创建SignalR测试器
            print(f"🔗 开始 SignalR 对话测试...")
            chat_tester = SignalRChatTester(base_url=agent_config['base_url'])
            chat_tester.set_log_function(print)
            
            # 执行对话测试
            # ⭐ 传递 AI generator（如果配置了的话）
            ai_gen_for_test = getattr(self, 'ai_generator', None)
            if ai_gen_for_test:
                print(f"🤖 使用 AI 生成测试问题")
            else:
                print(f"💡 使用智能降级方案生成测试问题")
            
            report = chat_tester.test_conversation_with_tools(
                agent_token=agent_client.session_key,
                conversation_id=conversation_id,
                agent_id=self.agent_id,
                mcp_name=self.package_name,
                template_id=self.template_id,
                plugin_ids=plugin_ids,
                emcp_base_url=self.emcp_manager.base_url,
                emcp_token=self.emcp_manager.session_key,
                emcp_manager=self.emcp_manager,
                ai_generator=ai_gen_for_test  # ⭐ 传递 AI generator
            )
            
            if report and report.get('success'):
                conversation_id = report.get('conversation_id', '')
                report_file = f"agent_chat_test_{conversation_id[:8]}.html"
                
                print(f"✅ SignalR 对话测试完成")
                print(f"📊 测试报告: {report_file}")
                print(f"📋 会话ID: {conversation_id}")
                
                # 显示测试统计
                total = report.get('total_tools', 0)
                passed = report.get('passed_tools', 0)
                failed = report.get('failed_tools', 0)
                success_rate = (passed / total * 100) if total > 0 else 0
                
                print(f"  总工具数: {total}")
                print(f"  通过: {passed}")
                print(f"  失败: {failed}")
                print(f"  成功率: {success_rate:.1f}%")
                
                if report.get('edgeone_url'):
                    print(f"🌐 公开链接: {report['edgeone_url']}")
            else:
                print(f"⚠️ 对话测试未成功")
            
        except Exception as e:
            import traceback
            print(f"⚠️ 对话测试失败: {str(e)}")
            print(f"详细错误:\n{traceback.format_exc()}")
            print(f"ℹ️ 跳过测试，继续执行")
        
        print(f"✅ 步骤完成\n")
    
    # ===== 克隆和发布工作流程 =====
    
    def workflow_clone_and_publish(
        self,
        github_url: str,
        prefix: str = "bachai",
        output_dir: Optional[Path] = None
    ) -> Dict:
        """
        完整的克隆和发布工作流程
        
        1. 克隆GitHub仓库
        2. 修改包名（添加前缀）
        3. 上传到组织的GitHub
        4. 生成CI/CD流水线
        5. 推送代码（立即触发打包发布）
        6. 等待包发布
        7. 发布到EMCP
        8. 可选：运行测试
        
        Args:
            github_url: 要克隆的GitHub仓库URL
            prefix: 包名前缀，默认为 "bachai"
            output_dir: 输出目录（可选）
            
        Returns:
            Dict: 工作流程执行结果
        """
        print(f"\n{'='*70}")
        print(f"🚀 开始克隆和发布工作流程")
        print(f"{'='*70}")
        print(f"🔗 源仓库: {github_url}")
        print(f"🏷️  包名前缀: {prefix}")
        
        cloner = None
        result = {
            'success': False,
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # ===== 步骤 1: 克隆并修改包名 =====
            self.update_progress(5)
            cloner = RepoCloner(prefix=prefix)
            clone_result = cloner.clone_and_modify(github_url, output_dir, prefix)
            
            if not clone_result['success']:
                raise Exception(f"克隆失败: {clone_result.get('error', '未知错误')}")
            
            result['steps_completed'].append('clone')
            
            # 设置项目信息
            repo_path = clone_result['repo_path']
            new_package_name = clone_result['new_package_name']
            project_type = clone_result['project_type']
            
            self.project_path = repo_path
            self.package_name = new_package_name
            self.package_type = project_type
            self.repo_name = new_package_name  # 使用新包名作为仓库名
            
            # 从项目中检测版本
            from src.project_detector import ProjectDetector
            detector = ProjectDetector(repo_path)
            project_info = detector.detect()
            self.version = project_info.get('version', '1.0.0')
            
            print(f"\n✅ 克隆和修改完成")
            print(f"📁 项目路径: {repo_path}")
            print(f"📦 新包名: {new_package_name}")
            print(f"🔧 项目类型: {project_type}")
            print(f"🏷️  版本: {self.version}")
            
            # ===== 步骤 2: 扫描敏感信息 =====
            self.update_progress(15)
            self.step_scan_project()
            result['steps_completed'].append('scan')
            
            # ===== 步骤 2.5: SonarQube 代码质量扫描 =====
            self.update_progress(20)
            try:
                self.step_sonar_scan(run_scan=False)  # 先只检查状态，不运行完整扫描
                result['steps_completed'].append('sonar_scan')
            except Exception as e:
                print(f"⚠️ SonarQube 扫描失败（继续流程）: {e}")
                result['errors'].append(f"SonarQube: {e}")
            
            # ===== 步骤 3: 创建GitHub仓库 =====
            self.update_progress(25)
            self.step_create_repo()
            result['steps_completed'].append('create_repo')
            result['github_repo_url'] = self.github_repo_url
            
            # ===== 步骤 4: 生成CI/CD Pipeline =====
            self.update_progress(35)
            self.step_generate_pipeline()
            result['steps_completed'].append('generate_pipeline')
            
            # ===== 步骤 5: 配置GitHub Secrets（如果需要） =====
            self.update_progress(40)
            self._configure_github_secrets()
            result['steps_completed'].append('configure_secrets')
            
            # ===== 步骤 6: 推送代码到GitHub =====
            self.update_progress(50)
            self.step_push_code()
            result['steps_completed'].append('push_code')
            
            # ===== 步骤 7: 立即触发发布（创建Tag） =====
            self.update_progress(60)
            print(f"\n{'='*60}")
            print(f"🚀 立即触发发布")
            print(f"{'='*60}")
            print(f"💡 首次推送后立即创建版本标签以触发打包发布")
            
            self.step_trigger_publish()
            result['steps_completed'].append('trigger_publish')
            
            # ===== 步骤 8: 获取包信息 =====
            self.update_progress(70)
            self.step_fetch_package()
            result['steps_completed'].append('fetch_package')
            
            # ===== 步骤 9: AI生成模板 =====
            self.update_progress(75)
            self.step_ai_generate()
            result['steps_completed'].append('ai_generate')
            
            # ===== 步骤 10: 生成Logo（可选） =====
            self.update_progress(80)
            try:
                self.step_generate_logo()
                result['steps_completed'].append('generate_logo')
            except Exception as e:
                print(f"⚠️  Logo生成失败（继续流程）: {e}")
                result['errors'].append(f"Logo生成: {e}")
            
            # ===== 步骤 11: 发布到EMCP =====
            self.update_progress(85)
            self.step_publish_emcp()
            result['steps_completed'].append('publish_emcp')
            result['template_id'] = self.template_id
            
            # ===== 步骤 12: MCP测试（可选） =====
            self.update_progress(90)
            try:
                self.step_test_mcp()
                result['steps_completed'].append('test_mcp')
            except Exception as e:
                print(f"⚠️  MCP测试失败（继续流程）: {e}")
                result['errors'].append(f"MCP测试: {e}")
            
            # ===== 步骤 13: Agent测试（可选） =====
            self.update_progress(95)
            try:
                self.step_test_agent()
                result['steps_completed'].append('test_agent')
            except Exception as e:
                print(f"⚠️  Agent测试失败（继续流程）: {e}")
                result['errors'].append(f"Agent测试: {e}")
            
            # ===== 完成 =====
            self.update_progress(100)
            result['success'] = True
            result['package_name'] = self.package_name
            result['github_repo_url'] = self.github_repo_url
            result['template_id'] = self.template_id
            
            print(f"\n{'='*70}")
            print(f"✅ 克隆和发布工作流程完成！")
            print(f"{'='*70}")
            print(f"📦 包名: {self.package_name}")
            print(f"🔗 GitHub: {self.github_repo_url}")
            if self.template_id:
                print(f"🆔 模板ID: {self.template_id}")
            print(f"✅ 完成步骤: {', '.join(result['steps_completed'])}")
            if result['errors']:
                print(f"⚠️  错误: {len(result['errors'])} 个")
            
            return result
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            result['success'] = False
            result['error'] = error_msg
            result['error_trace'] = error_trace
            result['errors'].append(error_msg)
            
            print(f"\n{'='*70}")
            print(f"❌ 工作流程失败")
            print(f"{'='*70}")
            print(f"错误: {error_msg}")
            print(f"已完成步骤: {', '.join(result['steps_completed'])}")
            print(f"\n详细错误:")
            print(error_trace)
            
            return result
            
        finally:
            # 清理临时目录（如果使用了临时目录）
            if cloner and cloner.temp_dir:
                print(f"\n💡 提示: 临时目录位于 {cloner.temp_dir}")
                print(f"   如果不再需要，可以手动删除或调用 cloner.cleanup()")
    
    def _configure_github_secrets(self):
        """配置GitHub Secrets用于自动发布"""
        print(f"\n{'='*60}")
        print(f"步骤: 配置 GitHub Secrets")
        print(f"{'='*60}")
        
        github_token = self.config.get("github", {}).get("token", "")
        if not github_token:
            print(f"⚠️  未配置GitHub Token，跳过")
            return
        
        github_mgr = GitHubManager(github_token)
        
        secrets_to_set = {}
        
        # 根据项目类型配置不同的 Secrets
        if self.package_type == 'python':
            # PyPI Token
            pypi_token = self.config.get("pypi", {}).get("token", "")
            if pypi_token:
                secrets_to_set['PYPI_TOKEN'] = pypi_token
                print(f"  ✓ 准备设置 PYPI_TOKEN")
            else:
                print(f"  ⚠️  未配置 PyPI Token")
        
        elif self.package_type == 'node.js':
            # NPM Token
            npm_token = self.config.get("npm", {}).get("token", "")
            if npm_token:
                secrets_to_set['NPM_TOKEN'] = npm_token
                print(f"  ✓ 准备设置 NPM_TOKEN")
            else:
                print(f"  ⚠️  未配置 NPM Token")
        
        if not secrets_to_set:
            print(f"ℹ️  没有需要设置的 Secrets")
            return
        
        # 批量设置 Secrets
        try:
            results = github_mgr.set_multiple_secrets(
                self.org_name,
                self.repo_name,
                secrets_to_set
            )
            
            success_count = sum(1 for v in results.values() if v)
            print(f"✅ 设置了 {success_count}/{len(secrets_to_set)} 个 Secrets")
            
            for name, success in results.items():
                status = "✓" if success else "✗"
                print(f"  {status} {name}")
                
        except Exception as e:
            print(f"⚠️  设置 Secrets 失败: {e}")
            print(f"💡 请手动在GitHub仓库设置中添加 Secrets")
        
        print(f"✅ 步骤完成\n")


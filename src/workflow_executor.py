#!/usr/bin/env python3
"""
工作流执行器 - 真实执行所有步骤
"""

from pathlib import Path
from typing import Dict, Any
import sys

from src.github_manager import GitHubManager
from src.git_manager import GitManager
from src.secret_scanner import SecretScanner
from src.pipeline_generator import PipelineGenerator
from src.emcp_manager import EMCPManager
from src.package_fetcher import PackageFetcher
from src.ai_generator import AITemplateGenerator
from src.jimeng_logo_generator import JimengLogoGenerator
from src.mcp_tester import MCPTester
from src.agent_tester import AgentTester
from src.signalr_chat_tester import SignalRChatTester
from src.unified_config_manager import UnifiedConfigManager


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
        
        # 创建生成器（不需要参数）
        generator = PipelineGenerator()
        
        # 根据类型生成
        if project_type == "python":
            print(f"📝 生成 PyPI 发布工作流...")
            generator.generate('pypi', Path(self.project_path))
        elif project_type == "node.js":
            print(f"📝 生成 NPM 发布工作流...")
            generator.generate('npm', Path(self.project_path))
        else:
            print(f"⚠️ 未知项目类型，跳过 Pipeline 生成")
            return
        
        print(f"✅ Pipeline 文件已生成到: .github/workflows/")
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
    
    def _generate_command_by_type(self) -> str:
        """根据项目类型生成启动命令"""
        if self.package_type and self.package_type.lower() == 'node.js':
            return f"npx {self.package_name}"
        else:
            return f"uvx {self.package_name}"
    
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
        # 移除 bachai- 前缀
        name = name.replace('bachai-', '').replace('bachai', '')
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
        
        # 从项目配置文件读取真实的包名，而不是自动添加前缀
        if self.package_type and self.package_type.lower() == 'node.js':
            # Node.js 项目从 package.json 读取包名
            import json
            package_json_path = Path(self.project_path) / 'package.json'
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                        self.package_name = package_data.get('name', self.repo_name)
                except Exception as e:
                    print(f"⚠️ 读取 package.json 失败: {e}")
                    self.package_name = self.repo_name
            else:
                self.package_name = self.repo_name
        else:
            # Python 项目从 setup.py 或 pyproject.toml 读取包名
            # 如果没有特殊前缀，使用仓库名
            self.package_name = self.repo_name
        
        print(f"📦 包名: {self.package_name}")
        print(f"🔧 项目类型: {self.package_type}")
        print(f"✅ 步骤完成\n")
    
    def step_ai_generate(self):
        """AI生成模板"""
        print(f"\n{'='*60}")
        print(f"步骤: AI 生成模板")
        print(f"{'='*60}")
        
        # 检测环境变量配置需求
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
            
            # 找到主窗口
            root = self.parent if hasattr(self, 'parent') else tk._default_root
            
            dialog = EnvVarDialog(root, env_vars, self.package_name)
            configured_vars = dialog.show()
            
            if not configured_vars:
                print(f"❌ 用户取消了环境变量配置")
                raise Exception("必须配置环境变量才能发布到 EMCP")
            
            # 保存配置的环境变量
            self.env_vars_config = configured_vars
            print(f"✅ 用户已配置 {len(configured_vars)} 个环境变量")
        else:
            print(f"   ✅ 未检测到需要配置的环境变量")
            self.env_vars_config = []
        
        ai_config = self.config.get("azure_openai", {})
        
        if not ai_config.get("endpoint") or not ai_config.get("api_key"):
            print(f"\n⚠️ 未配置 Azure OpenAI，使用基础生成器")
            # 使用简单的模板
            self.template_data = {
                "name_zh_cn": self.package_name,
                "name_zh_tw": self.package_name,
                "name_en": self.package_name,
                "description_zh_cn": f"{self.package_name} MCP服务器",
                "description_zh_tw": f"{self.package_name} MCP伺服器",
                "description_en": f"{self.package_name} MCP Server"
            }
            print(f"✅ 使用基础模板")
            print(f"✅ 步骤完成\n")
            return
        
        print(f"🤖 Azure OpenAI Endpoint: {ai_config['endpoint']}")
        print(f"🤖 Deployment: {ai_config['deployment_name']}")
        print(f"🤖 正在调用 AI 生成描述...")
        
        try:
            # 初始化并登录EMCP（用于Logo上传认证）
            emcp_config = self.config.get("emcp", {})
            if not self.emcp_manager:
                self.emcp_manager = EMCPManager()
                self.emcp_manager.base_url = emcp_config.get('base_url', 'https://sit-emcp.kaleido.guru')
            
            # 确保已登录（为了上传Logo）
            if emcp_config.get("phone_number") and not self.emcp_manager.session_key:
                print(f"🔐 登录 EMCP（为Logo上传准备）...")
                try:
                    user_info = self.emcp_manager.login(
                        emcp_config['phone_number'],
                        emcp_config['validation_code']
                    )
                    print(f"✅ EMCP 登录成功")
                except Exception as e:
                    print(f"⚠️ EMCP 登录失败: {e}")
                    print(f"   Logo 将使用默认图片")
            
            ai_gen = AITemplateGenerator(
                azure_endpoint=ai_config['endpoint'],
                api_key=ai_config['api_key'],
                api_version=ai_config.get('api_version', '2024-02-15-preview'),
                deployment_name=ai_config['deployment_name'],
                emcp_manager=self.emcp_manager  # 使用已登录的实例
            )
            
            # 从本地项目读取完整信息
            from src.project_detector import ProjectDetector
            detector = ProjectDetector(self.project_path)
            project_info = detector.detect()
            
            # 构建包信息（包含完整 README）
            package_info = {
                "package_name": self.package_name,
                "type": self.package_type,
                "info": {
                    "name": project_info.get('name', self.package_name),
                    "version": project_info.get('version', '1.0.0'),
                    "summary": project_info.get('description', f"{self.package_name} MCP Server"),
                    "description": project_info.get('readme', ''),  # ✅ 完整 README
                    "readme": project_info.get('readme', ''),  # ✅ 完整 README
                    "author": "BACH Studio"
                }
            }
            
            print(f"📝 读取到的 README: {len(project_info.get('readme', ''))} 字符")
            print(f"📝 生成中文描述...")
            print(f"📝 生成繁体描述...")
            print(f"📝 生成英文描述...")
            
            result = ai_gen.generate_template_info(package_info, self.package_type)
            self.template_data = result
            
            print(f"✅ AI 生成完成")
            print(f"  中文: {result.get('name_zh_cn', '')}")
            print(f"  繁体: {result.get('name_zh_tw', '')}")
            print(f"  英文: {result.get('name_en', '')}")
            
        except Exception as e:
            print(f"⚠️ AI 生成失败: {str(e)}")
            print(f"⚠️ 使用基础模板")
            self.template_data = {
                "name_zh_cn": self.package_name,
                "name_zh_tw": self.package_name,
                "name_en": self.package_name
            }
        
        print(f"✅ 步骤完成\n")
    
    def step_generate_logo(self):
        """生成Logo"""
        print(f"\n{'='*60}")
        print(f"步骤: 生成 Logo")
        print(f"{'='*60}")
        
        jimeng_config = self.config.get("jimeng", {})
        
        if not jimeng_config.get("enabled", True):
            print(f"⚠️ 即梦 AI 未启用，跳过 Logo 生成")
            return
        
        mcp_url = jimeng_config.get("mcp_url", "sse+https://jm-mcp.kaleido.guru/sse")
        print(f"🎨 即梦 MCP URL: {mcp_url}")
        
        # TODO: 集成真实的Logo生成
        print(f"ℹ️ Logo 生成功能待集成")
        print(f"ℹ️ 可配置 Azure OpenAI 后启用AI Logo生成")
        print(f"✅ 步骤完成\n")
    
    def step_publish_emcp(self):
        """发布到EMCP"""
        print(f"\n{'='*60}")
        print(f"步骤: 发布到 EMCP")
        print(f"{'='*60}")
        
        emcp_config = self.config.get("emcp", {})
        
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
                
                user_info = emcp_mgr.login(phone, code)
                
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
                    "description_zh_cn": f"{self.package_name} MCP服务器",
                    "description_zh_tw": f"{self.package_name} MCP伺服器",
                    "description_en": f"{self.package_name} MCP Server"
                }
            
            print(f"\n📝 获取EMCP平台配置...")
            
            # 获取默认的Logo URL
            default_logo = "https://emcp.kaleido.guru/logo/default-mcp-logo.png"
            print(f"🖼️ 使用默认Logo: {default_logo}")
            
            # 获取模板分类ID
            print(f"📋 获取模板分类...")
            try:
                categories = emcp_mgr.get_all_template_categories()
                if categories and len(categories) > 0:
                    first_category = categories[0]
                    # 尝试不同的字段名
                    template_category_id = first_category.get('templateCategoryId')
                    if not template_category_id:
                        template_category_id = first_category.get('template_category_id')
                    if not template_category_id:
                        template_category_id = first_category.get('id')
                    if not template_category_id:
                        template_category_id = "1"
                    
                    category_name = first_category.get('name', '未知')
                    print(f"✓ 使用分类: {category_name} (ID: {template_category_id})")
                    print(f"  完整分类数据: {first_category}")
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
                    # 使用正确的API格式
                    arg_item = {
                        "arg_name": env_var['name'],  # ✅ 使用 arg_name
                        "default_value": env_var.get('example', ''),  # ✅ 使用 default_value
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
                    print(f"     • {env_var['name']}: {env_var['description']}")
            else:
                print(f"   ℹ️ 无需环境变量配置")
            
            # 使用build_template_data构建完整数据
            full_template_data = emcp_mgr.build_template_data(
                name=self.template_data.get("name_zh_cn", self.package_name),
                summary=self.template_data.get("description_zh_cn", f"{self.package_name} MCP服务器"),
                description=self.template_data.get("description_zh_cn", f"{self.package_name} MCP服务器"),
                logo_url=default_logo,  # 使用默认Logo
                template_category_id=template_category_id,  # 使用获取的分类ID
                template_source_id=self.package_name,  # 使用包名作为来源ID
                command=self._generate_command_by_type(),  # 根据类型生成命令
                route_prefix=self._generate_route_prefix(),  # 生成合法的路由前缀
                package_type=self._get_package_type_code(),  # 根据类型获取代码
                args=args_list,  # ✅ 添加环境变量配置
                name_en=self.template_data.get("name_en", self.package_name),
                summary_en=self.template_data.get("description_en", f"{self.package_name} MCP Server"),
                description_en=self.template_data.get("description_en", f"{self.package_name} MCP Server"),
                name_tw=self.template_data.get("name_zh_tw", self.package_name),
                summary_tw=self.template_data.get("description_zh_tw", f"{self.package_name} MCP伺服器"),
                description_tw=self.template_data.get("description_zh_tw", f"{self.package_name} MCP伺服器")
            )
            
            print(f"📦 包名: {self.package_name}")
            print(f"🔧 命令: uvx {self.package_name}")
            print(f"🛤️ 路由: {self.package_name[:10]}")
            
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
        print(f"🧪 开始测试 MCP 工具...")
        
        try:
            # 复用EMCP管理器
            if not self.emcp_manager or not self.emcp_manager.session_key:
                print(f"⚠️ EMCP未登录，跳过MCP测试")
                return
            
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
    
    def step_test_agent(self):
        """Agent测试"""
        print(f"\n{'='*60}")
        print(f"步骤: Agent 测试")
        print(f"{'='*60}")
        
        if not self.template_id:
            print(f"⚠️ 未找到模板ID，跳过 Agent 测试")
            return
        
        agent_config = self.config.get("agent", {})
        
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
        
        agent_config = self.config.get("agent", {})
        
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
                ai_generator=None
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


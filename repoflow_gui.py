#!/usr/bin/env python3
"""
RepoFlow GUI - 极简可视化界面
用于快速发布项目到 GitHub
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import sys
import os

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import locale
    # PyInstaller 打包后 stdout/stderr 可能是 None
    if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from src.github_manager import GitHubManager
from src.secret_scanner import SecretScanner
from src.pipeline_generator import PipelineGenerator
from src.git_manager import GitManager
from src.config_manager import ConfigManager
from src.project_detector import ProjectDetector


class LogHandler:
    """日志处理器，将日志输出到GUI"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
    
    def write(self, message):
        """写入日志"""
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.update()
    
    def flush(self):
        """刷新"""
        pass


class RepoFlowGUI:
    """RepoFlow GUI 主应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("RepoFlow - 项目发布工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 配置样式
        self.setup_styles()
        
        # 变量
        self.project_path = tk.StringVar()
        self.repo_name = tk.StringVar()
        self.org_name = tk.StringVar(value="BACH-AI-Tools")
        self.private_var = tk.BooleanVar(value=False)
        self.pipeline_type = tk.StringVar()
        self.github_token = tk.StringVar()
        self.auto_publish_var = tk.BooleanVar(value=True)  # 默认勾选
        self.version_number = tk.StringVar(value="1.0.0")
        
        # 发布状态标志
        self.is_publishing = False
        
        # 加载配置
        self.load_config()
        
        # 创建UI
        self.create_widgets()
        
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色
        style.configure('Title.TLabel', font=('微软雅黑', 14, 'bold'), foreground='#2196F3')
        style.configure('Info.TLabel', font=('微软雅黑', 10))
        style.configure('Success.TLabel', font=('微软雅黑', 10), foreground='#4CAF50')
        style.configure('Warning.TLabel', font=('微软雅黑', 10), foreground='#FF9800')
        style.configure('Error.TLabel', font=('微软雅黑', 10), foreground='#F44336')
        style.configure('Big.TButton', font=('微软雅黑', 11, 'bold'), padding=10)
        
    def load_config(self):
        """加载配置"""
        config_mgr = ConfigManager()
        config = config_mgr.load_config()
        
        if config.get('github_token'):
            self.github_token.set(config['github_token'])
        # 设置组织名称，优先使用配置文件，否则使用默认值
        org = config.get('default_org', 'BACH-AI-Tools')
        self.org_name.set(org)
    
    def create_widgets(self):
        """创建UI组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        current_row = 0
        
        # 标题
        title = ttk.Label(main_frame, text="🚀 RepoFlow - 项目发布工具", style='Title.TLabel')
        title.grid(row=current_row, column=0, columnspan=3, pady=(0, 20))
        current_row += 1
        
        # GitHub Token 配置区域（简洁版）
        token_frame = ttk.LabelFrame(main_frame, text="⚙️ GitHub Token", padding="10")
        token_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        current_row += 1
        
        if not self.github_token.get():
            # 未配置 - 显示配置向导
            ttk.Label(token_frame, text="需要 GitHub Token 才能发布项目", style='Info.TLabel').pack(anchor=tk.W, pady=(0, 5))
            
            # Token 输入框和按钮
            input_frame = ttk.Frame(token_frame)
            input_frame.pack(fill=tk.X, pady=5)
            
            ttk.Entry(input_frame, textvariable=self.github_token, width=50, show='*').pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
            ttk.Button(input_frame, text="💾 保存", command=self.save_token).pack(side=tk.LEFT)
            
            # 快捷按钮
            button_frame = ttk.Frame(token_frame)
            button_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Button(button_frame, text="🔗 获取新 Token", command=self.open_token_page).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Label(button_frame, text="← 点击生成新 Token，然后粘贴到上方", style='Info.TLabel').pack(side=tk.LEFT)
        else:
            # 已配置 - 显示状态和重新配置按钮
            status_frame = ttk.Frame(token_frame)
            status_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(status_frame, text="✅ Token 已配置", style='Success.TLabel').pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(status_frame, text="🔄 重新配置", command=self.reconfigure_token).pack(side=tk.LEFT)
            ttk.Button(status_frame, text="🔗 生成新 Token", command=self.open_token_page).pack(side=tk.LEFT, padx=(5, 0))
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        current_row += 1
        
        # 1. 选择项目文件夹
        ttk.Label(main_frame, text="📁 项目文件夹:", style='Info.TLabel').grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.project_path, width=50).grid(
            row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_folder).grid(
            row=current_row, column=2, padx=5, pady=5)
        current_row += 1
        
        # 项目信息显示区域
        self.project_info_label = ttk.Label(main_frame, text="", style='Info.TLabel')
        self.project_info_label.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=5)
        current_row += 1
        
        # 2. 仓库名称
        ttk.Label(main_frame, text="📦 仓库名称:", style='Info.TLabel').grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.repo_name, width=50).grid(
            row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
        current_row += 1
        
        # 3. 组织名称
        ttk.Label(main_frame, text="🏢 组织名称:", style='Info.TLabel').grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        org_entry = ttk.Entry(main_frame, textvariable=self.org_name, width=50)
        org_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
        current_row += 1
        
        # 组织提示
        org_hint = ttk.Label(
            main_frame, 
            text="💡 仓库将创建在此组织下（不是个人账户）",
            style='Warning.TLabel'
        )
        org_hint.grid(row=current_row, column=1, sticky=tk.W, pady=(0, 5))
        current_row += 1
        
        # 4. Pipeline 类型（自动检测）
        ttk.Label(main_frame, text="🔧 Pipeline 类型:", style='Info.TLabel').grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        pipeline_frame = ttk.Frame(main_frame)
        pipeline_frame.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
        self.pipeline_combo = ttk.Combobox(
            pipeline_frame, 
            textvariable=self.pipeline_type,
            values=['自动检测', 'docker', 'pypi', 'npm'],
            state='readonly',
            width=20
        )
        self.pipeline_combo.set('自动检测')
        self.pipeline_combo.pack(side=tk.LEFT)
        current_row += 1
        
        # 5. 私有/公开
        ttk.Checkbutton(
            main_frame, 
            text="创建为私有仓库", 
            variable=self.private_var
        ).grid(row=current_row, column=1, sticky=tk.W, pady=5)
        current_row += 1
        
        # 6. 立即发布到 PyPI/NPM（仅当是 pypi 或 npm 项目时）
        self.publish_frame = ttk.LabelFrame(main_frame, text="📦 发布设置（PyPI/NPM）", padding="10")
        self.publish_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        current_row += 1
        
        # 自动发布复选框
        publish_check_frame = ttk.Frame(self.publish_frame)
        publish_check_frame.pack(fill=tk.X, pady=5)
        
        self.auto_publish_check = ttk.Checkbutton(
            publish_check_frame, 
            text="✅ 推送后立即发布到 PyPI/NPM（自动创建 Tag）", 
            variable=self.auto_publish_var,
            command=self.toggle_version_input
        )
        self.auto_publish_check.pack(side=tk.LEFT)
        
        # 版本号输入
        self.version_frame = ttk.Frame(self.publish_frame)
        self.version_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.version_frame, text="📌 版本号:", style='Info.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.version_entry = ttk.Entry(self.version_frame, textvariable=self.version_number, width=15)
        self.version_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(self.version_frame, text="(格式: x.y.z，如 1.0.0)", style='Info.TLabel').pack(side=tk.LEFT)
        
        # 初始状态：默认启用（因为默认勾选了）
        self.version_entry.config(state='normal')
        
        # 提示信息
        hint_label = ttk.Label(
            self.publish_frame,
            text="💡 勾选后，推送代码时会自动创建 v{version} Tag，触发 GitHub Actions 发布",
            style='Info.TLabel',
            wraplength=700
        )
        hint_label.pack(fill=tk.X, pady=(5, 0))
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        current_row += 1
        
        # 发布按钮
        self.publish_button = ttk.Button(
            main_frame, 
            text="🚀 一键发布到 GitHub", 
            command=self.publish_project,
            style='Big.TButton'
        )
        self.publish_button.grid(row=current_row, column=0, columnspan=3, pady=10)
        current_row += 1
        
        # 日志区域
        log_label = ttk.Label(main_frame, text="📋 日志输出:", style='Info.TLabel')
        log_label.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        current_row += 1
        
        # 日志文本框
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(current_row, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=15, 
            width=80,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 清空日志按钮
        current_row += 1
        ttk.Button(main_frame, text="清空日志", command=self.clear_log).grid(
            row=current_row, column=0, columnspan=3, pady=5)
    
    def open_token_page(self):
        """打开 GitHub Token 生成页面"""
        import webbrowser
        url = "https://github.com/settings/tokens/new?description=RepoFlow&scopes=repo,workflow,write:packages"
        webbrowser.open(url)
        
        self.log("\n🌐 浏览器已打开 GitHub Token 生成页面\n")
        self.log("\n📝 操作步骤：\n")
        self.log("1. 权限已自动勾选\n")
        self.log("2. 点击页面底部的 'Generate token'\n")
        self.log("3. 复制生成的 token\n")
        self.log("4. 粘贴到上方输入框\n")
        self.log("5. 点击保存\n")
    
    def handle_auth_error(self, error_message):
        """处理认证错误"""
        self.log("\n" + "=" * 60 + "\n")
        self.log("⚠️  GitHub Token 错误\n")
        self.log("=" * 60 + "\n")
        self.log(f"可能是 Token 无效或权限不足\n\n")
        self.log("💡 解决方法：\n")
        self.log("1. 点击上方的 [🔄 重新配置] 按钮\n")
        self.log("2. 或点击 [🔗 生成新 Token] 按钮\n")
        self.log("3. 生成新 Token 后重启 GUI\n")
        self.log("4. 粘贴新 Token 并保存\n")
    
    def reconfigure_token(self):
        """重新配置 Token"""
        # 打开 Token 生成页面
        self.open_token_page()
        
        # 清除配置
        config_mgr = ConfigManager()
        config_mgr.save_config({
            "github_token": "",
            "default_org": self.org_name.get()
        })
        
        self.log("\n✅ Token 已清除！\n")
        self.log("📝 请在打开的网页中生成新 Token\n")
        self.log("🔄 然后重启 GUI 重新配置\n")
        
        # 自动退出
        self.root.after(2000, self.root.quit)  # 2秒后自动退出
    
    def save_token(self):
        """保存 GitHub Token"""
        token = self.github_token.get().strip()
        if not token:
            self.log("❌ 请输入 GitHub Token\n")
            return
        
        config_mgr = ConfigManager()
        config_mgr.save_config({
            "github_token": token,
            "default_org": self.org_name.get()
        })
        
        self.log("\n✅ GitHub Token 已保存！\n")
        self.log("🔄 正在重启 GUI...\n")
        
        # 2秒后自动重启
        self.root.after(2000, self.root.quit)
    
    def browse_folder(self):
        """浏览并选择文件夹"""
        folder = filedialog.askdirectory(title="选择项目文件夹")
        if folder:
            self.project_path.set(folder)
            # 自动更新仓库名称为文件夹名
            project_name = Path(folder).name
            self.repo_name.set(project_name)
            self.log(f"\n📁 已选择项目: {folder}\n")
            self.log(f"📦 自动设置仓库名称: {project_name}\n\n")
            self.analyze_project(folder)
    
    def analyze_project(self, folder_path):
        """分析项目并显示信息"""
        try:
            project_path = Path(folder_path)
            
            # 检测项目类型
            detector = ProjectDetector(project_path)
            info = detector.get_project_info()
            
            # 自动读取版本号
            version = self.detect_version(project_path, info['detected_types'])
            if version:
                self.version_number.set(version)
                self.log(f"📌 检测到版本号: {version}\n")
            
            # 检查 README.md
            has_readme = (project_path / "README.md").exists() or (project_path / "readme.md").exists()
            
            # 构建信息文本
            info_text = ""
            
            if has_readme:
                info_text += "✅ 发现 README.md\n"
            else:
                info_text += "💡 建议添加 README.md\n"
            
            if info['detected_types']:
                type_names = {
                    'python': 'Python',
                    'nodejs': 'Node.js',
                    'docker': 'Docker',
                    'dotnet': '.NET/C#',
                    'java': 'Java',
                    'go': 'Go',
                    'rust': 'Rust'
                }
                types_str = ', '.join([type_names.get(t, t) for t in info['detected_types']])
                info_text += f"🔎 检测到: {types_str}\n"
            else:
                info_text += "⚠️ 未检测到已知项目类型\n"
            
            if info['recommended_pipelines']:
                pipeline_names = {
                    'pypi': 'PyPI (Python包)',
                    'npm': 'NPM (Node.js包)',
                    'docker': 'Docker (容器镜像)'
                }
                pipelines_str = ', '.join([pipeline_names.get(p, p) for p in info['recommended_pipelines']])
                info_text += f"📦 推荐 Pipeline: {pipelines_str}"
                
                # 自动设置第一个推荐的 pipeline
                self.pipeline_combo.set(info['recommended_pipelines'][0])
            else:
                info_text += "💡 建议手动选择 Pipeline"
            
            self.project_info_label.config(text=info_text)
            
        except Exception as e:
            self.log(f"❌ 分析项目时出错: {str(e)}\n")
    
    def log(self, message):
        """写入日志"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def toggle_version_input(self):
        """切换版本号输入框的启用/禁用状态"""
        if self.auto_publish_var.get():
            self.version_entry.config(state='normal')
        else:
            self.version_entry.config(state='disabled')
    
    def validate_version_format(self, version: str) -> bool:
        """验证版本号格式 (x.y.z)"""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return re.match(pattern, version) is not None
    
    def detect_version(self, project_path: Path, detected_types: list) -> str:
        """从项目文件中检测版本号"""
        import re
        
        # Python 项目
        if 'python' in detected_types:
            # 尝试从 setup.py 读取
            setup_py = project_path / 'setup.py'
            if setup_py.exists():
                try:
                    content = setup_py.read_text(encoding='utf-8')
                    match = re.search(r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', content)
                    if match:
                        return match.group(1)
                except:
                    pass
            
            # 尝试从 pyproject.toml 读取
            pyproject = project_path / 'pyproject.toml'
            if pyproject.exists():
                try:
                    content = pyproject.read_text(encoding='utf-8')
                    match = re.search(r'version\s*=\s*["\']v?(\d+\.\d+\.\d+)["\']', content)
                    if match:
                        return match.group(1)
                except:
                    pass
        
        # Node.js 项目
        if 'nodejs' in detected_types:
            package_json = project_path / 'package.json'
            if package_json.exists():
                try:
                    import json
                    data = json.loads(package_json.read_text(encoding='utf-8'))
                    version = data.get('version', '')
                    if re.match(r'^\d+\.\d+\.\d+$', version):
                        return version
                except:
                    pass
        
        # 默认版本
        return "1.0.0"
    
    def publish_project(self):
        """发布项目到 GitHub"""
        # 检查是否正在发布
        if self.is_publishing:
            self.log("⚠️  正在发布中，请等待当前任务完成...\n")
            return
        
        # 验证输入
        if not self.project_path.get():
            self.log("❌ 请选择项目文件夹\n")
            return
        
        if not self.repo_name.get():
            self.log("❌ 请输入仓库名称\n")
            return
        
        if not self.github_token.get():
            self.log("❌ 请配置 GitHub Token\n")
            return
        
        # 如果勾选了自动发布，验证版本号格式
        if self.auto_publish_var.get():
            version = self.version_number.get().strip()
            if not version:
                self.log("❌ 请输入版本号\n")
                return
            if not self.validate_version_format(version):
                self.log("❌ 版本号格式不正确，应该是 x.y.z 格式（如 1.0.0）\n")
                return
        
        # 设置发布状态
        self.is_publishing = True
        
        # 禁用按钮
        self.publish_button.config(state='disabled', text='🔄 发布中...')
        self.clear_log()
        
        # 记录当前要发布的路径
        current_path = self.project_path.get()
        current_repo = self.repo_name.get()
        self.log(f"📂 准备发布: {current_path}\n")
        self.log(f"📦 仓库名称: {current_repo}\n")
        self.log("=" * 60 + "\n\n")
        
        # 在新线程中执行发布
        thread = threading.Thread(target=self._do_publish)
        thread.daemon = True
        thread.start()
    
    def _do_publish(self):
        """执行发布流程"""
        try:
            project_path = Path(self.project_path.get())
            repo_name = self.repo_name.get()
            org_name = self.org_name.get()
            private = self.private_var.get()
            
            self.log("=" * 60 + "\n")
            self.log("🚀 RepoFlow 自动化发布流程\n")
            self.log("=" * 60 + "\n\n")
            
            # 步骤 1: 检查 README 和扫描密钥
            self.log("📋 步骤 1/5: 检查项目文件...\n")
            has_readme = (project_path / "README.md").exists() or (project_path / "readme.md").exists()
            if not has_readme:
                self.log("  ❌ 未发现 README.md\n")
                self.log("\n" + "=" * 60 + "\n")
                self.log("⚠️  发布失败：必须包含 README.md 文件\n")
                self.log("=" * 60 + "\n")
                self.log("\n💡 请在项目根目录创建 README.md 文件\n")
                self.log("示例内容：\n")
                self.log("```\n")
                self.log("# 项目名称\n\n")
                self.log("项目简介\n\n")
                self.log("## 安装\n\n")
                self.log("## 使用\n")
                self.log("```\n")
                return
            
            self.log("  ✅ 发现 README.md\n")
            
            # 扫描敏感信息
            self.log("\n🔍 扫描敏感信息...\n")
            scanner = SecretScanner()
            issues = scanner.scan_directory(project_path)
            
            if issues:
                self.log(f"  ⚠️  发现 {len(issues)} 个潜在敏感信息:\n")
                for issue in issues[:5]:  # 只显示前5个
                    self.log(f"    • {issue['file']}:{issue['line']} - {issue['type']}\n")
                if len(issues) > 5:
                    self.log(f"    ... 还有 {len(issues) - 5} 个\n")
                
                self.log("\n" + "=" * 60 + "\n")
                self.log("⚠️  发布失败：检测到敏感信息\n")
                self.log("=" * 60 + "\n")
                self.log("\n💡 请检查并删除敏感信息，例如：\n")
                self.log("- API Keys\n")
                self.log("- Passwords\n")
                self.log("- Private Keys\n")
                self.log("- Access Tokens\n")
                return
            
            self.log("  ✅ 未发现敏感信息\n")
            
            # 检测项目类型
            detector = ProjectDetector(project_path)
            info = detector.get_project_info()
            
            # 确定 pipeline 类型
            pipeline_selection = self.pipeline_type.get()
            if pipeline_selection == '自动检测':
                if info['recommended_pipelines']:
                    pipeline = info['recommended_pipelines'][0]
                    self.log(f"  🔎 自动检测到推荐 Pipeline: {pipeline}\n")
                else:
                    pipeline = 'docker'  # 默认使用 docker
                    self.log(f"  💡 使用默认 Pipeline: {pipeline}\n")
            else:
                pipeline = pipeline_selection
                self.log(f"  🔧 使用指定 Pipeline: {pipeline}\n")
            
            # 验证 Pipeline（只警告，不阻止）
            validation = detector.validate_pipeline(pipeline)
            if validation.get('warning'):
                self.log(f"  ⚠️  {validation['warning']}\n")
            if not validation.get('valid', True):
                self.log(f"  ⚠️  {validation.get('message', '')}\n")
                self.log("  💡 继续发布，但 Pipeline 可能无法正常工作\n")
            
            self.log("\n")
            
            # 步骤 2: 创建 GitHub 仓库
            self.log("\n📦 步骤 2/5: 创建 GitHub 仓库...\n")
            self.log(f"  组织: {org_name}\n")
            self.log(f"  仓库: {repo_name}\n")
            github_mgr = GitHubManager(self.github_token.get())
            
            repo_url, is_new = github_mgr.create_repository(org_name, repo_name, private=private)
            if is_new:
                self.log(f"  ✅ 仓库已创建: {repo_url}\n")
            else:
                self.log(f"  ⚠️  仓库已存在，将更新代码: {repo_url}\n")
            
            self.log("\n")
            
            # 步骤 3: 生成 CI/CD Pipeline
            self.log("\n🔧 步骤 3/5: 生成 CI/CD Pipeline...\n")
            pipeline_gen = PipelineGenerator()
            pipeline_gen.generate(pipeline, project_path)
            self.log(f"  ✅ {pipeline.upper()} Pipeline 配置已生成\n")
            
            # 步骤 4: 推送代码到 GitHub
            self.log("\n📤 步骤 4/5: 推送代码到 GitHub...\n")
            # 使用 GitHub Token 进行认证，避免弹出认证窗口
            git_mgr = GitManager(project_path, github_token=self.github_token.get())
            git_mgr.init_and_push(repo_url)
            self.log("  ✅ 代码已推送\n")
            
            # 步骤 4.5: 如果勾选了自动发布，创建并推送 Tag
            auto_publish = self.auto_publish_var.get()
            tag_created = False
            tag_name = None
            
            if auto_publish and pipeline in ['pypi', 'npm']:
                version = self.version_number.get().strip()
                
                # 验证版本号格式
                if self.validate_version_format(version):
                    tag_name = f"v{version}"
                    
                    # 检查 tag 是否已存在
                    if not git_mgr.tag_exists(tag_name):
                        self.log(f"\n🏷️  创建并推送 Tag: {tag_name}...\n")
                        try:
                            # 创建并推送 tag
                            git_mgr.create_and_push_tag(tag_name, f"Release {tag_name} by RepoFlow")
                            self.log(f"  ✅ Tag 已创建并推送: {tag_name}\n")
                            self.log(f"  🚀 GitHub Actions 将自动触发发布到 {pipeline.upper()}\n")
                            tag_created = True
                            
                            # 在 GUI 上显示 tag
                            self.log("\n" + "=" * 60 + "\n")
                            self.log("📦 发布信息\n")
                            self.log("=" * 60 + "\n")
                            self.log(f"  版本: {version}\n")
                            self.log(f"  Tag: {tag_name}\n")
                            self.log(f"  目标: {pipeline.upper()}\n")
                            self.log("=" * 60 + "\n\n")
                        except Exception as tag_error:
                            self.log(f"  ⚠️  创建 Tag 失败: {str(tag_error)}\n")
                            self.log("  💡 你可以稍后手动创建 Tag 来触发发布\n")
                    else:
                        self.log(f"\n⚠️  Tag '{tag_name}' 已存在，跳过创建\n")
                        self.log(f"💡 请修改版本号或手动删除已有 Tag\n")
                else:
                    self.log("\n⚠️  版本号格式不正确，应该是 x.y.z 格式（如 1.0.0）\n")
                    self.log("  跳过自动发布，请手动创建 Tag\n")
            
            # 步骤 5: 提示配置密钥
            self.log("\n💡 步骤 5/5: 检查组织密钥配置...\n")
            self.log(f"  请确保在组织中已配置 {pipeline.upper()} 相关的 Secrets\n")
            self.log(f"  访问：https://github.com/organizations/{org_name}/settings/secrets/actions\n")
            
            if pipeline == 'docker':
                self.log("  需要的 Secrets:\n")
                self.log("    • DOCKERHUB_USERNAME\n")
                self.log("    • DOCKERHUB_TOKEN\n")
            elif pipeline == 'pypi':
                self.log("  需要的 Secrets:\n")
                self.log("    • PYPI_TOKEN\n")
            elif pipeline == 'npm':
                self.log("  需要的 Secrets:\n")
                self.log("    • NPM_TOKEN\n")
            
            self.log("\n")
            self.log("=" * 60 + "\n")
            self.log("🎉 发布完成！\n")
            self.log("=" * 60 + "\n")
            self.log(f"📍 仓库地址: https://github.com/{org_name}/{repo_name}\n")
            self.log(f"🔗 Actions: https://github.com/{org_name}/{repo_name}/actions\n")
            
            # 根据是否创建了 tag 显示不同的提示
            if tag_created and tag_name:
                self.log(f"\n💡 GitHub Actions 正在构建和发布到 {pipeline.upper()}\n")
                self.log(f"📊 查看进度: https://github.com/{org_name}/{repo_name}/actions\n")
                
                # 获取包名（可能包含前缀）
                package_name = repo_name
                if pipeline == 'pypi':
                    package_name = f"bachai-{repo_name.lower()}"
                    self.log(f"\n📦 发布后可通过以下命令安装:\n")
                    self.log(f"   pip install {package_name}\n")
                elif pipeline == 'npm':
                    package_name = f"@bachai/{repo_name.lower()}"
                    self.log(f"\n📦 发布后可通过以下命令安装:\n")
                    self.log(f"   npm install {package_name}\n")
            else:
                self.log("\n💡 提示: GitHub Actions 将在推送时自动构建\n")
                if pipeline in ['pypi', 'npm']:
                    self.log(f"📦 要发布到 {pipeline.upper()}，请创建 v* Tag 或勾选'立即发布'选项\n")
            
            # 不显示弹窗，日志中已经有完整信息
            
        except Exception as e:
            error_msg = f"❌ 错误: {str(e)}\n"
            self.log("\n" + error_msg)
            error_message = str(e)
            
            # 检查是否是认证错误
            if any(keyword in str(e).lower() for keyword in ['401', '403', 'authentication', 'unauthorized', 'token', 'credential']):
                # Token 认证错误，提供快速解决方案
                self.root.after(0, lambda: self.handle_auth_error(error_message))
        
        finally:
            # 重置发布状态
            self.is_publishing = False
            # 重新启用按钮
            self.root.after(0, lambda: self.publish_button.config(state='normal', text='🚀 一键发布到 GitHub'))


def main():
    """主函数"""
    root = tk.Tk()
    app = RepoFlowGUI(root)
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    root.mainloop()


if __name__ == '__main__':
    main()


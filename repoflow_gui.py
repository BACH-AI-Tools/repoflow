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
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
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
            self.analyze_project(folder)
    
    def analyze_project(self, folder_path):
        """分析项目并显示信息"""
        try:
            project_path = Path(folder_path)
            
            # 检测项目类型
            detector = ProjectDetector(project_path)
            info = detector.get_project_info()
            
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
            
            # 自动填充仓库名称
            if not self.repo_name.get():
                self.repo_name.set(project_path.name)
            
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
    
    def publish_project(self):
        """发布项目到 GitHub"""
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
        
        # 禁用按钮
        self.publish_button.config(state='disabled')
        self.clear_log()
        
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
            git_mgr = GitManager(project_path)
            git_mgr.init_and_push(repo_url)
            self.log("  ✅ 代码已推送\n")
            
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
            self.log("\n💡 提示: GitHub Actions workflow 将自动构建和发布\n")
            
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
            # 重新启用按钮
            self.root.after(0, lambda: self.publish_button.config(state='normal'))


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


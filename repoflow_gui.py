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
        if config.get('default_org'):
            self.org_name.set(config['default_org'])
    
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
        
        # GitHub Token (如果未配置)
        if not self.github_token.get():
            ttk.Label(main_frame, text="GitHub Token:", style='Info.TLabel').grid(
                row=current_row, column=0, sticky=tk.W, pady=5)
            token_entry = ttk.Entry(main_frame, textvariable=self.github_token, width=40, show='*')
            token_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
            ttk.Button(main_frame, text="保存", command=self.save_token).grid(
                row=current_row, column=2, padx=5, pady=5)
            current_row += 1
            
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
        ttk.Entry(main_frame, textvariable=self.org_name, width=50).grid(
            row=current_row, column=1, sticky=(tk.W, tk.E), pady=5)
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
    
    def save_token(self):
        """保存 GitHub Token"""
        token = self.github_token.get().strip()
        if not token:
            messagebox.showerror("错误", "请输入 GitHub Token")
            return
        
        config_mgr = ConfigManager()
        config_mgr.save_config({
            "github_token": token,
            "default_org": self.org_name.get()
        })
        
        messagebox.showinfo("成功", "GitHub Token 已保存！")
        self.log("✅ GitHub Token 已保存\n")
    
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
                info_text += "⚠️ 未发现 README.md (建议添加)\n"
            
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
            messagebox.showerror("错误", "请选择项目文件夹")
            return
        
        if not self.repo_name.get():
            messagebox.showerror("错误", "请输入仓库名称")
            return
        
        if not self.github_token.get():
            messagebox.showerror("错误", "请配置 GitHub Token")
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
            
            # 步骤 1: 检查 README
            self.log("📋 步骤 1/4: 检查项目文件...\n")
            has_readme = (project_path / "README.md").exists() or (project_path / "readme.md").exists()
            if has_readme:
                self.log("  ✅ 发现 README.md\n")
            else:
                self.log("  ⚠️  未发现 README.md，建议添加项目说明文档\n")
            
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
            
            # 验证 Pipeline
            validation = detector.validate_pipeline(pipeline)
            if not validation['valid']:
                self.log(f"  ❌ {validation['message']}\n")
                self.log("\n❌ 发布失败\n")
                return
            elif validation['warning']:
                self.log(f"  ⚠️  {validation['warning']}\n")
            
            self.log("\n")
            
            # 步骤 2: 创建 GitHub 仓库
            self.log("📦 步骤 2/4: 创建 GitHub 仓库...\n")
            github_mgr = GitHubManager(self.github_token.get())
            
            try:
                repo_url = github_mgr.create_repository(org_name, repo_name, private=private)
                self.log(f"  ✅ 仓库已创建: {repo_url}\n")
            except Exception as e:
                if "已存在" in str(e):
                    repo_url = f"https://github.com/{org_name}/{repo_name}.git"
                    self.log(f"  ⚠️  仓库已存在: {repo_url}\n")
                else:
                    raise
            
            self.log("\n")
            
            # 步骤 3: 生成 CI/CD Pipeline
            self.log("🔧 步骤 3/4: 生成 CI/CD Pipeline...\n")
            pipeline_gen = PipelineGenerator()
            pipeline_gen.generate(pipeline, project_path)
            self.log(f"  ✅ {pipeline.upper()} Pipeline 配置已生成\n")
            
            # 提示：密钥在组织中已配置
            self.log(f"  💡 提示: 请确保在 GitHub 组织中已配置好 {pipeline.upper()} 相关的 Secrets\n")
            
            self.log("\n")
            
            # 步骤 4: 推送代码到 GitHub
            self.log("📤 步骤 4/4: 推送代码到 GitHub...\n")
            git_mgr = GitManager(project_path)
            git_mgr.init_and_push(repo_url)
            self.log("  ✅ 代码已推送\n")
            
            self.log("\n")
            self.log("=" * 60 + "\n")
            self.log("🎉 发布完成！\n")
            self.log("=" * 60 + "\n")
            self.log(f"📍 仓库地址: https://github.com/{org_name}/{repo_name}\n")
            self.log(f"🔗 Actions: https://github.com/{org_name}/{repo_name}/actions\n")
            self.log("\n💡 提示: GitHub Actions workflow 将自动构建和发布\n")
            
            # 显示成功消息框
            self.root.after(0, lambda: messagebox.showinfo(
                "成功", 
                f"项目已成功发布到 GitHub!\n\n仓库地址:\nhttps://github.com/{org_name}/{repo_name}"
            ))
            
        except Exception as e:
            error_msg = f"❌ 错误: {str(e)}\n"
            self.log("\n" + error_msg)
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
        
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


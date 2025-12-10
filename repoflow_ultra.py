#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RepoFlow Ultra - 超现代化 GUI
采用 Fluent Design + Glassmorphism 风格
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import threading
from pathlib import Path

# UTF-8 编码
if sys.platform == 'win32':
    if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

from src.unified_config_manager import UnifiedConfigManager
from src.project_detector import ProjectDetector
from src.github_manager import GitHubManager
from src.git_manager import GitManager
from src.pipeline_generator import PipelineGenerator


class UltraModernGUI:
    """超现代化GUI"""
    
    # 2025流行配色 - 深色主题
    COLORS = {
        'bg_gradient_start': '#0F0F23',  # 深蓝黑
        'bg_gradient_end': '#1A1A2E',  # 深紫
        'card_bg': '#1E1E2E',  # 卡片背景
        'card_hover': '#252535',  # 卡片悬停
        'primary': '#00D9FF',  # 荧光青
        'primary_glow': '#00F0FF',  # 发光效果
        'accent': '#FF006E',  # 荧光粉
        'success': '#00FF88',  # 荧光绿
        'warning': '#FFB800',  # 荧光黄
        'text': '#E0E0E0',  # 浅灰文字
        'text_dim': '#808080',  # 暗灰文字
        'border': '#2A2A3E',  # 边框
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("RepoFlow Ultra")
        
        # 窗口大小
        self.width = 1000
        self.height = 700
        self.center_window()
        
        # 设置背景
        self.root.configure(bg=self.COLORS['bg_gradient_start'])
        
        # 变量
        self.project_path = tk.StringVar()
        self.repo_name = tk.StringVar()
        self.org_name = tk.StringVar(value="BACH-AI-Tools")
        self.pipeline_type = tk.StringVar(value="auto")
        self.github_token = ""
        
        # 加载配置
        self.load_config()
        
        # 创建UI
        self.create_ui()
    
    def center_window(self):
        """窗口居中"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
    
    def load_config(self):
        """加载配置"""
        config_mgr = UnifiedConfigManager()
        config = config_mgr.load_config()
        
        github_config = config.get('github', {})
        self.github_token = github_config.get('token', '')
        if github_config.get('org_name'):
            self.org_name.set(github_config['org_name'])
    
    def create_ui(self):
        """创建UI"""
        # 主画布（用于绘制渐变背景）
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.COLORS['bg_gradient_start'],
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绘制渐变背景
        self.draw_gradient_background()
        
        # 内容容器
        content = tk.Frame(self.canvas, bg=self.COLORS['bg_gradient_start'], bd=0, highlightthickness=0)
        content.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=860, height=640)
        
        # 顶部区域（Logo + 标题）
        self.create_header(content)
        
        # Token 状态
        if not self.github_token:
            self.create_token_input(content)
        else:
            self.create_token_badge(content)
        
        # 主表单区域
        self.create_main_form(content)
        
        # 底部大按钮
        self.create_action_button(content)
        
        # 状态栏
        self.create_status_bar(content)
    
    def draw_gradient_background(self):
        """绘制渐变背景"""
        for i in range(self.height):
            ratio = i / self.height
            
            # 从深蓝黑渐变到深紫
            r = int(15 + (26 - 15) * ratio)
            g = int(15 + (26 - 15) * ratio)
            b = int(35 + (46 - 35) * ratio)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, self.width, i, fill=color, width=1)
    
    def create_header(self, parent):
        """创建头部"""
        header = tk.Frame(parent, bg=self.COLORS['bg_gradient_start'], bd=0)
        header.pack(fill=tk.X, pady=(0, 30))
        
        # Logo（大型荧光图标）
        logo = tk.Label(
            header,
            text="🚀",
            font=("Segoe UI Emoji", 48),
            bg=self.COLORS['bg_gradient_start'],
            fg=self.COLORS['primary']
        )
        logo.pack()
        
        # 标题
        title = tk.Label(
            header,
            text="RepoFlow",
            font=("微软雅黑", 32, "bold"),
            fg=self.COLORS['text'],
            bg=self.COLORS['bg_gradient_start']
        )
        title.pack(pady=(10, 5))
        
        # 副标题
        subtitle = tk.Label(
            header,
            text="⚡ 3 分钟发布到 GitHub  •  零配置  •  一键完成",
            font=("微软雅黑", 11),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['bg_gradient_start']
        )
        subtitle.pack()
    
    def create_token_input(self, parent):
        """创建 Token 输入区域"""
        card = self.create_glass_card(parent, height=130)
        card.pack(fill=tk.X, pady=(0, 20))
        
        content = tk.Frame(card, bg=self.COLORS['card_bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # 标题
        tk.Label(
            content,
            text="🔑 GitHub Token",
            font=("微软雅黑", 13, "bold"),
            fg=self.COLORS['primary'],
            bg=self.COLORS['card_bg']
        ).pack(anchor=tk.W, pady=(0, 12))
        
        # 输入区域
        input_frame = tk.Frame(content, bg=self.COLORS['card_bg'])
        input_frame.pack(fill=tk.X)
        
        # Token 输入框
        self.token_var = tk.StringVar()
        token_entry = self.create_cyber_entry(input_frame, self.token_var, "粘贴你的 GitHub Token", show='*')
        token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 按钮组
        btn_frame = tk.Frame(input_frame, bg=self.COLORS['card_bg'])
        btn_frame.pack(side=tk.LEFT)
        
        self.create_cyber_button(btn_frame, "🔗 获取", self.open_token_url, width=80, height=40, is_secondary=True)
        self.create_cyber_button(btn_frame, "💾 保存", self.save_token, width=80, height=40)
    
    def create_token_badge(self, parent):
        """Token 已配置徽章"""
        badge = tk.Frame(parent, bg=self.COLORS['bg_gradient_start'], bd=0)
        badge.pack(fill=tk.X, pady=(0, 20))
        
        badge_inner = tk.Frame(
            badge,
            bg=self.COLORS['card_bg'],
            bd=0
        )
        badge_inner.pack()
        
        content = tk.Frame(badge_inner, bg=self.COLORS['card_bg'])
        content.pack(padx=20, pady=12)
        
        # 绿点 + 文字
        tk.Label(
            content,
            text="● Token 已配置",
            font=("微软雅黑", 11),
            fg=self.COLORS['success'],
            bg=self.COLORS['card_bg']
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        # 重配按钮
        tk.Label(
            content,
            text="🔄 重新配置",
            font=("微软雅黑", 9),
            fg=self.COLORS['primary'],
            bg=self.COLORS['card_bg'],
            cursor="hand2"
        ).pack(side=tk.LEFT)
    
    def create_main_form(self, parent):
        """创建主表单"""
        card = self.create_glass_card(parent, height=280)
        card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        content = tk.Frame(card, bg=self.COLORS['card_bg'])
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # 项目文件夹
        self.create_form_field(
            content,
            "📁 项目文件夹",
            self.project_path,
            has_browse=True
        )
        
        # 项目信息显示区
        self.info_label = tk.Label(
            content,
            text="",
            font=("Consolas", 9),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['card_bg'],
            justify=tk.LEFT
        )
        self.info_label.pack(fill=tk.X, pady=(5, 15))
        
        # 仓库名称
        self.create_form_field(content, "📦 仓库名称", self.repo_name)
        
        # 组织名称
        self.create_form_field(content, "🏢 组织名称", self.org_name)
        
        # Pipeline 选择
        pipeline_frame = tk.Frame(content, bg=self.COLORS['card_bg'])
        pipeline_frame.pack(fill=tk.X, pady=(15, 0))
        
        tk.Label(
            pipeline_frame,
            text="🔧 Pipeline",
            font=("微软雅黑", 11),
            fg=self.COLORS['text'],
            bg=self.COLORS['card_bg']
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        # 自定义 Combobox 样式
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Cyber.TCombobox',
            fieldbackground=self.COLORS['border'],
            background=self.COLORS['card_bg'],
            foreground=self.COLORS['text'],
            borderwidth=0
        )
        
        pipeline_combo = ttk.Combobox(
            pipeline_frame,
            textvariable=self.pipeline_type,
            values=['自动检测', 'docker', 'pypi', 'npm'],
            state='readonly',
            width=15,
            font=("微软雅黑", 10),
            style='Cyber.TCombobox'
        )
        pipeline_combo.pack(side=tk.LEFT)
    
    def create_form_field(self, parent, label_text, variable, has_browse=False):
        """创建表单字段"""
        row = tk.Frame(parent, bg=self.COLORS['card_bg'])
        row.pack(fill=tk.X, pady=8)
        
        # 标签
        label = tk.Label(
            row,
            text=label_text,
            font=("微软雅黑", 11),
            fg=self.COLORS['text'],
            bg=self.COLORS['card_bg']
        )
        label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 输入框容器
        entry_container = tk.Frame(row, bg=self.COLORS['card_bg'])
        entry_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 输入框
        entry = self.create_cyber_entry(entry_container, variable)
        entry.pack(fill=tk.X)
        
        # 浏览按钮
        if has_browse:
            browse_frame = tk.Frame(row, bg=self.COLORS['card_bg'])
            browse_frame.pack(side=tk.LEFT, padx=(10, 0))
            
            self.create_cyber_button(
                browse_frame,
                "📂",
                lambda: self.browse_folder(),
                width=45,
                height=40,
                is_secondary=True
            )
    
    def create_action_button(self, parent):
        """创建大动作按钮"""
        btn_container = tk.Frame(parent, bg=self.COLORS['bg_gradient_start'])
        btn_container.pack(fill=tk.X, pady=(0, 15))
        
        # 超大荧光按钮
        self.publish_btn = self.create_neon_button(
            btn_container,
            "🚀 一键发布",
            self.start_publish
        )
        self.publish_btn.pack()
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = tk.Frame(parent, bg=self.COLORS['card_bg'], height=50)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            status_frame,
            text="准备就绪",
            font=("微软雅黑", 10),
            fg=self.COLORS['text_dim'],
            bg=self.COLORS['card_bg']
        )
        self.status_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # 进度条（隐藏，需要时显示）
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            mode='determinate',
            length=200
        )
        # 初始隐藏
    
    def create_glass_card(self, parent, height=None):
        """创建毛玻璃卡片"""
        # 外层容器（阴影）
        shadow = tk.Frame(parent, bg=self.COLORS['bg_gradient_start'])
        
        # 内层卡片（毛玻璃效果）
        card = tk.Frame(
            shadow,
            bg=self.COLORS['card_bg'],
            highlightbackground=self.COLORS['border'],
            highlightthickness=1
        )
        card.pack(padx=3, pady=3, fill=tk.BOTH, expand=True)
        
        if height:
            shadow.configure(height=height)
            shadow.pack_propagate(False)
        
        return card
    
    def create_cyber_entry(self, parent, variable, placeholder="", show=None):
        """创建赛博风格输入框"""
        # 容器
        container = tk.Frame(
            parent,
            bg=self.COLORS['border'],
            highlightbackground=self.COLORS['primary'],
            highlightthickness=0
        )
        
        # 输入框
        entry = tk.Entry(
            container,
            textvariable=variable,
            font=("微软雅黑", 10),
            bd=0,
            bg=self.COLORS['border'],
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['primary'],
            show=show
        )
        entry.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
        
        # 焦点效果
        def on_focus_in(e):
            container.configure(
                highlightthickness=2,
                bg=self.COLORS['card_bg']
            )
            entry.configure(bg=self.COLORS['card_bg'])
        
        def on_focus_out(e):
            container.configure(
                highlightthickness=0,
                bg=self.COLORS['border']
            )
            entry.configure(bg=self.COLORS['border'])
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
        return container
    
    def create_cyber_button(self, parent, text, command, width=100, height=40, is_secondary=False):
        """创建赛博风格按钮"""
        bg_color = self.COLORS['border'] if is_secondary else self.COLORS['primary']
        fg_color = self.COLORS['text'] if is_secondary else '#000000'
        hover_color = self.COLORS['card_hover'] if is_secondary else self.COLORS['primary_glow']
        
        btn = tk.Button(
            parent,
            text=text,
            font=("微软雅黑", 10, "bold"),
            fg=fg_color,
            bg=bg_color,
            activebackground=hover_color,
            activeforeground=fg_color,
            bd=0,
            cursor="hand2",
            command=command,
            width=width//10,
            height=height//20
        )
        btn.pack(side=tk.LEFT, padx=5)
        
        # 悬停效果
        def on_enter(e):
            btn.configure(bg=hover_color)
        
        def on_leave(e):
            btn.configure(bg=bg_color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def create_neon_button(self, parent, text, command):
        """创建荧光大按钮"""
        # 使用 Canvas 绘制发光效果
        canvas = tk.Canvas(
            parent,
            width=860,
            height=60,
            bg=self.COLORS['bg_gradient_start'],
            highlightthickness=0
        )
        
        # 发光效果（多层叠加）
        for i in range(3):
            offset = i * 2
            opacity = 50 - i * 15
            glow_color = self._add_alpha(self.COLORS['primary'], opacity)
            canvas.create_rounded_rectangle(
                2-offset, 2-offset, 858+offset, 58+offset,
                radius=30,
                fill='',
                outline=glow_color,
                width=2
            )
        
        # 主按钮
        canvas.create_rounded_rectangle(
            2, 2, 858, 58,
            radius=28,
            fill=self.COLORS['primary'],
            outline=''
        )
        
        # 文字
        canvas.create_text(
            430, 30,
            text=text,
            font=("微软雅黑", 16, "bold"),
            fill='#000000'
        )
        
        # 点击和悬停
        def on_click(e):
            command()
        
        def on_hover(e):
            canvas.configure(cursor="hand2")
            # 增强发光效果
            canvas.delete("all")
            for i in range(5):
                offset = i * 3
                opacity = 70 - i * 12
                canvas.create_rounded_rectangle(
                    2-offset, 2-offset, 858+offset, 58+offset,
                    radius=30,
                    fill='',
                    outline=self._add_alpha(self.COLORS['primary_glow'], opacity),
                    width=3
                )
            canvas.create_rounded_rectangle(
                2, 2, 858, 58,
                radius=28,
                fill=self.COLORS['primary_glow'],
                outline=''
            )
            canvas.create_text(
                430, 30,
                text=text,
                font=("微软雅黑", 16, "bold"),
                fill='#000000'
            )
        
        def on_leave(e):
            canvas.configure(cursor="")
            # 恢复正常
            canvas.delete("all")
            for i in range(3):
                offset = i * 2
                opacity = 50 - i * 15
                canvas.create_rounded_rectangle(
                    2-offset, 2-offset, 858+offset, 58+offset,
                    radius=30,
                    fill='',
                    outline=self._add_alpha(self.COLORS['primary'], opacity),
                    width=2
                )
            canvas.create_rounded_rectangle(
                2, 2, 858, 58,
                radius=28,
                fill=self.COLORS['primary'],
                outline=''
            )
            canvas.create_text(
                430, 30,
                text=text,
                font=("微软雅黑", 16, "bold"),
                fill='#000000'
            )
        
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<Enter>", on_hover)
        canvas.bind("<Leave>", on_leave)
        
        return canvas
    
    def _add_alpha(self, color, alpha):
        """添加透明度（模拟）"""
        # 简化：返回颜色本身
        return color
    
    # 辅助方法
    def browse_folder(self):
        """浏览文件夹"""
        folder = filedialog.askdirectory(title="选择项目文件夹")
        if folder:
            self.project_path.set(folder)
            self.analyze_project(folder)
    
    def analyze_project(self, folder):
        """分析项目"""
        try:
            path = Path(folder)
            detector = ProjectDetector(path)
            info = detector.detect()
            
            parts = []
            if (path / "README.md").exists():
                parts.append("✅ README")
            if info.get('type'):
                parts.append(f"🔍 {info['type'].upper()}")
            if info.get('version'):
                parts.append(f"v{info['version']}")
            
            self.info_label.configure(text=" • ".join(parts))
            
            if not self.repo_name.get():
                self.repo_name.set(path.name)
            
        except Exception as e:
            self.info_label.configure(text=f"⚠️ {str(e)}")
    
    def open_token_url(self):
        """打开 Token 页面"""
        import webbrowser
        webbrowser.open("https://github.com/settings/tokens/new?description=RepoFlow&scopes=repo,workflow,write:packages")
        self.show_neon_toast("🌐 已在浏览器中打开")
    
    def save_token(self):
        """保存 Token"""
        token = self.token_var.get().strip()
        if not token:
            self.show_neon_toast("❌ 请输入 Token", "error")
            return
        
        config_mgr = UnifiedConfigManager()
        config = config_mgr.load_config()
        if 'github' not in config:
            config['github'] = {}
        config['github']['token'] = token
        config_mgr.save_config(config)
        
        self.show_neon_toast("✅ Token 已保存！请重启", "success")
        self.root.after(2000, self.root.quit)
    
    def start_publish(self):
        """开始发布"""
        # 验证
        if not self.project_path.get():
            self.show_neon_toast("请选择项目文件夹", "error")
            return
        
        if not self.repo_name.get():
            self.show_neon_toast("请输入仓库名称", "error")
            return
        
        if not self.github_token:
            self.show_neon_toast("请先配置 GitHub Token", "error")
            return
        
        # 在新线程中执行
        self.publish_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="🚀 发布中...")
        
        thread = threading.Thread(target=self._do_publish, daemon=True)
        thread.start()
    
    def _do_publish(self):
        """执行发布"""
        try:
            project_path = Path(self.project_path.get())
            repo_name = self.repo_name.get()
            org_name = self.org_name.get()
            
            # 检查 README
            if not (project_path / "README.md").exists():
                self.root.after(0, lambda: self.show_neon_toast("❌ 必须包含 README.md", "error"))
                return
            
            # 创建仓库
            self.root.after(0, lambda: self.update_status("📦 创建 GitHub 仓库..."))
            github_mgr = GitHubManager(self.github_token)
            repo_url, is_new = github_mgr.create_repository(org_name, repo_name)
            
            # 生成 Pipeline
            self.root.after(0, lambda: self.update_status("🔧 生成 Pipeline 配置..."))
            pipeline = self.pipeline_type.get()
            if pipeline == '自动检测':
                detector = ProjectDetector(project_path)
                info = detector.detect()
                pipeline = info.get('type', 'docker')
            
            pipeline_gen = PipelineGenerator()
            pipeline_gen.generate(pipeline, project_path)
            
            # 推送代码
            self.root.after(0, lambda: self.update_status("📤 推送代码到 GitHub..."))
            git_mgr = GitManager(project_path)
            git_mgr.init_and_push(repo_url)
            
            # 完成
            self.root.after(0, lambda: self.show_neon_toast(f"🎉 发布成功！\n{repo_url}", "success"))
            self.root.after(0, lambda: self.update_status("✅ 发布完成"))
            
        except Exception as e:
            self.root.after(0, lambda: self.show_neon_toast(f"❌ {str(e)}", "error"))
            self.root.after(0, lambda: self.update_status("❌ 发布失败"))
        finally:
            self.root.after(0, lambda: self.publish_btn.configure(state=tk.NORMAL))
    
    def update_status(self, text):
        """更新状态"""
        self.status_label.configure(text=text)
    
    def show_neon_toast(self, message, type="info"):
        """显示荧光 Toast"""
        # 创建 Toast 窗口
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        
        # 如果是 Windows，设置透明度
        try:
            toast.attributes('-alpha', 0.95)
        except:
            pass
        
        # 颜色
        colors = {
            'info': self.COLORS['primary'],
            'success': self.COLORS['success'],
            'error': self.COLORS['accent'],
            'warning': self.COLORS['warning']
        }
        
        bg_color = colors.get(type, self.COLORS['primary'])
        
        # 内容
        frame = tk.Frame(toast, bg=bg_color)
        frame.pack()
        
        label = tk.Label(
            frame,
            text=message,
            font=("微软雅黑", 12, "bold"),
            fg='#000000',
            bg=bg_color,
            padx=30,
            pady=15
        )
        label.pack()
        
        # 位置（中央偏下）
        toast.update()
        width = toast.winfo_width()
        height = toast.winfo_height()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2 + 200
        toast.geometry(f"+{x}+{y}")
        
        # 渐入渐出动画
        self.fade_in(toast, 3000)
    
    def fade_in(self, window, duration):
        """渐入动画"""
        try:
            alpha = 0.0
            step = 0.05
            
            def animate():
                nonlocal alpha
                if alpha < 0.95:
                    alpha += step
                    try:
                        window.attributes('-alpha', alpha)
                        window.after(20, animate)
                    except:
                        pass
                else:
                    # 停留一段时间后关闭
                    window.after(duration, lambda: self.fade_out(window))
            
            animate()
        except:
            # 不支持透明度，直接显示
            window.after(duration, window.destroy)
    
    def fade_out(self, window):
        """渐出动画"""
        try:
            alpha = 0.95
            step = 0.1
            
            def animate():
                nonlocal alpha
                if alpha > 0:
                    alpha -= step
                    try:
                        window.attributes('-alpha', max(0, alpha))
                        window.after(20, animate)
                    except:
                        window.destroy()
                else:
                    window.destroy()
            
            animate()
        except:
            window.destroy()


# Canvas 扩展方法
def create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
    """在 Canvas 上创建圆角矩形"""
    points = [
        x1+radius, y1,
        x2-radius, y1,
        x2, y1,
        x2, y1+radius,
        x2, y2-radius,
        x2, y2,
        x2-radius, y2,
        x1+radius, y2,
        x1, y2,
        x1, y2-radius,
        x1, y1+radius,
        x1, y1
    ]
    return self.create_polygon(points, smooth=True, **kwargs)

# 添加到 Canvas 类
tk.Canvas.create_rounded_rectangle = create_rounded_rectangle


def main():
    root = tk.Tk()
    app = UltraModernGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()



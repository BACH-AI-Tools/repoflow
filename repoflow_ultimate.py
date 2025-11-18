#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RepoFlow Ultimate - 极致现代化 GUI
采用 Neumorphism + Glassmorphism + Fluent Design 融合风格
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import threading
from pathlib import Path
import math

# UTF-8 编码
if sys.platform == 'win32':
    if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

from src.unified_config_manager import UnifiedConfigManager
from src.project_detector import ProjectDetector
from src.github_manager import GitHubManager
from src.git_manager import GitManager
from src.pipeline_generator import PipelineGenerator


class UltimateModernGUI:
    """极致现代化GUI"""
    
    # 2025最新配色 - 深空渐变主题
    COLORS = {
        # 背景渐变
        'bg_top': '#0A0E27',        # 深空蓝
        'bg_bottom': '#1A1F3A',     # 深紫蓝
        'bg_accent': '#2D1B4E',     # 深紫
        
        # 卡片
        'card_bg': 'rgba(30, 35, 60, 0.7)',      # 半透明卡片
        'card_border': '#3D4668',                # 卡片边框
        'card_hover': 'rgba(40, 45, 75, 0.85)',  # 悬停效果
        
        # 主色调 - 霓虹渐变
        'primary_start': '#667EEA',   # 紫色
        'primary_end': '#764BA2',     # 深紫
        'accent': '#F093FB',          # 粉紫
        'accent2': '#4FACFE',         # 天蓝
        
        # 功能色
        'success': '#00F5A0',         # 荧光绿
        'warning': '#FFC837',         # 金黄
        'error': '#FF6B9D',           # 粉红
        'info': '#4FC3F7',            # 亮蓝
        
        # 文字
        'text_primary': '#FFFFFF',    # 纯白
        'text_secondary': '#B0B8D4',  # 浅灰蓝
        'text_dim': '#6B7199',        # 暗灰
        
        # 装饰
        'glow': '#A78BFA',            # 发光紫
        'shadow': '#000000',          # 阴影
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("RepoFlow Ultimate")
        
        # 窗口设置
        self.width = 1100
        self.height = 750
        self.center_window()
        
        # 去除默认边框，使用自定义边框
        self.root.configure(bg=self.COLORS['bg_top'])
        
        # 变量
        self.project_path = tk.StringVar()
        self.repo_name = tk.StringVar()
        self.org_name = tk.StringVar(value="BACH-AI-Tools")
        self.pipeline_type = tk.StringVar(value="auto")
        self.github_token = ""
        
        # 动画变量
        self.animation_running = False
        self.glow_offset = 0
        
        # 加载配置
        self.load_config()
        
        # 创建UI
        self.create_ui()
        
        # 启动背景动画
        self.start_background_animation()
    
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
        # 主画布
        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg=self.COLORS['bg_top'],
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绘制动态渐变背景
        self.draw_background()
        
        # 内容容器
        self.content_frame = tk.Frame(
            self.canvas,
            bg=self.COLORS['bg_top'],
            bd=0,
            highlightthickness=0
        )
        self.content_window = self.canvas.create_window(
            self.width // 2,
            self.height // 2,
            window=self.content_frame,
            width=960,
            height=680,
            anchor=tk.CENTER
        )
        
        # 创建顶部栏
        self.create_top_bar()
        
        # 创建主内容区
        self.create_main_content()
        
        # 创建底部按钮
        self.create_bottom_actions()
    
    def draw_background(self):
        """绘制动态渐变背景"""
        # 清空画布
        self.canvas.delete("bg")
        
        # 绘制径向渐变
        center_x = self.width // 2
        center_y = self.height // 2
        max_radius = max(self.width, self.height)
        
        for i in range(max_radius, 0, -20):
            ratio = i / max_radius
            
            # 计算渐变色
            r1, g1, b1 = self.hex_to_rgb(self.COLORS['bg_top'])
            r2, g2, b2 = self.hex_to_rgb(self.COLORS['bg_bottom'])
            
            r = int(r1 + (r2 - r1) * (1 - ratio))
            g = int(g1 + (g2 - g1) * (1 - ratio))
            b = int(b1 + (b2 - b1) * (1 - ratio))
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            # 绘制圆形渐变
            self.canvas.create_oval(
                center_x - i, center_y - i,
                center_x + i, center_y + i,
                fill=color, outline="", tags="bg"
            )
        
        # 添加装饰性光点
        self.draw_light_particles()
    
    def draw_light_particles(self):
        """绘制装饰光点"""
        import random
        
        # 创建随机分布的发光点
        for _ in range(30):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 3)
            opacity = random.randint(50, 150)
            
            color = '#A78BFA'  # 使用发光紫色
            self.canvas.create_oval(
                x - size, y - size,
                x + size, y + size,
                fill=color, outline="", tags="bg"
            )
    
    def start_background_animation(self):
        """启动背景动画"""
        if not self.animation_running:
            self.animation_running = True
            self.animate_glow()
    
    def animate_glow(self):
        """发光动画效果"""
        if self.animation_running:
            self.glow_offset = (self.glow_offset + 1) % 360
            # 这里可以添加动画效果，比如按钮发光等
            self.root.after(50, self.animate_glow)
    
    def create_top_bar(self):
        """创建顶部栏"""
        top_bar = tk.Frame(
            self.content_frame,
            bg=self.COLORS['bg_top'],
            height=120,
            bd=0
        )
        top_bar.pack(fill=tk.X, pady=(0, 30))
        
        # Logo容器 - 使用渐变圆形背景
        logo_canvas = tk.Canvas(
            top_bar,
            width=80,
            height=80,
            bg=self.COLORS['bg_top'],
            highlightthickness=0
        )
        logo_canvas.pack(pady=(0, 15))
        
        # 绘制渐变圆形背景
        self.draw_gradient_circle(logo_canvas, 40, 40, 35, 
                                  self.COLORS['primary_start'], 
                                  self.COLORS['primary_end'])
        
        # Logo图标
        logo_canvas.create_text(
            40, 40,
            text="🚀",
            font=("Segoe UI Emoji", 32),
        )
        
        # 标题 - 使用渐变文字效果
        title_frame = tk.Frame(top_bar, bg=self.COLORS['bg_top'])
        title_frame.pack()
        
        title_label = tk.Label(
            title_frame,
            text="RepoFlow Ultimate",
            font=("微软雅黑", 36, "bold"),
            fg=self.COLORS['text_primary'],
            bg=self.COLORS['bg_top']
        )
        title_label.pack()
        
        # 副标题
        subtitle = tk.Label(
            top_bar,
            text="⚡ 极速发布  •  智能检测  •  一键完成  •  3分钟上线",
            font=("微软雅黑", 12),
            fg=self.COLORS['text_secondary'],
            bg=self.COLORS['bg_top']
        )
        subtitle.pack(pady=(8, 0))
    
    def draw_gradient_circle(self, canvas, cx, cy, radius, color1, color2):
        """绘制渐变圆形"""
        r1, g1, b1 = self.hex_to_rgb(color1)
        r2, g2, b2 = self.hex_to_rgb(color2)
        
        steps = 30
        for i in range(steps, 0, -1):
            ratio = i / steps
            r = int(r1 + (r2 - r1) * (1 - ratio))
            g = int(g1 + (g2 - g1) * (1 - ratio))
            b = int(b1 + (b2 - b1) * (1 - ratio))
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            r_current = radius * ratio
            canvas.create_oval(
                cx - r_current, cy - r_current,
                cx + r_current, cy + r_current,
                fill=color, outline=""
            )
    
    def hex_to_rgb(self, hex_color):
        """十六进制转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def create_main_content(self):
        """创建主内容区"""
        # Token状态卡片
        if not self.github_token:
            self.create_token_card()
        else:
            self.create_token_status_badge()
        
        # 主表单卡片
        self.create_form_card()
    
    def create_token_card(self):
        """创建Token配置卡片"""
        card = self.create_glass_card(self.content_frame, 140)
        card.pack(fill=tk.X, pady=(0, 20))
        
        # 图标和标题
        header = tk.Frame(card, bg='#1E233C')
        header.pack(fill=tk.X, padx=30, pady=(20, 15))
        
        tk.Label(
            header,
            text="🔐",
            font=("Segoe UI Emoji", 24),
            bg='#1E233C'
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        title_frame = tk.Frame(header, bg='#1E233C')
        title_frame.pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="GitHub Token",
            font=("微软雅黑", 14, "bold"),
            fg=self.COLORS['text_primary'],
            bg='#1E233C'
        ).pack(anchor=tk.W)
        
        tk.Label(
            title_frame,
            text="用于创建仓库和推送代码",
            font=("微软雅黑", 10),
            fg=self.COLORS['text_dim'],
            bg='#1E233C'
        ).pack(anchor=tk.W)
        
        # 输入区域
        input_container = tk.Frame(card, bg='#1E233C')
        input_container.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        # Token输入框
        self.token_var = tk.StringVar()
        token_entry = self.create_modern_entry(
            input_container,
            self.token_var,
            "粘贴你的 GitHub Personal Access Token",
            show='*'
        )
        token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))
        
        # 按钮组
        btn_container = tk.Frame(input_container, bg='#1E233C')
        btn_container.pack(side=tk.LEFT)
        
        self.create_gradient_button(
            btn_container,
            "🔗 获取Token",
            self.open_token_url,
            width=120,
            is_secondary=True
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        self.create_gradient_button(
            btn_container,
            "💾 保存",
            self.save_token,
            width=100
        ).pack(side=tk.LEFT)
    
    def create_token_status_badge(self):
        """Token状态徽章"""
        badge_frame = tk.Frame(
            self.content_frame,
            bg=self.COLORS['bg_top']
        )
        badge_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 内容卡片
        badge_card = tk.Frame(
            badge_frame,
            bg='#1E233C',
            bd=0
        )
        badge_card.pack()
        
        # 添加发光边框效果
        self.add_glow_effect(badge_card)
        
        content = tk.Frame(badge_card, bg='#1E233C')
        content.pack(padx=25, pady=15)
        
        # 状态指示器
        indicator = tk.Canvas(
            content,
            width=12,
            height=12,
            bg='#1E233C',
            highlightthickness=0
        )
        indicator.pack(side=tk.LEFT, padx=(0, 10))
        indicator.create_oval(2, 2, 10, 10, fill=self.COLORS['success'], outline="")
        
        # 状态文字
        tk.Label(
            content,
            text="GitHub Token 已配置",
            font=("微软雅黑", 12, "bold"),
            fg=self.COLORS['success'],
            bg='#1E233C'
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        # 重新配置按钮
        reconfig_btn = tk.Label(
            content,
            text="🔄 重新配置",
            font=("微软雅黑", 10),
            fg=self.COLORS['info'],
            bg='#1E233C',
            cursor="hand2"
        )
        reconfig_btn.pack(side=tk.LEFT)
        reconfig_btn.bind("<Enter>", lambda e: reconfig_btn.config(fg=self.COLORS['accent2']))
        reconfig_btn.bind("<Leave>", lambda e: reconfig_btn.config(fg=self.COLORS['info']))
    
    def create_form_card(self):
        """创建表单卡片"""
        card = self.create_glass_card(self.content_frame, 350)
        card.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        content = tk.Frame(card, bg='#1E233C')
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
        
        # 项目文件夹
        self.create_form_row(
            content,
            "📁",
            "项目文件夹",
            "选择要发布的项目",
            self.project_path,
            has_button=True,
            button_text="浏览",
            button_cmd=self.browse_project
        )
        
        # 项目信息显示
        self.info_container = tk.Frame(content, bg='#1E233C')
        self.info_container.pack(fill=tk.X, pady=(10, 20))
        
        self.info_label = tk.Label(
            self.info_container,
            text="",
            font=("Consolas", 10),
            fg=self.COLORS['text_secondary'],
            bg='#1E233C',
            justify=tk.LEFT
        )
        self.info_label.pack(fill=tk.X)
        
        # 分隔线
        separator = tk.Frame(content, bg=self.COLORS['card_border'], height=1)
        separator.pack(fill=tk.X, pady=15)
        
        # 仓库名称
        self.create_form_row(
            content,
            "📦",
            "仓库名称",
            "GitHub 仓库名称",
            self.repo_name
        )
        
        # 组织名称
        self.create_form_row(
            content,
            "🏢",
            "组织名称",
            "GitHub 组织名称",
            self.org_name
        )
        
        # Pipeline类型
        pipeline_frame = tk.Frame(content, bg='#1E233C')
        pipeline_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 左侧标签
        label_container = tk.Frame(pipeline_frame, bg='#1E233C')
        label_container.pack(side=tk.LEFT)
        
        tk.Label(
            label_container,
            text="🔧",
            font=("Segoe UI Emoji", 18),
            bg='#1E233C'
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Label(
            label_container,
            text="Pipeline 类型",
            font=("微软雅黑", 12, "bold"),
            fg=self.COLORS['text_primary'],
            bg='#1E233C'
        ).pack(side=tk.LEFT)
        
        # Pipeline选择器
        pipeline_selector = self.create_modern_combobox(
            pipeline_frame,
            self.pipeline_type,
            ['自动检测', 'pypi', 'npm', 'docker']
        )
        pipeline_selector.pack(side=tk.RIGHT)
    
    def create_form_row(self, parent, icon, label, hint, variable, 
                       has_button=False, button_text="", button_cmd=None):
        """创建表单行"""
        row = tk.Frame(parent, bg='#1E233C')
        row.pack(fill=tk.X, pady=(0, 15))
        
        # 图标和标签
        label_frame = tk.Frame(row, bg='#1E233C', width=150)
        label_frame.pack(side=tk.LEFT)
        label_frame.pack_propagate(False)
        
        tk.Label(
            label_frame,
            text=icon,
            font=("Segoe UI Emoji", 18),
            bg='#1E233C'
        ).pack(side=tk.LEFT, padx=(0, 8))
        
        tk.Label(
            label_frame,
            text=label,
            font=("微软雅黑", 12, "bold"),
            fg=self.COLORS['text_primary'],
            bg='#1E233C'
        ).pack(side=tk.LEFT)
        
        # 输入框
        entry = self.create_modern_entry(row, variable, hint)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 可选按钮
        if has_button:
            btn = self.create_gradient_button(
                row,
                button_text,
                button_cmd,
                width=90,
                is_secondary=True
            )
            btn.pack(side=tk.LEFT, padx=(8, 0))
        
        return row
    
    def create_bottom_actions(self):
        """创建底部操作区"""
        actions = tk.Frame(self.content_frame, bg=self.COLORS['bg_top'])
        actions.pack(fill=tk.X)
        
        # 主要操作按钮
        main_btn = self.create_gradient_button(
            actions,
            "🚀 开始发布",
            self.start_publish,
            width=300,
            height=56,
            is_primary=True
        )
        main_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
        
        # 设置按钮
        settings_btn = self.create_gradient_button(
            actions,
            "⚙️ 设置",
            self.open_settings,
            width=120,
            height=56
        )
        settings_btn.pack(side=tk.LEFT)
    
    def create_glass_card(self, parent, height):
        """创建毛玻璃卡片"""
        # 外层容器（用于阴影）
        shadow_container = tk.Frame(
            parent,
            bg=self.COLORS['bg_top'],
            bd=0
        )
        
        # 卡片主体
        card = tk.Frame(
            shadow_container,
            bg='#1E233C',
            bd=0,
            height=height
        )
        card.pack(padx=2, pady=2)
        
        return card
    
    def add_glow_effect(self, widget):
        """添加发光效果"""
        # 这里可以添加发光边框的实现
        # 由于tkinter限制，可以用Canvas来实现
        pass
    
    def create_modern_entry(self, parent, variable, placeholder, show=None):
        """创建现代化输入框"""
        # 容器
        entry_container = tk.Frame(parent, bg='#2A2F4A', bd=0)
        
        # 输入框
        entry = tk.Entry(
            entry_container,
            textvariable=variable,
            font=("微软雅黑", 11),
            bg='#2A2F4A',
            fg=self.COLORS['text_primary'],
            insertbackground=self.COLORS['accent2'],
            bd=0,
            highlightthickness=0,
            show=show
        )
        entry.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)
        
        # Placeholder效果
        if placeholder:
            def on_focus_in(e):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(fg=self.COLORS['text_primary'])
            
            def on_focus_out(e):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(fg=self.COLORS['text_dim'])
            
            entry.insert(0, placeholder)
            entry.config(fg=self.COLORS['text_dim'])
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
        
        # 聚焦效果
        def on_enter(e):
            entry_container.config(bg='#333856')
        
        def on_leave(e):
            entry_container.config(bg='#2A2F4A')
        
        entry.bind('<Enter>', on_enter)
        entry.bind('<Leave>', on_leave)
        entry_container.bind('<Enter>', on_enter)
        entry_container.bind('<Leave>', on_leave)
        
        return entry_container
    
    def create_modern_combobox(self, parent, variable, values):
        """创建现代化下拉框"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Modern.TCombobox',
            fieldbackground='#2A2F4A',
            background='#2A2F4A',
            foreground=self.COLORS['text_primary'],
            borderwidth=0,
            arrowcolor=self.COLORS['accent2']
        )
        
        combo = ttk.Combobox(
            parent,
            textvariable=variable,
            values=values,
            state='readonly',
            font=("微软雅黑", 11),
            style='Modern.TCombobox',
            width=15
        )
        
        return combo
    
    def create_gradient_button(self, parent, text, command, 
                               width=150, height=45, 
                               is_primary=False, is_secondary=False):
        """创建渐变按钮"""
        # 创建Canvas按钮
        btn_canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=self.COLORS['bg_top'],
            highlightthickness=0,
            cursor="hand2"
        )
        
        # 确定颜色
        if is_primary:
            color1 = self.COLORS['primary_start']
            color2 = self.COLORS['primary_end']
            text_color = self.COLORS['text_primary']
        elif is_secondary:
            color1 = '#2A2F4A'
            color2 = '#353B5C'
            text_color = self.COLORS['text_secondary']
        else:
            color1 = self.COLORS['card_border']
            color2 = '#2A2F4A'
            text_color = self.COLORS['text_primary']
        
        # 绘制渐变背景
        self.draw_gradient_rect(btn_canvas, 0, 0, width, height, color1, color2)
        
        # 添加文字
        text_id = btn_canvas.create_text(
            width // 2,
            height // 2,
            text=text,
            font=("微软雅黑", 12, "bold"),
            fill=text_color
        )
        
        # 交互效果
        def on_enter(e):
            btn_canvas.config(cursor="hand2")
            btn_canvas.delete("all")
            # 变亮
            self.draw_gradient_rect(btn_canvas, 0, 0, width, height, 
                                   self.lighten_color(color1), 
                                   self.lighten_color(color2))
            btn_canvas.create_text(
                width // 2, height // 2,
                text=text,
                font=("微软雅黑", 12, "bold"),
                fill=text_color
            )
        
        def on_leave(e):
            btn_canvas.delete("all")
            self.draw_gradient_rect(btn_canvas, 0, 0, width, height, color1, color2)
            btn_canvas.create_text(
                width // 2, height // 2,
                text=text,
                font=("微软雅黑", 12, "bold"),
                fill=text_color
            )
        
        def on_click(e):
            if command:
                command()
        
        btn_canvas.bind('<Enter>', on_enter)
        btn_canvas.bind('<Leave>', on_leave)
        btn_canvas.bind('<Button-1>', on_click)
        
        return btn_canvas
    
    def draw_gradient_rect(self, canvas, x1, y1, x2, y2, color1, color2):
        """绘制渐变矩形"""
        r1, g1, b1 = self.hex_to_rgb(color1)
        r2, g2, b2 = self.hex_to_rgb(color2)
        
        height = y2 - y1
        for i in range(height):
            ratio = i / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            canvas.create_line(x1, y1 + i, x2, y1 + i, fill=color, width=1)
    
    def lighten_color(self, color):
        """变亮颜色"""
        r, g, b = self.hex_to_rgb(color)
        r = min(255, int(r * 1.2))
        g = min(255, int(g * 1.2))
        b = min(255, int(b * 1.2))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    # ========== 业务逻辑方法 ==========
    
    def browse_project(self):
        """浏览项目文件夹"""
        folder = filedialog.askdirectory(title="选择项目文件夹")
        if folder:
            self.project_path.set(folder)
            self.detect_project_info()
    
    def detect_project_info(self):
        """检测项目信息"""
        try:
            detector = ProjectDetector(self.project_path.get())
            info = detector.detect()
            
            # 更新显示
            info_text = f"✓ 类型: {info['type'].upper()}  |  版本: {info['version']}  |  语言: {info['language']}"
            self.info_label.config(text=info_text, fg=self.COLORS['success'])
            
            # 自动填充仓库名
            if not self.repo_name.get():
                folder_name = Path(self.project_path.get()).name
                self.repo_name.set(folder_name)
        except Exception as e:
            self.info_label.config(
                text=f"⚠ 检测失败: {str(e)}",
                fg=self.COLORS['warning']
            )
    
    def open_token_url(self):
        """打开Token获取页面"""
        import webbrowser
        webbrowser.open("https://github.com/settings/tokens/new?scopes=repo,workflow")
    
    def save_token(self):
        """保存Token"""
        token = self.token_var.get()
        if not token or token.startswith("粘贴"):
            messagebox.showwarning("警告", "请输入有效的 GitHub Token")
            return
        
        try:
            config_mgr = UnifiedConfigManager()
            config = config_mgr.load_config()
            
            if 'github' not in config:
                config['github'] = {}
            
            config['github']['token'] = token
            config_mgr.save_config(config)
            
            self.github_token = token
            messagebox.showinfo("成功", "Token 保存成功！")
            
            # 刷新UI
            self.refresh_ui()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def refresh_ui(self):
        """刷新UI"""
        # 清空内容
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # 重新创建
        self.create_top_bar()
        self.create_main_content()
        self.create_bottom_actions()
    
    def start_publish(self):
        """开始发布"""
        # 验证输入
        if not self.github_token:
            messagebox.showwarning("警告", "请先配置 GitHub Token")
            return
        
        if not self.project_path.get():
            messagebox.showwarning("警告", "请选择项目文件夹")
            return
        
        if not self.repo_name.get():
            messagebox.showwarning("警告", "请输入仓库名称")
            return
        
        # 启动发布流程（这里需要实现实际的发布逻辑）
        messagebox.showinfo("开始", "发布流程启动中...")
        
        # TODO: 实现发布逻辑
        def publish_thread():
            try:
                # 这里调用实际的发布逻辑
                pass
            except Exception as e:
                messagebox.showerror("错误", f"发布失败: {str(e)}")
        
        threading.Thread(target=publish_thread, daemon=True).start()
    
    def open_settings(self):
        """打开设置窗口"""
        from settings_window import SettingsWindow
        SettingsWindow(self.root)


def main():
    """主函数"""
    root = tk.Tk()
    app = UltimateModernGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


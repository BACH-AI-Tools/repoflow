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
from src.workflow_executor import WorkflowExecutor


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
        
        # 克隆功能变量
        self.clone_url = tk.StringVar()
        self.clone_prefix = tk.StringVar(value="bachai")
        self.current_tab = "local"  # 'local' 或 'clone'
        
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
        # Token状态卡片（总是显示，让用户知道是否已配置）
        if not self.github_token:
            # 创建简化的Token提示
            token_hint = tk.Frame(self.content_frame, bg=self.COLORS['bg_top'])
            token_hint.pack(fill=tk.X, pady=(0, 20))
            
            hint_card = tk.Frame(token_hint, bg='#2D1F3F')
            hint_card.pack(pady=5)
            
            hint_content = tk.Frame(hint_card, bg='#2D1F3F')
            hint_content.pack(padx=20, pady=10)
            
            tk.Label(
                hint_content,
                text="⚠️ GitHub Token 未配置",
                font=("微软雅黑", 11, "bold"),
                fg=self.COLORS['warning'],
                bg='#2D1F3F'
            ).pack(side=tk.LEFT, padx=(0, 15))
            
            config_link = tk.Label(
                hint_content,
                text="点击右下角「⚙️ 设置」进行配置",
                font=("微软雅黑", 10),
                fg=self.COLORS['info'],
                bg='#2D1F3F'
            )
            config_link.pack(side=tk.LEFT)
        else:
            self.create_token_status_badge()
        
        # 标签页切换（总是显示）
        self.create_tab_switcher()
        
        # 内容容器
        self.tab_content_frame = tk.Frame(self.content_frame, bg=self.COLORS['bg_top'])
        self.tab_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 根据当前标签显示内容
        self.show_current_tab()
    
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
    
    def create_tab_switcher(self):
        """创建标签页切换器"""
        print("🔧 创建标签页切换器...")  # 调试信息
        
        tab_frame = tk.Frame(self.content_frame, bg=self.COLORS['bg_top'])
        tab_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 标签容器 - 使用更明显的背景色和边框
        tab_container = tk.Frame(tab_frame, bg='#1E233C', relief=tk.RAISED, bd=2)
        tab_container.pack(pady=10)  # 增加外边距
        
        print(f"  标签容器已创建: {tab_container}")  # 调试信息
        
        # 本地项目标签
        print("  创建【本地项目】标签...")  # 调试信息
        self.local_tab_btn = self.create_tab_button(
            tab_container,
            "📁 本地项目",
            lambda: self.switch_tab("local"),
            is_active=True
        )
        self.local_tab_btn.pack(side=tk.LEFT, padx=5, pady=5)  # 增加内边距
        print(f"    本地标签已创建: {self.local_tab_btn}")  # 调试信息
        
        # 克隆仓库标签
        print("  创建【克隆仓库】标签...")  # 调试信息
        self.clone_tab_btn = self.create_tab_button(
            tab_container,
            "🔗 克隆仓库",
            lambda: self.switch_tab("clone"),
            is_active=False
        )
        self.clone_tab_btn.pack(side=tk.LEFT, padx=5, pady=5)  # 增加内边距
        print(f"    克隆标签已创建: {self.clone_tab_btn}")  # 调试信息
        print("✅ 标签页切换器创建完成！")  # 调试信息
    
    def create_tab_button(self, parent, text, command, is_active=False):
        """创建标签按钮"""
        btn = tk.Frame(parent, bg='#2D3250' if is_active else '#1E233C', cursor="hand2")
        # 不要禁用 pack_propagate，让按钮自动调整大小
        
        label = tk.Label(
            btn,
            text=text,
            font=("微软雅黑", 13, "bold" if is_active else "normal"),  # 增大字体
            fg=self.COLORS['accent'] if is_active else self.COLORS['text_secondary'],
            bg='#2D3250' if is_active else '#1E233C',
            cursor="hand2"
        )
        label.pack(padx=30, pady=15)  # 增大内边距，让按钮更大
        
        # 保存标签和按钮的引用
        btn._label = label
        btn._is_active = is_active
        btn._command = command
        
        # 绑定点击事件
        def on_click(e):
            command()
        
        btn.bind("<Button-1>", on_click)
        label.bind("<Button-1>", on_click)
        
        # 悬停效果（非活动状态）
        def on_enter(e):
            if not btn._is_active:
                btn.config(bg='#252A45')
                label.config(bg='#252A45')
        
        def on_leave(e):
            if not btn._is_active:
                btn.config(bg='#1E233C')
                label.config(bg='#1E233C')
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        label.bind("<Enter>", on_enter)
        label.bind("<Leave>", on_leave)
        
        return btn
    
    def switch_tab(self, tab_name):
        """切换标签页"""
        if self.current_tab == tab_name:
            return
        
        self.current_tab = tab_name
        
        # 更新标签按钮状态
        is_local = (tab_name == "local")
        
        # 更新本地标签
        self.local_tab_btn._is_active = is_local
        self.local_tab_btn.config(bg='#2D3250' if is_local else '#1E233C')
        self.local_tab_btn._label.config(
            font=("微软雅黑", 12, "bold" if is_local else "normal"),
            fg=self.COLORS['accent'] if is_local else self.COLORS['text_secondary'],
            bg='#2D3250' if is_local else '#1E233C'
        )
        
        # 更新克隆标签
        self.clone_tab_btn._is_active = not is_local
        self.clone_tab_btn.config(bg='#2D3250' if not is_local else '#1E233C')
        self.clone_tab_btn._label.config(
            font=("微软雅黑", 12, "bold" if not is_local else "normal"),
            fg=self.COLORS['accent'] if not is_local else self.COLORS['text_secondary'],
            bg='#2D3250' if not is_local else '#1E233C'
        )
        
        # 显示对应的内容
        self.show_current_tab()
        
        # 更新底部按钮
        if hasattr(self, 'actions_frame'):
            self.update_bottom_buttons()
    
    def show_current_tab(self):
        """显示当前标签页内容"""
        print(f"📄 显示标签页: {self.current_tab}")  # 调试
        
        # 清空当前内容
        for widget in self.tab_content_frame.winfo_children():
            widget.destroy()
        
        # 根据标签显示不同内容
        if self.current_tab == "local":
            print("  ➡️ 创建本地项目表单")  # 调试
            self.create_local_form_card()
        elif self.current_tab == "clone":
            print("  ➡️ 创建克隆仓库表单")  # 调试
            self.create_clone_form_card()
        else:
            print(f"  ❌ 未知标签: {self.current_tab}")  # 调试
    
    def create_local_form_card(self):
        """创建本地项目表单卡片"""
        card = self.create_glass_card(self.tab_content_frame, 350)
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
    
    def create_clone_form_card(self):
        """创建克隆仓库表单卡片"""
        print("🎨 开始创建克隆表单卡片...")  # 调试
        print(f"  容器: {self.tab_content_frame}")  # 调试
        
        # 创建带滚动条的容器
        card_container = tk.Frame(self.tab_content_frame, bg=self.COLORS['bg_top'])
        card_container.pack(fill=tk.BOTH, expand=True, pady=(10, 20), padx=20)
        
        # 创建Canvas用于滚动
        canvas = tk.Canvas(card_container, bg='#252A45', highlightthickness=0)
        scrollbar = tk.Scrollbar(card_container, orient="vertical", command=canvas.yview)
        
        # 创建内容框架
        card = tk.Frame(canvas, bg='#252A45')
        
        # 配置Canvas
        card.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=card, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 打包Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        print(f"  卡片已创建: {card}")  # 调试
        
        content = tk.Frame(card, bg='#252A45')
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
        
        # 标题说明
        desc_frame = tk.Frame(content, bg='#252A45')
        desc_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            desc_frame,
            text="🔗 克隆并发布 GitHub 仓库",
            font=("微软雅黑", 16, "bold"),
            fg='#F093FB',  # 使用亮色
            bg='#252A45'
        ).pack(anchor=tk.W)
        
        tk.Label(
            desc_frame,
            text="自动克隆、修改包名（添加前缀）、推送到你的组织、立即发布",
            font=("微软雅黑", 11),
            fg='#B0B8D4',  # 亮灰色
            bg='#252A45'
        ).pack(anchor=tk.W, pady=(8, 0))
        
        # GitHub URL
        self.create_form_row(
            content,
            "🌐",
            "GitHub 仓库URL",
            "例如: https://github.com/user/awesome-mcp",
            self.clone_url
        )
        
        # 包名前缀
        self.create_form_row(
            content,
            "🏷️",
            "包名前缀",
            "会自动添加到包名前（避免冲突）",
            self.clone_prefix
        )
        
        # 组织名称（共用）
        self.create_form_row(
            content,
            "🏢",
            "目标组织",
            "推送到哪个GitHub组织",
            self.org_name
        )
        
        # 说明文字 - 简化为单行
        info_frame = tk.Frame(content, bg='#1E233C')
        info_frame.pack(fill=tk.X, pady=(15, 20))
        
        tk.Label(
            info_frame,
            text="💡 流程：克隆 → 修改包名 → 推送到组织 → 自动打包发布",
            font=("微软雅黑", 10),
            fg='#4FC3F7',
            bg='#1E233C'
        ).pack()
        
        # 在表单内部添加发布按钮
        btn_frame = tk.Frame(content, bg='#1E233C')
        btn_frame.pack(fill=tk.X, pady=(20, 10))
        
        self.create_gradient_button(
            btn_frame,
            "🔗 克隆并发布",
            self.start_clone_and_publish,
            width=400,
            height=50,
            is_primary=True
        ).pack(expand=True)
    
    
    def create_form_row(self, parent, icon, label, hint, variable, 
                       has_button=False, button_text="", button_cmd=None):
        """创建表单行"""
        # 获取父容器的背景色
        parent_bg = parent.cget('bg')
        
        row = tk.Frame(parent, bg=parent_bg)
        row.pack(fill=tk.X, pady=(0, 20))
        
        # 图标和标签
        label_frame = tk.Frame(row, bg=parent_bg)
        label_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
        
        tk.Label(
            label_frame,
            text=f"{icon}  {label}",  # 合并图标和标签
            font=("微软雅黑", 13, "bold"),
            fg='#FFFFFF',  # 纯白色，更醒目
            bg=parent_bg
        ).pack(side=tk.LEFT)
        
        # 输入框
        entry = self.create_modern_entry(row, variable, hint)
        entry.pack(side=tk.TOP, fill=tk.X, expand=True)
        
        # 可选按钮
        if has_button:
            btn = self.create_gradient_button(
                row,
                button_text,
                button_cmd,
                width=100,
                is_secondary=True
            )
            btn.pack(side=tk.TOP, pady=(8, 0))
        
        return row
    
    def create_bottom_actions(self):
        """创建底部操作区"""
        self.actions_frame = tk.Frame(self.content_frame, bg=self.COLORS['bg_top'])
        self.actions_frame.pack(fill=tk.X)
        
        # 保存按钮引用，以便动态更新
        self.update_bottom_buttons()
    
    def update_bottom_buttons(self):
        """根据当前标签页更新底部按钮"""
        # 清空现有按钮
        for widget in self.actions_frame.winfo_children():
            widget.destroy()
        
        # 根据当前标签页显示不同按钮
        if self.current_tab == "local":
            # 本地项目模式
            main_btn = self.create_gradient_button(
                self.actions_frame,
                "🚀 开始发布",
                self.start_publish,
                width=300,
                height=56,
                is_primary=True
            )
            main_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
            
            # 设置按钮
            settings_btn = self.create_gradient_button(
                self.actions_frame,
                "⚙️ 设置",
                self.open_settings,
                width=120,
                height=56
            )
            settings_btn.pack(side=tk.LEFT)
        else:
            # 克隆仓库模式 - 只显示克隆按钮，更大更显眼
            main_btn = self.create_gradient_button(
                self.actions_frame,
                "🔗 克隆并发布",
                self.start_clone_and_publish,
                width=400,
                height=56,
                is_primary=True
            )
            main_btn.pack(expand=True, fill=tk.X)
    
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
    
    def start_clone_and_publish(self):
        """开始克隆并发布"""
        # 验证输入
        if not self.github_token:
            messagebox.showwarning("警告", "请先配置 GitHub Token")
            return
        
        clone_url = self.clone_url.get().strip()
        if not clone_url:
            messagebox.showwarning("警告", "请输入GitHub仓库URL")
            return
        
        # 验证URL格式
        if not ('github.com' in clone_url or 'github' in clone_url):
            messagebox.showwarning("警告", "请输入有效的GitHub仓库URL")
            return
        
        prefix = self.clone_prefix.get().strip()
        if not prefix:
            messagebox.showwarning("警告", "请输入包名前缀")
            return
        
        org_name = self.org_name.get().strip()
        if not org_name:
            messagebox.showwarning("警告", "请输入目标组织名称")
            return
        
        # 确认操作
        confirm_msg = (
            f"即将执行以下操作：\n\n"
            f"1. 克隆仓库: {clone_url}\n"
            f"2. 修改包名（添加前缀: {prefix}）\n"
            f"3. 推送到组织: {org_name}\n"
            f"4. 自动打包并发布\n\n"
            f"是否继续？"
        )
        
        if not messagebox.askyesno("确认", confirm_msg):
            return
        
        # 显示进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("克隆并发布")
        progress_window.geometry("600x400")
        progress_window.configure(bg=self.COLORS['bg_top'])
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # 居中显示
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (400 // 2)
        progress_window.geometry(f'600x400+{x}+{y}')
        
        # 标题
        title_label = tk.Label(
            progress_window,
            text="🚀 正在克隆并发布...",
            font=("微软雅黑", 16, "bold"),
            fg=self.COLORS['text_primary'],
            bg=self.COLORS['bg_top']
        )
        title_label.pack(pady=(20, 10))
        
        # 进度条
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            progress_window,
            variable=progress_var,
            maximum=100,
            length=500,
            mode='determinate'
        )
        progress_bar.pack(pady=20)
        
        # 日志文本框
        log_frame = tk.Frame(progress_window, bg=self.COLORS['bg_top'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        log_text = tk.Text(
            log_frame,
            font=("Consolas", 9),
            fg=self.COLORS['text_secondary'],
            bg='#1E233C',
            wrap=tk.WORD,
            bd=0
        )
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.config(yscrollcommand=scrollbar.set)
        
        def log_message(msg):
            """添加日志"""
            log_text.insert(tk.END, msg + "\n")
            log_text.see(tk.END)
            log_text.update()
        
        def update_progress(value):
            """更新进度"""
            progress_var.set(value)
            progress_window.update()
        
        # 在后台线程执行克隆和发布
        def clone_and_publish_thread():
            try:
                log_message(f"{'='*60}")
                log_message(f"开始克隆并发布工作流程")
                log_message(f"{'='*60}")
                log_message(f"源仓库: {clone_url}")
                log_message(f"包名前缀: {prefix}")
                log_message(f"目标组织: {org_name}")
                log_message("")
                
                # 创建配置管理器和工作流执行器
                config_mgr = UnifiedConfigManager()
                executor = WorkflowExecutor(config_mgr)
                
                # 设置进度回调
                executor.set_progress_callback(update_progress)
                
                # 重定向输出到GUI
                import io
                import contextlib
                
                output_buffer = io.StringIO()
                
                # 执行克隆和发布
                with contextlib.redirect_stdout(output_buffer):
                    result = executor.workflow_clone_and_publish(
                        github_url=clone_url,
                        prefix=prefix
                    )
                
                # 显示输出
                output = output_buffer.getvalue()
                if output:
                    log_message(output)
                
                # 检查结果
                if result['success']:
                    log_message("")
                    log_message(f"{'='*60}")
                    log_message("✅ 克隆并发布成功！")
                    log_message(f"{'='*60}")
                    log_message(f"新包名: {result.get('package_name', 'N/A')}")
                    log_message(f"GitHub仓库: {result.get('github_repo_url', 'N/A')}")
                    if result.get('template_id'):
                        log_message(f"EMCP模板ID: {result['template_id']}")
                    
                    # 延迟关闭窗口
                    progress_window.after(3000, progress_window.destroy)
                    
                    # 显示成功消息
                    self.root.after(3100, lambda: messagebox.showinfo(
                        "成功",
                        f"克隆并发布完成！\n\n"
                        f"包名: {result.get('package_name')}\n"
                        f"GitHub: {result.get('github_repo_url')}"
                    ))
                else:
                    log_message("")
                    log_message("❌ 克隆并发布失败")
                    log_message(f"错误: {result.get('error', '未知错误')}")
                    
                    # 显示错误
                    self.root.after(0, lambda: messagebox.showerror(
                        "失败",
                        f"克隆并发布失败:\n{result.get('error', '未知错误')}"
                    ))
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_trace = traceback.format_exc()
                
                log_message("")
                log_message("❌ 发生异常")
                log_message(f"错误: {error_msg}")
                log_message("")
                log_message("详细错误:")
                log_message(error_trace)
                
                self.root.after(0, lambda: messagebox.showerror(
                    "异常",
                    f"执行过程中发生异常:\n{error_msg}"
                ))
        
        # 启动后台线程
        thread = threading.Thread(target=clone_and_publish_thread, daemon=True)
        thread.start()
    
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


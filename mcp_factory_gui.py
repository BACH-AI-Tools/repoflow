#!/usr/bin/env python3
"""
MCP工厂 - 流程化发布平台
展示清晰的步骤流程和执行进度
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
import sys
import time
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

# 设置 UTF-8 编码
if sys.platform == 'win32':
    if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from src.unified_config_manager import UnifiedConfigManager
from src.workflow_executor import WorkflowExecutor
from settings_window import SettingsWindow


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 跳过


class LogHandler:
    """日志处理器 - 重定向输出到 GUI"""
    def __init__(self, text_widget, is_error=False):
        self.text_widget = text_widget
        self.is_error = is_error
    
    def write(self, message):
        """写入日志"""
        if self.text_widget and message.strip():
            try:
                tag = "ERROR" if self.is_error else "INFO"
                self.text_widget.insert(tk.END, message, tag)
                self.text_widget.see(tk.END)
                self.text_widget.update()
            except:
                pass
    
    def flush(self):
        pass


class Step:
    """步骤类"""
    def __init__(self, id: str, title: str, description: str = "", parent: Optional[str] = None):
        self.id = id
        self.title = title
        self.description = description
        self.parent = parent
        self.status = StepStatus.PENDING
        self.progress = 0  # 0-100
        self.logs: List[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.children: List[str] = []  # 子步骤ID列表
    
    def add_log(self, message: str, level: str = "INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
    
    def start(self):
        """开始执行"""
        self.status = StepStatus.RUNNING
        self.start_time = datetime.now()
        self.progress = 0
        self.add_log(f"开始执行: {self.title}")
    
    def complete(self, success: bool = True):
        """完成执行"""
        self.status = StepStatus.SUCCESS if success else StepStatus.FAILED
        self.end_time = datetime.now()
        self.progress = 100
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        status_text = "成功" if success else "失败"
        self.add_log(f"执行{status_text} (耗时: {duration:.2f}秒)", "SUCCESS" if success else "ERROR")


class StepTreeItem(ttk.Frame):
    """步骤树项目组件"""
    
    STATUS_COLORS = {
        StepStatus.PENDING: "#8E8E93",    # Apple 灰色
        StepStatus.RUNNING: "#007AFF",    # Apple 蓝色
        StepStatus.SUCCESS: "#34C759",    # Apple 绿色
        StepStatus.FAILED: "#FF3B30",     # Apple 红色
        StepStatus.SKIPPED: "#FF9500",    # Apple 橙色
    }
    
    STATUS_ICONS = {
        StepStatus.PENDING: "⏸",
        StepStatus.RUNNING: "▶",
        StepStatus.SUCCESS: "✓",
        StepStatus.FAILED: "✗",
        StepStatus.SKIPPED: "⊘",
    }
    
    def __init__(self, parent, step: Step, on_click, level: int = 0):
        super().__init__(parent)
        self.step = step
        self.on_click = on_click
        self.level = level
        self.expanded = True
        
        self.configure(style='StepItem.TFrame')
        
        # 主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.X, padx=(level * 20, 0))
        
        # 步骤信息框架
        info_frame = ttk.Frame(main_container, style='StepInfo.TFrame')
        info_frame.pack(fill=tk.X, pady=2)
        
        # 创建可点击的区域 - Apple 风格
        self.click_frame = tk.Frame(info_frame, cursor="hand2", bg="#FAFAFA")
        self.click_frame.pack(fill=tk.X, expand=True)
        
        # 绑定点击事件到 click_frame 和所有子组件
        def bind_click_recursive(widget):
            """递归绑定点击事件"""
            widget.bind("<Button-1>", lambda e: self.on_click(self.step))
            for child in widget.winfo_children():
                bind_click_recursive(child)
        
        bind_click_recursive(self.click_frame)
        
        # Apple 风格悬停效果
        self.click_frame.bind("<Enter>", lambda e: self.click_frame.config(bg="#F5F5F7"))
        self.click_frame.bind("<Leave>", lambda e: self.click_frame.config(bg="#FAFAFA"))
        
        # 内容框架 - 设置背景
        content_frame = tk.Frame(self.click_frame, bg="#FAFAFA")
        content_frame.pack(fill=tk.X, padx=12, pady=8)
        
        # 左侧：展开/折叠按钮（如果有子步骤）- Apple 风格
        left_frame = tk.Frame(content_frame, bg="#FAFAFA")
        left_frame.pack(side=tk.LEFT, padx=(0, 12))
        
        if step.children:
            self.expand_btn = tk.Label(left_frame, text="▼", cursor="hand2",
                                      bg="#FAFAFA", fg="#8E8E93",
                                      font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10))
            self.expand_btn.pack(side=tk.LEFT)
            # 绑定展开/折叠事件，并阻止事件冒泡
            self.expand_btn.bind("<Button-1>", lambda e: (self.toggle_expand(), "break")[1])
        else:
            tk.Label(left_frame, text="  ", bg="#FAFAFA").pack(side=tk.LEFT)
        
        # 状态图标 - Apple 风格
        self.status_label = tk.Label(left_frame, text=self.STATUS_ICONS[step.status], 
                                     font=("Apple Color Emoji", 14) if sys.platform == 'darwin' else ("Segoe UI Emoji", 14),
                                     bg="#FAFAFA", fg=self.STATUS_COLORS[step.status])
        self.status_label.pack(side=tk.LEFT, padx=6)
        
        # 中间：标题和描述 - Apple 风格
        middle_frame = tk.Frame(content_frame, bg="#FAFAFA")
        middle_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.title_label = tk.Label(middle_frame, text=step.title, 
                                    font=('SF Pro Text', 11, 'bold') if sys.platform == 'darwin' else ("微软雅黑", 11, "bold"),
                                    fg="#1D1D1F", bg="#FAFAFA")
        self.title_label.pack(anchor=tk.W)
        
        if step.description:
            self.desc_label = tk.Label(middle_frame, text=step.description, 
                                       font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10),
                                       fg="#6E6E73", bg="#FAFAFA")
            self.desc_label.pack(anchor=tk.W, pady=(2, 0))
        
        # 右侧：进度条 - Apple 风格
        right_frame = tk.Frame(content_frame, bg="#FAFAFA")
        right_frame.pack(side=tk.RIGHT, padx=(12, 0))
        
        self.progress_var = tk.IntVar(value=step.progress)
        self.progress_bar = ttk.Progressbar(right_frame, length=120, 
                                           variable=self.progress_var, 
                                           mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=6)
        
        self.progress_label = tk.Label(right_frame, text=f"{step.progress}%", 
                                       font=('SF Pro Text', 10, 'bold') if sys.platform == 'darwin' else ("微软雅黑", 10, "bold"),
                                       fg="#007AFF", bg="#FAFAFA", width=4)
        self.progress_label.pack(side=tk.LEFT)
        
        # 子步骤容器 - Apple 风格
        self.children_frame = tk.Frame(self, bg="#FFFFFF")
        if self.expanded:
            self.children_frame.pack(fill=tk.X)
    
    def toggle_expand(self):
        """切换展开/折叠"""
        self.expanded = not self.expanded
        if hasattr(self, 'expand_btn'):
            self.expand_btn.config(text="▼" if self.expanded else "▶")
        
        if self.expanded:
            self.children_frame.pack(fill=tk.X)
        else:
            self.children_frame.pack_forget()
    
    def update_status(self):
        """更新状态显示"""
        self.status_label.config(text=self.STATUS_ICONS[self.step.status])
        color = self.STATUS_COLORS[self.step.status]
        self.status_label.config(foreground=color)
        self.title_label.config(foreground=color)
        
        # 更新进度
        self.progress_var.set(self.step.progress)
        self.progress_label.config(text=f"{self.step.progress}%")


class MCPFactoryGUI:
    """MCP工厂主界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🏭 MCP 工厂 - 现代化发布平台")
        
        # 窗口大小和居中 - 增加高度以显示所有内容
        window_width = 1300
        window_height = 900  # 增加高度从850到900
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # 设置最小窗口大小，确保按钮可见
        self.root.minsize(1200, 800)
        
        # 设置 Apple 风格的浅色背景
        self.root.configure(bg='#F5F5F7')
        
        # 配置管理器
        self.config_mgr = UnifiedConfigManager()
        
        # 工作流执行器
        self.executor = WorkflowExecutor(self.config_mgr)
        
        # 步骤管理
        self.steps: Dict[str, Step] = {}
        self.step_widgets: Dict[str, StepTreeItem] = {}
        self.current_selected_step: Optional[Step] = None
        
        # 设置样式
        self.setup_styles()
        
        # 创建UI
        self.create_widgets()
        
        # 初始化步骤
        self.init_workflow_steps()
    
    def reload_config(self):
        """重新加载配置"""
        try:
            config = self.config_mgr.load_config()
            # 更新执行器的配置
            self.executor = WorkflowExecutor(self.config_mgr)
            print("✅ 配置已重新加载")
        except Exception as e:
            print(f"⚠️ 重新加载配置时出错: {e}")
    
    def setup_styles(self):
        """设置 Apple 风格的亮色主题"""
        style = ttk.Style()
        style.theme_use('aqua' if sys.platform == 'darwin' else 'clam')
        
        # Apple 亮色主题配色
        bg_light = '#F5F5F7'  # 浅灰背景
        card_bg = '#FFFFFF'  # 纯白卡片
        card_hover = '#FAFAFA'  # 悬停背景
        primary = '#007AFF'  # 系统蓝色
        primary_dark = '#0051D5'  # 深蓝
        accent = '#FF9500'  # 橙色强调
        success = '#34C759'  # 绿色
        text = '#1D1D1F'  # 深灰文字
        text_secondary = '#6E6E73'  # 次要文字
        border = '#D2D2D7'  # 边框
        
        # 标题样式
        style.configure('Title.TLabel', 
                       font=('SF Pro Display', 18, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 18, 'bold'), 
                       foreground=text,
                       background=card_bg)
        
        style.configure('Subtitle.TLabel', 
                       font=('SF Pro Text', 13, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 13, 'bold'),
                       foreground=text,
                       background=card_bg)
        
        style.configure('Info.TLabel', 
                       font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
                       foreground=text_secondary,
                       background=card_bg)
        
        # 框架样式
        style.configure('Card.TFrame', 
                       background=card_bg,
                       relief='flat')
        
        style.configure('StepItem.TFrame', 
                       background=card_bg)
        
        # 按钮样式 - Apple 风格
        style.configure('Big.TButton', 
                       font=('SF Pro Text', 13, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 13, 'bold'), 
                       padding=15,
                       background=primary,
                       foreground='#FFFFFF')
        
        style.map('Big.TButton',
                 background=[('active', primary_dark), ('pressed', primary_dark)])
        
        # 进度条样式 - Apple 风格
        style.configure('TProgressbar',
                       background=primary,
                       troughcolor='#E5E5EA',
                       borderwidth=0,
                       thickness=6)
    
    def create_widgets(self):
        """创建 Apple 风格的现代化UI"""
        # Apple 风格浅色背景
        self.root.configure(bg='#F5F5F7')
        
        # 顶部导航栏 - macOS 风格
        toolbar = tk.Frame(self.root, bg='#FFFFFF', height=70)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # 添加底部阴影
        shadow = tk.Frame(toolbar, bg='#E5E5EA', height=1)
        shadow.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 左侧 - Logo 和标题
        left_section = tk.Frame(toolbar, bg='#FFFFFF')
        left_section.pack(side=tk.LEFT, padx=30, pady=15)
        
        # Logo 图标
        logo_label = tk.Label(
            left_section,
            text="🏭",
            font=("Apple Color Emoji", 32) if sys.platform == 'darwin' else ("Segoe UI Emoji", 32),
            bg='#FFFFFF'
        )
        logo_label.pack(side=tk.LEFT, padx=(0, 12))
        
        # 标题区
        title_frame = tk.Frame(left_section, bg='#FFFFFF')
        title_frame.pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text="MCP 工厂",
            font=('SF Pro Display', 24, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 24, 'bold'),
            fg='#1D1D1F',
            bg='#FFFFFF'
        ).pack(anchor=tk.W)
        
        tk.Label(
            title_frame,
            text="现代化发布平台 • 3分钟完成全流程",
            font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11),
            fg='#6E6E73',
            bg='#FFFFFF'
        ).pack(anchor=tk.W)
        
        # 右侧 - 按钮
        right_section = tk.Frame(toolbar, bg='#FFFFFF')
        right_section.pack(side=tk.RIGHT, padx=30, pady=15)
        
        self.create_toolbar_button(right_section, "⚙️ 设置", self.open_settings)
        self.create_toolbar_button(right_section, "📖 帮助", self.show_help)
        
        # 主容器 - 三栏布局（浅色背景）
        main_container_bg = tk.Frame(self.root, bg='#F5F5F7')
        main_container_bg.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        main_container = ttk.PanedWindow(main_container_bg, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：输入和控制区域（30%）
        left_panel = self.create_left_panel()
        main_container.add(left_panel, weight=30)
        
        # 中间：步骤流程区域（40%）
        middle_panel = self.create_middle_panel()
        main_container.add(middle_panel, weight=40)
        
        # 右侧：日志查看区域（30%）- 使用选项卡
        right_panel = self.create_right_panel_with_tabs()
        main_container.add(right_panel, weight=30)
        
        # 底部状态栏 - Apple 风格
        status_frame = tk.Frame(self.root, bg='#FFFFFF', height=52)
        status_frame.pack(fill=tk.X)
        status_frame.pack_propagate(False)
        
        # 顶部分隔线
        tk.Frame(status_frame, bg='#E5E5EA', height=1).pack(side=tk.TOP, fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame, 
            text="⚡ 就绪",
            font=('SF Pro Text', 11) if sys.platform == 'darwin' else ("微软雅黑", 11),
            fg='#34C759',  # Apple 绿色
            bg='#FFFFFF'
        )
        self.status_label.pack(side=tk.LEFT, padx=30, pady=15)
        
        # 整体进度条 - Apple 风格
        progress_container = tk.Frame(status_frame, bg='#FFFFFF')
        progress_container.pack(side=tk.RIGHT, padx=30, pady=15)
        
        tk.Label(
            progress_container,
            text="整体进度",
            font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10),
            fg='#6E6E73',
            bg='#FFFFFF'
        ).pack(side=tk.LEFT, padx=(0, 12))
        
        self.overall_progress_var = tk.IntVar(value=0)
        self.overall_progress = ttk.Progressbar(
            progress_container, 
            length=300, 
            variable=self.overall_progress_var,
            mode='determinate'
        )
        self.overall_progress.pack(side=tk.LEFT, padx=(0, 12))
        
        self.overall_progress_label = tk.Label(
            progress_container, 
            text="0%",
            font=('SF Pro Text', 12, 'bold') if sys.platform == 'darwin' else ("微软雅黑", 12, "bold"),
            fg='#007AFF',  # Apple 蓝色
            bg='#FFFFFF',
            width=4
        )
        self.overall_progress_label.pack(side=tk.LEFT)
    
    def create_toolbar_button(self, parent, text, command):
        """创建 Apple 风格工具栏按钮"""
        btn = tk.Button(
            parent,
            text=text,
            font=('SF Pro Text', 11) if sys.platform == 'darwin' else ("微软雅黑", 11),
            fg='#007AFF',  # Apple 蓝色
            bg='#FFFFFF',
            activebackground='#F5F5F7',
            activeforeground='#0051D5',
            bd=0,
            cursor="hand2",
            command=command,
            padx=16,
            pady=8,
            relief=tk.FLAT
        )
        btn.pack(side=tk.LEFT, padx=6)
        
        # Apple 风格悬停效果
        def on_enter(e):
            btn.configure(bg='#F5F5F7')
        
        def on_leave(e):
            btn.configure(bg='#FFFFFF')
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def create_left_panel(self):
        """创建左侧面板 - Apple 风格白色卡片，带滚动"""
        panel = tk.Frame(self.root, bg='#F5F5F7')
        
        # 创建Canvas和滚动条用于滚动内容
        canvas = tk.Canvas(panel, bg='#F5F5F7', highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        
        # 可滚动框架
        scrollable_panel = tk.Frame(canvas, bg='#F5F5F7')
        scrollable_panel.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_panel, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        # 整合为一个卡片 - 减少卡片数量
        main_card = tk.Frame(scrollable_panel, bg='#FFFFFF', highlightbackground='#D2D2D7', highlightthickness=1)
        main_card.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # 内容区 - 舒适布局
        content = tk.Frame(main_card, bg='#FFFFFF')
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)
        
        # 标题
        tk.Label(
            content, 
            text="📋 项目配置", 
            font=('SF Pro Display', 14, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 14, 'bold'),
            foreground='#1D1D1F',
            background='#FFFFFF'
        ).pack(anchor=tk.W, pady=(0, 18))
        
        # 项目路径
        tk.Label(content, text="📁 项目文件夹", 
                font=('SF Pro Text', 10, 'bold') if sys.platform == 'darwin' else ("微软雅黑", 10, 'bold'),
                fg='#1D1D1F', bg='#FFFFFF').pack(anchor=tk.W, pady=(0, 6))
        
        self.project_path_var = tk.StringVar()
        path_frame = tk.Frame(content, bg='#FFFFFF')
        path_frame.pack(fill=tk.X, pady=(0, 15))
        
        path_entry = tk.Entry(path_frame, textvariable=self.project_path_var,
                             font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10), 
                             bd=1, bg='#F5F5F7',
                             fg='#1D1D1F', insertbackground='#007AFF',
                             relief=tk.SOLID, highlightthickness=0)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=10)
        
        browse_btn = tk.Button(path_frame, text="📂", 
                              font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10),
                              fg='#007AFF', bg='#F5F5F7', bd=1, cursor="hand2",
                              relief=tk.SOLID,
                              command=self.browse_project_folder, padx=11, pady=8)
        browse_btn.pack(side=tk.LEFT, padx=(6, 0))
        
        # 仓库名称
        tk.Label(content, text="📦 仓库名称", 
                font=('SF Pro Text', 10, 'bold') if sys.platform == 'darwin' else ("微软雅黑", 10, 'bold'),
                fg='#1D1D1F', bg='#FFFFFF').pack(anchor=tk.W, pady=(0, 6))
        
        self.repo_name_var = tk.StringVar()
        repo_entry = tk.Entry(content, textvariable=self.repo_name_var,
                             font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10), 
                             bd=1, bg='#F5F5F7',
                             fg='#1D1D1F', insertbackground='#007AFF',
                             relief=tk.SOLID, highlightthickness=0)
        repo_entry.pack(fill=tk.X, pady=(0, 15), ipady=8, ipadx=10)
        
        # 版本号
        tk.Label(content, text="🏷️ 版本号", 
                font=('SF Pro Text', 10, 'bold') if sys.platform == 'darwin' else ("微软雅黑", 10, 'bold'),
                fg='#1D1D1F', bg='#FFFFFF').pack(anchor=tk.W, pady=(0, 6))
        
        self.version_var = tk.StringVar(value="1.0.0")
        version_entry = tk.Entry(content, textvariable=self.version_var,
                                font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10), 
                                bd=1, bg='#F5F5F7',
                                fg='#1D1D1F', insertbackground='#007AFF',
                                relief=tk.SOLID, highlightthickness=0)
        version_entry.pack(fill=tk.X, pady=(0, 20), ipady=8, ipadx=10)
        
        # 项目信息显示
        self.project_info_label = tk.Label(
            content, 
            text="", 
            font=('SF Pro Text', 9) if sys.platform == 'darwin' else ("微软雅黑", 9),
            foreground='#6E6E73',
            background='#FFFFFF',
            wraplength=260,
            justify=tk.LEFT
        )
        self.project_info_label.pack(anchor=tk.W, pady=(0, 20))
        
        # 分隔线
        tk.Frame(content, bg='#E5E5EA', height=1).pack(fill=tk.X, pady=(10, 20))
        
        # 大按钮 - Apple 风格
        start_btn = tk.Button(
            content,
            text="🏭 开始生产",
            font=('SF Pro Text', 13, 'bold') if sys.platform == 'darwin' else ("微软雅黑", 13, "bold"),
            fg='#FFFFFF',
            bg='#007AFF',
            activebackground='#0051D5',
            activeforeground='#FFFFFF',
            bd=0,
            cursor="hand2",
            command=self.start_workflow,
            relief=tk.FLAT
        )
        start_btn.pack(fill=tk.X, pady=(0, 10), ipady=13)
        
        # 悬停效果
        def on_enter(e):
            start_btn.configure(bg='#0051D5')
        
        def on_leave(e):
            start_btn.configure(bg='#007AFF')
        
        start_btn.bind("<Enter>", on_enter)
        start_btn.bind("<Leave>", on_leave)
        
        # 次要按钮
        btn_container = tk.Frame(content, bg='#FFFFFF')
        btn_container.pack(fill=tk.X, pady=(0, 5))
        
        pause_btn = tk.Button(btn_container, text="⏸ 暂停",
                             font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10),
                             fg='#007AFF', bg='#F5F5F7', bd=1, cursor="hand2",
                             relief=tk.SOLID, command=self.pause_workflow, padx=10, pady=7)
        pause_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        reset_btn = tk.Button(btn_container, text="🔄 重新开始",
                             font=('SF Pro Text', 10) if sys.platform == 'darwin' else ("微软雅黑", 10),
                             fg='#007AFF', bg='#F5F5F7', bd=1, cursor="hand2",
                             relief=tk.SOLID, command=self.reset_workflow, padx=10, pady=7)
        reset_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 打包滚动区域
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return panel
    
    def create_middle_panel(self):
        """创建中间步骤流程面板 - Apple 风格"""
        panel = tk.Frame(self.root, bg='#F5F5F7')
        
        # 标题卡片 - Apple 风格
        header = tk.Frame(panel, bg='#FFFFFF', highlightbackground='#D2D2D7', highlightthickness=1)
        header.pack(fill=tk.X, padx=8, pady=(8, 0))
        
        tk.Label(
            header, 
            text="📋 执行流程", 
            font=('SF Pro Display', 16, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 16, 'bold'),
            foreground='#1D1D1F',
            background='#FFFFFF'
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        # 滚动容器
        scroll_container = tk.Frame(panel, bg='#FFFFFF', highlightbackground='#D2D2D7', highlightthickness=1)
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        # 滚动区域 - 使用标准滚动条
        canvas = tk.Canvas(scroll_container, bg='#FFFFFF', highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        
        self.steps_frame = tk.Frame(canvas, bg='#FFFFFF')
        
        self.steps_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.steps_frame, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        panel.bind("<Enter>", bind_mousewheel)
        panel.bind("<Leave>", unbind_mousewheel)
        
        # 绑定窗口大小变化
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(
            canvas.find_withtag("all")[0], width=e.width) if canvas.find_withtag("all") else None)
        
        # 布局
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return panel
    
    def create_right_panel_with_tabs(self):
        """创建右侧全局日志面板 - Apple 风格"""
        panel = tk.Frame(self.root, bg='#F5F5F7')
        
        # 标题栏 - Apple 风格
        header = tk.Frame(panel, bg='#FFFFFF', highlightbackground='#D2D2D7', highlightthickness=1)
        header.pack(fill=tk.X, padx=8, pady=(8, 0))
        
        tk.Label(
            header, 
            text="📋 实时日志", 
            font=('SF Pro Display', 16, 'bold') if sys.platform == 'darwin' else ("微软雅黑", 16, "bold"),
            foreground='#1D1D1F',
            background='#FFFFFF'
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        # 工具按钮 - Apple 风格
        tool_frame = tk.Frame(header, bg='#FFFFFF')
        tool_frame.pack(side=tk.RIGHT, padx=20)
        
        clear_btn = tk.Button(tool_frame, text="🗑️", 
                             font=('SF Pro Text', 11) if sys.platform == 'darwin' else ("微软雅黑", 11),
                             fg='#FF3B30', bg='#FFFFFF', bd=0, cursor="hand2",
                             command=self.clear_global_logs)
        clear_btn.pack(side=tk.LEFT, padx=4)
        
        scroll_btn = tk.Button(tool_frame, text="⬇️", 
                              font=('SF Pro Text', 11) if sys.platform == 'darwin' else ("微软雅黑", 11),
                              fg='#007AFF', bg='#FFFFFF', bd=0, cursor="hand2",
                              command=lambda: self.global_log_text.see(tk.END))
        scroll_btn.pack(side=tk.LEFT, padx=4)
        
        # 全局日志文本区域 - Apple 风格
        log_frame = tk.Frame(panel, bg='#FFFFFF', highlightbackground='#D2D2D7', highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        # 使用Text + Scrollbar 而不是ScrolledText，以便自定义滚动条
        text_container = tk.Frame(log_frame, bg='#FAFAFA')
        text_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        self.global_log_text = tk.Text(
            text_container, 
            wrap=tk.WORD, 
            font=("SF Mono", 10) if sys.platform == 'darwin' else ("Consolas", 10),
            bg="#FAFAFA",  # 浅灰背景
            fg="#1D1D1F",  # 深色文字
            insertbackground='#007AFF',
            bd=0
        )
        
        # Apple风格滚动条
        scrollbar = ttk.Scrollbar(text_container, orient="vertical", command=self.global_log_text.yview)
        self.global_log_text.config(yscrollcommand=scrollbar.set)
        
        self.global_log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置 Apple 风格标签
        self.global_log_text.tag_config("INFO", foreground="#007AFF")  # Apple 蓝
        self.global_log_text.tag_config("SUCCESS", foreground="#34C759")  # Apple 绿
        self.global_log_text.tag_config("WARNING", foreground="#FF9500")  # Apple 橙
        self.global_log_text.tag_config("ERROR", foreground="#FF3B30")  # Apple 红
        self.global_log_text.tag_config("DEBUG", foreground="#8E8E93")  # Apple 灰
        
        # 显示初始信息
        self.global_log_text.insert(tk.END, "🏭 MCP 工厂 - 实时日志\n", "SUCCESS")
        self.global_log_text.insert(tk.END, "=" * 50 + "\n", "DEBUG")
        self.global_log_text.insert(tk.END, "\n等待开始生产...\n\n", "INFO")
        
        # 重定向 stdout 和 stderr
        sys.stdout = LogHandler(self.global_log_text)
        sys.stderr = LogHandler(self.global_log_text, is_error=True)
        
        # 绑定鼠标滚轮到整个面板
        def _on_mousewheel(event):
            self.global_log_text.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def bind_mousewheel(event):
            panel.bind_all("<MouseWheel>", _on_mousewheel)
        
        def unbind_mousewheel(event):
            panel.unbind_all("<MouseWheel>")
        
        panel.bind("<Enter>", bind_mousewheel)
        panel.bind("<Leave>", unbind_mousewheel)
        
        return panel
    
    def clear_global_logs(self):
        """清空全局日志"""
        self.global_log_text.delete(1.0, tk.END)
        self.global_log_text.insert(tk.END, "🏭 MCP 工厂 - 实时日志\n", "SUCCESS")
        self.global_log_text.insert(tk.END, "=" * 50 + "\n", "DEBUG")
        self.global_log_text.insert(tk.END, "\n日志已清空\n\n", "INFO")
    
    def init_workflow_steps(self):
        """初始化工作流步骤"""
        # 定义完整的工作流（简化版 - 只保留主要步骤）
        steps_def = [
            # GitHub 发布流程
            ("github", "📦 GitHub 发布", "将项目发布到 GitHub + PyPI/NPM"),
            ("github.scan", "扫描项目", "检测项目类型和敏感信息", "github"),
            ("github.create_repo", "创建仓库", "在 GitHub 创建仓库", "github"),
            ("github.generate_pipeline", "生成 Pipeline", "生成 CI/CD 工作流", "github"),
            ("github.push", "推送代码", "推送代码到 GitHub", "github"),
            ("github.publish", "触发发布", "创建Tag触发自动发布", "github"),
            
            # EMCP 发布流程
            ("emcp", "🌐 EMCP 发布", "将 MCP 发布到 EMCP 平台"),
            ("emcp.fetch", "获取包信息", "获取已发布的包信息", "emcp"),
            ("emcp.generate", "AI 生成模板", "生成三语言描述", "emcp"),
            ("emcp.logo", "生成 Logo", "即梦 API 生成 Logo", "emcp"),
            ("emcp.publish", "发布模板", "发布到 EMCP 平台", "emcp"),
            
            # 测试流程
            ("test", "🧪 功能测试", "测试 MCP 工具和 Agent"),
            ("test.mcp", "MCP 测试", "测试 MCP 工具可用性", "test"),
            ("test.agent", "Agent 测试", "创建 Agent 并发布", "test"),
            ("test.chat", "对话测试", "SignalR 对话测试", "test"),
        ]
        
        # 创建步骤对象
        for step_def in steps_def:
            step_id = step_def[0]
            title = step_def[1]
            description = step_def[2]
            parent = step_def[3] if len(step_def) > 3 else None
            
            step = Step(step_id, title, description, parent)
            self.steps[step_id] = step
            
            # 建立父子关系
            if parent and parent in self.steps:
                self.steps[parent].children.append(step_id)
        
        # 渲染步骤树
        self.render_step_tree()
    
    def render_step_tree(self):
        """渲染步骤树"""
        # 清空现有内容
        for widget in self.steps_frame.winfo_children():
            widget.destroy()
        
        self.step_widgets.clear()
        
        # 渲染根步骤
        root_steps = [s for s in self.steps.values() if s.parent is None]
        for step in root_steps:
            self.render_step_item(step, self.steps_frame, 0)
    
    def render_step_item(self, step: Step, parent_frame, level: int):
        """渲染步骤项"""
        # 创建步骤组件
        step_widget = StepTreeItem(parent_frame, step, self.on_step_clicked, level)
        step_widget.pack(fill=tk.X, pady=1)
        
        self.step_widgets[step.id] = step_widget
        
        # 渲染子步骤
        for child_id in step.children:
            if child_id in self.steps:
                child_step = self.steps[child_id]
                self.render_step_item(child_step, step_widget.children_frame, level + 1)
    
    def on_step_clicked(self, step: Step):
        """步骤被点击 - 在全局日志中显示步骤信息"""
        self.current_selected_step = step
        
        # 在全局日志显示步骤信息
        print(f"\n{'='*50}")
        print(f"📌 查看步骤: {step.title}")
        print(f"{'='*50}")
        print(f"说明: {step.description}")
        print(f"状态: {step.status.value}")
        print(f"进度: {step.progress}%")
        
        if step.logs:
            print(f"\n执行日志:")
            for log in step.logs:
                print(f"  {log}")
        else:
            if step.status == StepStatus.PENDING:
                print(f"\n⏸ 此步骤尚未开始执行")
            elif step.status == StepStatus.RUNNING:
                print(f"\n▶ 此步骤正在执行中...")
        
        print(f"{'='*50}\n")
    
    def update_overall_progress(self):
        """更新整体进度"""
        if not self.steps:
            return
        
        total = len(self.steps)
        completed = len([s for s in self.steps.values() 
                        if s.status in [StepStatus.SUCCESS, StepStatus.SKIPPED]])
        
        progress = int((completed / total) * 100) if total > 0 else 0
        self.overall_progress_var.set(progress)
        self.overall_progress_label.config(text=f"{progress}%")
    
    def start_workflow(self):
        """开始工作流"""
        # 验证输入
        project_path = self.project_path_var.get().strip()
        repo_name = self.repo_name_var.get().strip()
        version = self.version_var.get().strip()
        
        if not project_path:
            messagebox.showwarning("警告", "请选择项目文件夹", parent=self.root)
            return
        
        if not repo_name:
            messagebox.showwarning("警告", "请输入仓库名称", parent=self.root)
            return
        
        # 验证仓库名格式
        if repo_name.startswith('.'):
            messagebox.showerror("错误", 
                f"仓库名不能以点开头：{repo_name}\n\n"
                f"请修改为有效的仓库名，例如：\n"
                f"• mcp-server\n"
                f"• my-project", 
                parent=self.root)
            return
        
        if not version:
            messagebox.showwarning("警告", "请输入版本号", parent=self.root)
            return
        
        # 验证配置 - 重新加载最新配置
        config = self.config_mgr.load_config()
        github_token = config.get('github', {}).get('token', '')
        
        if not github_token:
            result = messagebox.askyesno(
                "配置缺失",
                "未检测到 GitHub Token 配置\n\n是否现在去设置？",
                parent=self.root
            )
            if result:
                self.open_settings()
            return
        
        # 确认信息
        from pathlib import Path
        folder_name = Path(project_path).name
        
        # 检查仓库名和文件夹名是否一致
        warning_text = ""
        if repo_name != folder_name:
            warning_text = f"\n⚠️ 注意：仓库名 ({repo_name}) 与文件夹名 ({folder_name}) 不同"
        
        # 确认开始
        msg = f"""
即将开始完整的发布流程：

📁 文件夹: {folder_name}
📦 仓库名: {repo_name}
🏷️ 版本号: {version}
📂 路径: {project_path}{warning_text}

将自动完成以下步骤：
1. 发布到 GitHub + PyPI/NPM
2. 等待 GitHub Actions 完成
3. 注册到 EMCP 平台
4. AI 生成 Logo
5. MCP 工具测试
6. Agent 对话测试
7. 生成测试报告

预计耗时: 3-5 分钟

确定要开始吗？
        """
        
        if not messagebox.askyesno("确认", msg, parent=self.root):
            return
        
        self.status_label.config(text="正在生产...")
        
        # 在后台线程执行
        threading.Thread(target=self._execute_workflow, daemon=True).start()
    
    def _execute_workflow(self):
        """执行工作流（后台线程）"""
        try:
            # 设置项目信息给执行器
            self.executor.set_project_info(
                self.project_path_var.get(),
                self.repo_name_var.get(),
                self.version_var.get()
            )
            
            print(f"\n{'#'*60}")
            print(f"🏭 开始执行完整工作流")
            print(f"{'#'*60}")
            print(f"项目: {self.repo_name_var.get()}")
            print(f"版本: {self.version_var.get()}")
            print(f"路径: {self.project_path_var.get()}")
            print(f"{'#'*60}\n")
            
            # 执行所有根步骤（GitHub -> EMCP -> 测试）
            root_steps = [s for s in self.steps.values() if s.parent is None]
            
            for i, root_step in enumerate(root_steps):
                # 更新状态
                step_name = root_step.title
                self.root.after(0, lambda name=step_name: 
                               self.status_label.config(text=f"正在执行: {name}"))
                
                # 执行步骤
                self._execute_step(root_step)
                
                # 如果不是最后一个步骤，添加过渡时间
                if i < len(root_steps) - 1:
                    time.sleep(0.5)
            
            # 全部完成
            print(f"\n{'#'*60}")
            print(f"🎉 工作流执行完成！")
            print(f"{'#'*60}\n")
            
            self.root.after(0, lambda: self.status_label.config(text="✅ 生产完成！"))
            self.root.after(0, lambda: self.show_completion_message())
            
        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            print(f"\n{'!'*60}")
            print(f"❌ 错误: {error_msg}")
            print(f"{'!'*60}\n")
            
            self.root.after(0, lambda: self.status_label.config(text=f"❌ {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg, parent=self.root))
    
    def show_completion_message(self):
        """显示完成消息"""
        msg = """
🎉 MCP工厂生产完成！

已完成以下任务：
✅ 发布到 GitHub + PyPI/NPM
✅ 注册到 EMCP 平台
✅ AI 生成 Logo
✅ MCP 工具测试
✅ Agent 对话测试
✅ 生成测试报告

所有报告已保存到本地，请查看日志了解详情。
        """
        messagebox.showinfo("完成", msg, parent=self.root)
    
    def _execute_step(self, step: Step):
        """执行单个步骤（递归）"""
        # 开始执行
        step.start()
        step.progress = 0
        self.root.after(0, lambda: self._update_step_ui(step))
        
        # 设置进度回调
        def progress_callback(progress):
            step.progress = progress
            self.root.after(0, lambda: self._update_step_ui(step))
        
        self.executor.set_progress_callback(progress_callback)
        
        try:
            # 根据步骤ID调用对应的真实函数
            if step.id == "github.scan":
                self.executor.step_scan_project()
            elif step.id == "github.create_repo":
                self.executor.step_create_repo()
            elif step.id == "github.generate_pipeline":
                self.executor.step_generate_pipeline()
            elif step.id == "github.push":
                self.executor.step_push_code()
            elif step.id == "github.publish":
                self.executor.step_trigger_publish()
            elif step.id == "emcp.fetch":
                self.executor.step_fetch_package()
            elif step.id == "emcp.generate":
                self.executor.step_ai_generate()
            elif step.id == "emcp.logo":
                self.executor.step_generate_logo()
            elif step.id == "emcp.publish":
                self.executor.step_publish_emcp()
            elif step.id == "test.mcp":
                self.executor.step_test_mcp()
            elif step.id == "test.agent":
                self.executor.step_test_agent()
            elif step.id == "test.chat":
                self.executor.step_test_chat()
            else:
                # 对于父步骤或未实现的步骤，只执行子步骤
                if step.children:
                    print(f"\n{'─'*50}")
                    print(f"▶ 开始: {step.title} ({len(step.children)} 个子步骤)")
                    print(f"{'─'*50}\n")
            
            # 执行子步骤
            for child_id in step.children:
                if child_id in self.steps:
                    child_step = self.steps[child_id]
                    self._execute_step(child_step)
            
            # 完成执行
            step.progress = 100
            step.complete(success=True)
            duration = (step.end_time - step.start_time).total_seconds() if step.start_time and step.end_time else 0
            
            if step.children:
                print(f"✅ 完成: {step.title} (总耗时: {duration:.1f}秒)\n")
            
            self.root.after(0, lambda: self._update_step_ui(step))
            self.root.after(0, self.update_overall_progress)
            
        except Exception as e:
            # 步骤失败
            step.add_log(f"执行失败: {str(e)}", "ERROR")
            step.complete(success=False)
            
            print(f"\n{'!'*60}")
            print(f"❌ 步骤失败: {step.title}")
            print(f"❌ 错误: {str(e)}")
            print(f"{'!'*60}\n")
            
            self.root.after(0, lambda: self._update_step_ui(step))
            self.root.after(0, self.update_overall_progress)
            
            # 抛出异常，中止后续执行
            raise
    
    def _update_step_ui(self, step: Step):
        """更新步骤UI"""
        if step.id in self.step_widgets:
            self.step_widgets[step.id].update_status()
        
        # 如果当前选中此步骤，更新日志
        if self.current_selected_step and self.current_selected_step.id == step.id:
            self.show_step_logs(step)
    
    def pause_workflow(self):
        """暂停工作流"""
        messagebox.showinfo("提示", "暂停功能开发中...")
    
    def reset_workflow(self):
        """重置工作流"""
        for step in self.steps.values():
            step.status = StepStatus.PENDING
            step.progress = 0
            step.logs.clear()
            step.start_time = None
            step.end_time = None
        
        # 更新UI
        for widget in self.step_widgets.values():
            widget.update_status()
        
        self.update_overall_progress()
        self.status_label.config(text="已重置")
    
    def browse_project_folder(self):
        """浏览项目文件夹"""
        folder = filedialog.askdirectory(title="选择项目文件夹")
        if folder:
            self.project_path_var.set(folder)
            # 自动检测项目信息并填充仓库名
            self.detect_project_info_and_fill_repo(folder)
    
    def detect_project_info_and_fill_repo(self, folder_path):
        """检测项目信息并自动填充仓库名"""
        # 首先使用文件夹名作为仓库名
        from pathlib import Path
        folder_name = Path(folder_path).name
        
        # ✅ 验证文件夹名是否合法
        if folder_name.startswith('.'):
            # 如果选择了 .git, .github 等隐藏文件夹，使用父文件夹名
            parent_folder = Path(folder_path).parent.name
            print(f"⚠️ 检测到隐藏文件夹: {folder_name}")
            print(f"💡 使用父文件夹名作为仓库名: {parent_folder}")
            folder_name = parent_folder
        
        # 始终设置（会覆盖之前的值，确保正确）
        self.repo_name_var.set(folder_name)
        print(f"📦 设置仓库名: {folder_name}")
        
        # 然后检测项目详细信息
        self.detect_project_info(folder_path)
    
    def detect_project_info(self, folder_path):
        """检测项目信息"""
        # 在全局日志显示
        print(f"\n{'='*50}")
        print(f"🔍 开始检测项目信息")
        print(f"{'='*50}")
        
        try:
            from src.project_detector import ProjectDetector
            from pathlib import Path
            
            print(f"📁 项目路径: {folder_path}")
            
            detector = ProjectDetector(folder_path)
            info = detector.detect()
            
            project_type = info.get("type", "未知")
            print(f"✓ 项目类型: {project_type}")
            
            # 设置版本号
            if info.get("version"):
                self.version_var.set(info["version"])
                print(f"✓ 版本号: {info['version']}")
            else:
                # 如果检测不到版本号，使用默认值
                if not self.version_var.get():
                    self.version_var.set("1.0.0")
                print(f"💡 使用默认版本号: 1.0.0")
            
            # 显示项目信息
            version = self.version_var.get()
            repo_name = self.repo_name_var.get()
            folder_name = Path(folder_path).name
            
            print(f"✅ 检测完成")
            print(f"   📁 文件夹: {folder_name}")
            print(f"   📦 仓库名: {repo_name}")
            print(f"   🏷️ 版本号: {version}")
            print(f"   🔧 类型: {project_type}")
            print(f"{'='*50}\n")
            
            self.project_info_label.config(
                text=f"✅ {project_type} 项目\n📁 {folder_name}\n📦 {repo_name}\n🏷️ v{version}")
            
        except Exception as e:
            # 即使检测失败，也尝试使用文件夹名
            from pathlib import Path
            
            print(f"⚠️ 检测异常: {str(e)}")
            
            # 设置默认版本号
            if not self.version_var.get() or self.version_var.get() == "":
                self.version_var.set("1.0.0")
                print(f"💡 使用默认版本号: 1.0.0")
            
            # 友好的提示信息
            repo_name = self.repo_name_var.get()
            version = self.version_var.get()
            folder_name = Path(folder_path).name
            
            print(f"✅ 已自动填充: {repo_name} v{version}")
            print(f"{'='*50}\n")
            
            self.project_info_label.config(
                text=f"⚠️ 检测信息不完整\n📁 {folder_name}\n📦 {repo_name}\n🏷️ v{version}\n💡 未找到配置文件")
    
    
    def open_settings(self):
        """打开设置"""
        settings = SettingsWindow(self.root)
        # 等待设置窗口关闭
        self.root.wait_window(settings.window)
        # 重新加载配置
        self.reload_config()
    
    def show_help(self):
        """显示帮助"""
        help_text = """
🏭 MCP工厂使用指南

1. 在左侧输入区域填写项目信息
2. 点击"开始发布"启动工作流
3. 在中间查看执行步骤和进度
4. 点击步骤查看详细日志
5. 点击大步骤可展开/折叠子步骤

详细文档请查看 README.md
        """
        messagebox.showinfo("帮助", help_text, parent=self.root)


def main():
    """主函数"""
    root = tk.Tk()
    app = MCPFactoryGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


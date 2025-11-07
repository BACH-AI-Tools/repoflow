#!/usr/bin/env python3
"""
MCP工厂 - 流程化发布平台
展示清晰的步骤流程和执行进度
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
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
        StepStatus.PENDING: "#9E9E9E",    # 灰色
        StepStatus.RUNNING: "#2196F3",    # 蓝色
        StepStatus.SUCCESS: "#4CAF50",    # 绿色
        StepStatus.FAILED: "#F44336",     # 红色
        StepStatus.SKIPPED: "#FF9800",    # 橙色
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
        
        # 创建可点击的区域
        self.click_frame = tk.Frame(info_frame, cursor="hand2", bg="#f0f0f0")
        self.click_frame.pack(fill=tk.X, expand=True)
        
        # 绑定点击事件到 click_frame 和所有子组件
        def bind_click_recursive(widget):
            """递归绑定点击事件"""
            widget.bind("<Button-1>", lambda e: self.on_click(self.step))
            for child in widget.winfo_children():
                bind_click_recursive(child)
        
        bind_click_recursive(self.click_frame)
        
        self.click_frame.bind("<Enter>", lambda e: self.click_frame.config(bg="#e0e0e0"))
        self.click_frame.bind("<Leave>", lambda e: self.click_frame.config(bg="#f0f0f0"))
        
        # 内容框架
        content_frame = ttk.Frame(self.click_frame)
        content_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 左侧：展开/折叠按钮（如果有子步骤）
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        if step.children:
            self.expand_btn = ttk.Label(left_frame, text="▼", cursor="hand2")
            self.expand_btn.pack(side=tk.LEFT)
            # 绑定展开/折叠事件，并阻止事件冒泡
            self.expand_btn.bind("<Button-1>", lambda e: (self.toggle_expand(), "break")[1])
        else:
            ttk.Label(left_frame, text="  ").pack(side=tk.LEFT)
        
        # 状态图标
        self.status_label = ttk.Label(left_frame, text=self.STATUS_ICONS[step.status], 
                                      font=("Arial", 14))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 中间：标题和描述
        middle_frame = ttk.Frame(content_frame)
        middle_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.title_label = ttk.Label(middle_frame, text=step.title, 
                                     font=("微软雅黑", 10, "bold"))
        self.title_label.pack(anchor=tk.W)
        
        if step.description:
            self.desc_label = ttk.Label(middle_frame, text=step.description, 
                                        font=("微软雅黑", 9), foreground="gray")
            self.desc_label.pack(anchor=tk.W)
        
        # 右侧：进度条
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.progress_var = tk.IntVar(value=step.progress)
        self.progress_bar = ttk.Progressbar(right_frame, length=100, 
                                           variable=self.progress_var, 
                                           mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        self.progress_label = ttk.Label(right_frame, text=f"{step.progress}%", 
                                        font=("Arial", 9))
        self.progress_label.pack(side=tk.LEFT)
        
        # 子步骤容器
        self.children_frame = ttk.Frame(self)
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
        self.root.title("MCP工厂 - 流程化MCP发布平台")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
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
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel', font=('微软雅黑', 16, 'bold'), foreground='#2196F3')
        style.configure('Subtitle.TLabel', font=('微软雅黑', 12, 'bold'))
        style.configure('Info.TLabel', font=('微软雅黑', 10))
        style.configure('StepItem.TFrame', background='#ffffff')
        style.configure('StepInfo.TFrame', background='#f0f0f0', relief='solid')
        style.configure('Big.TButton', font=('微软雅黑', 12, 'bold'), padding=10)
    
    def create_widgets(self):
        """创建UI组件"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding=10)
        toolbar.pack(fill=tk.X)
        
        ttk.Label(toolbar, text="🏭 MCP工厂", style='Title.TLabel').pack(side=tk.LEFT)
        
        ttk.Button(toolbar, text="⚙️ 设置", 
                  command=self.open_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="📖 帮助", 
                  command=self.show_help).pack(side=tk.RIGHT)
        
        ttk.Separator(self.root, orient='horizontal').pack(fill=tk.X, padx=10)
        
        # 主容器 - 三栏布局
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：输入和控制区域（30%）
        left_panel = self.create_left_panel()
        main_container.add(left_panel, weight=30)
        
        # 中间：步骤流程区域（40%）
        middle_panel = self.create_middle_panel()
        main_container.add(middle_panel, weight=40)
        
        # 右侧：日志查看区域（30%）- 使用选项卡
        right_panel = self.create_right_panel_with_tabs()
        main_container.add(right_panel, weight=30)
        
        # 底部状态栏
        status_frame = ttk.Frame(self.root, padding=5)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="就绪", style='Info.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        # 整体进度条
        self.overall_progress_var = tk.IntVar(value=0)
        self.overall_progress = ttk.Progressbar(status_frame, length=200, 
                                               variable=self.overall_progress_var)
        self.overall_progress.pack(side=tk.RIGHT, padx=10)
        
        self.overall_progress_label = ttk.Label(status_frame, text="0%", style='Info.TLabel')
        self.overall_progress_label.pack(side=tk.RIGHT)
    
    def create_left_panel(self):
        """创建左侧面板"""
        panel = ttk.Frame(self.root)
        
        # 输入区域（统一，不分标签）
        input_frame = ttk.Frame(panel, padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(input_frame, text="📋 项目信息", 
                 style='Subtitle.TLabel').pack(anchor=tk.W, pady=(0, 10))
        
        # 项目路径
        ttk.Label(input_frame, text="项目文件夹:", style='Info.TLabel').pack(anchor=tk.W, pady=5)
        self.project_path_var = tk.StringVar()
        path_frame = ttk.Frame(input_frame)
        path_frame.pack(fill=tk.X, pady=5)
        ttk.Entry(path_frame, textvariable=self.project_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="浏览", command=self.browse_project_folder).pack(side=tk.LEFT, padx=5)
        
        # 仓库名称
        ttk.Label(input_frame, text="仓库名称:", style='Info.TLabel').pack(anchor=tk.W, pady=5)
        self.repo_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.repo_name_var).pack(fill=tk.X, pady=5)
        
        # 版本号
        ttk.Label(input_frame, text="版本号:", style='Info.TLabel').pack(anchor=tk.W, pady=5)
        self.version_var = tk.StringVar(value="1.0.0")
        ttk.Entry(input_frame, textvariable=self.version_var).pack(fill=tk.X, pady=5)
        
        # 分隔线
        ttk.Separator(input_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # 说明
        info_label = ttk.Label(input_frame, 
                               text="💡 点击\"开始生产\"后，将自动完成：",
                               style='Info.TLabel')
        info_label.pack(anchor=tk.W, pady=(0, 5))
        
        workflow_text = """
        1️⃣ 发布到 GitHub + PyPI/NPM
        2️⃣ 注册到 EMCP 平台
        3️⃣ 生成 AI Logo
        4️⃣ MCP 工具测试
        5️⃣ Agent 对话测试
        6️⃣ 生成测试报告
        """
        
        workflow_label = ttk.Label(input_frame, text=workflow_text,
                                   font=("微软雅黑", 9),
                                   foreground="#666")
        workflow_label.pack(anchor=tk.W, padx=10)
        
        # 项目信息显示
        self.project_info_label = ttk.Label(input_frame, text="", 
                                           style='Info.TLabel',
                                           wraplength=250)
        self.project_info_label.pack(anchor=tk.W, pady=10)
        
        # 控制按钮
        button_frame = ttk.Frame(panel, padding=10)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(button_frame, text="🏭 开始生产", 
                  command=self.start_workflow,
                  style='Big.TButton').pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="⏸ 暂停", 
                  command=self.pause_workflow).pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="🔄 重新开始", 
                  command=self.reset_workflow).pack(fill=tk.X, pady=5)
        
        return panel
    
    def create_middle_panel(self):
        """创建中间步骤流程面板"""
        panel = ttk.Frame(self.root)
        
        # 标题
        header = ttk.Frame(panel, padding=10)
        header.pack(fill=tk.X)
        
        ttk.Label(header, text="📋 执行流程", style='Subtitle.TLabel').pack(side=tk.LEFT)
        
        # 滚动区域
        canvas = tk.Canvas(panel, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        self.steps_frame = ttk.Frame(canvas)
        
        self.steps_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.steps_frame, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 绑定窗口大小变化
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(
            canvas.find_withtag("all")[0], width=e.width))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return panel
    
    def create_right_panel_with_tabs(self):
        """创建右侧全局日志面板"""
        panel = ttk.Frame(self.root)
        
        # 标题栏
        header = ttk.Frame(panel, padding=5)
        header.pack(fill=tk.X)
        
        ttk.Label(header, text="📋 全局日志（实时输出）", 
                 font=("微软雅黑", 11, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(header, text="清空", command=self.clear_global_logs).pack(side=tk.RIGHT)
        ttk.Button(header, text="📋 滚动到底部", 
                  command=lambda: self.global_log_text.see(tk.END)).pack(side=tk.RIGHT, padx=5)
        
        # 全局日志文本区域
        log_frame = ttk.Frame(panel, padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.global_log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                         font=("Consolas", 10),
                                                         bg="#1e1e1e", fg="#d4d4d4")
        self.global_log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置全局日志颜色（深色主题）
        self.global_log_text.tag_config("INFO", foreground="#4FC3F7")
        self.global_log_text.tag_config("SUCCESS", foreground="#81C784")
        self.global_log_text.tag_config("WARNING", foreground="#FFB74D")
        self.global_log_text.tag_config("ERROR", foreground="#E57373")
        self.global_log_text.tag_config("DEBUG", foreground="#9E9E9E")
        
        # 显示初始信息
        self.global_log_text.insert(tk.END, "🏭 MCP工厂 - 全局日志\n", "SUCCESS")
        self.global_log_text.insert(tk.END, "=" * 50 + "\n", "DEBUG")
        self.global_log_text.insert(tk.END, "\n等待开始生产...\n\n", "INFO")
        
        # 重定向 stdout 和 stderr
        sys.stdout = LogHandler(self.global_log_text)
        sys.stderr = LogHandler(self.global_log_text, is_error=True)
        
        return panel
    
    def clear_global_logs(self):
        """清空全局日志"""
        self.global_log_text.delete(1.0, tk.END)
        self.global_log_text.insert(tk.END, "🏭 MCP工厂 - 全局日志\n", "SUCCESS")
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
            ("emcp.logo", "生成 Logo", "即梦 AI 生成 Logo", "emcp"),
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
        
        if not version:
            messagebox.showwarning("警告", "请输入版本号", parent=self.root)
            return
        
        # 确认开始
        msg = f"""
即将开始完整的发布流程：

项目: {repo_name}
版本: {version}
路径: {project_path}

将自动完成以下步骤：
1. 发布到 GitHub + PyPI/NPM
2. 注册到 EMCP 平台
3. AI 生成 Logo
4. MCP 工具测试
5. Agent 对话测试
6. 生成测试报告

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
            # 自动检测项目信息
            self.detect_project_info(folder)
    
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
            print(f"✓ 检测到项目类型: {project_type}")
            
            # 设置仓库名称（优先使用检测到的名称，否则使用文件夹名）
            if not self.repo_name_var.get():
                if info.get("name"):
                    self.repo_name_var.set(info["name"])
                    print(f"✓ 检测到项目名称: {info['name']}")
                else:
                    # 使用文件夹名作为仓库名
                    folder_name = Path(folder_path).name
                    self.repo_name_var.set(folder_name)
                    print(f"💡 使用文件夹名作为仓库名: {folder_name}")
            
            # 设置版本号
            if info.get("version"):
                self.version_var.set(info["version"])
                print(f"✓ 检测到版本号: {info['version']}")
            else:
                # 如果检测不到版本号，使用默认值
                if not self.version_var.get():
                    self.version_var.set("1.0.0")
                print(f"💡 使用默认版本号: 1.0.0")
            
            # 显示项目信息
            version = self.version_var.get()
            repo_name = self.repo_name_var.get()
            
            print(f"✅ 检测完成: {project_type} 项目, {repo_name} v{version}")
            print(f"{'='*50}\n")
            
            self.project_info_label.config(
                text=f"✅ 检测到 {project_type} 项目\n仓库名: {repo_name}\n版本: {version}")
            
        except Exception as e:
            # 即使检测失败，也尝试使用文件夹名
            from pathlib import Path
            
            print(f"⚠️ 检测异常: {str(e)}")
            
            if not self.repo_name_var.get():
                try:
                    folder_name = Path(folder_path).name
                    self.repo_name_var.set(folder_name)
                    # 设置默认版本号
                    if not self.version_var.get() or self.version_var.get() == "":
                        self.version_var.set("1.0.0")
                    
                    print(f"💡 使用降级方案:")
                    print(f"  - 仓库名称: {folder_name}")
                    print(f"  - 版本号: 1.0.0")
                except Exception as e2:
                    print(f"❌ 降级方案失败: {str(e2)}")
            
            # 友好的提示信息
            repo_name = self.repo_name_var.get()
            version = self.version_var.get()
            
            print(f"✅ 已自动填充: {repo_name} v{version}")
            print(f"{'='*50}\n")
            
            self.project_info_label.config(
                text=f"✅ 已自动填充信息\n仓库名: {repo_name}\n版本: {version}\n\n💡 未找到配置文件，使用文件夹名")
    
    
    def open_settings(self):
        """打开设置"""
        SettingsWindow(self.root)
    
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


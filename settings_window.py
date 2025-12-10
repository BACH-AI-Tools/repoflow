#!/usr/bin/env python3
"""
统一设置窗口
管理所有平台和服务的配置
"""

import tkinter as tk
import sys
from tkinter import ttk, filedialog, messagebox
from src.unified_config_manager import UnifiedConfigManager
from datetime import datetime


class SettingsWindow:
    """统一设置窗口"""
    
    def __init__(self, parent):
        self.parent = parent
        self.config_mgr = UnifiedConfigManager()
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("⚙️ 设置")
        self.window.geometry("750x820")
        self.window.resizable(False, False)
        
        # Apple 风格背景
        self.window.configure(bg='#F5F5F7')
        
        # 使窗口置顶
        self.window.transient(parent)
        self.window.grab_set()
        
        # 设置样式
        self.setup_styles()
        
        # 创建UI
        self.create_widgets()
        
        # 加载配置
        self.load_config()
        
        # 居中显示
        self.center_window()
    
    def center_window(self):
        """窗口居中"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """设置Apple风格样式"""
        style = ttk.Style()
        style.theme_use('aqua' if sys.platform == 'darwin' else 'clam')
        
        # Apple风格配色
        style.configure('TFrame', background='#F5F5F7')
        style.configure('TLabel', background='#FFFFFF', foreground='#1D1D1F',
                       font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11))
        style.configure('TLabelframe', background='#FFFFFF', borderwidth=1, relief='solid')
        style.configure('TLabelframe.Label', background='#FFFFFF', foreground='#1D1D1F',
                       font=('SF Pro Display', 13, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 13, 'bold'))
        
        # 输入框样式
        style.configure('TEntry', fieldbackground='#F5F5F7', foreground='#1D1D1F',
                       insertcolor='#007AFF', borderwidth=1, relief='solid')
        style.configure('TCombobox', fieldbackground='#F5F5F7', foreground='#1D1D1F',
                       borderwidth=1)
        
        # 按钮样式
        style.configure('TButton', background='#007AFF', foreground='#FFFFFF',
                       font=('SF Pro Text', 11, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 11, 'bold'),
                       borderwidth=0, relief='flat', padding=(16, 8))
        style.map('TButton', background=[('active', '#0051D5'), ('pressed', '#0051D5')])
        
        # Checkbutton 样式
        style.configure('TCheckbutton', background='#FFFFFF', foreground='#1D1D1F',
                       font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10))
    
    def create_widgets(self):
        """创建界面组件 - Apple风格"""
        # 主容器 - Apple风格
        main_frame = tk.Frame(self.window, bg='#F5F5F7')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 创建带滚动条的 Canvas
        canvas = tk.Canvas(main_frame, highlightthickness=0, bg='#F5F5F7')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#F5F5F7')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ===== 1. GitHub 配置 ===== Apple风格
        github_frame = tk.LabelFrame(scrollable_frame, text="  🔗 GitHub 配置  ", 
                                     bg='#FFFFFF', fg='#1D1D1F',
                                     font=('SF Pro Display', 13, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 13, 'bold'),
                                     bd=1, relief='solid', padx=20, pady=15)
        github_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(github_frame, text="GitHub Token:", bg='#FFFFFF', fg='#1D1D1F',
                font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11)).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.github_token_var = tk.StringVar()
        token_entry = tk.Entry(github_frame, textvariable=self.github_token_var, width=40, show="*",
                             bg='#F5F5F7', fg='#1D1D1F', insertbackground='#007AFF',
                             bd=1, relief='solid', font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11))
        token_entry.grid(row=0, column=1, sticky=tk.EW, padx=8, pady=8, ipady=6, ipadx=8)
        
        token_btn = tk.Button(github_frame, text="🔗 获取 Token",
                             bg='#007AFF', fg='#FFFFFF', bd=0, cursor='hand2',
                             font=('SF Pro Text', 10, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 10, 'bold'),
                             padx=14, pady=8, command=self.open_github_token_url)
        token_btn.grid(row=0, column=2, padx=8)
        
        tk.Label(github_frame, text="组织名称:", bg='#FFFFFF', fg='#1D1D1F',
                font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11)).grid(row=1, column=0, sticky=tk.W, pady=8)
        self.github_org_var = tk.StringVar()
        org_entry = tk.Entry(github_frame, textvariable=self.github_org_var, width=40,
                            bg='#F5F5F7', fg='#1D1D1F', insertbackground='#007AFF',
                            bd=1, relief='solid', font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11))
        org_entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=8, pady=8, ipady=6, ipadx=8)
        
        github_frame.columnconfigure(1, weight=1)
        
        # ===== 2. EMCP 平台配置 =====
        emcp_frame = ttk.LabelFrame(scrollable_frame, text="🌐 EMCP 平台配置", padding=10)
        emcp_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(emcp_frame, text="平台域名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.emcp_url_var = tk.StringVar()
        emcp_url_combo = ttk.Combobox(emcp_frame, textvariable=self.emcp_url_var, width=47, 
                                      values=["https://sit-emcp.kaleido.guru", "https://emcp.kaleido.guru"])
        emcp_url_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(emcp_frame, text="手机号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.emcp_phone_var = tk.StringVar()
        ttk.Entry(emcp_frame, textvariable=self.emcp_phone_var, width=50).grid(
            row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(emcp_frame, text="验证码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.emcp_code_var = tk.StringVar()
        code_frame = ttk.Frame(emcp_frame)
        code_frame.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # 验证码自动生成，只读显示
        code_entry = ttk.Entry(code_frame, textvariable=self.emcp_code_var, width=30, state='readonly')
        code_entry.pack(side=tk.LEFT)
        ttk.Label(code_frame, text="(自动生成)", foreground="green").pack(side=tk.LEFT, padx=10)
        
        # 自动生成今日验证码
        self.emcp_code_var.set(datetime.now().strftime("%m%Y%d"))
        
        emcp_frame.columnconfigure(1, weight=1)
        
        # ===== 3. Agent 平台配置 =====
        agent_frame = ttk.LabelFrame(scrollable_frame, text="🤖 Agent 平台配置", padding=10)
        agent_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(agent_frame, text="平台域名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.agent_url_var = tk.StringVar()
        agent_url_combo = ttk.Combobox(agent_frame, textvariable=self.agent_url_var, width=47,
                                       values=["https://v5.kaleido.guru", "https://v5-sit.kaleido.guru"])
        agent_url_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(agent_frame, text="手机号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.agent_phone_var = tk.StringVar()
        ttk.Entry(agent_frame, textvariable=self.agent_phone_var, width=50).grid(
            row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(agent_frame, text="验证码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.agent_code_var = tk.StringVar()
        agent_code_frame = ttk.Frame(agent_frame)
        agent_code_frame.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # 验证码自动生成，只读显示
        agent_code_entry = ttk.Entry(agent_code_frame, textvariable=self.agent_code_var, width=30, state='readonly')
        agent_code_entry.pack(side=tk.LEFT)
        ttk.Label(agent_code_frame, text="(自动生成)", foreground="green").pack(side=tk.LEFT, padx=10)
        
        # 自动生成今日验证码
        self.agent_code_var.set(datetime.now().strftime("%m%Y%d"))
        
        # 使用相同验证码复选框
        self.same_code_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(agent_frame, text="与 EMCP 使用相同手机号和验证码", 
                       variable=self.same_code_var,
                       command=self.on_same_code_changed).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 监听手机号变化，自动同步
        self.emcp_phone_var.trace('w', self.auto_sync_code)
        
        agent_frame.columnconfigure(1, weight=1)
        
        # ===== 4. Azure OpenAI 配置 =====
        openai_frame = ttk.LabelFrame(scrollable_frame, text="🤖 Azure OpenAI 配置", padding=10)
        openai_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(openai_frame, text="Endpoint:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.openai_endpoint_var = tk.StringVar()
        ttk.Entry(openai_frame, textvariable=self.openai_endpoint_var, width=50).grid(
            row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(openai_frame, text="API Key:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.openai_key_var = tk.StringVar()
        ttk.Entry(openai_frame, textvariable=self.openai_key_var, width=50, show="*").grid(
            row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(openai_frame, text="API Version:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.openai_version_var = tk.StringVar()
        version_combo = ttk.Combobox(openai_frame, textvariable=self.openai_version_var, width=47,
                                     values=["2024-02-15-preview", "2023-12-01-preview", "2023-05-15"])
        version_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(openai_frame, text="Deployment:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.openai_deployment_var = tk.StringVar()
        deployment_combo = ttk.Combobox(openai_frame, textvariable=self.openai_deployment_var, width=47,
                                       values=["gpt-4o", "gpt-4", "gpt-35-turbo"])
        deployment_combo.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        openai_frame.columnconfigure(1, weight=1)
        
        # ===== 5. PyPI 配置 =====
        pypi_frame = ttk.LabelFrame(scrollable_frame, text="📦 PyPI 配置", padding=10)
        pypi_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pypi_frame, text="镜像源:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pypi_mirror_var = tk.StringVar()
        mirror_combo = ttk.Combobox(pypi_frame, textvariable=self.pypi_mirror_var, width=47,
                                    values=[
                                        "https://pypi.tuna.tsinghua.edu.cn/simple",
                                        "https://mirrors.aliyun.com/pypi/simple",
                                        "https://pypi.mirrors.ustc.edu.cn/simple",
                                        "https://pypi.org/simple"
                                    ])
        mirror_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        pypi_frame.columnconfigure(1, weight=1)
        
        # ===== 6. 即梦 API 配置 ===== 使用火山引擎 API
        jimeng_frame = tk.LabelFrame(scrollable_frame, text="  🎨 即梦 AI 配置 (Logo 生成)  ",
                                     bg='#FFFFFF', fg='#1D1D1F',
                                     font=('SF Pro Display', 13, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 13, 'bold'),
                                     bd=1, relief='solid', padx=20, pady=15)
        jimeng_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.jimeng_enabled_var = tk.BooleanVar(value=True)
        enable_check = tk.Checkbutton(jimeng_frame, text="启用即梦 AI Logo 生成（使用即梦 4.0）",
                                     variable=self.jimeng_enabled_var,
                                     bg='#FFFFFF', fg='#1D1D1F',
                                     font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11),
                                     selectcolor='#FFFFFF', activebackground='#FFFFFF')
        enable_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))
        
        # Access Key
        tk.Label(jimeng_frame, text="Access Key:", bg='#FFFFFF', fg='#1D1D1F',
                font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11)).grid(row=1, column=0, sticky=tk.W, pady=8)
        
        self.jimeng_ak_var = tk.StringVar()
        ak_entry = tk.Entry(jimeng_frame, textvariable=self.jimeng_ak_var,
                           font=('SF Mono', 10) if sys.platform == 'darwin' else ('Consolas', 10),
                           bg='#F5F5F7', fg='#1D1D1F', insertbackground='#007AFF',
                           bd=1, relief='solid')
        ak_entry.grid(row=1, column=1, sticky=tk.EW, padx=8, pady=8, ipady=6)
        
        # Secret Key
        tk.Label(jimeng_frame, text="Secret Key:", bg='#FFFFFF', fg='#1D1D1F',
                font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11)).grid(row=2, column=0, sticky=tk.W, pady=8)
        
        self.jimeng_sk_var = tk.StringVar()
        sk_entry = tk.Entry(jimeng_frame, textvariable=self.jimeng_sk_var, show="*",
                           font=('SF Mono', 10) if sys.platform == 'darwin' else ('Consolas', 10),
                           bg='#F5F5F7', fg='#1D1D1F', insertbackground='#007AFF',
                           bd=1, relief='solid')
        sk_entry.grid(row=2, column=1, sticky=tk.EW, padx=8, pady=8, ipady=6)
        
        # 提示文字
        hint_label = tk.Label(
            jimeng_frame,
            text='💡 在火山引擎控制台获取密钥: https://console.volcengine.com/iam/keymanage/',
            bg='#FFFFFF',
            fg='#86868B',
            font=('SF Pro Text', 9) if sys.platform == 'darwin' else ('微软雅黑', 9),
            cursor="hand2"
        )
        hint_label.grid(row=3, column=1, sticky=tk.W, padx=8, pady=(0, 8))
        
        jimeng_frame.columnconfigure(1, weight=1)
        
        # ===== 7. 高级选项 ===== Apple风格
        advanced_frame = tk.LabelFrame(scrollable_frame, text="  ⚙️ 高级选项  ",
                                      bg='#FFFFFF', fg='#1D1D1F',
                                      font=('SF Pro Display', 13, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 13, 'bold'),
                                      bd=1, relief='solid', padx=20, pady=15)
        advanced_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.edgeone_enabled_var = tk.BooleanVar(value=True)
        edge_check = tk.Checkbutton(advanced_frame, text="启用 EdgeOne Pages 报告分享",
                                   variable=self.edgeone_enabled_var,
                                   bg='#FFFFFF', fg='#1D1D1F',
                                   font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11),
                                   selectcolor='#FFFFFF', activebackground='#FFFFFF')
        edge_check.pack(anchor=tk.W, pady=3)
        
        self.auto_publish_var = tk.BooleanVar(value=True)
        publish_check = tk.Checkbutton(advanced_frame, text="默认自动发布到包管理平台",
                                      variable=self.auto_publish_var,
                                      bg='#FFFFFF', fg='#1D1D1F',
                                      font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11),
                                      selectcolor='#FFFFFF', activebackground='#FFFFFF')
        publish_check.pack(anchor=tk.W, pady=3)
        
        self.private_repo_var = tk.BooleanVar(value=False)
        private_check = tk.Checkbutton(advanced_frame, text="默认创建私有仓库",
                                      variable=self.private_repo_var,
                                      bg='#FFFFFF', fg='#1D1D1F',
                                      font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11),
                                      selectcolor='#FFFFFF', activebackground='#FFFFFF')
        private_check.pack(anchor=tk.W, pady=3)
        
        # ===== 按钮区域 =====
        button_frame = tk.Frame(scrollable_frame, bg='#F5F5F7')
        button_frame.pack(fill=tk.X, pady=20)
        
        # 左侧按钮 - Apple风格次要按钮
        left_buttons = tk.Frame(button_frame, bg='#F5F5F7')
        left_buttons.pack(side=tk.LEFT)
        
        # 导入按钮
        import_btn = tk.Button(left_buttons, text="📥 导入配置",
                              bg='#FFFFFF', fg='#007AFF', bd=1, relief='solid', cursor='hand2',
                              font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
                              padx=14, pady=8, command=self.import_config)
        import_btn.pack(side=tk.LEFT, padx=4)
        
        # 导出按钮
        export_btn = tk.Button(left_buttons, text="📤 导出配置",
                              bg='#FFFFFF', fg='#007AFF', bd=1, relief='solid', cursor='hand2',
                              font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
                              padx=14, pady=8, command=self.export_config)
        export_btn.pack(side=tk.LEFT, padx=4)
        
        # 打开文件夹按钮
        folder_btn = tk.Button(left_buttons, text="📁 打开配置文件夹",
                              bg='#FFFFFF', fg='#007AFF', bd=1, relief='solid', cursor='hand2',
                              font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
                              padx=14, pady=8, command=self.open_config_folder)
        folder_btn.pack(side=tk.LEFT, padx=4)
        
        # 右侧按钮 - Apple风格主要/次要按钮
        right_buttons = tk.Frame(button_frame, bg='#F5F5F7')
        right_buttons.pack(side=tk.RIGHT)
        
        # 取消按钮 - 次要按钮
        cancel_btn = tk.Button(right_buttons, text="❌ 取消",
                              bg='#FFFFFF', fg='#6E6E73', bd=1, relief='solid', cursor='hand2',
                              font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11),
                              padx=20, pady=10, command=self.window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=4)
        
        # 保存按钮 - 主要按钮
        save_btn = tk.Button(right_buttons, text="💾 保存",
                            bg='#007AFF', fg='#FFFFFF', bd=0, cursor='hand2',
                            font=('SF Pro Text', 12, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 12, 'bold'),
                            padx=28, pady=11, command=self.save_config, relief='flat')
        save_btn.pack(side=tk.LEFT, padx=4)
        
        # 添加悬停效果
        def on_save_enter(e):
            save_btn.configure(bg='#0051D5')
        def on_save_leave(e):
            save_btn.configure(bg='#007AFF')
        save_btn.bind("<Enter>", on_save_enter)
        save_btn.bind("<Leave>", on_save_leave)
        
        # 打包滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 绑定鼠标滚轮（绑定到 canvas 而不是 bind_all）
        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass  # 窗口已关闭时忽略错误
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # 当窗口关闭时解绑
        def _on_destroy(event=None):
            try:
                canvas.unbind("<MouseWheel>")
            except:
                pass
        
        self.window.protocol("WM_DELETE_WINDOW", lambda: (_on_destroy(), self.window.destroy()))
    
    def load_config(self):
        """加载配置"""
        config = self.config_mgr.load_config()
        
        # 自动生成今日验证码
        today_code = datetime.now().strftime("%m%Y%d")
        
        # GitHub
        self.github_token_var.set(config.get("github", {}).get("token", ""))
        self.github_org_var.set(config.get("github", {}).get("org_name", "BACH-AI-Tools"))
        
        # EMCP
        emcp_config = config.get("emcp", {})
        self.emcp_url_var.set(emcp_config.get("base_url", "https://sit-emcp.kaleido.guru"))
        self.emcp_phone_var.set(emcp_config.get("phone_number", ""))
        # 始终使用自动生成的验证码
        self.emcp_code_var.set(today_code)
        
        # Agent
        agent_config = config.get("agent", {})
        self.agent_url_var.set(agent_config.get("base_url", "https://v5.kaleido.guru"))
        self.agent_phone_var.set(agent_config.get("phone_number", ""))
        # 始终使用自动生成的验证码
        self.agent_code_var.set(today_code)
        
        # Azure OpenAI
        openai_config = config.get("azure_openai", {})
        self.openai_endpoint_var.set(openai_config.get("endpoint", ""))
        self.openai_key_var.set(openai_config.get("api_key", ""))
        self.openai_version_var.set(openai_config.get("api_version", "2024-02-15-preview"))
        self.openai_deployment_var.set(openai_config.get("deployment_name", "gpt-4o"))
        
        # PyPI
        self.pypi_mirror_var.set(config.get("pypi", {}).get("mirror_url", "https://pypi.tuna.tsinghua.edu.cn/simple"))
        
        # 即梦 API 配置
        jimeng_config = config.get("jimeng", {})
        self.jimeng_enabled_var.set(jimeng_config.get("enabled", True))
        self.jimeng_ak_var.set(jimeng_config.get("access_key", ""))
        self.jimeng_sk_var.set(jimeng_config.get("secret_key", ""))
        
        self.edgeone_enabled_var.set(config.get("edgeone", {}).get("enabled", True))
        self.auto_publish_var.set(config.get("other", {}).get("auto_publish", True))
        self.private_repo_var.set(config.get("other", {}).get("private_repo", False))
    
    def save_config(self):
        """保存配置"""
        config = self.config_mgr.load_config()
        
        # 自动生成最新的验证码
        today_code = datetime.now().strftime("%m%Y%d")
        
        # GitHub
        config["github"] = {
            "token": self.github_token_var.get().strip(),
            "org_name": self.github_org_var.get().strip()
        }
        
        # EMCP - 使用自动生成的验证码
        config["emcp"] = {
            "base_url": self.emcp_url_var.get().strip(),
            "phone_number": self.emcp_phone_var.get().strip(),
            "validation_code": today_code  # 自动生成
        }
        
        # Agent - 使用自动生成的验证码
        config["agent"] = {
            "base_url": self.agent_url_var.get().strip(),
            "phone_number": self.agent_phone_var.get().strip(),
            "validation_code": today_code  # 自动生成
        }
        
        # Azure OpenAI
        config["azure_openai"] = {
            "endpoint": self.openai_endpoint_var.get().strip(),
            "api_key": self.openai_key_var.get().strip(),
            "api_version": self.openai_version_var.get().strip(),
            "deployment_name": self.openai_deployment_var.get().strip()
        }
        
        # PyPI
        if "pypi" not in config:
            config["pypi"] = {}
        config["pypi"]["mirror_url"] = self.pypi_mirror_var.get().strip()
        
        # 即梦 API 配置
        if "jimeng" not in config:
            config["jimeng"] = {}
        config["jimeng"]["enabled"] = self.jimeng_enabled_var.get()
        config["jimeng"]["access_key"] = self.jimeng_ak_var.get().strip()
        config["jimeng"]["secret_key"] = self.jimeng_sk_var.get().strip()
        
        if "edgeone" not in config:
            config["edgeone"] = {}
        config["edgeone"]["enabled"] = self.edgeone_enabled_var.get()
        
        if "other" not in config:
            config["other"] = {}
        config["other"]["auto_publish"] = self.auto_publish_var.get()
        config["other"]["private_repo"] = self.private_repo_var.get()
        
        # 保存
        if self.config_mgr.save_config(config):
            messagebox.showinfo("成功", "配置已保存！", parent=self.window)
            self.window.destroy()
        else:
            messagebox.showerror("错误", "保存配置失败！", parent=self.window)
    
    def import_config(self):
        """导入配置"""
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="选择配置文件",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            if self.config_mgr.import_config(file_path):
                messagebox.showinfo("成功", "配置已导入！", parent=self.window)
                self.load_config()  # 重新加载显示
            else:
                messagebox.showerror("错误", "导入配置失败！", parent=self.window)
    
    def export_config(self):
        """导出配置"""
        file_path = filedialog.asksaveasfilename(
            parent=self.window,
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            if self.config_mgr.export_config(file_path):
                messagebox.showinfo("成功", f"配置已导出到:\n{file_path}", parent=self.window)
            else:
                messagebox.showerror("错误", "导出配置失败！", parent=self.window)
    
    def open_config_folder(self):
        """打开配置文件夹"""
        import os
        import subprocess
        config_dir = self.config_mgr.config_dir
        
        if os.path.exists(config_dir):
            if sys.platform == 'win32':
                os.startfile(config_dir)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', config_dir])
            else:
                subprocess.Popen(['xdg-open', config_dir])
        else:
            messagebox.showwarning("提示", "配置文件夹不存在", parent=self.window)
    
    def open_github_token_url(self):
        """打开 GitHub Token 获取页面"""
        import webbrowser
        webbrowser.open("https://github.com/settings/tokens/new?scopes=repo,workflow,admin:org")
    
    def auto_sync_code(self, *args):
        """自动同步验证码"""
        if self.same_code_var.get():
            self.agent_phone_var.set(self.emcp_phone_var.get())
            self.agent_code_var.set(self.emcp_code_var.get())
    
    def on_same_code_changed(self):
        """相同验证码复选框变化"""
        if self.same_code_var.get():
            # 同步手机号和验证码
            self.agent_phone_var.set(self.emcp_phone_var.get())
            self.agent_code_var.set(self.emcp_code_var.get())


if __name__ == "__main__":
    import sys
    # 测试设置窗口
    root = tk.Tk()
    root.withdraw()
    SettingsWindow(root)
    root.mainloop()


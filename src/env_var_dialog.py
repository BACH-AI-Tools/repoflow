"""环境变量配置对话框"""

import tkinter as tk
import sys
from tkinter import ttk, scrolledtext
from typing import List, Dict, Optional


class EnvVarDialog:
    """环境变量配置对话框"""
    
    def __init__(self, parent, env_vars: List[Dict], package_name: str):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            env_vars: 环境变量列表
            package_name: 包名
        """
        self.parent = parent
        self.env_vars = env_vars
        self.package_name = package_name
        self.result = None
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"⚙️ 环境变量配置 - {package_name}")
        self.dialog.geometry("750x650")
        self.dialog.resizable(True, True)
        
        # Apple风格背景
        self.dialog.configure(bg='#F5F5F7')
        
        # 模态对话框
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建UI
        self.create_widgets()
        
        # 居中显示
        self.center_window()
    
    def center_window(self):
        """窗口居中"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """创建UI组件 - Apple风格"""
        main_frame = tk.Frame(self.dialog, bg='#F5F5F7')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题卡片
        header_card = tk.Frame(main_frame, bg='#FFFFFF', highlightbackground='#D2D2D7', highlightthickness=1)
        header_card.pack(fill=tk.X, pady=(0, 15))
        
        header_content = tk.Frame(header_card, bg='#FFFFFF')
        header_content.pack(fill=tk.X, padx=20, pady=15)
        
        # 标题
        title = tk.Label(
            header_content,
            text=f"🔧 环境变量配置",
            font=('SF Pro Display', 16, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 16, 'bold'),
            foreground='#1D1D1F',
            bg='#FFFFFF'
        )
        title.pack(anchor=tk.W, pady=(0, 8))
        
        # 说明
        info = tk.Label(
            header_content,
            text="请填写环境变量的配置说明，这些信息将显示在 EMCP 平台上，\n帮助用户正确配置和使用你的 MCP Server。",
            font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
            foreground='#6E6E73',
            bg='#FFFFFF',
            justify=tk.LEFT
        )
        info.pack(anchor=tk.W)
        
        # 环境变量列表（可滚动） - Apple风格
        list_frame = tk.LabelFrame(main_frame, text="  📋 环境变量列表  ",
                                   bg='#FFFFFF', fg='#1D1D1F',
                                   font=('SF Pro Display', 13, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 13, 'bold'),
                                   bd=1, relief='solid', padx=15, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 创建滚动区域 - Apple风格
        canvas = tk.Canvas(list_frame, highlightthickness=0, bg='#FFFFFF')
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#FFFFFF')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 为每个环境变量创建输入区域 - Apple风格
        self.var_widgets = {}
        
        for i, env_var in enumerate(self.env_vars):
            var_frame = tk.Frame(scrollable_frame, bg='#FFFFFF')
            var_frame.pack(fill=tk.X, pady=8)
            
            # 变量名和必需标记
            name_frame = tk.Frame(var_frame, bg='#FFFFFF')
            name_frame.pack(fill=tk.X)
            
            name_label = tk.Label(
                name_frame,
                text=env_var['name'],
                font=('SF Mono', 11, 'bold') if sys.platform == 'darwin' else ('Consolas', 11, 'bold'),
                foreground='#007AFF',
                bg='#FFFFFF'
            )
            name_label.pack(side=tk.LEFT)
            
            if env_var['required']:
                required_label = tk.Label(
                    name_frame,
                    text="  *必需",
                    foreground='#FF3B30',
                    font=('SF Pro Text', 9) if sys.platform == 'darwin' else ('微软雅黑', 9),
                    bg='#FFFFFF'
                )
                required_label.pack(side=tk.LEFT, padx=(5, 0))
            
            # 描述输入框
            desc_label = tk.Label(var_frame, text="说明：", 
                                 font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
                                 foreground='#6E6E73', bg='#FFFFFF')
            desc_label.pack(anchor=tk.W, pady=(8, 4))
            
            desc_var = tk.StringVar(value=env_var.get('description', ''))
            desc_entry = tk.Entry(var_frame, textvariable=desc_var, width=60,
                                 font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
                                 bd=1, bg='#F5F5F7', fg='#1D1D1F',
                                 insertbackground='#007AFF', relief=tk.SOLID)
            desc_entry.pack(fill=tk.X, pady=(0, 8), ipady=7, ipadx=10)
            
            # 示例值输入框
            example_label = tk.Label(var_frame, text="示例值（可选）：", 
                                    font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
                                    foreground='#6E6E73', bg='#FFFFFF')
            example_label.pack(anchor=tk.W, pady=(0, 4))
            
            example_var = tk.StringVar(value="")
            example_entry = tk.Entry(var_frame, textvariable=example_var, width=60,
                                    font=('SF Pro Text', 10) if sys.platform == 'darwin' else ('微软雅黑', 10),
                                    bd=1, bg='#F5F5F7', fg='#1D1D1F',
                                    insertbackground='#007AFF', relief=tk.SOLID)
            example_entry.pack(fill=tk.X, pady=(0, 8), ipady=7, ipadx=10)
            
            # 保存引用
            self.var_widgets[env_var['name']] = {
                'description': desc_var,
                'example': example_var,
                'required': env_var['required']
            }
            
            # 分隔线 - Apple风格
            if i < len(self.env_vars) - 1:
                tk.Frame(var_frame, bg='#E5E5EA', height=1).pack(fill=tk.X, pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 按钮区域 - Apple风格
        button_frame = tk.Frame(main_frame, bg='#F5F5F7')
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 提示
        hint = tk.Label(
            button_frame,
            text="💡 提示：这些信息将帮助用户正确配置你的 MCP Server",
            foreground='#8E8E93',
            font=('SF Pro Text', 9) if sys.platform == 'darwin' else ('微软雅黑', 9),
            bg='#F5F5F7'
        )
        hint.pack(side=tk.LEFT)
        
        # 按钮
        button_right = tk.Frame(button_frame, bg='#F5F5F7')
        button_right.pack(side=tk.RIGHT)
        
        # 取消按钮
        cancel_btn = tk.Button(
            button_right,
            text="❌ 取消",
            command=self.on_cancel,
            bg='#FFFFFF', fg='#6E6E73', bd=1, relief='solid', cursor='hand2',
            font=('SF Pro Text', 11) if sys.platform == 'darwin' else ('微软雅黑', 11),
            padx=20, pady=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # 确认按钮
        confirm_btn = tk.Button(
            button_right,
            text="✅ 确认",
            command=self.on_confirm,
            bg='#007AFF', fg='#FFFFFF', bd=0, cursor='hand2',
            font=('SF Pro Text', 12, 'bold') if sys.platform == 'darwin' else ('微软雅黑', 12, 'bold'),
            padx=28, pady=11, relief='flat'
        )
        confirm_btn.pack(side=tk.LEFT)
        
        # 悬停效果
        def on_confirm_enter(e):
            confirm_btn.configure(bg='#0051D5')
        def on_confirm_leave(e):
            confirm_btn.configure(bg='#007AFF')
        confirm_btn.bind("<Enter>", on_confirm_enter)
        confirm_btn.bind("<Leave>", on_confirm_leave)
    
    def on_confirm(self):
        """确认按钮"""
        # 收集所有配置
        result = []
        for var_name, widgets in self.var_widgets.items():
            desc = widgets['description'].get().strip()
            example = widgets['example'].get().strip()
            required = widgets['required']
            
            # 必需的环境变量必须填写说明
            if required and not desc:
                tk.messagebox.showerror(
                    "错误",
                    f"必需的环境变量 '{var_name}' 必须填写说明",
                    parent=self.dialog
                )
                return
            
            result.append({
                "name": var_name,
                "description": desc or self._guess_description(var_name),
                "example": example,
                "required": required
            })
        
        self.result = result
        self.dialog.destroy()
    
    def on_cancel(self):
        """取消按钮"""
        self.result = None
        self.dialog.destroy()
    
    def _guess_description(self, var_name: str) -> str:
        """猜测变量说明"""
        from src.env_var_detector import EnvVarDetector
        detector = EnvVarDetector()
        return detector._guess_description(var_name)
    
    def show(self) -> Optional[List[Dict]]:
        """显示对话框并等待结果"""
        self.dialog.wait_window()
        return self.result


# 测试代码
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    
    test_vars = [
        {"name": "OPENAI_API_KEY", "description": "OpenAI API 密钥", "required": True},
        {"name": "DATABASE_URL", "description": "数据库连接地址", "required": True},
        {"name": "PORT", "description": "服务端口", "required": False},
    ]
    
    dialog = EnvVarDialog(root, test_vars, "test-mcp-server")
    result = dialog.show()
    
    if result:
        print("用户配置的环境变量：")
        for var in result:
            print(f"  {var['name']}: {var['description']}")
            if var.get('example'):
                print(f"    示例: {var['example']}")
    else:
        print("用户取消了配置")


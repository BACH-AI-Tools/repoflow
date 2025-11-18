#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RepoFlow - 超现代化 GUI
采用 Fluent Design + Material Design 混合风格
"""

import tkinter as tk
from tkinter import ttk, filedialog
import sys
from pathlib import Path

# UTF-8 编码设置
if sys.platform == 'win32':
    if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

from src.unified_config_manager import UnifiedConfigManager
from src.project_detector import ProjectDetector
from src.github_manager import GitHubManager
from src.git_manager import GitManager
from src.pipeline_generator import PipelineGenerator


class ModernGUI:
    """超现代化GUI"""
    
    # 现代配色方案
    COLORS = {
        'bg': '#F5F5F7',  # 浅灰背景
        'card': '#FFFFFF',  # 卡片白色
        'primary': '#007AFF',  # iOS 蓝
        'primary_hover': '#0051D5',
        'success': '#34C759',  # iOS 绿
        'warning': '#FF9500',  # iOS 橙
        'danger': '#FF3B30',  # iOS 红
        'text': '#1D1D1F',  # 深灰文字
        'text_secondary': '#86868B',  # 次要文字
        'border': '#E5E5EA',  # 边框
        'shadow': '#00000015',  # 阴影
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("RepoFlow - 一键发布工具")
        
        # 窗口大小和居中
        window_width = 900
        window_height = 750
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置背景色
        self.root.configure(bg=self.COLORS['bg'])
        
        # 变量
        self.project_path = tk.StringVar()
        self.repo_name = tk.StringVar()
        self.org_name = tk.StringVar(value="BACH-AI-Tools")
        self.pipeline_type = tk.StringVar(value="自动检测")
        
        # 加载配置
        self.load_config()
        
        # 创建UI
        self.create_ui()
    
    def load_config(self):
        """加载配置"""
        config_mgr = UnifiedConfigManager()
        config = config_mgr.load_config()
        
        github_config = config.get('github', {})
        self.github_token = github_config.get('token', '')
        self.org_name.set(github_config.get('org_name', 'BACH-AI-Tools'))
    
    def create_ui(self):
        """创建UI"""
        # 主容器（使用 Canvas 实现渐变背景）
        main_canvas = tk.Canvas(self.root, bg=self.COLORS['bg'], highlightthickness=0)
        main_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 渐变背景
        self.create_gradient_bg(main_canvas)
        
        # 内容容器
        content_frame = tk.Frame(main_canvas, bg=self.COLORS['bg'])
        main_canvas.create_window(450, 375, window=content_frame, width=850, height=700)
        
        # 顶部标题卡片
        self.create_header_card(content_frame)
        
        # Token 状态卡片
        if not self.github_token:
            self.create_token_card(content_frame)
        else:
            self.create_token_status_card(content_frame)
        
        # 主表单卡片
        self.create_form_card(content_frame)
        
        # 底部操作栏
        self.create_action_bar(content_frame)
    
    def create_gradient_bg(self, canvas):
        """创建渐变背景"""
        # 简单的双色渐变
        for i in range(750):
            # 从浅灰到白色
            ratio = i / 750
            r = int(245 + (255 - 245) * ratio)
            g = int(245 + (255 - 245) * ratio)
            b = int(247 + (255 - 247) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_line(0, i, 900, i, fill=color, width=1)
    
    def create_header_card(self, parent):
        """创建顶部标题卡片"""
        card = self.create_card(parent, height=100)
        card.pack(fill=tk.X, padx=30, pady=(30, 15))
        
        # 图标和标题
        title_frame = tk.Frame(card, bg=self.COLORS['card'])
        title_frame.pack(expand=True)
        
        # 图标
        icon_label = tk.Label(
            title_frame,
            text="🚀",
            font=("Segoe UI Emoji", 36),
            bg=self.COLORS['card']
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 文字
        text_frame = tk.Frame(title_frame, bg=self.COLORS['card'])
        text_frame.pack(side=tk.LEFT)
        
        title = tk.Label(
            text_frame,
            text="RepoFlow",
            font=("微软雅黑", 24, "bold"),
            fg=self.COLORS['text'],
            bg=self.COLORS['card']
        )
        title.pack(anchor=tk.W)
        
        subtitle = tk.Label(
            text_frame,
            text="一键发布项目到 GitHub",
            font=("微软雅黑", 11),
            fg=self.COLORS['text_secondary'],
            bg=self.COLORS['card']
        )
        subtitle.pack(anchor=tk.W)
    
    def create_token_card(self, parent):
        """创建 Token 配置卡片"""
        card = self.create_card(parent, height=140)
        card.pack(fill=tk.X, padx=30, pady=(0, 15))
        
        # 内容
        content = tk.Frame(card, bg=self.COLORS['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # 标题
        title = tk.Label(
            content,
            text="⚙️ 首次配置",
            font=("微软雅黑", 14, "bold"),
            fg=self.COLORS['text'],
            bg=self.COLORS['card']
        )
        title.pack(anchor=tk.W, pady=(0, 10))
        
        # Token 输入
        input_frame = tk.Frame(content, bg=self.COLORS['card'])
        input_frame.pack(fill=tk.X)
        
        token_entry = self.create_modern_entry(input_frame, "GitHub Token", show='*')
        token_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 按钮
        btn_frame = tk.Frame(input_frame, bg=self.COLORS['card'])
        btn_frame.pack(side=tk.LEFT)
        
        self.create_secondary_button(btn_frame, "🔗 获取", lambda: self.open_token_url(), width=80)
        self.create_primary_button(btn_frame, "💾 保存", lambda: self.save_token(), width=80)
    
    def create_token_status_card(self, parent):
        """Token 已配置状态"""
        card = self.create_card(parent, height=80)
        card.pack(fill=tk.X, padx=30, pady=(0, 15))
        
        content = tk.Frame(card, bg=self.COLORS['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)
        
        # 状态指示
        status_frame = tk.Frame(content, bg=self.COLORS['card'])
        status_frame.pack(fill=tk.X)
        
        # 绿色指示点
        dot = tk.Label(status_frame, text="●", fg=self.COLORS['success'], 
                      bg=self.COLORS['card'], font=("Arial", 16))
        dot.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            status_frame,
            text="GitHub Token 已配置",
            font=("微软雅黑", 12),
            fg=self.COLORS['text'],
            bg=self.COLORS['card']
        ).pack(side=tk.LEFT)
        
        # 重新配置按钮
        tk.Button(
            status_frame,
            text="🔄 重新配置",
            font=("微软雅黑", 9),
            fg=self.COLORS['primary'],
            bg=self.COLORS['card'],
            bd=0,
            cursor="hand2",
            command=lambda: self.reconfigure_token()
        ).pack(side=tk.RIGHT)
    
    def create_form_card(self, parent):
        """创建表单卡片"""
        card = self.create_card(parent)
        card.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 15))
        
        content = tk.Frame(card, bg=self.COLORS['card'])
        content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # 项目文件夹
        self.create_form_row(
            content,
            "📁 项目文件夹",
            self.project_path,
            has_browse=True
        )
        
        # 项目信息显示
        self.info_label = tk.Label(
            content,
            text="",
            font=("微软雅黑", 9),
            fg=self.COLORS['text_secondary'],
            bg=self.COLORS['card'],
            justify=tk.LEFT
        )
        self.info_label.pack(fill=tk.X, pady=(5, 15))
        
        # 仓库名称
        self.create_form_row(content, "📦 仓库名称", self.repo_name)
        
        # 组织名称
        self.create_form_row(content, "🏢 组织名称", self.org_name)
        
        # Pipeline 类型
        pipeline_frame = tk.Frame(content, bg=self.COLORS['card'])
        pipeline_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            pipeline_frame,
            text="🔧 Pipeline 类型",
            font=("微软雅黑", 11),
            fg=self.COLORS['text'],
            bg=self.COLORS['card']
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        pipeline_combo = ttk.Combobox(
            pipeline_frame,
            textvariable=self.pipeline_type,
            values=['自动检测', 'docker', 'pypi', 'npm'],
            state='readonly',
            width=18,
            font=("微软雅黑", 10)
        )
        pipeline_combo.pack(side=tk.LEFT)
    
    def create_form_row(self, parent, label_text, variable, has_browse=False):
        """创建表单行"""
        row = tk.Frame(parent, bg=self.COLORS['card'])
        row.pack(fill=tk.X, pady=10)
        
        # 标签
        label = tk.Label(
            row,
            text=label_text,
            font=("微软雅黑", 11),
            fg=self.COLORS['text'],
            bg=self.COLORS['card']
        )
        label.pack(side=tk.LEFT, padx=(0, 15))
        
        # 输入框
        entry_frame = tk.Frame(row, bg=self.COLORS['card'])
        entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        entry = tk.Entry(
            entry_frame,
            textvariable=variable,
            font=("微软雅黑", 10),
            bd=0,
            relief=tk.FLAT,
            bg='#F9F9F9',
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['primary']
        )
        entry.pack(fill=tk.X, ipady=8, ipadx=10)
        
        # 浏览按钮
        if has_browse:
            browse_btn = tk.Button(
                row,
                text="📂 浏览",
                font=("微软雅黑", 10),
                fg=self.COLORS['primary'],
                bg=self.COLORS['card'],
                bd=0,
                cursor="hand2",
                activeforeground=self.COLORS['primary_hover'],
                activebackground=self.COLORS['card'],
                command=lambda: self.browse_folder()
            )
            browse_btn.pack(side=tk.LEFT, padx=(10, 0))
    
    def create_action_bar(self, parent):
        """创建底部操作栏"""
        action_frame = tk.Frame(parent, bg=self.COLORS['bg'])
        action_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 大按钮
        self.publish_btn = self.create_gradient_button(
            action_frame,
            "🚀 一键发布到 GitHub",
            self.start_publish,
            width=850,
            height=56
        )
        self.publish_btn.pack()
    
    def create_card(self, parent, height=None):
        """创建卡片容器"""
        card = tk.Frame(
            parent,
            bg=self.COLORS['card'],
            relief=tk.FLAT,
            bd=0
        )
        
        if height:
            card.configure(height=height)
        
        # 添加阴影效果（通过边框模拟）
        card.configure(highlightbackground=self.COLORS['border'], highlightthickness=1)
        
        return card
    
    def create_modern_entry(self, parent, placeholder="", show=None):
        """创建现代化输入框"""
        entry_frame = tk.Frame(parent, bg='#F9F9F9', highlightthickness=1, 
                              highlightbackground=self.COLORS['border'])
        
        entry = tk.Entry(
            entry_frame,
            font=("微软雅黑", 10),
            bd=0,
            bg='#F9F9F9',
            fg=self.COLORS['text'],
            insertbackground=self.COLORS['primary'],
            show=show
        )
        entry.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
        
        # 焦点效果
        def on_focus_in(e):
            entry_frame.configure(highlightbackground=self.COLORS['primary'], 
                                 highlightthickness=2)
        
        def on_focus_out(e):
            entry_frame.configure(highlightbackground=self.COLORS['border'], 
                                 highlightthickness=1)
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
        return entry_frame
    
    def create_primary_button(self, parent, text, command, width=100):
        """创建主按钮"""
        btn = tk.Button(
            parent,
            text=text,
            font=("微软雅黑", 10, "bold"),
            fg='white',
            bg=self.COLORS['primary'],
            activebackground=self.COLORS['primary_hover'],
            activeforeground='white',
            bd=0,
            cursor="hand2",
            command=command,
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        
        if width:
            btn.configure(width=width//8)  # 大致宽度
        
        btn.pack(side=tk.LEFT, padx=5)
        
        # 悬停效果
        def on_enter(e):
            btn.configure(bg=self.COLORS['primary_hover'])
        
        def on_leave(e):
            btn.configure(bg=self.COLORS['primary'])
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def create_secondary_button(self, parent, text, command, width=100):
        """创建次要按钮"""
        btn = tk.Button(
            parent,
            text=text,
            font=("微软雅黑", 10),
            fg=self.COLORS['primary'],
            bg=self.COLORS['card'],
            activebackground='#F0F0F0',
            activeforeground=self.COLORS['primary'],
            bd=1,
            relief=tk.SOLID,
            cursor="hand2",
            command=command,
            padx=15,
            pady=8
        )
        
        if width:
            btn.configure(width=width//8)
        
        btn.pack(side=tk.LEFT, padx=5)
        
        # 悬停效果
        def on_enter(e):
            btn.configure(bg='#F0F0F0')
        
        def on_leave(e):
            btn.configure(bg=self.COLORS['card'])
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def create_gradient_button(self, parent, text, command, width=200, height=50):
        """创建渐变大按钮"""
        canvas = tk.Canvas(parent, width=width, height=height, 
                          bg=self.COLORS['bg'], highlightthickness=0)
        
        # 绘制渐变圆角矩形
        self.draw_gradient_rect(canvas, 0, 0, width, height, 
                                self.COLORS['primary'], self.COLORS['primary_hover'])
        
        # 文字
        canvas.create_text(
            width//2, height//2,
            text=text,
            font=("微软雅黑", 14, "bold"),
            fill='white'
        )
        
        # 点击效果
        def on_click(e):
            command()
        
        def on_hover(e):
            canvas.configure(cursor="hand2")
        
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<Enter>", on_hover)
        
        return canvas
    
    def draw_gradient_rect(self, canvas, x1, y1, x2, y2, color1, color2, radius=12):
        """绘制渐变圆角矩形"""
        # 简化：使用单色 + 圆角
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
        canvas.create_polygon(points, smooth=True, fill=color1, outline="")
    
    def browse_folder(self):
        """浏览文件夹"""
        folder = filedialog.askdirectory(title="选择项目文件夹")
        if folder:
            self.project_path.set(folder)
            self.analyze_project(folder)
    
    def analyze_project(self, folder_path):
        """分析项目"""
        try:
            project_path = Path(folder_path)
            detector = ProjectDetector(project_path)
            info = detector.detect()
            
            # 构建信息文本
            info_parts = []
            
            # README 检查
            has_readme = (project_path / "README.md").exists()
            if has_readme:
                info_parts.append("✅ README.md")
            else:
                info_parts.append("💡 建议添加 README.md")
            
            # 项目类型
            if info.get('type'):
                type_map = {
                    'pypi': 'Python', 'npm': 'Node.js', 'docker': 'Docker'
                }
                info_parts.append(f"🔍 {type_map.get(info['type'], info['type'])}")
            
            # 版本
            if info.get('version'):
                info_parts.append(f"📌 v{info['version']}")
            
            self.info_label.configure(text=" • ".join(info_parts))
            
            # 自动填充仓库名
            if not self.repo_name.get():
                self.repo_name.set(project_path.name)
            
        except Exception as e:
            self.info_label.configure(text=f"⚠️ {str(e)}")
    
    def open_token_url(self):
        """打开 Token 获取页面"""
        import webbrowser
        webbrowser.open("https://github.com/settings/tokens/new?description=RepoFlow&scopes=repo,workflow,write:packages")
        self.show_toast("已在浏览器中打开 Token 生成页面", "info")
    
    def save_token(self):
        """保存 Token"""
        # TODO: 实现保存逻辑
        self.show_toast("Token 已保存！请重启应用", "success")
    
    def reconfigure_token(self):
        """重新配置 Token"""
        # TODO: 实现重新配置逻辑
        pass
    
    def start_publish(self):
        """开始发布"""
        # 验证
        if not self.project_path.get():
            self.show_toast("请选择项目文件夹", "error")
            return
        
        if not self.repo_name.get():
            self.show_toast("请输入仓库名称", "error")
            return
        
        if not self.github_token:
            self.show_toast("请先配置 GitHub Token", "error")
            return
        
        # TODO: 实现发布逻辑
        self.show_toast("开始发布...", "info")
    
    def show_toast(self, message, type="info"):
        """显示 Toast 提示"""
        # 创建 Toast
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        
        # 颜色
        colors = {
            'info': self.COLORS['primary'],
            'success': self.COLORS['success'],
            'error': self.COLORS['danger'],
            'warning': self.COLORS['warning']
        }
        
        bg_color = colors.get(type, self.COLORS['primary'])
        
        # 内容
        label = tk.Label(
            toast,
            text=message,
            font=("微软雅黑", 11),
            fg='white',
            bg=bg_color,
            padx=20,
            pady=12
        )
        label.pack()
        
        # 位置（屏幕底部居中）
        toast.update()
        width = toast.winfo_width()
        height = toast.winfo_height()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = self.root.winfo_screenheight() - height - 100
        toast.geometry(f"+{x}+{y}")
        
        # 3秒后自动关闭
        toast.after(3000, toast.destroy)


def main():
    root = tk.Tk()
    app = ModernGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()


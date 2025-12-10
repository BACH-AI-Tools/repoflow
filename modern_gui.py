#!/usr/bin/env python3
"""
RepoFlow - 现代化 GUI
采用 Material Design 3 风格
"""

import tkinter as tk
from tkinter import ttk, filedialog
import sys
from pathlib import Path

# 设置 UTF-8 编码
if sys.platform == 'win32':
    if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr and hasattr(sys.stderr, 'encoding') and sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from src.unified_config_manager import UnifiedConfigManager
from src.project_detector import ProjectDetector
from src.github_manager import GitHubManager
from src.git_manager import GitManager
from src.pipeline_generator import PipelineGenerator


class ModernButton(tk.Canvas):
    """现代化按钮组件"""
    
    def __init__(self, parent, text, command, bg_color="#6750A4", fg_color="#FFFFFF", 
                 width=200, height=50, corner_radius=25):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=parent['bg'])
        
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = self._lighten_color(bg_color)
        self.corner_radius = corner_radius
        self.text = text
        self.width = width
        self.height = height
        
        self.draw()
        
        # 绑定事件
        self.bind("<Button-1>", lambda e: self.on_click())
        self.bind("<Enter>", lambda e: self.on_hover())
        self.bind("<Leave>", lambda e: self.on_leave())
    
    def draw(self, bg=None):
        """绘制按钮"""
        self.delete("all")
        color = bg or self.bg_color
        
        # 绘制圆角矩形
        self.create_rounded_rectangle(
            2, 2, self.width-2, self.height-2,
            radius=self.corner_radius,
            fill=color, outline=""
        )
        
        # 绘制文字
        self.create_text(
            self.width//2, self.height//2,
            text=self.text,
            fill=self.fg_color,
            font=("微软雅黑", 12, "bold")
        )
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        """创建圆角矩形"""
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
    
    def _lighten_color(self, color):
        """变亮颜色"""
        # 简单的颜色处理
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        lighter = tuple(min(255, int(c * 1.2)) for c in rgb)
        return f'#{lighter[0]:02x}{lighter[1]:02x}{lighter[2]:02x}'
    
    def on_hover(self):
        """悬停效果"""
        self.draw(self.hover_color)
        self.config(cursor="hand2")
    
    def on_leave(self):
        """离开效果"""
        self.draw(self.bg_color)
        self.config(cursor="")
    
    def on_click(self):
        """点击效果"""
        if self.command:
            self.command()


class ModernCard(tk.Frame):
    """现代化卡片组件"""
    
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, bg="#FFFFFF", relief=tk.FLAT, **kwargs)
        
        # 添加阴影效果（通过边框模拟）
        self.config(highlightbackground="#E0E0E0", highlightthickness=1)
        
        if title:
            title_label = tk.Label(
                self, text=title,
                bg="#FFFFFF",
                fg="#1C1B1F",
                font=("微软雅黑", 14, "bold")
            )
            title_label.pack(anchor=tk.W, padx=20, pady=(15, 10))


class ModernGUI:
    """现代化主界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 RepoFlow - 现代化项目发布平台")
        
        # 设置窗口大小和最小尺寸
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 1000
        window_height = 700
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(900, 600)
        
        # Material Design 3 配色
        self.colors = {
            'primary': '#6750A4',           # 紫色
            'primary_container': '#EADDFF',
            'secondary': '#625B71',
            'surface': '#FFFBFE',
            'surface_variant': '#E7E0EC',
            'background': '#F5F5F5',
            'on_primary': '#FFFFFF',
            'on_surface': '#1C1B1F',
            'on_surface_variant': '#49454F',
            'outline': '#79747E',
            'success': '#4CAF50',
            'error': '#B3261E',
            'warning': '#F59E0B',
        }
        
        self.root.configure(bg=self.colors['background'])
        
        # 配置管理器
        self.config_mgr = UnifiedConfigManager()
        
        # 变量
        self.project_path = tk.StringVar()
        self.repo_name = tk.StringVar()
        self.org_name = tk.StringVar(value="BACH-AI-Tools")
        self.pipeline_type = tk.StringVar(value="自动检测")
        
        # 加载配置
        self.load_config()
        
        # 创建UI
        self.create_widgets()
    
    def load_config(self):
        """加载配置"""
        config = self.config_mgr.load_config()
        github_config = config.get('github', {})
        if github_config.get('org_name'):
            self.org_name.set(github_config['org_name'])
    
    def create_widgets(self):
        """创建界面组件"""
        # 主容器 - 使用渐变背景
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 顶部栏
        self.create_top_bar(main_container)
        
        # 内容区域
        content_area = tk.Frame(main_container, bg=self.colors['background'])
        content_area.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # 左侧 - 配置卡片
        left_panel = tk.Frame(content_area, bg=self.colors['background'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        self.create_config_card(left_panel)
        
        # 右侧 - 信息和日志
        right_panel = tk.Frame(content_area, bg=self.colors['background'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_info_card(right_panel)
        self.create_log_card(right_panel)
    
    def create_top_bar(self, parent):
        """创建顶部栏"""
        top_bar = tk.Frame(parent, bg=self.colors['primary'], height=80)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        # 标题
        title = tk.Label(
            top_bar,
            text="🚀 RepoFlow",
            bg=self.colors['primary'],
            fg=self.colors['on_primary'],
            font=("微软雅黑", 24, "bold")
        )
        title.pack(side=tk.LEFT, padx=30, pady=20)
        
        # 副标题
        subtitle = tk.Label(
            top_bar,
            text="现代化项目发布平台",
            bg=self.colors['primary'],
            fg=self.colors['on_primary'],
            font=("微软雅黑", 11)
        )
        subtitle.pack(side=tk.LEFT, pady=20)
        
        # 设置按钮
        settings_btn = tk.Label(
            top_bar,
            text="⚙️ 设置",
            bg=self.colors['primary'],
            fg=self.colors['on_primary'],
            font=("微软雅黑", 11),
            cursor="hand2"
        )
        settings_btn.pack(side=tk.RIGHT, padx=30, pady=20)
        settings_btn.bind("<Button-1>", lambda e: self.open_settings())
        settings_btn.bind("<Enter>", lambda e: settings_btn.config(font=("微软雅黑", 11, "underline")))
        settings_btn.bind("<Leave>", lambda e: settings_btn.config(font=("微软雅黑", 11)))
    
    def create_config_card(self, parent):
        """创建配置卡片"""
        card = ModernCard(parent, title="📁 项目配置")
        card.pack(fill=tk.BOTH, expand=True)
        
        content = tk.Frame(card, bg="#FFFFFF")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 项目文件夹
        self.create_input_field(
            content,
            "项目文件夹",
            self.project_path,
            has_browse=True
        )
        
        # 仓库名称
        self.create_input_field(
            content,
            "仓库名称",
            self.repo_name
        )
        
        # 组织名称
        self.create_input_field(
            content,
            "组织名称",
            self.org_name
        )
        
        # Pipeline 选择
        self.create_pipeline_selector(content)
        
        # 发布按钮
        btn_frame = tk.Frame(content, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X, pady=(30, 10))
        
        publish_btn = ModernButton(
            btn_frame,
            "🚀 一键发布",
            self.publish_project,
            bg_color=self.colors['primary'],
            width=250,
            height=56
        )
        publish_btn.pack(anchor=tk.CENTER)
    
    def create_input_field(self, parent, label_text, variable, has_browse=False):
        """创建输入字段"""
        container = tk.Frame(parent, bg="#FFFFFF")
        container.pack(fill=tk.X, pady=12)
        
        # 标签
        label = tk.Label(
            container,
            text=label_text,
            bg="#FFFFFF",
            fg=self.colors['on_surface_variant'],
            font=("微软雅黑", 10)
        )
        label.pack(anchor=tk.W, pady=(0, 5))
        
        # 输入框容器
        input_container = tk.Frame(container, bg="#FFFFFF")
        input_container.pack(fill=tk.X)
        
        # 输入框
        entry = tk.Entry(
            input_container,
            textvariable=variable,
            bg=self.colors['surface_variant'],
            fg=self.colors['on_surface'],
            font=("微软雅黑", 11),
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground=self.colors['outline'],
            highlightcolor=self.colors['primary']
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=12)
        
        # 浏览按钮
        if has_browse:
            browse_btn = tk.Label(
                input_container,
                text="📁",
                bg=self.colors['primary_container'],
                fg=self.colors['primary'],
                font=("Segoe UI Emoji", 20),
                cursor="hand2",
                width=3,
                relief=tk.FLAT
            )
            browse_btn.pack(side=tk.RIGHT, padx=(8, 0), ipady=4)
            browse_btn.bind("<Button-1>", lambda e: self.browse_folder())
            browse_btn.bind("<Enter>", lambda e: browse_btn.config(bg=self._darken_color(self.colors['primary_container'])))
            browse_btn.bind("<Leave>", lambda e: browse_btn.config(bg=self.colors['primary_container']))
    
    def create_pipeline_selector(self, parent):
        """创建 Pipeline 选择器"""
        container = tk.Frame(parent, bg="#FFFFFF")
        container.pack(fill=tk.X, pady=12)
        
        # 标签
        label = tk.Label(
            container,
            text="Pipeline 类型",
            bg="#FFFFFF",
            fg=self.colors['on_surface_variant'],
            font=("微软雅黑", 10)
        )
        label.pack(anchor=tk.W, pady=(0, 5))
        
        # 选项卡式选择
        options_frame = tk.Frame(container, bg="#FFFFFF")
        options_frame.pack(fill=tk.X)
        
        options = [
            ("🔍 自动检测", "自动检测"),
            ("🐳 Docker", "docker"),
            ("🐍 PyPI", "pypi"),
            ("📦 NPM", "npm")
        ]
        
        self.pipeline_buttons = {}
        for text, value in options:
            btn = tk.Label(
                options_frame,
                text=text,
                bg=self.colors['surface_variant'],
                fg=self.colors['on_surface_variant'],
                font=("微软雅黑", 10),
                cursor="hand2",
                relief=tk.FLAT,
                padx=20,
                pady=10
            )
            btn.pack(side=tk.LEFT, padx=4)
            btn.bind("<Button-1>", lambda e, v=value: self.select_pipeline(v))
            self.pipeline_buttons[value] = btn
        
        # 默认选中
        self.select_pipeline("自动检测")
    
    def select_pipeline(self, value):
        """选择 Pipeline"""
        self.pipeline_type.set(value)
        
        # 更新按钮样式
        for v, btn in self.pipeline_buttons.items():
            if v == value:
                btn.config(
                    bg=self.colors['primary'],
                    fg=self.colors['on_primary'],
                    font=("微软雅黑", 10, "bold")
                )
            else:
                btn.config(
                    bg=self.colors['surface_variant'],
                    fg=self.colors['on_surface_variant'],
                    font=("微软雅黑", 10)
                )
    
    def create_info_card(self, parent):
        """创建信息卡片"""
        card = ModernCard(parent, title="📊 项目信息")
        card.pack(fill=tk.X, pady=(0, 15))
        
        content = tk.Frame(card, bg="#FFFFFF")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.info_text = tk.Text(
            content,
            bg="#FAFAFA",
            fg=self.colors['on_surface'],
            font=("微软雅黑", 10),
            relief=tk.FLAT,
            height=6,
            padx=15,
            pady=10,
            state=tk.DISABLED
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
    
    def create_log_card(self, parent):
        """创建日志卡片"""
        card = ModernCard(parent, title="📋 发布日志")
        card.pack(fill=tk.BOTH, expand=True)
        
        content = tk.Frame(card, bg="#FFFFFF")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 日志文本框（深色主题）
        self.log_text = tk.Text(
            content,
            bg="#1E1E1E",
            fg="#D4D4D4",
            font=("Consolas", 9),
            relief=tk.FLAT,
            padx=15,
            pady=10,
            insertbackground='white'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置标签颜色
        self.log_text.tag_config("success", foreground="#4CAF50")
        self.log_text.tag_config("error", foreground="#F44336")
        self.log_text.tag_config("warning", foreground="#FF9800")
        self.log_text.tag_config("info", foreground="#2196F3")
        
        # 清空按钮
        clear_btn = tk.Label(
            content,
            text="🗑️ 清空日志",
            bg=self.colors['surface_variant'],
            fg=self.colors['on_surface_variant'],
            font=("微软雅黑", 9),
            cursor="hand2",
            padx=15,
            pady=6
        )
        clear_btn.pack(anchor=tk.E, pady=(8, 0))
        clear_btn.bind("<Button-1>", lambda e: self.clear_log())
    
    def open_settings(self):
        """打开设置"""
        from settings_window import SettingsWindow
        SettingsWindow(self.root)
    
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
            
            # 显示项目信息
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            
            info_lines = []
            
            # README 状态
            if (project_path / "README.md").exists():
                info_lines.append("✅ 包含 README.md")
            else:
                info_lines.append("⚠️  缺少 README.md（必需）")
            
            # 项目类型
            project_type = info.get('type', 'unknown')
            type_names = {
                'pypi': '🐍 Python (PyPI)',
                'npm': '📦 Node.js (NPM)',
                'docker': '🐳 Docker'
            }
            info_lines.append(f"类型: {type_names.get(project_type, project_type)}")
            
            # 版本号
            if info.get('version'):
                info_lines.append(f"版本: {info['version']}")
            
            # 包名
            if info.get('package_name'):
                info_lines.append(f"包名: {info['package_name']}")
            
            # 描述
            if info.get('description'):
                desc = info['description'][:100]
                info_lines.append(f"\n描述: {desc}...")
            
            self.info_text.insert(1.0, '\n'.join(info_lines))
            self.info_text.config(state=tk.DISABLED)
            
            # 自动填充仓库名
            if not self.repo_name.get():
                self.repo_name.set(project_path.name)
            
            # 自动选择 Pipeline
            if project_type in ['pypi', 'npm', 'docker']:
                self.select_pipeline(project_type)
            
        except Exception as e:
            self.log(f"❌ 分析项目失败: {str(e)}\n", "error")
    
    def publish_project(self):
        """发布项目"""
        # 验证
        if not self.project_path.get():
            self.log("❌ 请选择项目文件夹\n", "error")
            return
        
        if not self.repo_name.get():
            self.log("❌ 请输入仓库名称\n", "error")
            return
        
        # 检查配置
        config = self.config_mgr.load_config()
        if not config.get('github', {}).get('token'):
            self.log("❌ 请先在设置中配置 GitHub Token\n", "error")
            return
        
        self.log("🚀 开始发布流程...\n\n", "info")
        
        # 在新线程中执行
        import threading
        thread = threading.Thread(target=self._do_publish)
        thread.daemon = True
        thread.start()
    
    def _do_publish(self):
        """执行发布"""
        try:
            project_path = Path(self.project_path.get())
            repo_name = self.repo_name.get()
            org_name = self.org_name.get()
            pipeline = self.pipeline_type.get()
            
            config = self.config_mgr.load_config()
            github_token = config.get('github', {}).get('token')
            
            # 步骤 1: 检查 README
            self.log("📋 步骤 1/4: 检查项目文件\n", "info")
            if not (project_path / "README.md").exists():
                self.log("  ❌ 缺少 README.md，无法发布\n", "error")
                return
            self.log("  ✅ README.md 存在\n", "success")
            
            # 步骤 2: 检测项目类型
            self.log("\n🔍 步骤 2/4: 检测项目类型\n", "info")
            detector = ProjectDetector(project_path)
            info = detector.detect()
            
            if pipeline == "自动检测":
                pipeline = info.get('type', 'docker')
                self.log(f"  自动检测: {pipeline}\n", "success")
            else:
                self.log(f"  使用指定: {pipeline}\n", "info")
            
            # 步骤 3: 创建 GitHub 仓库
            self.log("\n📦 步骤 3/4: 创建 GitHub 仓库\n", "info")
            self.log(f"  组织: {org_name}\n", "info")
            self.log(f"  仓库: {repo_name}\n", "info")
            
            github_mgr = GitHubManager(github_token)
            repo_url, is_new = github_mgr.create_repository(org_name, repo_name)
            
            if is_new:
                self.log("  ✅ 仓库已创建\n", "success")
            else:
                self.log("  ⚠️  仓库已存在，将更新代码\n", "warning")
            
            # 生成 Pipeline
            self.log("\n🔧 生成 CI/CD Pipeline\n", "info")
            pipeline_gen = PipelineGenerator()
            pipeline_gen.generate(pipeline, project_path)
            self.log(f"  ✅ {pipeline.upper()} Pipeline 已生成\n", "success")
            
            # 步骤 4: 推送代码
            self.log("\n📤 步骤 4/4: 推送代码到 GitHub\n", "info")
            git_mgr = GitManager(project_path)
            git_mgr.init_and_push(repo_url)
            self.log("  ✅ 代码已推送\n", "success")
            
            # 完成
            self.log("\n" + "="*60 + "\n", "success")
            self.log("🎉 发布完成！\n", "success")
            self.log("="*60 + "\n", "success")
            self.log(f"\n📍 仓库: https://github.com/{org_name}/{repo_name}\n", "info")
            self.log(f"🔗 Actions: https://github.com/{org_name}/{repo_name}/actions\n", "info")
            
        except Exception as e:
            self.log(f"\n❌ 发布失败: {str(e)}\n", "error")
    
    def log(self, message, tag="info"):
        """写入日志"""
        self.log_text.insert(tk.END, message, tag)
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def _darken_color(self, color):
        """变暗颜色"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darker = tuple(max(0, int(c * 0.8)) for c in rgb)
        return f'#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}'


def main():
    """主函数"""
    root = tk.Tk()
    app = ModernGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()


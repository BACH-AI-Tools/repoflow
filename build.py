#!/usr/bin/env python3
"""
RepoFlow 打包脚本
使用 PyInstaller 将 GUI 打包成 .exe 应用程序
"""

import PyInstaller.__main__
import sys
from pathlib import Path

def build():
    """构建 RepoFlow 可执行文件"""
    
    # 获取项目根目录
    root_dir = Path(__file__).parent
    
    # 根据平台设置文件名
    if sys.platform == 'win32':
        app_name = 'RepoFlow.exe'
    else:
        app_name = 'RepoFlow'
    
    print(f"🔨 开始构建 {app_name}...")
    print(f"📁 项目目录: {root_dir}")
    print(f"🖥️  平台: {sys.platform}")
    print()
    
    # 数据文件分隔符（Windows 用 ; 其他用 :）
    data_separator = ';' if sys.platform == 'win32' else ':'
    
    # PyInstaller 参数
    args = [
        'repoflow_gui.py',          # 主程序
        '--name=RepoFlow',           # 应用名称
        '--onefile',                 # 打包成单个文件
        '--windowed',                # GUI 模式（不显示控制台）
        '--icon=NONE',               # 图标（如果有的话）
        
        # 添加依赖的包
        '--hidden-import=github',
        '--hidden-import=git',
        '--hidden-import=rich',
        '--hidden-import=click',
        '--hidden-import=nacl',
        
        # 添加数据文件（跨平台兼容）
        f'--add-data=src{data_separator}src',
        
        # 清理选项
        '--clean',
        '--noconfirm',
        
        # 输出目录
        '--distpath=dist',
        '--workpath=build',
        '--specpath=.',
    ]
    
    print("📦 PyInstaller 参数:")
    for arg in args:
        print(f"  {arg}")
    print()
    
    # 运行 PyInstaller
    PyInstaller.__main__.run(args)
    
    # 获取实际生成的文件名
    if sys.platform == 'win32':
        exe_name = 'RepoFlow.exe'
        run_cmd = '双击 dist\\RepoFlow.exe 即可启动'
    else:
        exe_name = 'RepoFlow'
        run_cmd = 'chmod +x dist/RepoFlow && ./dist/RepoFlow'
    
    print()
    print("=" * 60)
    print("✅ 构建完成！")
    print("=" * 60)
    print()
    print(f"📍 可执行文件位置: {root_dir / 'dist' / exe_name}")
    print(f"📊 文件大小: {(root_dir / 'dist' / exe_name).stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("🚀 运行方式:")
    print(f"  {run_cmd}")
    print()

if __name__ == '__main__':
    try:
        build()
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        sys.exit(1)


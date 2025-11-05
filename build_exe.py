#!/usr/bin/env python3
"""
RepoFlow 打包脚本
使用 PyInstaller 将 GUI 打包成 .exe 应用程序
"""

import PyInstaller.__main__
import sys
import os
from pathlib import Path

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    # 强制使用 UTF-8 编码
    sys.stdout.reconfigure(encoding='utf-8') if sys.stdout else None
    sys.stderr.reconfigure(encoding='utf-8') if sys.stderr else None
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def build():
    """构建 RepoFlow 可执行文件"""
    
    # 获取项目根目录
    root_dir = Path(__file__).parent
    
    # 根据平台设置文件名
    if sys.platform == 'win32':
        app_name = 'RepoFlow.exe'
    else:
        app_name = 'RepoFlow'
    
    print(f"Building {app_name}...")
    print(f"Project directory: {root_dir}")
    print(f"Platform: {sys.platform}")
    print()
    
    # 数据文件分隔符（Windows 用 ; 其他用 :）
    data_separator = ';' if sys.platform == 'win32' else ':'
    
    # PyInstaller 参数
    args = [
        'repoflow_gui.py',          # 主程序
        '--name=RepoFlow',           # 应用名称
        '--onefile',                 # 打包成单个文件
        
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
    
    # 平台特定参数
    if sys.platform == 'win32':
        # Windows: 使用 windowed 模式隐藏控制台
        args.append('--windowed')
    # macOS 和 Linux 不使用 windowed，避免兼容性问题
    
    print("PyInstaller arguments:")
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
    print("BUILD SUCCESSFUL!")
    print("=" * 60)
    print()
    print(f"Executable location: {root_dir / 'dist' / exe_name}")
    print(f"File size: {(root_dir / 'dist' / exe_name).stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("How to run:")
    print(f"  {run_cmd}")
    print()

if __name__ == '__main__':
    try:
        build()
    except Exception as e:
        print(f"BUILD FAILED: {e}")
        sys.exit(1)


"""GitHub 仓库克隆和包名修改模块"""

import subprocess
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Tuple
import tempfile
import json


# 允许再发布的许可证：(SPDX ID, 许可证正文特征)，按顺序匹配
KNOWN_LICENSES = [
    ('AGPL-3.0', r'GNU AFFERO GENERAL PUBLIC LICENSE'),
    ('LGPL', r'GNU LESSER GENERAL PUBLIC LICENSE'),
    ('GPL', r'GNU GENERAL PUBLIC LICENSE'),
    ('Apache-2.0', r'Apache License,?\s+Version 2\.0'),
    ('MPL-2.0', r'Mozilla Public License,?\s+(Version|v\.?)\s*2\.0'),
    ('MIT', r'Permission is hereby granted,?\s+free of charge'),
    ('BSD-3-Clause', r'Neither the name of'),
    ('BSD-2-Clause', r'Redistribution and use in source and binary forms'),
    ('ISC', r'Permission to use, copy, modify, and/?or distribute this software for any\s+purpose'),
    ('Unlicense', r'This is free and unencumbered software released into the public domain'),
]

LICENSE_FILE_NAMES = ('LICENSE', 'LICENCE', 'COPYING', 'LICENSE-MIT', 'LICENSE-APACHE')


class RepoCloner:
    """克隆GitHub仓库并修改包名"""

    def __init__(self, prefix: str = "bachai", accept_unknown_license: bool = False):
        """
        初始化克隆器

        Args:
            prefix: 包名前缀，默认为 "bachai"
            accept_unknown_license: 许可证文件存在但无法自动识别时，是否在人工确认后继续
        """
        self.prefix = prefix
        self.accept_unknown_license = accept_unknown_license
        self.temp_dir = None
        self.cloned_repo_path = None
        self.original_package_name = None
        self.new_package_name = None
        self.project_type = None
        self.license_id = None
        self.license_file = None
        self.original_author = None
    
    def clone_repository(self, github_url: str, target_dir: Optional[Path] = None) -> Path:
        """
        克隆GitHub仓库
        
        Args:
            github_url: GitHub仓库URL（支持 https 和 git 格式）
            target_dir: 目标目录，如果为None则创建临时目录
            
        Returns:
            Path: 克隆后的仓库路径
        """
        print(f"\n{'='*60}")
        print(f"步骤 1: 克隆 GitHub 仓库")
        print(f"{'='*60}")
        print(f"🔗 仓库URL: {github_url}")
        
        # 提取仓库名称
        repo_name = self._extract_repo_name(github_url)
        print(f"📦 仓库名称: {repo_name}")
        
        # 创建目标目录
        if target_dir is None:
            self.temp_dir = Path(tempfile.mkdtemp(prefix="repoflow_clone_"))
            target_dir = self.temp_dir / repo_name
        else:
            target_dir = Path(target_dir)
        
        print(f"📁 克隆到: {target_dir}")
        
        # 如果目标目录已存在，先删除
        if target_dir.exists():
            print(f"⚠️  目标目录已存在，删除中...")
            shutil.rmtree(target_dir)
        
        # 克隆仓库
        try:
            print(f"⏬ 正在克隆...")
            result = subprocess.run(
                ['git', 'clone', github_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise Exception(f"克隆失败: {result.stderr}")
            
            print(f"✅ 克隆成功")
            self.cloned_repo_path = target_dir
            return target_dir
            
        except subprocess.TimeoutExpired:
            raise Exception("克隆超时（5分钟）")
        except Exception as e:
            raise Exception(f"克隆失败: {str(e)}")
    
    def detect_project_type(self, repo_path: Path) -> str:
        """
        检测项目类型
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            str: 项目类型（'python', 'node.js', 'unknown'）
        """
        print(f"\n{'='*60}")
        print(f"步骤 2: 检测项目类型")
        print(f"{'='*60}")
        
        # 检查 Python 项目标志
        python_files = [
            repo_path / 'setup.py',
            repo_path / 'pyproject.toml',
            repo_path / 'requirements.txt'
        ]
        
        if any(f.exists() for f in python_files):
            self.project_type = 'python'
            print(f"🐍 检测到: Python 项目")
            return 'python'
        
        # 检查 Node.js 项目标志
        nodejs_files = [
            repo_path / 'package.json',
            repo_path / 'package-lock.json',
            repo_path / 'yarn.lock'
        ]
        
        if any(f.exists() for f in nodejs_files):
            self.project_type = 'node.js'
            print(f"📦 检测到: Node.js 项目")
            return 'node.js'
        
        self.project_type = 'unknown'
        print(f"❓ 未知项目类型")
        return 'unknown'
    
    def get_original_package_name(self, repo_path: Path) -> Optional[str]:
        """
        获取原始包名
        
        Args:
            repo_path: 仓库路径
            
        Returns:
            str: 原始包名，如果找不到返回 None
        """
        print(f"\n{'='*60}")
        print(f"步骤 3: 获取原始包名")
        print(f"{'='*60}")
        
        if self.project_type == 'python':
            return self._get_python_package_name(repo_path)
        elif self.project_type == 'node.js':
            return self._get_nodejs_package_name(repo_path)
        else:
            print(f"❌ 无法获取包名（未知项目类型）")
            return None
    
    def _get_python_package_name(self, repo_path: Path) -> Optional[str]:
        """获取Python项目的包名"""
        # 1. 尝试从 pyproject.toml 读取
        pyproject_file = repo_path / 'pyproject.toml'
        if pyproject_file.exists():
            try:
                content = pyproject_file.read_text(encoding='utf-8')
                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    package_name = match.group(1)
                    print(f"📦 从 pyproject.toml 读取: {package_name}")
                    self.original_package_name = package_name
                    return package_name
            except Exception as e:
                print(f"⚠️  读取 pyproject.toml 失败: {e}")
        
        # 2. 尝试从 setup.py 读取
        setup_file = repo_path / 'setup.py'
        if setup_file.exists():
            try:
                content = setup_file.read_text(encoding='utf-8')
                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    package_name = match.group(1)
                    print(f"📦 从 setup.py 读取: {package_name}")
                    self.original_package_name = package_name
                    return package_name
            except Exception as e:
                print(f"⚠️  读取 setup.py 失败: {e}")
        
        print(f"❌ 未找到包名")
        return None
    
    def _get_nodejs_package_name(self, repo_path: Path) -> Optional[str]:
        """获取Node.js项目的包名"""
        package_json = repo_path / 'package.json'
        if package_json.exists():
            try:
                content = json.loads(package_json.read_text(encoding='utf-8'))
                package_name = content.get('name')
                if package_name:
                    print(f"📦 从 package.json 读取: {package_name}")
                    self.original_package_name = package_name
                    return package_name
            except Exception as e:
                print(f"⚠️  读取 package.json 失败: {e}")
        
        print(f"❌ 未找到包名")
        return None
    
    def modify_package_name(self, repo_path: Path, new_prefix: Optional[str] = None) -> Tuple[str, str]:
        """
        修改包名，添加前缀
        
        Args:
            repo_path: 仓库路径
            new_prefix: 新前缀，如果为None则使用初始化时的前缀
            
        Returns:
            Tuple[str, str]: (原始包名, 新包名)
        """
        print(f"\n{'='*60}")
        print(f"步骤 4: 修改包名")
        print(f"{'='*60}")
        
        if new_prefix:
            self.prefix = new_prefix
        
        if not self.original_package_name:
            self.get_original_package_name(repo_path)
        
        if not self.original_package_name:
            raise Exception("无法获取原始包名")
        
        # 生成新包名
        # 如果原包名已经有 @scope/ 前缀（NPM），保留 scope
        if '/' in self.original_package_name and self.project_type == 'node.js':
            scope, name = self.original_package_name.split('/', 1)
            # 检查名称是否已有前缀
            if not name.startswith(f"{self.prefix}-"):
                self.new_package_name = f"{scope}/{self.prefix}-{name}"
            else:
                self.new_package_name = self.original_package_name
        else:
            # 检查名称是否已有前缀
            if not self.original_package_name.startswith(f"{self.prefix}-"):
                self.new_package_name = f"{self.prefix}-{self.original_package_name}"
            else:
                self.new_package_name = self.original_package_name
        
        print(f"📦 原始包名: {self.original_package_name}")
        print(f"📦 新包名: {self.new_package_name}")
        
        # 执行修改
        if self.project_type == 'python':
            self._modify_python_package_name(repo_path)
        elif self.project_type == 'node.js':
            self._modify_nodejs_package_name(repo_path)
        
        print(f"✅ 包名修改完成")
        return (self.original_package_name, self.new_package_name)
    
    def _modify_python_package_name(self, repo_path: Path):
        """修改Python项目的包名"""
        modified_files = []
        
        # 修改 pyproject.toml
        pyproject_file = repo_path / 'pyproject.toml'
        if pyproject_file.exists():
            try:
                content = pyproject_file.read_text(encoding='utf-8')
                new_content = re.sub(
                    r'(name\s*=\s*["\'])' + re.escape(self.original_package_name) + r'(["\'])',
                    r'\1' + self.new_package_name + r'\2',
                    content
                )
                pyproject_file.write_text(new_content, encoding='utf-8')
                modified_files.append('pyproject.toml')
                print(f"  ✓ 修改 pyproject.toml")
            except Exception as e:
                print(f"  ⚠️  修改 pyproject.toml 失败: {e}")
        
        # 修改 setup.py
        setup_file = repo_path / 'setup.py'
        if setup_file.exists():
            try:
                content = setup_file.read_text(encoding='utf-8')
                new_content = re.sub(
                    r'(name\s*=\s*["\'])' + re.escape(self.original_package_name) + r'(["\'])',
                    r'\1' + self.new_package_name + r'\2',
                    content
                )
                setup_file.write_text(new_content, encoding='utf-8')
                modified_files.append('setup.py')
                print(f"  ✓ 修改 setup.py")
            except Exception as e:
                print(f"  ⚠️  修改 setup.py 失败: {e}")
        
        if not modified_files:
            raise Exception("未找到可修改的配置文件")
    
    def _modify_nodejs_package_name(self, repo_path: Path):
        """修改Node.js项目的包名"""
        package_json = repo_path / 'package.json'
        if not package_json.exists():
            raise Exception("未找到 package.json")
        
        try:
            content = json.loads(package_json.read_text(encoding='utf-8'))
            content['name'] = self.new_package_name
            
            # 保存修改
            package_json.write_text(
                json.dumps(content, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            print(f"  ✓ 修改 package.json")
        except Exception as e:
            raise Exception(f"修改 package.json 失败: {e}")
    
    def check_license(self, repo_path: Path) -> str:
        """
        检查上游许可证是否允许再发布

        没有许可证文件 = 保留所有权利，不能再发布；
        许可证无法识别时，需人工确认后通过 accept_unknown_license 放行。

        Args:
            repo_path: 仓库路径

        Returns:
            str: 许可证 SPDX ID
        """
        print(f"\n{'='*60}")
        print(f"步骤: 检查上游许可证")
        print(f"{'='*60}")

        license_file = None
        for f in sorted(repo_path.iterdir()):
            if f.is_file() and f.stem.upper() in LICENSE_FILE_NAMES:
                license_file = f
                break

        if not license_file:
            raise Exception(
                "上游仓库没有 LICENSE 文件（默认保留所有权利），不能再发布。"
                "请联系原作者添加开源许可证或取得授权"
            )

        text = license_file.read_text(encoding='utf-8', errors='ignore')
        license_id = None
        for spdx_id, pattern in KNOWN_LICENSES:
            if re.search(pattern, text, re.IGNORECASE):
                license_id = spdx_id
                break

        if not license_id:
            if not self.accept_unknown_license:
                raise Exception(
                    f"无法识别上游许可证（{license_file.name}），请人工确认允许再发布后，"
                    f"使用 --accept-license 继续"
                )
            license_id = 'see LICENSE'
            print(f"⚠️  许可证无法自动识别，已人工确认: {license_file.name}")

        print(f"📜 许可证: {license_id}（{license_file.name}）")
        if license_id in ('AGPL-3.0', 'LGPL', 'GPL', 'MPL-2.0'):
            print(f"💡 Copyleft 许可证：再发布的包必须继续使用 {license_id} 并公开源码")

        self.license_id = license_id
        self.license_file = license_file.name
        return license_id

    def add_attribution(self, repo_path: Path, github_url: str):
        """
        写入上游署名：新增 UPSTREAM.md，并在 README 顶部加 fork 说明

        原有 LICENSE / NOTICE / 作者信息保持不变。

        Args:
            repo_path: 仓库路径
            github_url: 上游仓库 URL
        """
        print(f"\n{'='*60}")
        print(f"步骤: 写入上游署名")
        print(f"{'='*60}")

        upstream_url = github_url.rstrip('/')
        if upstream_url.endswith('.git'):
            upstream_url = upstream_url[:-4]

        commit = ''
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path, capture_output=True, text=True, timeout=30
            )
            commit = result.stdout.strip()
        except Exception:
            pass

        self.original_author = self._get_original_author(repo_path, upstream_url)

        upstream_md = repo_path / 'UPSTREAM.md'
        upstream_md.write_text(
            f"# Upstream\n\n"
            f"This package is a republished fork of [{upstream_url}]({upstream_url}).\n"
            f"All credit for the original work goes to its authors.\n\n"
            f"- Upstream repository: {upstream_url}\n"
            f"- Upstream commit: {commit or 'unknown'}\n"
            f"- Original author(s): {self.original_author}\n"
            f"- Original package name: `{self.original_package_name}`\n"
            f"- Republished as: `{self.new_package_name}`\n"
            f"- License: {self.license_id} (unchanged, see [{self.license_file}]({self.license_file}))\n\n"
            f"## Changes\n\n"
            f"- Package renamed from `{self.original_package_name}` to `{self.new_package_name}`\n"
            f"- Added CI/CD publishing workflow\n",
            encoding='utf-8'
        )
        print(f"  ✓ 写入 UPSTREAM.md")

        notice = (
            f"> **Fork notice:** this package is a republished fork of "
            f"[{upstream_url}]({upstream_url}) (original package `{self.original_package_name}`, "
            f"by {self.original_author}). "
            f"All credit goes to the original authors. It is distributed under the original "
            f"license ({self.license_id}) — see [{self.license_file}]({self.license_file}) "
            f"and [UPSTREAM.md](UPSTREAM.md).\n\n"
        )
        readme = next((f for f in sorted(repo_path.iterdir())
                       if f.is_file() and f.name.lower() == 'readme.md'), None)
        if readme:
            content = readme.read_text(encoding='utf-8', errors='ignore')
            if 'Fork notice:' not in content:
                readme.write_text(notice + content, encoding='utf-8')
                print(f"  ✓ README 顶部加入 fork 说明")
        else:
            print(f"  ⚠️  未找到 README.md，仅写入 UPSTREAM.md")

    def _get_original_author(self, repo_path: Path, upstream_url: str) -> str:
        """
        读取上游作者：依次查 package.json / pyproject.toml / setup.py，
        都没有则用上游仓库的 GitHub 用户名

        Args:
            repo_path: 仓库路径
            upstream_url: 上游仓库 URL

        Returns:
            str: 上游作者
        """
        package_json = repo_path / 'package.json'
        if package_json.exists():
            try:
                author = json.loads(package_json.read_text(encoding='utf-8')).get('author')
                if isinstance(author, dict):
                    author = author.get('name')
                if author:
                    return str(author)
            except Exception:
                pass

        patterns = [
            ('pyproject.toml', r'authors\s*=\s*\[\s*\{[^}]*name\s*=\s*["\']([^"\']+)["\']'),
            ('setup.py', r'author\s*=\s*["\']([^"\']+)["\']'),
        ]
        for file_name, pattern in patterns:
            f = repo_path / file_name
            if f.exists():
                match = re.search(pattern, f.read_text(encoding='utf-8', errors='ignore'))
                if match:
                    return match.group(1)

        # https://github.com/<owner>/<repo> 或 git@github.com:<owner>/<repo>
        parts = re.split(r'[/:]', upstream_url)
        return parts[-2] if len(parts) >= 2 else 'unknown'

    def _extract_repo_name(self, github_url: str) -> str:
        """
        从GitHub URL提取仓库名称
        
        Args:
            github_url: GitHub URL
            
        Returns:
            str: 仓库名称
        """
        # 移除 .git 后缀
        url = github_url.rstrip('/').replace('.git', '')
        
        # 提取最后一部分作为仓库名
        parts = url.split('/')
        repo_name = parts[-1]
        
        return repo_name
    
    def cleanup(self):
        """清理临时目录"""
        if self.temp_dir and self.temp_dir.exists():
            print(f"\n🧹 清理临时目录: {self.temp_dir}")
            try:
                shutil.rmtree(self.temp_dir)
                print(f"✅ 清理完成")
            except Exception as e:
                print(f"⚠️  清理失败: {e}")
    
    def clone_and_modify(
        self,
        github_url: str,
        output_dir: Optional[Path] = None,
        prefix: Optional[str] = None
    ) -> Dict:
        """
        一站式克隆和修改
        
        Args:
            github_url: GitHub仓库URL
            output_dir: 输出目录（可选）
            prefix: 包名前缀（可选）
            
        Returns:
            Dict: 包含处理结果的字典
        """
        try:
            # 1. 克隆仓库
            repo_path = self.clone_repository(github_url, output_dir)
            
            # 2. 检测项目类型
            project_type = self.detect_project_type(repo_path)
            
            if project_type == 'unknown':
                raise Exception("不支持的项目类型")
            
            # 3. 获取原始包名
            original_name = self.get_original_package_name(repo_path)
            
            if not original_name:
                raise Exception("无法获取包名")
            
            # 4. 检查许可证（不允许再发布则中止）
            license_id = self.check_license(repo_path)

            # 5. 修改包名
            old_name, new_name = self.modify_package_name(repo_path, prefix)

            # 6. 写入上游署名
            self.add_attribution(repo_path, github_url)

            print(f"\n{'='*60}")
            print(f"✅ 处理完成")
            print(f"{'='*60}")
            print(f"📁 仓库路径: {repo_path}")
            print(f"📦 原始包名: {old_name}")
            print(f"📦 新包名: {new_name}")
            print(f"🔧 项目类型: {project_type}")
            print(f"📜 许可证: {license_id}")

            return {
                'success': True,
                'repo_path': repo_path,
                'project_type': project_type,
                'original_package_name': old_name,
                'new_package_name': new_name,
                'license': license_id,
                'original_author': self.original_author
            }
            
        except Exception as e:
            print(f"\n❌ 处理失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# 测试代码
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python repo_cloner.py <github_url> [prefix]")
        print("示例: python repo_cloner.py https://github.com/user/repo bachai")
        sys.exit(1)
    
    github_url = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else "bachai"
    
    cloner = RepoCloner(prefix=prefix)
    result = cloner.clone_and_modify(github_url)
    
    if result['success']:
        print(f"\n✅ 成功！")
        print(f"仓库已克隆到: {result['repo_path']}")
        print(f"新包名: {result['new_package_name']}")
    else:
        print(f"\n❌ 失败: {result['error']}")
        sys.exit(1)






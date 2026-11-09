"""GitHub 仓库克隆和包名修改模块"""

import subprocess
import shutil
import re
from pathlib import Path
from typing import Optional, Dict, Tuple
import tempfile
import json


class RepoCloner:
    """克隆GitHub仓库并修改包名"""
    
    def __init__(self, prefix: str = "bachai"):
        """
        初始化克隆器
        
        Args:
            prefix: 包名前缀，默认为 "bachai"
        """
        self.prefix = prefix
        self.temp_dir = None
        self.cloned_repo_path = None
        self.original_package_name = None
        self.new_package_name = None
        self.project_type = None
    
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
        prefix: Optional[str] = None,
        allow_unlicensed: bool = False
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

            # 2.5 上游来源与许可证（必须在改包名之前读，改完就读不到原作者了）
            from src import provenance
            prov = provenance.require_license(provenance.detect(repo_path, github_url), allow_unlicensed)
            print(f"📜 上游许可证: {prov['license'] or '未识别'}（{', '.join(prov['license_files']) or '无许可证文件'}）")
            print(f"👤 原作者: {', '.join(prov['authors']) or '未知'}")
            for w in prov['warnings']:
                print(f"⚠️  {w}")

            # 3. 获取原始包名
            original_name = self.get_original_package_name(repo_path)
            
            if not original_name:
                raise Exception("无法获取包名")
            
            # 4. 修改包名
            old_name, new_name = self.modify_package_name(repo_path, prefix)
            
            print(f"\n{'='*60}")
            print(f"✅ 处理完成")
            print(f"{'='*60}")
            print(f"📁 仓库路径: {repo_path}")
            print(f"📦 原始包名: {old_name}")
            print(f"📦 新包名: {new_name}")
            print(f"🔧 项目类型: {project_type}")
            
            return {
                'success': True,
                'repo_path': repo_path,
                'project_type': project_type,
                'original_package_name': old_name,
                'new_package_name': new_name,
                'provenance': prov
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






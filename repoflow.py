#!/usr/bin/env python3
"""
RepoFlow - 自动化项目发布工具
用于简化从本地项目到GitHub发布的完整流程
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import sys
import os

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    import locale
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
    # 设置控制台代码页为 UTF-8
    os.system('chcp 65001 >nul 2>&1')

from src.github_manager import GitHubManager
from src.secret_scanner import SecretScanner
from src.pipeline_generator import PipelineGenerator
from src.git_manager import GitManager
from src.config_manager import ConfigManager
from src.unified_config_manager import UnifiedConfigManager
from src.docker_manager import DockerManager
from src.pypi_manager import PyPIManager
from src.project_detector import ProjectDetector

console = Console()


def load_cli_config() -> dict:
    """
    读取 CLI 配置：与 GUI 共用 ~/.repoflow/config.json，
    旧版 CLI 保存在 ~/.emcpflow/config.json 的值仅作兜底
    """
    unified = UnifiedConfigManager()
    # 文件不存在时 load_config() 返回默认值，会盖住旧配置里的组织名
    config = unified.load_config() if unified.config_file.exists() else {}
    legacy = ConfigManager().load_config()
    return {
        "github_token": config.get("github", {}).get("token") or legacy.get("github_token", ""),
        "default_org": config.get("github", {}).get("org_name") or legacy.get("default_org", "BACH-AI-Tools"),
        "dockerhub_username": config.get("dockerhub", {}).get("username") or legacy.get("dockerhub_username", ""),
    }


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """RepoFlow - 自动化项目发布工具"""
    pass


@cli.command()
def config():
    """配置 RepoFlow（GitHub Token 等）"""
    console.print(Panel.fit("🔧 RepoFlow 配置", style="bold blue"))
    
    config_mgr = UnifiedConfigManager()
    
    github_token = click.prompt("请输入 GitHub Personal Access Token", hide_input=True)
    default_org = click.prompt("默认 GitHub 组织名称", default=config_mgr.get_github_org())
    dockerhub_username = click.prompt("DockerHub 用户名（可选）", default="")
    
    # 只更新相关字段，保留 GUI 中保存的其他配置
    config = config_mgr.load_config()
    config.setdefault("github", {}).update({"token": github_token, "org_name": default_org})
    config.setdefault("dockerhub", {})["username"] = dockerhub_username
    if not config_mgr.save_config(config):
        console.print("❌ 保存配置失败", style="bold red")
        sys.exit(1)
    
    console.print(f"✅ 配置已保存到 {config_mgr.get_config_file_path()}（与 GUI 共用）", style="bold green")


@cli.command()
@click.option('--org', help='GitHub 组织名称')
@click.option('--repo', required=True, help='仓库名称')
@click.option('--path', type=click.Path(exists=True), default='.', help='要发布的项目路径（默认当前目录）')
@click.option('--private/--public', default=False, help='是否创建私有仓库')
@click.option('--pipeline', type=click.Choice(['docker', 'npm', 'pypi', 'all', 'auto']), 
              help='Pipeline 类型（auto=自动检测）')
@click.option('--skip-scan', is_flag=True, help='跳过敏感信息扫描')
@click.option('--setup-secrets', is_flag=True, help='自动设置 GitHub Secrets')
@click.option('--deploy-method', 
              type=click.Choice(['workflow', 'local', 'both']),
              default='workflow',
              help='部署方式：workflow=GitHub Actions, local=本地构建推送, both=两者都要')
@click.option('--docker-image', help='Docker 镜像名称（用于本地部署，如: username/repo）')
@click.option('--docker-tag', default='latest', help='Docker 镜像标签')
def init(org, repo, path, private, pipeline, skip_scan, setup_secrets, deploy_method, docker_image, docker_tag):
    """初始化并发布项目到 GitHub（完整流程）"""
    console.print(Panel.fit("🚀 RepoFlow 自动化发布流程", style="bold magenta"))
    
    config = load_cli_config()
    
    if not config.get('github_token'):
        console.print("❌ 请先运行 'repoflow config' 或在 GUI 设置中配置 GitHub Token", style="bold red")
        sys.exit(1)
    
    org = org or config.get('default_org', 'BACH-AI-Tools')
    
    # 转换为绝对路径
    project_path = Path(path).resolve()
    console.print(f"\n📁 [cyan]项目路径:[/cyan] {project_path}")
    
    # 自动检测项目类型
    detector = ProjectDetector(project_path)
    
    if pipeline == 'auto' or not pipeline:
        info = detector.get_project_info()
        
        if info['recommended_pipelines']:
            detected_pipeline = info['recommended_pipelines'][0]
            console.print(f"\n🔎 [cyan]自动检测:[/cyan] {', '.join(info['detected_types'])}")
            console.print(f"📦 [cyan]推荐 Pipeline:[/cyan] {detected_pipeline}")
            
            if not click.confirm(f"\n使用推荐的 Pipeline '{detected_pipeline}'?", default=True):
                pipeline = click.prompt("请选择 Pipeline", 
                                       type=click.Choice(['docker', 'npm', 'pypi', 'all']))
            else:
                pipeline = detected_pipeline
        else:
            console.print("\n⚠️  [yellow]未能自动检测项目类型[/yellow]")
            pipeline = click.prompt("请选择 Pipeline", 
                                   type=click.Choice(['docker', 'npm', 'pypi', 'all']))
    
    # 验证 Pipeline 是否适合当前项目
    if pipeline:
        validation = detector.validate_pipeline(pipeline)
        if not validation['valid']:
            console.print(f"\n{validation['message']}", style="bold red")
            sys.exit(1)
        elif validation['warning']:
            console.print(f"\n{validation['warning']}", style="yellow")
            if not click.confirm("\n继续吗?", default=False):
                sys.exit(0)
    
    try:
        # 步骤 1: 安全提示
        console.print("\n[bold cyan]步骤 1/4:[/bold cyan] 安全检查...")
        console.print("ℹ️  使用 GitHub Push Protection 自动阻止敏感信息推送", style="cyan")
        console.print("   组织管理员请确保已启用: https://github.com/organizations/{}/settings/security_analysis".format(org), style="dim")
        
        # 可选：本地快速扫描（不可靠，仅作提示）
        if not skip_scan:
            scanner = SecretScanner()
            issues = scanner.scan_directory(project_path)
            
            if issues:
                console.print(f"\n⚠️  本地扫描发现 {len(issues)} 个潜在敏感信息（仅供参考）:", style="yellow")
                for issue in issues[:5]:  # 只显示前5个
                    console.print(f"  • {issue['file']}:{issue['line']} - {issue['type']}")
                
                console.print("\n💡 推荐：让 GitHub Push Protection 自动处理（更准确）", style="cyan")
                if not click.confirm("是否继续发布？（GitHub 会在推送时再次检查）", default=True):
                    console.print("已取消", style="yellow")
                    return
        
        # 步骤 2: 创建 GitHub 仓库
        console.print("\n[bold cyan]步骤 2/4:[/bold cyan] 创建 GitHub 仓库...")
        github_mgr = GitHubManager(config['github_token'])
        
        repo_url, is_new = github_mgr.create_repository(org, repo, private=private)
        if is_new:
            console.print(f"✅ 仓库已创建: {repo_url}", style="green")
        else:
            console.print(f"⚠️  仓库已存在，将更新代码: {repo_url}", style="yellow")
        
        # 步骤 3: 生成 Pipeline 配置（根据部署方式）
        if pipeline and deploy_method in ['workflow', 'both']:
            console.print("\n[bold cyan]步骤 3/4:[/bold cyan] 生成 CI/CD Pipeline...")
            pipeline_gen = PipelineGenerator()
            
            pipelines = [pipeline] if pipeline != 'all' else ['docker', 'npm', 'pypi']
            for p_type in pipelines:
                pipeline_gen.generate(p_type, project_path)
                console.print(f"✅ {p_type.upper()} Pipeline 已生成", style="green")
        elif deploy_method == 'local':
            console.print("\n[bold cyan]步骤 3/4:[/bold cyan] 跳过 Pipeline 生成（使用本地部署）", style="yellow")
        
        # 步骤 4: 初始化 Git 并推送
        step_count = 5 if setup_secrets else 4
        console.print(f"\n[bold cyan]步骤 4/{step_count}:[/bold cyan] 推送代码到 GitHub...")
        # 使用 GitHub Token 进行认证，避免弹出认证窗口
        git_mgr = GitManager(project_path, github_token=config['github_token'])
        git_mgr.init_and_push(repo_url)
        console.print("✅ 代码已推送", style="green")
        
        # 步骤 5: 检查并设置 GitHub Secrets
        dockerhub_username = None
        dockerhub_password = None
        
        # 检查哪些 Secrets 需要设置
        required_secrets = []
        if pipeline in ['docker', 'all']:
            required_secrets.extend(['DOCKERHUB_USERNAME', 'DOCKERHUB_TOKEN'])
        if pipeline in ['npm', 'all']:
            required_secrets.append('NPM_TOKEN')
        if pipeline in ['pypi', 'all']:
            required_secrets.append('PYPI_TOKEN')
        
        # 检查 Secrets 是否已存在
        existing_secrets = []
        if required_secrets and deploy_method in ['workflow', 'both']:
            try:
                # 获取仓库的 Secrets
                try:
                    org_obj = github_mgr.github.get_organization(org)
                    repo_obj = org_obj.get_repo(repo)
                except:
                    repo_obj = github_mgr.user.get_repo(repo)
                
                existing_secrets = [s.name for s in repo_obj.get_secrets()]
            except:
                pass
        
        # 判断是否需要设置 Secrets
        missing_secrets = [s for s in required_secrets if s not in existing_secrets]
        should_setup = setup_secrets or bool(missing_secrets)
        
        if should_setup and pipeline and deploy_method in ['workflow', 'both']:
            if missing_secrets and not setup_secrets:
                console.print(f"\n⚠️  [yellow]检测到缺少必要的 Secrets:[/yellow] {', '.join(missing_secrets)}")
                if not click.confirm("是否现在配置 Secrets?", default=True):
                    console.print("\n💡 [yellow]提示:[/yellow] 请稍后手动在 GitHub 设置 Secrets，否则 workflow 会失败")
                    console.print(f"   https://github.com/{org}/{repo}/settings/secrets/actions")
                    should_setup = False
            
            if should_setup:
                console.print(f"\n[bold cyan]步骤 5/{step_count}:[/bold cyan] 设置 GitHub Secrets...")
                
                secrets_to_set = {}
                
                # 根据 Pipeline 类型收集需要的 Secrets
                if pipeline in ['docker', 'all'] and ('DOCKERHUB_USERNAME' in missing_secrets or 'DOCKERHUB_TOKEN' in missing_secrets or setup_secrets):
                    dockerhub_username = config.get('dockerhub_username') or click.prompt("DockerHub 用户名")
                    dockerhub_password = click.prompt("DockerHub Token/密码", hide_input=True)
                    if 'DOCKERHUB_USERNAME' in missing_secrets or setup_secrets:
                        secrets_to_set['DOCKERHUB_USERNAME'] = dockerhub_username
                    if 'DOCKERHUB_TOKEN' in missing_secrets or setup_secrets:
                        secrets_to_set['DOCKERHUB_TOKEN'] = dockerhub_password
                
                if pipeline in ['npm', 'all'] and ('NPM_TOKEN' in missing_secrets or setup_secrets):
                    npm_token = click.prompt("NPM Token", hide_input=True)
                    secrets_to_set['NPM_TOKEN'] = npm_token
                
                if pipeline in ['pypi', 'all'] and ('PYPI_TOKEN' in missing_secrets or setup_secrets):
                    pypi_token = click.prompt("PyPI Token", hide_input=True)
                    secrets_to_set['PYPI_TOKEN'] = pypi_token
                
                # 设置 Secrets
                if secrets_to_set:
                    results = github_mgr.set_multiple_secrets(org, repo, secrets_to_set)
                    
                    success_count = sum(1 for v in results.values() if v)
                    if success_count == len(results):
                        console.print(f"✅ 所有 Secrets 已设置 ({success_count}/{len(results)})", style="green")
                    else:
                        console.print(f"⚠️  部分 Secrets 设置失败 ({success_count}/{len(results)})", style="yellow")
                        for name, success in results.items():
                            status = "✅" if success else "❌"
                            console.print(f"  {status} {name}")
                else:
                    console.print("✅ 所有 Secrets 已存在，跳过设置", style="green")
        
        # 步骤 6: 本地构建并推送 Docker（可选）
        if deploy_method in ['local', 'both'] and pipeline in ['docker', 'all']:
            step_num = step_count + 1 if setup_secrets else step_count
            console.print(f"\n[bold cyan]步骤 {step_num}/{step_num}:[/bold cyan] 本地构建并推送 Docker 镜像...")
            
            # 确定镜像名称
            if not docker_image:
                if not dockerhub_username:
                    dockerhub_username = config.get('dockerhub_username') or click.prompt("DockerHub 用户名")
                docker_image = f"{dockerhub_username}/{repo}"
            
            # 获取密码（如果还没有）
            if not dockerhub_password:
                dockerhub_password = click.prompt("DockerHub Token/密码", hide_input=True)
            
            # 本地构建和推送
            try:
                docker_mgr = DockerManager(project_path)
                
                # 检查 Docker
                if not docker_mgr.check_docker_installed():
                    console.print("⚠️  Docker 未安装，跳过本地部署", style="yellow")
                else:
                    # 登录
                    console.print("  登录 Docker Hub...")
                    docker_mgr.login(dockerhub_username, dockerhub_password)
                    
                    # 构建
                    console.print(f"  构建镜像: {docker_image}:{docker_tag}")
                    docker_mgr.build_image(docker_image, docker_tag)
                    
                    # 推送
                    console.print(f"  推送镜像...")
                    docker_mgr.push_image(docker_image, docker_tag)
                    
                    console.print(f"✅ Docker 镜像已推送: {docker_image}:{docker_tag}", style="green")
            except Exception as e:
                console.print(f"⚠️  Docker 部署失败: {str(e)}", style="yellow")
        
        console.print(f"\n🎉 [bold green]完成！[/bold green] 项目已发布到: {repo_url}")
        
        # 提示信息
        if deploy_method == 'workflow' and not setup_secrets and pipeline:
            console.print("\n💡 [yellow]提示:[/yellow] 使用 --setup-secrets 可以自动配置 GitHub Secrets")
        
        if deploy_method == 'workflow' and pipeline == 'docker':
            console.print("\n💡 [yellow]提示:[/yellow] 使用 --deploy-method local 或 --deploy-method both 可以立即构建推送 Docker 镜像")
        
    except Exception as e:
        console.print(f"❌ 错误: {str(e)}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.')
def scan(path):
    """扫描项目中的敏感信息"""
    console.print(Panel.fit("🔍 扫描敏感信息", style="bold yellow"))
    
    scanner = SecretScanner()
    issues = scanner.scan_directory(Path(path))
    
    if issues:
        console.print(f"\n发现 {len(issues)} 个潜在问题:\n", style="bold red")
        for issue in issues:
            console.print(f"📄 [cyan]{issue['file']}[/cyan]:[yellow]{issue['line']}[/yellow]")
            console.print(f"   类型: [red]{issue['type']}[/red]")
            console.print(f"   内容: {issue['content'][:80]}...")
            console.print()
    else:
        console.print("✅ 未发现敏感信息", style="bold green")


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.')
def detect(path):
    """自动检测项目类型并推荐 Pipeline"""
    console.print(Panel.fit("🔎 项目类型检测", style="bold cyan"))
    
    detector = ProjectDetector(Path(path))
    info = detector.get_project_info()
    
    # 显示检测到的类型
    if info['detected_types']:
        console.print("\n[bold green]检测到的项目类型:[/bold green]")
        type_map = {
            'python': '🐍 Python',
            'nodejs': '📗 Node.js',
            'dotnet': '💎 .NET/C#',
            'docker': '🐳 Docker',
            'java': '☕ Java',
            'go': '🔵 Go',
            'rust': '🦀 Rust'
        }
        for ptype in info['detected_types']:
            console.print(f"  • {type_map.get(ptype, ptype)}")
    else:
        console.print("\n[yellow]未检测到已知的项目类型[/yellow]")
    
    # 显示推荐的 Pipeline
    if info['recommended_pipelines']:
        console.print("\n[bold cyan]推荐的 Pipeline:[/bold cyan]")
        pipeline_map = {
            'pypi': '📦 PyPI (Python 包)',
            'npm': '📦 NPM (Node.js 包)',
            'nuget': '📦 NuGet (C#/.NET 包)',
            'docker': '🐳 Docker (容器镜像)',
            'maven': '📦 Maven (Java 包)',
            'go': '📦 Go Modules',
            'cargo': '📦 Crates.io (Rust 包)'
        }
        for pipeline in info['recommended_pipelines']:
            console.print(f"  • {pipeline_map.get(pipeline, pipeline)}")
        
        # 生成推荐命令
        console.print("\n[bold green]推荐命令:[/bold green]")
        pipeline_str = ','.join(info['recommended_pipelines'][:2])  # 最多显示2个
        console.print(f"  python repoflow.py init --repo your-repo --pipeline {info['recommended_pipelines'][0]}")
    else:
        console.print("\n[yellow]无法推荐 Pipeline，请手动指定[/yellow]")
    
    # 多语言项目提示
    if info['is_multi_language']:
        console.print("\n[bold yellow]💡 提示:[/bold yellow]")
        console.print("  这是一个多语言项目，可以使用 --pipeline all 生成所有类型的 Pipeline")


@cli.command()
@click.option('--type', 'pipeline_type', 
              type=click.Choice(['docker', 'npm', 'pypi']), 
              required=True)
@click.option('--path', type=click.Path(exists=True), default='.')
def pipeline(pipeline_type, path):
    """生成 CI/CD Pipeline 配置文件"""
    console.print(Panel.fit(f"🏗️  生成 {pipeline_type.upper()} Pipeline", style="bold blue"))
    
    pipeline_gen = PipelineGenerator()
    pipeline_gen.generate(pipeline_type, Path(path))
    
    console.print(f"✅ {pipeline_type.upper()} Pipeline 配置已生成", style="bold green")


@cli.command()
@click.option('--image', required=True, help='Docker 镜像名称 (例如: username/repo)')
@click.option('--tag', default='latest', help='镜像标签')
@click.option('--username', help='Docker Hub 用户名')
@click.option('--password', help='Docker Hub 密码/Token')
@click.option('--build-only', is_flag=True, help='仅构建，不推送')
@click.option('--path', type=click.Path(exists=True), default='.', help='项目路径')
def docker(image, tag, username, password, build_only, path):
    """构建并推送 Docker 镜像到 Docker Hub"""
    console.print(Panel.fit("🐳 Docker 构建和推送", style="bold blue"))
    
    docker_mgr = DockerManager(Path(path))
    
    # 检查 Docker 是否安装
    if not docker_mgr.check_docker_installed():
        console.print("❌ Docker 未安装或未运行", style="bold red")
        console.print("请先安装 Docker: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    config = load_cli_config()
    
    # 如果未提供用户名，尝试从配置读取
    if not username and not build_only:
        username = config.get('dockerhub_username')
        if not username:
            console.print("❌ 请提供 Docker Hub 用户名（使用 --username 或运行 'repoflow config'）", 
                         style="bold red")
            sys.exit(1)
    
    # 如果需要推送但没有密码，提示输入
    if not build_only and not password:
        password = click.prompt("请输入 Docker Hub 密码/Token", hide_input=True)
    
    try:
        # 步骤 1: 登录（如果需要推送）
        if not build_only:
            console.print("\n[bold cyan]步骤 1/3:[/bold cyan] 登录 Docker Hub...")
            docker_mgr.login(username, password)
            console.print("✅ 登录成功", style="green")
        
        # 步骤 2: 构建镜像
        step_num = "2/3" if not build_only else "1/1"
        console.print(f"\n[bold cyan]步骤 {step_num}:[/bold cyan] 构建 Docker 镜像...")
        console.print(f"镜像: {image}:{tag}")
        
        docker_mgr.build_image(image, tag)
        console.print("✅ 构建成功", style="green")
        
        # 步骤 3: 推送镜像
        if not build_only:
            console.print(f"\n[bold cyan]步骤 3/3:[/bold cyan] 推送到 Docker Hub...")
            docker_mgr.push_image(image, tag)
            console.print("✅ 推送成功", style="green")
            console.print(f"\n🎉 [bold green]完成！[/bold green] 镜像已推送: {image}:{tag}")
        else:
            console.print(f"\n🎉 [bold green]完成！[/bold green] 镜像已构建: {image}:{tag}")
        
    except Exception as e:
        console.print(f"\n❌ 错误: {str(e)}", style="bold red")
        sys.exit(1)


@cli.command()
@click.option('--token', help='PyPI API Token')
@click.option('--test', is_flag=True, help='上传到 Test PyPI')
@click.option('--build-only', is_flag=True, help='仅构建，不上传')
@click.option('--clean', is_flag=True, default=True, help='构建前清理旧文件')
@click.option('--path', type=click.Path(exists=True), default='.', help='项目路径')
def pypi(token, test, build_only, clean, path):
    """构建并发布 Python 包到 PyPI"""
    console.print(Panel.fit("📦 PyPI 构建和发布", style="bold blue"))
    
    pypi_mgr = PyPIManager(Path(path))
    
    # 检查工具
    tools = pypi_mgr.check_tools_installed()
    if not all(tools.values()):
        console.print("⚠️  检测到缺少必要工具，正在安装...", style="yellow")
        try:
            pypi_mgr.install_tools()
            console.print("✅ 工具安装完成", style="green")
        except Exception as e:
            console.print(f"❌ 工具安装失败: {str(e)}", style="bold red")
            sys.exit(1)
    
    # 获取包信息
    pkg_info = pypi_mgr.get_package_info()
    if pkg_info['name']:
        console.print(f"\n包名: [cyan]{pkg_info['name']}[/cyan]")
    if pkg_info['version']:
        console.print(f"版本: [cyan]{pkg_info['version']}[/cyan]")
    
    # 如果需要上传但没有 token，提示输入
    if not build_only and not token:
        token = click.prompt("请输入 PyPI Token", hide_input=True)
    
    try:
        # 步骤 1: 清理（如果需要）
        if clean:
            console.print("\n[bold cyan]步骤 1/3:[/bold cyan] 清理旧文件...")
            pypi_mgr.clean_dist()
            console.print("✅ 清理完成", style="green")
            step_offset = 0
        else:
            step_offset = 1
        
        # 步骤 2: 构建包
        step_num = f"{2-step_offset}/{3-step_offset}" if not build_only else "1/1"
        console.print(f"\n[bold cyan]步骤 {step_num}:[/bold cyan] 构建 Python 包...")
        
        pypi_mgr.build_package()
        console.print("✅ 构建成功", style="green")
        
        # 步骤 3: 上传到 PyPI
        if not build_only:
            target = "Test PyPI" if test else "PyPI"
            console.print(f"\n[bold cyan]步骤 {3-step_offset}/{3-step_offset}:[/bold cyan] 上传到 {target}...")
            pypi_mgr.upload_to_pypi(token, test)
            console.print("✅ 上传成功", style="green")
            
            if pkg_info['name']:
                if test:
                    console.print(f"\n🎉 [bold green]完成！[/bold green] 包已发布到 Test PyPI")
                    console.print(f"安装: pip install --index-url https://test.pypi.org/simple/ {pkg_info['name']}")
                else:
                    console.print(f"\n🎉 [bold green]完成！[/bold green] 包已发布到 PyPI")
                    console.print(f"安装: pip install {pkg_info['name']}")
            else:
                console.print(f"\n🎉 [bold green]完成！[/bold green] 包已发布")
        else:
            console.print(f"\n🎉 [bold green]完成！[/bold green] 包已构建")
            console.print(f"构建文件位于: {Path(path) / 'dist'}")
        
    except Exception as e:
        console.print(f"\n❌ 错误: {str(e)}", style="bold red")
        sys.exit(1)


if __name__ == '__main__':
    cli()


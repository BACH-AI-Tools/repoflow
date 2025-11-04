"""项目类型检测模块"""

from pathlib import Path
from typing import List, Dict


class ProjectDetector:
    """检测项目类型和推荐的 Pipeline"""
    
    def __init__(self, project_path: Path):
        """
        初始化项目检测器
        
        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)
    
    def detect_project_type(self) -> List[str]:
        """
        检测项目类型
        
        Returns:
            检测到的项目类型列表（可能多个）
        """
        detected_types = []
        
        # Python 项目检测
        if self._is_python_project():
            detected_types.append('python')
        
        # Node.js 项目检测
        if self._is_nodejs_project():
            detected_types.append('nodejs')
        
        # .NET/C# 项目检测
        if self._is_dotnet_project():
            detected_types.append('dotnet')
        
        # Docker 项目检测
        if self._is_docker_project():
            detected_types.append('docker')
        
        # Java 项目检测
        if self._is_java_project():
            detected_types.append('java')
        
        # Go 项目检测
        if self._is_go_project():
            detected_types.append('go')
        
        # Rust 项目检测
        if self._is_rust_project():
            detected_types.append('rust')
        
        return detected_types
    
    def _is_python_project(self) -> bool:
        """检测是否为 Python 项目"""
        indicators = [
            'requirements.txt',
            'setup.py',
            'pyproject.toml',
            'Pipfile',
            'poetry.lock',
            'setup.cfg'
        ]
        return any((self.project_path / f).exists() for f in indicators)
    
    def _is_nodejs_project(self) -> bool:
        """检测是否为 Node.js 项目"""
        indicators = [
            'package.json',
            'package-lock.json',
            'yarn.lock',
            'pnpm-lock.yaml'
        ]
        return any((self.project_path / f).exists() for f in indicators)
    
    def _is_dotnet_project(self) -> bool:
        """检测是否为 .NET/C# 项目"""
        # 查找 .csproj, .sln, .fsproj, .vbproj 文件
        csproj_files = list(self.project_path.glob('*.csproj'))
        sln_files = list(self.project_path.glob('*.sln'))
        fsproj_files = list(self.project_path.glob('*.fsproj'))
        vbproj_files = list(self.project_path.glob('*.vbproj'))
        
        return bool(csproj_files or sln_files or fsproj_files or vbproj_files)
    
    def _is_docker_project(self) -> bool:
        """检测是否有 Docker 配置"""
        indicators = [
            'Dockerfile',
            'docker-compose.yml',
            'docker-compose.yaml',
            '.dockerignore'
        ]
        return any((self.project_path / f).exists() for f in indicators)
    
    def _is_java_project(self) -> bool:
        """检测是否为 Java 项目"""
        indicators = [
            'pom.xml',          # Maven
            'build.gradle',     # Gradle
            'build.gradle.kts'  # Kotlin Gradle
        ]
        return any((self.project_path / f).exists() for f in indicators)
    
    def _is_go_project(self) -> bool:
        """检测是否为 Go 项目"""
        indicators = [
            'go.mod',
            'go.sum'
        ]
        return any((self.project_path / f).exists() for f in indicators)
    
    def _is_rust_project(self) -> bool:
        """检测是否为 Rust 项目"""
        return (self.project_path / 'Cargo.toml').exists()
    
    def recommend_pipelines(self) -> List[str]:
        """
        推荐合适的 Pipeline 类型
        
        Returns:
            推荐的 Pipeline 列表
        """
        detected = self.detect_project_type()
        recommendations = []
        
        # PyPI - 仅限 Python 项目
        if 'python' in detected:
            recommendations.append('pypi')
        
        # NPM - 仅限 Node.js 项目
        if 'nodejs' in detected:
            recommendations.append('npm')
        
        # Docker - 任何项目都可以（推荐！）
        # 总是推荐 Docker，因为任何语言都能容器化
        recommendations.append('docker')
        
        return recommendations
    
    def get_project_info(self) -> Dict:
        """
        获取项目详细信息
        
        Returns:
            项目信息字典
        """
        types = self.detect_project_type()
        pipelines = self.recommend_pipelines()
        
        return {
            'detected_types': types,
            'recommended_pipelines': pipelines,
            'primary_type': types[0] if types else 'unknown',
            'is_multi_language': len(types) > 1
        }
    
    def validate_pipeline(self, pipeline: str) -> Dict:
        """
        验证选择的 Pipeline 是否适合当前项目
        
        Args:
            pipeline: 用户选择的 Pipeline
            
        Returns:
            验证结果 {'valid': bool, 'message': str, 'warning': str}
        """
        detected = self.detect_project_type()
        result = {
            'valid': True,
            'message': '',
            'warning': ''
        }
        
        # PyPI 验证 - 必须是 Python 项目
        if pipeline == 'pypi':
            if 'python' not in detected:
                result['valid'] = False
                result['message'] = (
                    "❌ PyPI 只能发布 Python 包！\n"
                    "   当前项目不是 Python 项目（未找到 requirements.txt/setup.py/pyproject.toml）\n"
                    "   建议：使用 --pipeline docker 将任何语言打包为容器镜像"
                )
            else:
                result['valid'] = True
                result['message'] = "✅ Python 项目，适合发布到 PyPI"
        
        # NPM 验证 - 必须是 Node.js 项目
        elif pipeline == 'npm':
            if 'nodejs' not in detected:
                result['valid'] = False
                result['message'] = (
                    "❌ NPM 只能发布 JavaScript/TypeScript 包！\n"
                    "   当前项目不是 Node.js 项目（未找到 package.json）\n"
                    "   建议：使用 --pipeline docker 将任何语言打包为容器镜像"
                )
            else:
                result['valid'] = True
                result['message'] = "✅ Node.js 项目，适合发布到 NPM"
        
        # Docker 验证 - 任何项目都可以
        elif pipeline == 'docker':
            result['valid'] = True
            result['message'] = f"✅ 任何项目都可以使用 Docker！检测到: {', '.join(detected) if detected else '未知语言'}"
        
        # All 验证 - 根据项目类型提示
        elif pipeline == 'all':
            result['valid'] = True
            warnings = []
            if 'python' not in detected:
                warnings.append("PyPI")
            if 'nodejs' not in detected:
                warnings.append("NPM")
            
            if warnings:
                result['warning'] = (
                    f"⚠️  项目类型不匹配：{', '.join(warnings)}\n"
                    f"   这些 Pipeline 可能无法正常工作"
                )
        
        return result
    
    def print_detection_result(self):
        """打印检测结果（用于调试）"""
        info = self.get_project_info()
        
        print(f"检测到的项目类型: {', '.join(info['detected_types']) if info['detected_types'] else '未知'}")
        print(f"推荐的 Pipeline: {', '.join(info['recommended_pipelines']) if info['recommended_pipelines'] else '无'}")
        print(f"主要类型: {info['primary_type']}")
        print(f"多语言项目: {'是' if info['is_multi_language'] else '否'}")


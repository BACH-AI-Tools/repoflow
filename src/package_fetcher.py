"""包信息提取器 - 从 PyPI/NPM/Docker Hub 获取包信息"""

import requests
from typing import Dict, Optional
from urllib.parse import urlparse
import re
import json


class PackageLogger:
    """包 API 日志记录器"""
    log_func = None
    
    @classmethod
    def set_log_function(cls, log_func):
        """设置日志函数"""
        cls.log_func = log_func
    
    @classmethod
    def log(cls, message):
        """记录日志"""
        if cls.log_func:
            cls.log_func(message)
        else:
            print(message)


def log_package_api_request(method: str, url: str):
    """记录包管理 API 请求"""
    PackageLogger.log(f"\n{'='*70}")
    PackageLogger.log(f"📤 {method.upper()} {url}")
    PackageLogger.log(f"{'='*70}\n")


def log_package_api_response(status_code: int, data: Dict = None):
    """记录包管理 API 响应"""
    PackageLogger.log(f"\n{'='*70}")
    PackageLogger.log(f"📥 响应: {status_code}")
    if data:
        # 只显示关键信息
        info = data.get('info', {})
        PackageLogger.log(f"   包名: {info.get('name', 'N/A')}")
        PackageLogger.log(f"   版本: {info.get('version', 'N/A')}")
        PackageLogger.log(f"   简介: {info.get('summary', 'N/A')[:50]}...")
    PackageLogger.log(f"{'='*70}\n")



class PackageFetcher:
    """从各种包管理平台获取包信息"""
    
    def __init__(self):
        self.timeout = 10
    
    def detect_package_type(self, url_or_name: str) -> Dict:
        """
        检测包类型并提取包信息
        
        Args:
            url_or_name: 包地址或包名
                - https://pypi.org/project/package-name
                - https://www.npmjs.com/package/package-name
                - https://hub.docker.com/r/username/image
                - 或直接输入包名
        
        Returns:
            {
                'type': 'pypi' | 'npm' | 'docker' | 'unknown',
                'package_name': str,
                'url': str,
                'info': Dict  # 从API获取的详细信息
            }
        """
        url_or_name = url_or_name.strip()
        
        # 检测 PyPI
        if 'pypi.org' in url_or_name or 'pypi.python.org' in url_or_name:
            return self._fetch_from_url(url_or_name, 'pypi')
        
        # 检测 NPM
        if 'npmjs.com' in url_or_name or 'npm' in url_or_name.lower():
            return self._fetch_from_url(url_or_name, 'npm')
        
        # 检测 Docker Hub
        if 'hub.docker.com' in url_or_name or 'docker.io' in url_or_name:
            return self._fetch_from_url(url_or_name, 'docker')
        
        # 尝试直接作为包名搜索
        # 优先尝试 PyPI
        result = self.fetch_pypi(url_or_name)
        if result['type'] != 'unknown':
            return result
        
        # 然后尝试 NPM
        result = self.fetch_npm(url_or_name)
        if result['type'] != 'unknown':
            return result
        
        # 最后尝试 Docker
        result = self.fetch_docker(url_or_name)
        if result['type'] != 'unknown':
            return result
        
        return {
            'type': 'unknown',
            'package_name': url_or_name,
            'url': '',
            'info': {}
        }
    
    def _fetch_from_url(self, url: str, pkg_type: str) -> Dict:
        """从URL提取包名并获取信息"""
        if pkg_type == 'pypi':
            # 从 URL 提取包名: https://pypi.org/project/package-name/
            match = re.search(r'pypi\.org/project/([^/]+)', url)
            if match:
                package_name = match.group(1)
                return self.fetch_pypi(package_name)
        
        elif pkg_type == 'npm':
            # 从 URL 提取包名: https://www.npmjs.com/package/package-name
            match = re.search(r'npmjs\.com/package/(@?[^/]+(?:/[^/]+)?)', url)
            if match:
                package_name = match.group(1)
                return self.fetch_npm(package_name)
        
        elif pkg_type == 'docker':
            # 从 URL 提取镜像名: https://hub.docker.com/r/username/image
            match = re.search(r'hub\.docker\.com/r/([^/]+/[^/]+)', url)
            if match:
                image_name = match.group(1)
                return self.fetch_docker(image_name)
        
        return {
            'type': 'unknown',
            'package_name': url,
            'url': url,
            'info': {}
        }
    
    def fetch_pypi(self, package_name: str) -> Dict:
        """
        从 PyPI 获取包信息
        
        Args:
            package_name: PyPI 包名
        
        Returns:
            包信息字典
        """
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            
            # 记录请求
            log_package_api_request("GET", url)
            
            response = requests.get(url, timeout=self.timeout)
            
            # 记录响应
            try:
                data = response.json()
                log_package_api_response(response.status_code, data={'info': data.get('info', {})})
            except:
                PackageLogger.log(f"响应状态: {response.status_code}")
            
            response.raise_for_status()
            info = data.get('info', {})
            
            return {
                'type': 'pypi',
                'package_name': package_name,
                'url': f"https://pypi.org/project/{package_name}",
                'info': {
                    'name': info.get('name', package_name),
                    'version': info.get('version', '1.0.0'),
                    'summary': info.get('summary', ''),
                    'description': info.get('description', ''),
                    'author': info.get('author', ''),
                    'license': info.get('license', ''),
                    'home_page': info.get('home_page', ''),
                    'project_urls': info.get('project_urls', {}),
                }
            }
        except:
            return {
                'type': 'unknown',
                'package_name': package_name,
                'url': '',
                'info': {}
            }
    
    def fetch_npm(self, package_name: str) -> Dict:
        """
        从 NPM 获取包信息
        
        Args:
            package_name: NPM 包名（支持 @scope/package）
        
        Returns:
            包信息字典
        """
        try:
            # NPM Registry API
            url = f"https://registry.npmjs.org/{package_name}"
            
            # 记录请求
            log_package_api_request("GET", url)
            
            response = requests.get(url, timeout=self.timeout)
            
            # 记录响应
            try:
                data = response.json()
                latest_version = data.get('dist-tags', {}).get('latest', '1.0.0')
                log_package_api_response(
                    response.status_code,
                    data={'info': {'name': data.get('name'), 'version': latest_version}}
                )
            except:
                PackageLogger.log(f"响应状态: {response.status_code}")
            
            response.raise_for_status()
            latest_version = data.get('dist-tags', {}).get('latest', '1.0.0')
            version_info = data.get('versions', {}).get(latest_version, {})
            
            return {
                'type': 'npm',
                'package_name': package_name,
                'url': f"https://www.npmjs.com/package/{package_name}",
                'info': {
                    'name': data.get('name', package_name),
                    'version': latest_version,
                    'summary': version_info.get('description', ''),
                    'description': data.get('readme', ''),
                    'author': version_info.get('author', {}).get('name', '') if isinstance(version_info.get('author'), dict) else str(version_info.get('author', '')),
                    'license': version_info.get('license', ''),
                    'home_page': version_info.get('homepage', ''),
                    'repository': version_info.get('repository', {}),
                }
            }
        except:
            return {
                'type': 'unknown',
                'package_name': package_name,
                'url': '',
                'info': {}
            }
    
    def fetch_docker(self, image_name: str) -> Dict:
        """
        从 Docker Hub 获取镜像信息
        
        Args:
            image_name: Docker 镜像名（格式: username/image）
        
        Returns:
            镜像信息字典
        """
        try:
            # Docker Hub API
            # 如果没有 /，默认是 library/ （官方镜像）
            if '/' not in image_name:
                image_name = f"library/{image_name}"
            
            url = f"https://hub.docker.com/v2/repositories/{image_name}"
            
            # 记录请求
            log_package_api_request("GET", url)
            
            response = requests.get(url, timeout=self.timeout)
            
            # 记录响应
            try:
                data = response.json()
                log_package_api_response(
                    response.status_code,
                    data={'info': {'name': data.get('name'), 'version': 'latest'}}
                )
            except:
                PackageLogger.log(f"响应状态: {response.status_code}")
            
            response.raise_for_status()
            
            return {
                'type': 'docker',
                'package_name': image_name,
                'url': f"https://hub.docker.com/r/{image_name}",
                'info': {
                    'name': data.get('name', image_name.split('/')[-1]),
                    'version': 'latest',
                    'summary': data.get('description', ''),
                    'description': data.get('full_description', ''),
                    'author': data.get('user', ''),
                    'star_count': data.get('star_count', 0),
                    'pull_count': data.get('pull_count', 0),
                    'last_updated': data.get('last_updated', ''),
                }
            }
        except:
            return {
                'type': 'unknown',
                'package_name': image_name,
                'url': '',
                'info': {}
            }


# 测试代码
if __name__ == '__main__':
    fetcher = PackageFetcher()
    
    # 测试 PyPI
    print("=" * 60)
    print("测试 PyPI:")
    result = fetcher.detect_package_type("https://pypi.org/project/requests")
    print(f"类型: {result['type']}")
    print(f"包名: {result['package_name']}")
    print(f"版本: {result['info'].get('version')}")
    print(f"简介: {result['info'].get('summary')}")
    
    # 测试 NPM
    print("\n" + "=" * 60)
    print("测试 NPM:")
    result = fetcher.detect_package_type("https://www.npmjs.com/package/express")
    print(f"类型: {result['type']}")
    print(f"包名: {result['package_name']}")
    print(f"版本: {result['info'].get('version')}")
    print(f"简介: {result['info'].get('summary')}")
    
    # 测试 Docker
    print("\n" + "=" * 60)
    print("测试 Docker:")
    result = fetcher.detect_package_type("https://hub.docker.com/r/nginx/nginx")
    print(f"类型: {result['type']}")
    print(f"包名: {result['package_name']}")
    print(f"简介: {result['info'].get('summary')}")



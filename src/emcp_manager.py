"""EMCP 平台管理模块"""

import requests
from typing import Dict, List, Optional
from pathlib import Path
import json


class HTTPLogger:
    """HTTP 日志记录器（可注入自定义 log 函数）"""
    
    log_func = None  # 类变量，存储 log 函数
    
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
    
    @classmethod
    def log_request(cls, method: str, url: str, headers: Dict = None, payload: Dict = None):
        """记录HTTP请求详情"""
        cls.log(f"\n{'='*70}")
        cls.log(f"📤 HTTP 请求: {method.upper()} {url}")
        if headers:
            cls.log(f"📋 请求头:")
            for key, value in headers.items():
                cls.log(f"   {key}: {value}")
        if payload:
            cls.log(f"📦 请求参数:")
            payload_json = json.dumps(payload, indent=2, ensure_ascii=False)
            for line in payload_json.split('\n')[:100]:  # 限制行数
                cls.log(f"   {line}")
            if len(payload_json.split('\n')) > 100:
                cls.log(f"   ... (省略 {len(payload_json.split('\n')) - 100} 行)")
        cls.log(f"{'='*70}\n")
    
    @classmethod
    def log_response(cls, status_code: int, response_data: Dict = None, response_text: str = None):
        """记录HTTP响应详情"""
        cls.log(f"\n{'='*70}")
        cls.log(f"📥 HTTP 响应: {status_code}")
        if response_data:
            cls.log(f"📋 响应数据:")
            response_json = json.dumps(response_data, indent=2, ensure_ascii=False)
            for line in response_json.split('\n')[:100]:
                cls.log(f"   {line}")
            if len(response_json.split('\n')) > 100:
                cls.log(f"   ... (省略 {len(response_json.split('\n')) - 100} 行)")
        elif response_text:
            cls.log(f"📋 响应文本:")
            for line in response_text[:500].split('\n'):
                cls.log(f"   {line}")
        cls.log(f"{'='*70}\n")


# 便捷函数
def log_http_request(method: str, url: str, headers: Dict = None, payload: Dict = None):
    HTTPLogger.log_request(method, url, headers, payload)

def log_http_response(status_code: int, response_data: Dict = None, response_text: str = None):
    HTTPLogger.log_response(status_code, response_data, response_text)



class EMCPManager:
    """管理 EMCP 平台的 MCP 发布操作"""
    
    def __init__(self, base_url: str = "https://sit-emcp.kaleido.guru"):
        """
        初始化 EMCP Manager
        
        Args:
            base_url: EMCP 平台基础 URL
        """
        self.base_url = base_url
        self.session_key = None
        self.user_info = None
    
    def login(self, phone_number: str, validation_code: str) -> Dict:
        """
        登录 EMCP 平台
        
        Args:
            phone_number: 手机号
            validation_code: 验证码
            
        Returns:
            用户信息字典
        """
        url = f"{self.base_url}/api/Login/login"
        
        payload = {
            "phone_number": phone_number,
            "validation_code": validation_code
        }
        
        try:
            # 记录请求
            log_http_request("POST", url, payload=payload)
            
            response = requests.post(url, json=payload, timeout=10)
            
            # 记录响应
            try:
                data = response.json()
                log_http_response(response.status_code, response_data=data)
            except:
                log_http_response(response.status_code, response_text=response.text)
            
            response.raise_for_status()
            
            if data.get('err_code') != 0:
                raise Exception(f"登录失败: {data.get('err_message', '未知错误')}")
            
            # 保存 session key 和用户信息
            body = data.get('body', {})
            self.session_key = body.get('session_key')
            self.user_info = body
            
            return body
            
        except requests.exceptions.Timeout:
            raise Exception("请求超时，请检查网络连接")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头（包含 token）"""
        if not self.session_key:
            raise Exception("请先登录 EMCP 平台")
        
        return {
            "Content-Type": "application/json",
            "token": self.session_key
        }
    
    @staticmethod
    def generate_validation_code() -> str:
        """
        生成当天的验证码
        
        格式: MMyyyydd (月月年年年年日日)
        例如: 11202506 表示 2025年11月06日
        
        Returns:
            验证码字符串
        """
        from datetime import datetime
        now = datetime.now()
        
        # 格式: MMyyyydd
        # %m = 月份（01-12）
        # %Y = 年份（4位）
        # %d = 日期（01-31）
        validation_code = now.strftime("%m%Y%d")
        
        # ⭐ 详细日志
        HTTPLogger.log(f"🔑 生成验证码:")
        HTTPLogger.log(f"   当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        HTTPLogger.log(f"   格式: MMyyyydd")
        HTTPLogger.log(f"   月份(MM): {now.strftime('%m')}")
        HTTPLogger.log(f"   年份(yyyy): {now.strftime('%Y')}")
        HTTPLogger.log(f"   日期(dd): {now.strftime('%d')}")
        HTTPLogger.log(f"   最终验证码: {validation_code}")
        
        return validation_code
    
    def auto_login(self, phone_number: str) -> Dict:
        """
        自动登录（自动生成验证码）
        
        Args:
            phone_number: 手机号
        
        Returns:
            用户信息
        """
        validation_code = self.generate_validation_code()
        HTTPLogger.log(f"🔐 自动生成验证码: {validation_code}")
        return self.login(phone_number, validation_code)
    
    def create_mcp_template(self, template_data: Dict, retry_count: int = 0, max_retries: int = 3, auto_login_on_401: bool = True, route_retry_count: int = 0) -> Dict:
        """
        创建 MCP 模板（支持 AI 自动修复重试）
        
        Args:
            template_data: 模板数据
            retry_count: 当前重试次数
            max_retries: 最大重试次数
            
        Returns:
            创建结果
        """
        url = f"{self.base_url}/api/Template/create_mcp_template"
        
        try:
            # 记录请求
            log_http_request("POST", url, headers=self._get_headers(), payload=template_data)
            
            response = requests.post(
                url, 
                json=template_data,
                headers=self._get_headers(),
                timeout=30
            )
            
            # 记录响应
            try:
                response_data = response.json()
                log_http_response(response.status_code, response_data=response_data)
            except:
                log_http_response(response.status_code, response_text=response.text)
            
            # 如果请求失败
            if response.status_code != 200:
                print(f"\n❌ API 返回错误 (状态码: {response.status_code})")
                
                # 获取错误详情
                error_data = {}
                try:
                    error_data = response.json()
                    print(f"   错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   响应文本: {response.text[:300]}")
                
                # 如果是 401 未授权，尝试自动登录
                if response.status_code == 401 and auto_login_on_401:
                    HTTPLogger.log(f"\n🔐 检测到 401 未授权，尝试自动登录...")
                    
                    # 尝试从配置获取手机号
                    try:
                        from config_manager import ConfigManager
                        config_mgr = ConfigManager()
                        credentials = config_mgr.load_emcp_credentials()
                        
                        if credentials and credentials.get('phone_number'):
                            phone = credentials['phone_number']
                            
                            # 自动登录
                            HTTPLogger.log(f"   使用手机号: {phone}")
                            user_info = self.auto_login(phone)
                            HTTPLogger.log(f"   ✅ 自动登录成功: {user_info.get('user_name')}")
                            
                            # 保存 Session
                            config_mgr.save_session(self.session_key, user_info)
                            
                            # 重新发送请求
                            HTTPLogger.log(f"   🔄 重新发送请求...")
                            return self.create_mcp_template(
                                template_data,
                                retry_count=retry_count,
                                max_retries=max_retries,
                                auto_login_on_401=False  # 避免循环
                            )
                        else:
                            HTTPLogger.log(f"   ❌ 未找到配置的手机号")
                    except Exception as e:
                        HTTPLogger.log(f"   ❌ 自动登录失败: {e}")
                
                # 如果还有重试次数，尝试 AI 修复
                if retry_count < max_retries:
                    HTTPLogger.log(f"\n🤖 尝试使用 LLM 自动修复... (重试 {retry_count + 1}/{max_retries})")
                    
                    # 使用 AI 修复
                    fixed_data = self._try_fix_with_ai(
                        template_data,
                        error_data,
                        str(response.status_code)
                    )
                    
                    if fixed_data:
                        HTTPLogger.log("   ✅ LLM 已修复数据，重新发送...")
                        # 递归调用，重试
                        return self.create_mcp_template(
                            fixed_data,
                            retry_count=retry_count + 1,
                            max_retries=max_retries
                        )
                    else:
                        HTTPLogger.log("   ❌ LLM 无法修复")
            
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('err_code') != 0:
                error_msg = data.get('err_message', '未知错误')
                
                # ⭐ 检测路由占用错误
                if ('路由' in error_msg and '占用' in error_msg) or \
                   ('route' in error_msg.lower() and ('exist' in error_msg.lower() or 'occupied' in error_msg.lower())):
                    
                    if route_retry_count < 5:  # 最多尝试5次
                        HTTPLogger.log(f"\n⚠️ 检测到路由占用: {error_msg}")
                        HTTPLogger.log(f"🔄 自动换路由重试 ({route_retry_count + 1}/5)...")
                        
                        # 修改路由前缀（添加数字后缀）
                        import random
                        original_prefix = template_data.get('route_prefix', '')
                        
                        # 如果已经有数字后缀，增加数字
                        if route_retry_count > 0:
                            # 移除旧的数字后缀
                            original_prefix = ''.join(c for c in original_prefix if not c.isdigit())
                        
                        # 截断以确保有空间添加数字
                        if len(original_prefix) > 8:
                            original_prefix = original_prefix[:8]
                        
                        # 添加随机数字后缀
                        new_suffix = random.randint(10, 99)
                        new_prefix = f"{original_prefix}{new_suffix}"
                        
                        # 确保不超过10个字符
                        if len(new_prefix) > 10:
                            new_prefix = new_prefix[:10]
                        
                        template_data['route_prefix'] = new_prefix
                        HTTPLogger.log(f"   ✅ 新路由前缀: {new_prefix}")
                        
                        # 递归调用，使用新路由重试
                        return self.create_mcp_template(
                            template_data,
                            retry_count=retry_count,
                            max_retries=max_retries,
                            auto_login_on_401=auto_login_on_401,
                            route_retry_count=route_retry_count + 1
                        )
                    else:
                        HTTPLogger.log(f"\n❌ 路由占用且已尝试{route_retry_count}次，放弃重试")
                
                raise Exception(f"创建模板失败: {error_msg}")
            
            return data.get('body', {})
            
        except requests.exceptions.Timeout:
            raise Exception("请求超时，模板创建可能需要更长时间")
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def _try_fix_with_ai(
        self,
        template_data: Dict,
        error_response: Dict,
        error_code: str
    ) -> Optional[Dict]:
        """
        尝试使用 AI 修复数据
        
        Args:
            template_data: 原始数据
            error_response: 错误响应
            error_code: 错误代码
        
        Returns:
            修复后的数据或 None
        """
        try:
            # 需要有 Azure OpenAI 客户端
            if not hasattr(self, '_ai_fixer'):
                # 尝试创建 AI 修复器
                from config_manager import ConfigManager
                from error_fixer import AIErrorFixer
                from openai import AzureOpenAI
                
                config_mgr = ConfigManager()
                ai_config = config_mgr.load_azure_openai_config()
                
                if not ai_config:
                    return None
                
                client = AzureOpenAI(
                    azure_endpoint=ai_config['azure_endpoint'],
                    api_key=ai_config['api_key'],
                    api_version=ai_config.get('api_version', '2024-02-15-preview')
                )
                
                self._ai_fixer = AIErrorFixer(
                    client,
                    deployment_name=ai_config.get('deployment_name', 'gpt-4o')
                )
            
            # 使用 AI 修复
            fixed_data = self._ai_fixer.fix_template_data(
                template_data,
                error_response,
                f"HTTP {error_code}"
            )
            
            return fixed_data
            
        except Exception as e:
            HTTPLogger.log(f"   ⚠️ AI 修复异常: {e}")
            return None
    
    @staticmethod
    def make_multi_lang(content_cn: str, content_tw: str = None, content_en: str = None) -> List[Dict]:
        """
        构建多语言内容（直接使用LLM生成的三种语言）
        
        Args:
            content_cn: 中文简体内容
            content_tw: 中文繁体内容（LLM生成）
            content_en: 英文内容（LLM生成）
        
        Returns:
            多语言列表
            - type 1: zh-cn (中文简体)
            - type 2: zh-tw (中文繁体) 
            - type 3: en (英文)
        """
        # 如果没有提供繁体，使用简体
        if not content_tw:
            content_tw = content_cn
        
        # 如果没有提供英文，使用简体
        if not content_en:
            content_en = content_cn
        
        return [
            {"type": 1, "content": content_cn},   # zh-cn 中文简体
            {"type": 2, "content": content_tw},   # zh-tw 中文繁体
            {"type": 3, "content": content_en}    # en 英文
        ]
    
    def build_template_data(
        self,
        name: str,
        summary: str,
        description: str,
        logo_url: str,
        template_category_id: str,
        template_source_id: str = "bach-001",  # 默认使用 bach-001
        command: str = "",
        route_prefix: str = "",
        package_type: int = 1,  # 1=npx, 2=pip, 4=container, 5=direct_proxy
        args: List[Dict] = None,
        name_en: str = None,
        summary_en: str = None,
        description_en: str = None,
        name_tw: str = None,
        summary_tw: str = None,
        description_tw: str = None,
        **kwargs
    ) -> Dict:
        """
        构建模板数据
        
        Args:
            name: 模板名称（中文简体）
            summary: 简介（中文简体）
            description: 详细描述（中文简体）
            logo_url: Logo URL
            template_category_id: 模板类型ID
            template_source_id: 模板来源ID
            command: 启动命令
            route_prefix: MCP endpoint 地址前缀
            package_type: 包类型 (1=npx, 2=pip, 4=container)
            args: 参数列表
            name_en: 模板名称（英文）
            summary_en: 简介（英文）
            description_en: 详细描述（英文）
            name_tw: 模板名称（中文繁体）
            summary_tw: 简介（中文繁体）
            description_tw: 详细描述（中文繁体）
            **kwargs: 其他可选参数
            
        Returns:
            模板数据字典
        """
        # 处理 args 参数
        final_args = args or []
        
        # ⭐ PyPI 包自动添加 UV_INDEX_URL 参数（清华源）
        if package_type == 2:  # package_type=2 表示 PyPI (uvx)
            # 检查是否已存在 UV_INDEX_URL
            has_uv_index = any(arg.get('arg_name') == 'UV_INDEX_URL' for arg in final_args)
            
            if not has_uv_index:
                uv_index_arg = {
                    "arg_name": "UV_INDEX_URL",
                    "default_value": "https://pypi.tuna.tsinghua.edu.cn/simple/",
                    "description": [
                        {
                            "type": 1,  # zh-cn
                            "content": "PyPI 镜像源地址（默认使用清华源加速下载）"
                        },
                        {
                            "type": 2,  # zh-tw
                            "content": "PyPI 鏡像源地址（默認使用清華源加速下載）"
                        },
                        {
                            "type": 3,  # en
                            "content": "PyPI mirror source URL (default: Tsinghua mirror for faster downloads)"
                        }
                    ],
                    "auth_method_id": "",
                    "type": 2,  # custom_value
                    "paramter_type": 1,  # StartupParameter
                    "input_source": 1,  # AdminInput
                    "showDefault": False,
                    "oauth_authorized": False
                }
                final_args.append(uv_index_arg)
        
        template_data = {
            "name": self.make_multi_lang(name, name_tw, name_en),
            "summary": self.make_multi_lang(summary, summary_tw, summary_en),
            "description": self.make_multi_lang(description, description_tw, description_en),
            "logo_url": logo_url,
            "template_category_id": template_category_id,
            "template_source_id": template_source_id,
            "command": command,
            "route_prefix": route_prefix,
            "package_type": package_type,
            "mcp_host": kwargs.get('mcp_host', 1),
            "publish_type": kwargs.get('publish_type', 1),
            "expose_protocal": kwargs.get('expose_protocal', 0),
            "args": final_args,  # ⭐ 使用处理后的 args
            "enable_display": kwargs.get('enable_display', True),
            "is_attach_user_storage": kwargs.get('is_attach_user_storage', False),
            "attach_container_path": kwargs.get('attach_container_path', ""),
            "auth_method_id": kwargs.get('auth_method_id', ""),
            "container_port": kwargs.get('container_port', ""),
            "server_image": kwargs.get('server_image', ""),
            "targetSseServerHost": kwargs.get('targetSseServerHost', ""),
            "targetSseServerPort": kwargs.get('targetSseServerPort', 0),
        }
        
        return template_data
    
    def auto_generate_from_project(
        self, 
        project_path: Path,
        package_name: str,
        package_type_name: str  # 'pypi', 'npm', 'docker'
    ) -> Dict:
        """
        从项目自动生成模板数据
        
        Args:
            project_path: 项目路径
            package_name: 包名（如 bachai-data-analysis-mcp）
            package_type_name: 包类型名称
            
        Returns:
            模板数据字典（供用户编辑）
        """
        # 读取 README.md
        readme_path = project_path / "README.md"
        description = ""
        summary = f"{project_path.name} MCP Server"
        
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text(encoding='utf-8')
                # 提取第一段作为简介
                lines = [l.strip() for l in readme_content.split('\n') if l.strip()]
                if len(lines) > 1:
                    summary = lines[1][:200]  # 第一行通常是标题，第二行是简介
                description = readme_content[:1000]  # 限制长度
            except:
                pass
        
        # 项目名称
        project_name = project_path.name.replace('-', ' ').replace('_', ' ').title()
        
        # 根据包类型设置参数（根据EMCP PackageType枚举）
        package_type_map = {
            'npm': 1,      # npx
            'pypi': 2,     # uvx (Python)
            'deno': 3,     # deno
            'docker': 4,   # container
            'direct_proxy': 6,
            'adaptive_proxy': 7
        }
        
        package_type = package_type_map.get(package_type_name, 1)
        
        # 根据包类型生成命令（包含工具前缀）
        if package_type_name == 'npm':
            # NPM 包：npx + 包名
            command = f"npx {package_name}"
        elif package_type_name == 'pypi':
            # PyPI 包：uvx + 包名
            command = f"uvx {package_name}"
        elif package_type_name == 'deno':
            # Deno 包：deno + 包名
            command = f"deno {package_name}"
        elif package_type_name == 'docker':
            # Docker 容器：不需要命令
            command = ""
        else:
            command = package_name
        
        # 生成 route_prefix（符合格式要求）
        import re
        route_prefix = project_path.name.lower().replace('_', '').replace('mcp', '').replace('-', '')
        # 移除非字母数字字符
        route_prefix = re.sub(r'[^a-z0-9]', '', route_prefix)
        # 如果以数字开头，添加前缀
        if route_prefix and route_prefix[0].isdigit():
            route_prefix = 'mcp' + route_prefix
        # 限制长度
        if len(route_prefix) > 10:
            route_prefix = route_prefix[:10]
        # 如果为空，使用默认值
        if not route_prefix:
            route_prefix = 'mcp'
        
        # 返回模板数据（供用户编辑）
        return {
            'name': project_name,
            'summary': summary if summary else f"{project_name} - MCP Server",
            'description': description if description else f"功能强大的 {project_name}",
            'logo_url': "/api/proxyStorage/NoAuth/default-mcp-logo.png",
            'template_category_id': "1",
            'template_source_id': package_name,
            'command': command,
            'route_prefix': route_prefix,
            'package_type': package_type,
            'package_type_name': package_type_name,
            'server_image': package_name if package_type_name == 'docker' else "",
            'container_port': "3000" if package_type_name == 'docker' else "",
        }
    
    def query_mcp_templates(
        self,
        template_source_id: str = None,
        page_index: int = 1,
        page_size: int = 20,
        auto_login_on_401: bool = True
    ) -> Dict:
        """
        查询MCP模板
        
        Args:
            template_source_id: 模板来源ID（包名）
            page_index: 页码
            page_size: 每页数量
        
        Returns:
            查询结果
        """
        url = f"{self.base_url}/api/Template/query_mcp_template_auth"
        
        payload = {
            "page_index": page_index,
            "page_size": page_size,
            "name": "",
            "template_category_id": "",
            "template_source_ids": [template_source_id] if template_source_id else [],
            "auth_method_ids": [],
            "template_ids": [],
            "publish_type": None,
            "publish_status": None,
            "enable_display": None,
            "mcp_host": None,
            "package_types": []
        }
        
        try:
            # 记录请求
            log_http_request("POST", url, headers=self._get_headers(), payload=payload)
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )
            
            # 记录响应
            try:
                data = response.json()
                log_http_response(response.status_code, response_data=data)
            except:
                log_http_response(response.status_code, response_text=response.text)
            
            # 如果是 401，自动登录
            if response.status_code == 401 and auto_login_on_401:
                HTTPLogger.log(f"\n🔐 检测到 401，自动登录并重试...")
                try:
                    from config_manager import ConfigManager
                    config_mgr = ConfigManager()
                    credentials = config_mgr.load_emcp_credentials()
                    
                    if credentials and credentials.get('phone_number'):
                        user_info = self.auto_login(credentials['phone_number'])
                        config_mgr.save_session(self.session_key, user_info)
                        HTTPLogger.log(f"   ✅ 自动登录成功，重新查询...")
                        
                        # 重新查询
                        return self.query_mcp_templates(
                            template_source_id,
                            page_index,
                            page_size,
                            auto_login_on_401=False
                        )
                except Exception as e:
                    HTTPLogger.log(f"   ❌ 自动登录失败: {e}")
            
            response.raise_for_status()
            
            if data.get('err_code') != 0:
                raise Exception(f"查询模板失败: {data.get('err_message', '未知错误')}")
            
            return data.get('body', [])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def update_mcp_template(
        self,
        template_id: str,
        template_data: Dict
    ) -> Dict:
        """
        更新MCP模板
        
        Args:
            template_id: 模板ID
            template_data: 模板数据
        
        Returns:
            更新结果
        """
        url = f"{self.base_url}/api/Template/update_mcp_template"
        
        # 添加template_id到数据中
        template_data['template_id'] = template_id
        
        try:
            # 记录请求
            log_http_request("POST", url, headers=self._get_headers(), payload=template_data)
            
            response = requests.post(
                url,
                json=template_data,
                headers=self._get_headers(),
                timeout=30
            )
            
            # 记录响应
            try:
                response_data = response.json()
                log_http_response(response.status_code, response_data=response_data)
            except:
                log_http_response(response.status_code, response_text=response.text)
            
            # 打印详细的错误信息
            if response.status_code != 200:
                print(f"\n❌ API 错误响应:")
                print(f"   状态码: {response.status_code}")
                print(f"   URL: {url}")
                try:
                    error_data = response.json()
                    print(f"   错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"   响应文本: {response.text[:500]}")
                
                # 打印发送的数据
                print(f"\n发送的数据:")
                print(json.dumps(template_data, indent=2, ensure_ascii=False)[:1000])
            
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('err_code') != 0:
                raise Exception(f"更新模板失败: {data.get('err_message', '未知错误')}")
            
            return data.get('body', {})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def create_or_update_mcp_template(
        self,
        template_source_id: str,
        template_data: Dict
    ) -> tuple:
        """
        创建或更新MCP模板（智能判断）
        
        Args:
            template_source_id: 模板来源ID（包名）
            template_data: 模板数据
        
        Returns:
            (操作类型, 结果) - 操作类型为 'created' 或 'updated'
        """
        # 1. 查询是否已存在
        try:
            existing = self.query_mcp_templates(template_source_id=template_source_id)
            
            if existing and len(existing) > 0:
                # 存在，执行更新
                template_id = existing[0]['template_id']
                result = self.update_mcp_template(template_id, template_data)
                return ('updated', result)
            else:
                # 不存在，执行创建
                result = self.create_mcp_template(template_data)
                return ('created', result)
                
        except Exception as e:
            # 查询失败，尝试创建
            result = self.create_mcp_template(template_data)
            return ('created', result)
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.session_key is not None
    
    def get_user_name(self) -> str:
        """获取用户名"""
        if self.user_info:
            return self.user_info.get('user_name', '未知用户')
        return '未登录'
    
    def get_user_code(self) -> str:
        """获取用户代码"""
        if self.user_info:
            return self.user_info.get('user_code', '')
        return ''
    
    def get_all_template_sources(self, auto_login_on_401: bool = True) -> List[Dict]:
        """
        获取所有模板来源
        
        Returns:
            模板来源列表
        """
        url = f"{self.base_url}/api/TemplateSource/get_all_template_source"
        
        try:
            # 记录请求
            log_http_request("GET", url, headers=self._get_headers())
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            
            # 记录响应
            try:
                data = response.json()
                log_http_response(response.status_code, response_data=data)
            except:
                log_http_response(response.status_code, response_text=response.text)
            
            # 如果是 401，自动登录
            if response.status_code == 401 and auto_login_on_401:
                HTTPLogger.log(f"\n🔐 检测到 401，自动登录并重试...")
                try:
                    from config_manager import ConfigManager
                    config_mgr = ConfigManager()
                    credentials = config_mgr.load_emcp_credentials()
                    
                    if credentials and credentials.get('phone_number'):
                        user_info = self.auto_login(credentials['phone_number'])
                        config_mgr.save_session(self.session_key, user_info)
                        HTTPLogger.log(f"   ✅ 自动登录成功，重新获取...")
                        
                        # 重新获取
                        return self.get_all_template_sources(auto_login_on_401=False)
                except Exception as e:
                    HTTPLogger.log(f"   ❌ 自动登录失败: {e}")
            
            response.raise_for_status()
            
            if data.get('err_code') != 0:
                raise Exception(f"获取模板来源失败: {data.get('err_message', '未知错误')}")
            
            return data.get('body', [])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def get_bach_template_source_id(self) -> str:
        """
        获取包含'bach'的模板来源ID
        
        Returns:
            模板来源ID（如 'bach-001'）
        """
        try:
            sources = self.get_all_template_sources()
            
            # 查找包含'bach'的来源
            for source in sources:
                source_id = source.get('template_source_id', '')
                source_name = source.get('template_source_name', '')
                
                if 'bach' in source_id.lower() or 'bach' in source_name.lower():
                    return source_id
            
            # 如果没找到，返回默认值
            return 'bach-001'
            
        except Exception as e:
            # 失败时返回默认值
            HTTPLogger.log(f"⚠️ 获取Bach模板来源失败: {e}，使用默认值 bach-001")
            return 'bach-001'
    
    def get_all_template_categories(self, auto_login_on_401: bool = True) -> List[Dict]:
        """
        获取所有模板分类
        
        Returns:
            分类列表
        """
        url = f"{self.base_url}/api/Template/get_all_template_category"
        
        try:
            # 记录请求
            log_http_request("GET", url, headers=self._get_headers())
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            
            # 记录响应
            try:
                data = response.json()
                log_http_response(response.status_code, response_data=data)
            except:
                log_http_response(response.status_code, response_text=response.text)
            
            # 如果是 401，自动登录
            if response.status_code == 401 and auto_login_on_401:
                HTTPLogger.log(f"\n🔐 检测到 401，自动登录并重试...")
                try:
                    from config_manager import ConfigManager
                    config_mgr = ConfigManager()
                    credentials = config_mgr.load_emcp_credentials()
                    
                    if credentials and credentials.get('phone_number'):
                        user_info = self.auto_login(credentials['phone_number'])
                        config_mgr.save_session(self.session_key, user_info)
                        HTTPLogger.log(f"   ✅ 自动登录成功，重新获取...")
                        
                        # 重新获取
                        return self.get_all_template_categories(auto_login_on_401=False)
                except Exception as e:
                    HTTPLogger.log(f"   ❌ 自动登录失败: {e}")
            
            response.raise_for_status()
            
            if data.get('err_code') != 0:
                raise Exception(f"获取分类失败: {data.get('err_message', '未知错误')}")
            
            return data.get('body', [])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
    
    def get_categories_for_llm(self) -> str:
        """
        获取分类列表的文本描述（供LLM使用）
        
        Returns:
            分类列表的文本描述
        """
        try:
            categories = self.get_all_template_categories()
            
            category_text = "可选的分类列表：\n"
            for cat in categories:
                cat_id = cat.get('template_category_id', '')
                # 获取中文名称
                name_list = cat.get('name', [])
                cat_name = '未知'
                for item in name_list:
                    if item.get('type') == 1:  # 简体中文
                        cat_name = item.get('content', '未知')
                        break
                
                category_text += f"- ID: {cat_id}, 名称: {cat_name}\n"
            
            return category_text
            
        except Exception as e:
            HTTPLogger.log(f"⚠️ 获取分类列表失败: {e}，使用默认分类")
            # 失败时返回默认分类
            return "可选的分类列表：\n- ID: 1, 名称: 数据分析\n- ID: 2, 名称: 文件处理\n- ID: 3, 名称: 开发工具\n"






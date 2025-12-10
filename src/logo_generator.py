"""Logo 获取和生成模块"""

import requests
from typing import Optional
from openai import AzureOpenAI
import base64
from pathlib import Path
import hashlib
import json


class LogoLogger:
    """Logo生成日志记录器"""
    log_func = None
    
    @classmethod
    def set_log_function(cls, log_func):
        cls.log_func = log_func
    
    @classmethod
    def log(cls, message):
        if cls.log_func:
            cls.log_func(message)
        else:
            print(message)


class LogoGenerator:
    """Logo 获取和生成器"""
    
    def __init__(
        self,
        azure_openai_client: Optional[AzureOpenAI] = None,
        jimeng_mcp_client = None,  # 已废弃，保留兼容
        jimeng_api_generator = None,  # 新：即梦 API 生成器
        emcp_base_url: str = "https://sit-emcp.kaleido.guru",
        emcp_manager = None
    ):
        """
        初始化 Logo 生成器
        
        Args:
            azure_openai_client: Azure OpenAI 客户端（可选，用于 DALL-E 生成）
            jimeng_mcp_client: [已废弃] 即梦MCP客户端
            jimeng_api_generator: 即梦 API 生成器（推荐）
            emcp_base_url: EMCP 平台地址
            emcp_manager: EMCP管理器实例（用于获取登录token）
        """
        self.openai_client = azure_openai_client
        self.jimeng_client = jimeng_mcp_client  # 兼容旧代码
        self.jimeng_api = jimeng_api_generator  # 新：即梦 API
        self.emcp_base_url = emcp_base_url
        self.emcp_manager = emcp_manager
        self.default_logo = "/api/proxyStorage/NoAuth/default-mcp-logo.png"
    
    def get_or_generate_logo(
        self,
        package_info: dict,
        package_type: str,
        generate_with_ai: bool = False,
        use_jimeng: bool = True
    ) -> str:
        """
        获取或生成 Logo（优先使用即梦MCP）
        
        Args:
            package_info: 包信息
            package_type: 包类型
            generate_with_ai: 是否使用 DALL-E 生成
            use_jimeng: 是否使用即梦MCP生成（默认True）
        
        Returns:
            Logo URL（EMCP存储URL）
        """
        LogoLogger.log(f"\n🖼️ 开始生成Logo...")
        
        # 1. 尝试从包信息中获取现有 logo
        existing_logo = self._get_existing_logo(package_info, package_type)
        if existing_logo:
            LogoLogger.log(f"   ✅ 使用包的官方Logo: {existing_logo}")
            # 下载并上传到EMCP
            emcp_logo = self._upload_logo_to_emcp(image_url=existing_logo)
            if emcp_logo != self.default_logo:
                return emcp_logo
        
        # 2. 优先使用即梦 API 生成（推荐）
        if use_jimeng:
            # 优先使用即梦 API
            if self.jimeng_api:
                try:
                    LogoLogger.log(f"   🎨 使用即梦 API 生成 Logo...")
                    jimeng_logo = self._generate_logo_with_jimeng_api(package_info)
                    if jimeng_logo:
                        LogoLogger.log(f"   ✅ 即梦 API 生成成功")
                        return jimeng_logo
                    else:
                        LogoLogger.log(f"   ⚠️ 即梦 API 返回空结果")
                except Exception as e:
                    LogoLogger.log(f"   ❌ 即梦 API 生成失败: {e}")
                    import traceback
                    LogoLogger.log(f"   详细错误: {traceback.format_exc()}")
            # 降级使用即梦 MCP（兼容旧代码）
            elif self.jimeng_client:
                try:
                    LogoLogger.log(f"   🎨 使用即梦 MCP 生成 Logo...")
                    jimeng_logo = self._generate_logo_with_jimeng(package_info)
                    if jimeng_logo:
                        LogoLogger.log(f"   ✅ 即梦 MCP 生成成功")
                        return jimeng_logo
                except Exception as e:
                    LogoLogger.log(f"   ❌ 即梦 MCP 生成失败: {e}")
            else:
                LogoLogger.log(f"   ⚠️ 即梦未配置（请在设置中配置 API 密钥）")
        
        # 3. 如果配置了 DALL-E
        if generate_with_ai and self.openai_client:
            try:
                LogoLogger.log(f"   🤖 使用DALL-E生成Logo...")
                generated_logo = self._generate_logo_with_dalle(package_info)
                if generated_logo:
                    return generated_logo
            except Exception as e:
                LogoLogger.log(f"   ⚠️ DALL-E生成失败: {e}")
        
        # 4. 使用默认 logo
        LogoLogger.log(f"   ℹ️ 使用默认Logo")
        return self.default_logo
    
    def _generate_logo_with_jimeng_api(self, package_info: dict) -> Optional[str]:
        """
        使用即梦 API 生成 Logo 并上传到 EMCP
        
        Args:
            package_info: 包信息
        
        Returns:
            EMCP Logo URL 或 None
        """
        try:
            info = package_info.get('info', {})
            package_name = package_info.get('package_name', '')
            
            # 获取描述
            readme = info.get('readme', info.get('description', ''))
            summary = info.get('summary', '')
            description = readme[:500] if readme and len(readme) > 100 else (summary or f"{package_name} package")
            
            LogoLogger.log(f"   📋 使用描述: {description[:80]}...")
            
            # 使用即梦 API 生成 Logo
            result = self.jimeng_api.generate_logo_for_mcp(
                description=description,
                mcp_name=package_name
            )
            
            if result and result.get('success'):
                image_url = result.get('image_url')
                LogoLogger.log(f"   ✅ 即梦 API 生成成功!")
                LogoLogger.log(f"   📥 图片 URL: {image_url[:60]}...")
                
                # 上传到 EMCP
                LogoLogger.log(f"   ⬆️ 上传到 EMCP...")
                emcp_logo_url = self._upload_logo_to_emcp(image_url=image_url)
                
                if emcp_logo_url and emcp_logo_url != self.default_logo:
                    LogoLogger.log(f"   ✅ Logo 已上传 EMCP: {emcp_logo_url}")
                    return emcp_logo_url
                else:
                    LogoLogger.log(f"   ❌ EMCP 上传失败，使用默认 Logo")
                    return self.default_logo
            else:
                error = result.get('error', '未知错误') if result else '无结果'
                LogoLogger.log(f"   ❌ 即梦 API 生成失败: {error}")
                return None
                
        except Exception as e:
            import traceback
            LogoLogger.log(f"   ❌ 即梦 API 生成异常: {e}")
            LogoLogger.log(f"   详情: {traceback.format_exc()[:200]}")
            return None
    
    def _generate_logo_with_jimeng(self, package_info: dict) -> Optional[str]:
        """
        [已废弃] 使用即梦 MCP 生成 Logo 并上传到 EMCP
        
        Args:
            package_info: 包信息
        
        Returns:
            EMCP Logo URL 或 None
        """
        try:
            info = package_info.get('info', {})
            package_name = package_info.get('package_name', '')
            package_type = package_info.get('type', 'unknown')
            
            # 获取描述（优先使用完整 README）
            readme = info.get('readme', info.get('description', ''))
            summary = info.get('summary', '')
            
            # 构建详细的描述用于 Logo 生成
            if readme and len(readme) > 100:
                # 使用 README 的前500字符（更详细）
                description = readme[:500]
            elif summary:
                description = summary
            else:
                description = f"{package_name} package"
            
            LogoLogger.log(f"   📋 使用描述: {description[:100]}...")
            LogoLogger.log(f"   📄 描述来源: {'README' if readme else 'summary'}")
            
            # ⭐ 从描述中提取核心功能
            core_function = self._extract_core_function(description, package_name)
            design_elements = self._get_design_elements(core_function, description)
            
            # 构建中文提示词 - 基于 MCP 实际功能
            prompt = f"""MCP 服务 Logo 设计

服务名称: {core_function}
功能描述: {description[:500] if description else core_function}

设计要求:
- 主题: 现代科技风格，蓝色或紫色渐变
- 核心元素: {design_elements}
- 风格: 扁平化、简约、专业、高端
- 布局: 方形图标，简洁背景
- 整体感觉: 智能、可靠、专业的 AI 服务

请设计一个能体现"{core_function}"功能的现代化 Logo"""
            
            LogoLogger.log(f"   📝 提示词: {prompt[:80]}...")
            
            # 调用即梦MCP生成图片（不上传，因为需要token）
            # 传入降级描述，即使包不存在也可以生成
            result = self.jimeng_client.generate_logo_from_package(
                package_url=package_name,
                emcp_base_url=self.emcp_base_url,
                use_v40=True,
                fallback_description=description  # 降级描述
            )
            
            if result and result.get('success'):
                jimeng_url = result.get('jimeng_url')
                local_file = result.get('local_file')
                
                LogoLogger.log(f"   ✅ 即梦MCP生成成功!")
                LogoLogger.log(f"   📥 即梦URL: {jimeng_url[:60]}...")
                
                # 自己上传到 EMCP（带token认证）
                LogoLogger.log(f"   ⬆️ 上传到EMCP...")
                emcp_logo_url = self._upload_logo_to_emcp(image_url=jimeng_url)
                
                if emcp_logo_url and emcp_logo_url != self.default_logo:
                    LogoLogger.log(f"   ✅ Logo已上传EMCP: {emcp_logo_url}")
                    return emcp_logo_url  # ✅ 返回 EMCP URL
                else:
                    # 上传失败，使用默认 logo（不使用即梦临时URL）
                    LogoLogger.log(f"   ❌ EMCP上传失败，使用默认Logo")
                    if local_file:
                        LogoLogger.log(f"   💾 本地备份: {local_file}")
                    return self.default_logo  # ✅ 返回默认 logo，不返回即梦URL
            
            return None
            
        except Exception as e:
            import traceback
            LogoLogger.log(f"   ❌ 即梦MCP生成Logo异常: {e}")
            LogoLogger.log(f"   详情: {traceback.format_exc()[:200]}")
            return None
    
    def _extract_core_function(self, description: str, package_name: str) -> str:
        """从描述中提取核心功能"""
        import re
        
        # 清理包名，提取有意义的部分
        clean_name = package_name.replace('bach-', '').replace('bachai-', '')
        clean_name = clean_name.replace('-mcp', '').replace('_mcp', '')
        clean_name = clean_name.replace('-', ' ').replace('_', ' ')
        
        # 尝试从描述中提取功能关键词
        if description:
            patterns = [
                r'用于[「【]?([^」】,，。.]+)[」】]?的',
                r'提供[「【]?([^」】,，。.]+)[」】]?服务',
                r'一个[「【]?([^」】,，。.]+)[」】]?的',
                r'for\s+([a-zA-Z\s]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, description)
                if match:
                    extracted = match.group(1).strip()
                    if len(extracted) > 2 and len(extracted) < 30:
                        return extracted
            
            first_sentence = description.split('。')[0].split('.')[0]
            if len(first_sentence) > 5 and len(first_sentence) < 50:
                return first_sentence[:30]
        
        return clean_name if clean_name else "AI 服务"
    
    def _get_design_elements(self, core_function: str, description: str) -> str:
        """根据核心功能获取设计元素"""
        text = f"{core_function} {description}".lower()
        
        element_map = {
            ('数据', 'data', '分析', 'analytics'): '数据图表、统计曲线、智能分析',
            ('搜索', 'search', '检索', '查询'): '搜索图标、放大镜、数据流',
            ('商品', '电商', 'amazon', 'walmart', '购物'): '购物车、商品标签、价格曲线',
            ('支付', 'pay', 'payment', '金融'): '金融符号、安全盾牌、交易流程',
            ('社交', 'social', '媒体', 'twitter', 'instagram'): '社交网络、连接节点、对话气泡',
            ('视频', 'video', 'youtube', '影音'): '播放按钮、视频帧、流媒体',
            ('地图', 'map', '位置', 'location'): '地图标记、定位图标、路线',
            ('房产', 'real', 'estate', 'property'): '建筑剪影、房屋图标、城市天际线',
            ('消息', 'message', 'whatsapp', '通讯'): '消息气泡、通讯图标、连接线',
            ('文件', 'file', 'document', '文档'): '文件图标、文档堆叠、整理',
            ('翻译', 'translat', '语言'): '语言符号、翻译箭头、地球',
            ('天气', 'weather', '气象'): '天气图标、云朵、温度计',
            ('工作', 'job', '招聘', 'career'): '公文包、职业图标、人才网络',
            ('新闻', 'news', '资讯'): '报纸、信息流、新闻图标',
            ('ai', '智能', 'intelligent'): '神经网络、AI芯片、智能大脑',
        }
        
        for keywords, elements in element_map.items():
            if any(kw in text for kw in keywords):
                return elements
        
        return '科技齿轮、数据节点、智能连接'
    
    def _get_existing_logo(self, package_info: dict, package_type: str) -> Optional[str]:
        """
        尝试从包信息中获取现有 logo
        
        Returns:
            Logo URL 或 None
        """
        info = package_info.get('info', {})
        
        # PyPI 包可能在 project_urls 中有 logo
        if package_type == 'pypi':
            project_urls = info.get('project_urls', {})
            
            # 检查常见的 logo 链接
            for key in ['Logo', 'Icon', 'Image']:
                if key in project_urls:
                    return project_urls[key]
            
            # 尝试从 home_page 获取
            home_page = info.get('home_page', '')
            if home_page and 'github.com' in home_page:
                # GitHub 项目可能有 logo
                # 格式: https://github.com/user/repo
                # Logo: https://github.com/user/repo/raw/main/logo.png
                pass  # 需要额外的 API 调用
        
        # NPM 包可能在 readme 或 repository 中有 logo
        elif package_type == 'npm':
            # NPM 包的 readme 中可能有 logo 链接
            readme = info.get('description', '')
            # 可以解析 markdown 中的图片链接
            pass
        
        # Docker 镜像可能有 logo
        elif package_type == 'docker':
            # Docker Hub 有 logo 字段
            pass
        
        return None
    
    def _generate_logo_with_dalle(self, package_info: dict) -> Optional[str]:
        """
        使用 DALL-E 生成 logo
        
        注意：这需要额外的配置和成本
        
        Args:
            package_info: 包信息
        
        Returns:
            生成的 logo URL 或 None
        """
        if not self.openai_client:
            return None
        
        info = package_info.get('info', {})
        package_name = package_info.get('package_name', '')
        summary = info.get('summary', '')
        
        # 构建 prompt
        prompt = f"""
Create a modern, professional, minimalist logo for a software package called "{package_name}".
The package is: {summary[:100]}

Style requirements:
- Simple and clean design
- Flat design style
- Technology/software themed
- Use 2-3 colors maximum
- Square format (512x512)
- Professional and modern
"""
        
        try:
            # 注意: DALL-E 生成需要特定的 Azure OpenAI 部署
            # 这里仅作示例，实际使用需要配置 DALL-E 部署
            
            # response = self.openai_client.images.generate(
            #     model="dall-e-3",  # 或 dall-e-2
            #     prompt=prompt,
            #     size="512x512",
            #     quality="standard",
            #     n=1,
            # )
            # 
            # image_url = response.data[0].url
            # 
            # # 下载并上传到 EMCP 存储
            # uploaded_url = self._upload_logo_to_emcp(image_url)
            # return uploaded_url
            
            # 当前返回 None，因为需要额外配置
            return None
            
        except Exception as e:
            print(f"DALL-E 生成失败: {e}")
            return None
    
    def _upload_logo_to_emcp(
        self,
        image_url: str = None,
        image_path: str = None,
        base_url: str = "https://sit-emcp.kaleido.guru",
        _retry_count: int = 0
    ) -> str:
        """
        上传图片到 EMCP 存储（支持401自动重登录重试）
        
        Args:
            image_url: 图片 URL（二选一）
            image_path: 本地图片路径（二选一）
            base_url: EMCP 平台地址
            _retry_count: 内部重试计数（避免无限循环）
        
        Returns:
            EMCP 存储中的 URL
        """
        try:
            # 准备图片数据
            if image_url:
                # 步骤 1: 从 URL 下载图片
                LogoLogger.log(f"   ⬇️ 下载图片: {image_url[:60]}...")
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                image_data = response.content
                LogoLogger.log(f"   ✅ 下载完成: {len(image_data):,} 字节")
                # 从 URL 推断文件名
                filename = image_url.split('/')[-1].split('?')[0] or 'logo.png'
                if not filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    filename = 'logo.png'
            elif image_path:
                # 从本地读取图片
                LogoLogger.log(f"   📂 读取本地文件: {image_path}")
                from pathlib import Path
                path = Path(image_path)
                with open(path, 'rb') as f:
                    image_data = f.read()
                LogoLogger.log(f"   ✅ 读取完成: {len(image_data):,} 字节")
                filename = path.name
            else:
                return self.default_logo
            
            # 步骤 2: 上传到 EMCP
            upload_url = f"{base_url}/api/proxyStorage/NoAuth/upload_file"
            
            # 构建 multipart/form-data 文件流
            files = {
                'file': (filename, image_data, 'image/png')
            }
            
            # 添加 token header (如果已登录)
            headers = {}
            if self.emcp_manager and hasattr(self.emcp_manager, 'session_key') and self.emcp_manager.session_key:
                headers['token'] = self.emcp_manager.session_key
                headers['language'] = 'ch_cn'
                LogoLogger.log(f"\n{'='*70}")
                LogoLogger.log(f"📤 上传文件流到 EMCP")
                LogoLogger.log(f"   URL: {upload_url}")
                LogoLogger.log(f"   文件名: {filename}")
                LogoLogger.log(f"   大小: {len(image_data):,} 字节")
                LogoLogger.log(f"   Token: {self.emcp_manager.session_key[:20]}...")
                LogoLogger.log(f"{'='*70}\n")
            else:
                LogoLogger.log(f"\n{'='*70}")
                LogoLogger.log(f"📤 上传文件流到 EMCP (无认证)")
                LogoLogger.log(f"   URL: {upload_url}")
                LogoLogger.log(f"   文件名: {filename}")
                LogoLogger.log(f"   大小: {len(image_data):,} 字节")
                LogoLogger.log(f"   ⚠️ 未登录")
                LogoLogger.log(f"{'='*70}\n")
            
            # 上传文件流
            response = requests.post(upload_url, files=files, headers=headers, timeout=30)
            
            # 检查 401 错误（token 过期）
            if response.status_code == 401 and _retry_count == 0:
                LogoLogger.log(f"\n⚠️ 收到 401 Unauthorized - Token 可能已过期")
                
                # 尝试重新登录
                if self.emcp_manager and hasattr(self.emcp_manager, 'auto_login'):
                    LogoLogger.log(f"🔄 尝试重新登录 EMCP...")
                    
                    try:
                        # 调用自动登录
                        from src.unified_config_manager import UnifiedConfigManager
                        config_mgr = UnifiedConfigManager()
                        config = config_mgr.load_config()
                        creds = config.get('emcp', {})
                        
                        if creds:
                            login_result = self.emcp_manager.login(
                                creds['phone_number'],
                                creds['validation_code']
                            )
                            
                            if login_result:
                                LogoLogger.log(f"✅ 重新登录成功，获得新 token")
                                LogoLogger.log(f"🔄 重试上传...")
                                
                                # 重试上传（_retry_count=1 避免无限循环）
                                return self._upload_logo_to_emcp(
                                    image_url=image_url,
                                    image_path=image_path,
                                    base_url=base_url,
                                    _retry_count=1
                                )
                            else:
                                LogoLogger.log(f"❌ 重新登录失败")
                        else:
                            LogoLogger.log(f"⚠️ 未找到登录凭据，无法重新登录")
                            
                    except Exception as login_error:
                        LogoLogger.log(f"❌ 重新登录异常: {login_error}")
                
                # 重新登录失败，返回默认 logo
                LogoLogger.log(f"❌ Token 过期且重新登录失败，使用默认 logo")
                return self.default_logo
            
            data = response.json()
            
            LogoLogger.log(f"\n{'='*70}")
            LogoLogger.log(f"📥 响应: {response.status_code}")
            LogoLogger.log(f"📋 {json.dumps(data, indent=2, ensure_ascii=False)}")
            LogoLogger.log(f"{'='*70}\n")
            
            response.raise_for_status()
            
            if data.get('err_code') == 0:
                file_url = data.get('body', {}).get('fileUrl', '')
                if file_url:
                    LogoLogger.log(f"✅ Logo 上传成功: {file_url}")
                    return file_url
            
            # 上传失败，使用默认 logo
            LogoLogger.log(f"⚠️ Logo 上传失败，使用默认 logo")
            return self.default_logo
            
        except Exception as e:
            LogoLogger.log(f"❌ Logo 上传异常: {e}")
            return self.default_logo
    
    def generate_simple_text_logo(
        self,
        package_name: str,
        upload_to_emcp: bool = True,
        base_url: str = "https://sit-emcp.kaleido.guru"
    ) -> str:
        """
        生成简单的文字 logo（使用 PIL）并上传到 EMCP
        
        这是一个轻量级方案，不需要 DALL-E
        
        Args:
            package_name: 包名
            upload_to_emcp: 是否上传到 EMCP
            base_url: EMCP 平台地址
        
        Returns:
            Logo URL
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import tempfile
            
            # 创建 512x512 的图片
            img = Image.new('RGB', (512, 512), color=(33, 150, 243))
            draw = ImageDraw.Draw(img)
            
            # 获取包名首字母
            initials = ''.join([word[0].upper() for word in package_name.split('-')[:2]])
            if len(initials) > 3:
                initials = initials[:3]
            
            # 绘制文字
            try:
                font = ImageFont.truetype("arial.ttf", 200)
            except:
                try:
                    # Windows 系统字体
                    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 200)
                except:
                    font = ImageFont.load_default()
            
            # 计算文字位置（居中）
            bbox = draw.textbbox((0, 0), initials, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((512 - text_width) // 2, (512 - text_height) // 2)
            
            # 绘制文字
            draw.text(position, initials, fill=(255, 255, 255), font=font)
            
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                img.save(tmp_file.name)
                temp_path = tmp_file.name
            
            # 上传到 EMCP
            if upload_to_emcp:
                logo_url = self._upload_logo_to_emcp(
                    image_path=temp_path,
                    base_url=base_url
                )
                # 删除临时文件
                try:
                    from pathlib import Path
                    Path(temp_path).unlink()
                except:
                    pass
                return logo_url
            else:
                return temp_path
            
        except ImportError:
            print("PIL/Pillow 未安装，无法生成文字 logo")
            return self.default_logo
        except Exception as e:
            print(f"生成文字 logo 失败: {e}")
            return self.default_logo


# 测试代码
if __name__ == '__main__':
    generator = LogoGenerator()
    
    # 测试包信息
    package_info = {
        'package_name': 'test-package',
        'info': {
            'summary': 'A test package',
        }
    }
    
    # 获取 logo
    logo = generator.get_or_generate_logo(package_info, 'pypi')
    print(f"Logo: {logo}")
    
    # 生成简单文字 logo
    # text_logo = generator.generate_simple_text_logo('test-package')
    # print(f"Text Logo: {text_logo}")


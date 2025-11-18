"""AI模板生成器 - 使用 Azure OpenAI 自动生成模板信息"""

from openai import AzureOpenAI
from typing import Dict, Optional
import json
from src.logo_generator import LogoGenerator


class AITemplateGenerator:
    """使用 Azure OpenAI 生成 MCP 模板信息"""
    
    def __init__(
        self,
        azure_endpoint: str,
        api_key: str,
        api_version: str = "2024-02-15-preview",
        deployment_name: str = "gpt-4",
        enable_logo_generation: bool = False,
        emcp_manager = None
    ):
        """
        初始化 AI 生成器
        
        Args:
            azure_endpoint: Azure OpenAI endpoint
            api_key: Azure OpenAI API key
            api_version: API 版本
            deployment_name: 部署名称（模型名）
            enable_logo_generation: 是否启用 Logo 生成（需要 DALL-E）
            emcp_manager: EMCP管理器实例（用于Logo上传时获取token）
        """
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version
        )
        self.deployment_name = deployment_name
        self.enable_logo_generation = enable_logo_generation
        self.emcp_manager = emcp_manager
        
        # 初始化即梦MCP客户端（用于Logo生成）
        self.jimeng_client = None
        try:
            from src.jimeng_logo_generator import JimengLogoGenerator
            from src.unified_config_manager import UnifiedConfigManager
            
            # 从配置文件读取即梦 MCP 配置
            config_mgr = UnifiedConfigManager()
            jimeng_cfg = config_mgr.get_jimeng_config()
            
            print(f"\n📋 即梦配置:")
            print(f"   启用状态: {jimeng_cfg.get('enabled', True)}")
            print(f"   MCP URL: {jimeng_cfg.get('mcp_url', '未配置')}")
            
            if jimeng_cfg.get("enabled", True):
                jimeng_config = {
                    "base_url": jimeng_cfg.get("mcp_url", "http://mcptest013.sitmcp.kaleido.guru/sse"),
                    "headers": {
                        "emcp-key": jimeng_cfg.get("emcp_key", "PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n"),
                        "emcp-usercode": jimeng_cfg.get("emcp_usercode", "VGSdDTgj")
                    }
                }
                
                print(f"   正在初始化即梦 MCP 客户端...")
                self.jimeng_client = JimengLogoGenerator(jimeng_config)
                print("✅ 即梦 MCP 客户端已初始化")
                print(f"   Base URL: {jimeng_config['base_url']}")
            else:
                print("⚠️  即梦 AI Logo 生成已在设置中禁用")
        except Exception as e:
            # 即梦客户端初始化失败，不影响其他功能
            print(f"❌ 即梦客户端初始化失败: {str(e)}")
            import traceback
            print(f"   详细错误:\n{traceback.format_exc()}")
            pass
        
        # 初始化 Logo 生成器
        self.logo_generator = LogoGenerator(
            azure_openai_client=self.client if enable_logo_generation else None,
            jimeng_mcp_client=self.jimeng_client,
            emcp_manager=self.emcp_manager  # 传递 EMCP 管理器用于上传认证
        )
    
    def generate_template_info(
        self,
        package_info: Dict,
        package_type: str,
        available_categories: str = None
    ) -> Dict:
        """
        根据包信息生成模板数据
        
        Args:
            package_info: 从 PackageFetcher 获取的包信息
            package_type: 包类型 ('pypi', 'npm', 'docker')
            available_categories: 可用分类列表（文本格式）
        
        Returns:
            {
                'name': str,          # MCP 名称（简体）
                'name_tw': str,       # MCP 名称（繁体）
                'name_en': str,       # MCP 名称（英文）
                'summary': str,       # 简介（简体）
                'summary_tw': str,    # 简介（繁体）
                'summary_en': str,    # 简介（英文）
                'description': str,   # 描述（简体）
                'description_tw': str,  # 描述（繁体）
                'description_en': str,  # 描述（英文）
                'command': str,       # 启动命令
                'route_prefix': str,  # 路由前缀
                'category_id': str,   # 分类ID
            }
        """
        # 构建 prompt
        prompt = self._build_prompt(package_info, package_type, available_categories)
        
        try:
            # 调用 Azure OpenAI 生成三语言内容
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的 MCP (Model Context Protocol) Server 描述生成助手。你需要根据包信息生成吸引人的、专业的模板描述。你必须同时生成中文简体、中文繁体、英文三个版本，其中繁体中文必须使用正确的繁体字（如：數據、伺服器、檔案、網絡、檢索等）。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # 解析响应
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # 补充默认值
            return self._complete_template_info(result, package_info, package_type)
            
        except Exception as e:
            # 如果 AI 生成失败，使用备用方案
            print(f"AI 生成失败，使用备用方案: {str(e)}")
            return self._fallback_generate(package_info, package_type)
    
    def _build_prompt(self, package_info: Dict, package_type: str, available_categories: str = None) -> str:
        """构建 AI prompt"""
        info = package_info.get('info', {})
        package_name = package_info.get('package_name', '')
        
        # 分类列表
        categories_text = available_categories or """
可选的分类列表：
- ID: 1, 名称: 数据分析
- ID: 2, 名称: 文件处理
- ID: 3, 名称: 开发工具
- ID: 4, 名称: 网络服务
- ID: 5, 名称: 其他
"""
        
        # 获取完整的 README/描述
        full_readme = info.get('readme', info.get('description', ''))
        
        # 如果有 README，使用完整内容；否则使用简介
        description_for_ai = full_readme if full_readme else info.get('summary', '暂无')
        
        # 限制 AI prompt 的长度（但保留更多信息）
        if len(description_for_ai) > 3000:
            description_for_ai = description_for_ai[:3000] + "\n\n... (描述较长，已截取前3000字符)"
        
        prompt = f"""
请根据以下包信息，为一个 MCP (Model Context Protocol) Server 生成吸引人的模板描述。

**包类型**: {package_type.upper()}
**包名**: {package_name}
**版本**: {info.get('version', '1.0.0')}
**原始简介**: {info.get('summary', '暂无')}
**完整描述/README**:
{description_for_ai}

**作者**: {info.get('author', '未知')}

{categories_text}

请生成以下 JSON 格式的内容（包含简体中文、繁体中文、英文三个版本）：

{{
  "name_cn": "MCP Server 的中文简体名称（简短、吸引人）",
  "name_tw": "MCP Server 的中文繁體名稱（請使用正確的繁體字）",
  "name_en": "English name of the MCP Server (concise and attractive)",
  "summary_cn": "一句话中文简体简介（20-50字，突出核心功能和价值）",
  "summary_tw": "一句話中文繁體簡介（請使用正確的繁體字，如：資料、檔案、網絡、伺服器等）",
  "summary_en": "One-sentence English summary (highlighting core features and value)",
  "description_cn": "详细功能描述（简体中文，100-300字，包括：核心功能、使用场景、特色优势）",
  "description_tw": "詳細功能描述（繁體中文，100-300字，請使用正確的繁體字）",
  "description_en": "Detailed English description (100-300 words: core features, use cases, advantages)",
  "route_prefix": "建议的路由前缀（仅小写字母和数字，不能以数字开头，不超过10字符，如 filesearch）",
  "category_id": "从上面分类列表中选择最合适的ID（只填写ID，如 1、2、3 等）"
}}

**重要要求**：
1. 名称、简介、描述都要提供简体、繁体、英文三个版本
2. 繁体中文必须使用正确的繁体字，例如：
   - 数据 → 數據
   - 服务器 → 伺服器
   - 文件 → 檔案
   - 网络 → 網絡
   - 检索 → 檢索
   - 内容 → 內容
3. **特殊翻译规则**：
   - bachai → 巴赫 (不是巴凯)
   - bachstudio → 巴赫工作室
   - BACH → 巴赫
   例如：bachai-data-analysis-mcp → 巴赫数据分析服务器
4. route_prefix 规则：
   - 只能包含小写字母(a-z)和数字(0-9)
   - 不能以数字开头
   - 不超过10个字符
   - 不要使用横杠或下划线
   - 示例：filesearch, dataanaly, webparser
5. category_id 必须从上面的分类列表中选择
6. 所有文本要专业、流畅、吸引人
7. 必须返回有效的 JSON 格式
"""
        return prompt
    
    def _complete_template_info(
        self,
        ai_result: Dict,
        package_info: Dict,
        package_type: str
    ) -> Dict:
        """补充完整的模板信息"""
        package_name = package_info.get('package_name', '')
        
        # 生成启动命令
        command = self._generate_command(package_name, package_type)
        
        # 直接使用 LLM 生成的 category_id
        category_id = ai_result.get('category_id', '1')
        
        # 生成路由前缀（确保符合格式要求）
        route_prefix = ai_result.get('route_prefix', package_name.lower().replace('_', '').replace('/', '').replace('-', ''))
        route_prefix = self._normalize_route_prefix(route_prefix)
        
        # 获取或生成 Logo (即梦MCP已启用 ✅)
        print(f"\n🖼️ 开始生成 Logo...")
        print(f"   即梦客户端状态: {'已初始化' if self.jimeng_client else '未初始化'}")
        
        logo_url = self.logo_generator.get_or_generate_logo(
            package_info,
            package_type,
            generate_with_ai=self.enable_logo_generation,
            use_jimeng=True  # ✅ 启用即梦MCP生成Logo
        )
        
        print(f"✅ Logo URL: {logo_url}")
        
        return {
            'name': ai_result.get('name_cn', ai_result.get('name', package_name)),
            'name_tw': ai_result.get('name_tw', ai_result.get('name_cn', package_name)),
            'name_en': ai_result.get('name_en', package_name),
            'summary': ai_result.get('summary_cn', ai_result.get('summary', '')),
            'summary_tw': ai_result.get('summary_tw', ai_result.get('summary_cn', '')),
            'summary_en': ai_result.get('summary_en', ''),
            'description': ai_result.get('description_cn', ai_result.get('description', '')),
            'description_tw': ai_result.get('description_tw', ai_result.get('description_cn', '')),
            'description_en': ai_result.get('description_en', ''),
            'command': command,
            'route_prefix': route_prefix,
            'category_id': category_id,
            'package_type': package_type,
            'package_name': package_name,
            'logo_url': logo_url,
            'version': package_info.get('info', {}).get('version', '1.0.0')
        }
    
    def _normalize_route_prefix(self, route_prefix: str) -> str:
        """
        规范化路由前缀
        
        规则：
        - 只能包含小写字母和数字
        - 不能以数字开头
        - 长度不超过10个字符
        
        Args:
            route_prefix: 原始路由前缀
        
        Returns:
            规范化后的路由前缀
        """
        import re
        
        # 移除所有非字母数字字符
        route_prefix = re.sub(r'[^a-z0-9]', '', route_prefix.lower())
        
        # 如果以数字开头，添加字母前缀
        if route_prefix and route_prefix[0].isdigit():
            route_prefix = 'mcp' + route_prefix
        
        # 如果为空，使用默认值
        if not route_prefix:
            route_prefix = 'mcp'
        
        # 限制长度不超过10个字符
        if len(route_prefix) > 10:
            route_prefix = route_prefix[:10]
        
        return route_prefix
    
    def _generate_command(self, package_name: str, package_type: str) -> str:
        """
        生成启动命令（包含工具前缀）
        
        包类型映射：
        - npm → npx package-name (package_type=1)
        - pypi → uvx package-name (package_type=2)
        - deno → deno package-name (package_type=3)
        - docker → (空) (package_type=4)
        """
        if package_type == 'npm':
            # NPM 包：npx + 包名
            return f"npx {package_name}"
        elif package_type == 'pypi':
            # PyPI 包：uvx + 包名
            return f"uvx {package_name}"
        elif package_type == 'deno':
            # Deno 包：deno + 包名
            return f"deno {package_name}"
        elif package_type == 'docker':
            # Docker 容器：不需要命令
            return ""
        else:
            # 默认：直接返回包名
            return package_name
    
    def _fallback_generate(
        self,
        package_info: Dict,
        package_type: str
    ) -> Dict:
        """
        备用生成方案（当 AI 失败时）
        
        直接使用包信息，不经过 AI 处理
        """
        info = package_info.get('info', {})
        package_name = package_info.get('package_name', '')
        
        # 从包名生成名称
        name = package_name.replace('-', ' ').replace('_', ' ').title()
        
        # 使用原始简介
        summary = info.get('summary', f'{name} MCP Server')[:200]
        
        # 使用原始描述
        description = info.get('description', summary)[:1000]
        if not description:
            description = f"{name} - 功能强大的 MCP Server"
        
        # 生成路由前缀（确保不超过10个字符，且符合格式要求）
        route_prefix = package_name.lower().replace('_', '').replace('/', '').replace('-', '')
        route_prefix = self._normalize_route_prefix(route_prefix)
        
        # 生成命令
        command = self._generate_command(package_name, package_type)
        
        return {
            'name': name,
            'name_tw': name,  # 简单转换，不如LLM准确
            'name_en': package_name.replace('-', ' ').replace('_', ' ').title(),
            'summary': summary,
            'summary_tw': summary,  # 简单转换
            'summary_en': info.get('summary', summary),  # 使用包的原始英文简介
            'description': description,
            'description_tw': description,  # 简单转换
            'description_en': info.get('description', description)[:1000],  # 使用包的原始英文描述
            'command': command,
            'route_prefix': route_prefix,
            'category_id': '1',
            'package_type': package_type,
            'package_name': package_name,
            'logo_url': '/api/proxyStorage/NoAuth/default-mcp-logo.png',
            'version': info.get('version', '1.0.0')
        }


# 测试代码
if __name__ == '__main__':
    # 这里需要替换为真实的 Azure OpenAI 配置
    # generator = AITemplateGenerator(
    #     azure_endpoint="https://your-resource.openai.azure.com/",
    #     api_key="your-api-key",
    #     deployment_name="gpt-4"
    # )
    
    # 测试备用方案
    package_info = {
        'type': 'pypi',
        'package_name': 'requests',
        'url': 'https://pypi.org/project/requests',
        'info': {
            'name': 'requests',
            'version': '2.31.0',
            'summary': 'Python HTTP for Humans.',
            'description': 'Requests is an elegant and simple HTTP library for Python, built for human beings.'
        }
    }
    
    generator = AITemplateGenerator(
        azure_endpoint="https://placeholder.openai.azure.com/",
        api_key="placeholder-key"
    )
    
    result = generator._fallback_generate(package_info, 'pypi')
    print(json.dumps(result, indent=2, ensure_ascii=False))


"""AI模板生成器 - 使用 Azure OpenAI 自动生成模板信息"""

from openai import AzureOpenAI
from typing import Dict, Optional
import json
import httpx
from src.logo_generator import LogoGenerator


class AITemplateGenerator:
    """使用 Azure OpenAI 生成 MCP 模板信息"""
    
    # 超时设置（秒）
    DEFAULT_TIMEOUT = 60  # 默认 60 秒超时
    
    def __init__(
        self,
        azure_endpoint: str,
        api_key: str,
        api_version: str = "2024-02-15-preview",
        deployment_name: str = "gpt-4",
        enable_logo_generation: bool = False,
        emcp_manager = None,
        timeout: int = None
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
            timeout: 请求超时时间（秒），默认 60 秒
        """
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version=api_version,
            timeout=httpx.Timeout(self.timeout, connect=10.0)  # 连接超时 10s，总超时 60s
        )
        self.deployment_name = deployment_name
        self.enable_logo_generation = enable_logo_generation
        self.emcp_manager = emcp_manager
        
        # 初始化即梦 API 客户端（用于 Logo 生成）
        self.jimeng_api = None
        try:
            from src.jimeng_api_generator import JimengAPIGenerator
            from src.unified_config_manager import UnifiedConfigManager
            
            config_mgr = UnifiedConfigManager()
            jimeng_cfg = config_mgr.get_jimeng_config()
            
            print(f"\n📋 即梦配置:")
            print(f"   启用状态: {jimeng_cfg.get('enabled', True)}")
            
            if jimeng_cfg.get("enabled", True):
                # 获取 API 密钥
                access_key = jimeng_cfg.get("access_key", "")
                secret_key = jimeng_cfg.get("secret_key", "")
                
                if access_key and secret_key:
                    print(f"   Access Key: {access_key[:20]}...")
                    self.jimeng_api = JimengAPIGenerator(access_key, secret_key)
                else:
                    print("⚠️  即梦 API 密钥未配置，Logo 生成功能将被禁用")
                    print("   请在设置窗口的「即梦 AI 配置」中配置 Access Key 和 Secret Key")
            else:
                print("⚠️  即梦 AI Logo 生成已在设置中禁用")
        except Exception as e:
            print(f"❌ 即梦 API 初始化失败: {str(e)}")
            import traceback
            print(f"   详细错误:\n{traceback.format_exc()}")
        
        # 初始化 Logo 生成器
        self.logo_generator = LogoGenerator(
            azure_openai_client=self.client if enable_logo_generation else None,
            jimeng_api_generator=self.jimeng_api,  # 使用即梦 API
            emcp_manager=self.emcp_manager
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
        
        # ⭐ 保存 prompt 到文件
        try:
            from pathlib import Path
            log_dir = Path("outputs/ai_logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            package_name = package_info.get('package_name', 'unknown')
            prompt_file = log_dir / f"prompt_{package_name}.txt"
            prompt_file.write_text(prompt, encoding='utf-8')
            print(f"\n📝 AI Prompt 已保存到: {prompt_file}")
            print(f"   文件大小: {len(prompt)} 字符")
        except Exception as e:
            print(f"⚠️ 保存 prompt 失败: {e}")
        
        # ⭐ 打印 prompt 摘要
        print(f"\n{'='*70}")
        print(f"📤 发送给 AI 的 Prompt (前 500 字符):")
        print(f"{'='*70}")
        print(prompt[:500])
        if len(prompt) > 500:
            print(f"... (总共 {len(prompt)} 字符，已截取)")
        print(f"{'='*70}\n")
        
        try:
            # 调用 Azure OpenAI 生成三语言内容
            print(f"🤖 调用 Azure OpenAI...")
            print(f"   模型: {self.deployment_name}")
            print(f"   温度: 0.7")
            print(f"   最大 tokens: 2000")
            print(f"   超时: {self.timeout} 秒")
            
            # ⭐ 带超时重试的 AI 调用
            max_retries = 2
            response = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        print(f"   🔄 重试第 {attempt} 次...")
                    
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
                    break  # 成功，退出重试循环
                    
                except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as timeout_err:
                    print(f"   ⏰ 请求超时: {timeout_err}")
                    if attempt < max_retries:
                        print(f"   将在 5 秒后重试...")
                        import time
                        time.sleep(5)
                    else:
                        raise Exception(f"AI 请求超时（已重试 {max_retries} 次）: {timeout_err}")
            
            if response is None:
                raise Exception("AI 请求失败：未收到响应")
            
            # 解析响应
            result_text = response.choices[0].message.content
            
            # ⭐ 保存响应到文件
            try:
                from pathlib import Path
                log_dir = Path("outputs/ai_logs")
                log_dir.mkdir(parents=True, exist_ok=True)
                
                package_name = package_info.get('package_name', 'unknown')
                response_file = log_dir / f"response_{package_name}.json"
                response_file.write_text(result_text, encoding='utf-8')
                print(f"\n📥 AI 响应已保存到: {response_file}")
                print(f"   文件大小: {len(result_text)} 字符")
            except Exception as e:
                print(f"⚠️ 保存响应失败: {e}")
            
            # ⭐ 打印完整的 AI 响应
            print(f"\n{'='*70}")
            print(f"📥 AI 原始响应 (JSON):")
            print(f"{'='*70}")
            print(result_text)
            print(f"{'='*70}\n")
            
            result = json.loads(result_text)
            
            # ⭐ 检查并验证描述字段
            print(f"\n{'='*70}")
            print(f"🔍 验证 AI 生成的描述:")
            print(f"{'='*70}")
            
            if result.get('description_cn'):
                desc = result['description_cn']
                desc_len = len(desc)
                
                print(f"✓ 中文描述长度: {desc_len} 字符")
                print(f"\n📄 中文描述内容:")
                print(f"{'─'*70}")
                print(desc)
                print(f"{'─'*70}\n")
                
                # 检查是否包含错误格式
                bad_patterns = [
                    ('- **PyPI 包名', '列表格式的包名'),
                    ('- **版本', '列表格式的版本'),
                    ('- **传输协议', '列表格式的传输协议'),
                    ('这是一个\n\n-', '"这是一个"后直接跟列表'),
                    ('PyPI 包名:', '包名字段'),
                    ('版本:', '版本字段'),
                    ('传输协议:', '传输协议字段'),
                ]
                
                has_error = False
                for pattern, reason in bad_patterns:
                    if pattern in desc:
                        has_error = True
                        print(f"❌ 错误：描述包含禁止内容")
                        print(f"   模式: {pattern}")
                        print(f"   原因: {reason}")
                        break
                
                if desc_len < 50:
                    has_error = True
                    print(f"❌ 错误：描述太短（少于 50 字符）")
                
                if has_error:
                    print(f"\n⚠️ AI 生成的描述格式不正确，将使用备用方案")
                    print(f"{'='*70}\n")
                    # 清空错误的描述，让后续使用备用方案
                    result['description_cn'] = ""
                    result['description_tw'] = ""
                    result['description_en'] = ""
                else:
                    print(f"✅ 描述格式正确")
                    print(f"{'='*70}\n")
            else:
                print(f"❌ 警告：AI 响应中缺少 description_cn 字段")
                print(f"{'='*70}\n")
            
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
        
        # ⭐ 添加调试输出
        print(f"\n📋 传给 AI 的 README 内容:")
        print(f"   长度: {len(description_for_ai)} 字符")
        print(f"   前200字符: {description_for_ai[:200]}")
        print()
        
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

⚠️ 特别注意（非常重要！）：

1. **description 字段绝对不能包含以下内容**：
   - ❌ "这是一个" 开头后就列表
   - ❌ PyPI 包名、NPM 包名
   - ❌ 版本号、版本信息
   - ❌ 传输协议（stdio、http等）
   - ❌ 安装命令、运行命令
   - ❌ 项目路径、GitHub 链接
   - ❌ 列表格式的元信息

2. **description 字段必须：**
   - ✅ 直接描述功能："这是一个用于...的 MCP Server"
   - ✅ 说明用途和应用场景
   - ✅ 列出可用工具及功能
   - ✅ 使用完整的句子，不要列表

3. **示例对比**：

【✅ 正确示例 - 职场搜索（无段落标题）】：
"这是一个用于**职场搜索**的 MCP Server，提供全球工作机会的精准检索功能。该服务集成了多个主流招聘平台的数据，支持按地点、职位类型、薪资范围等条件进行高级筛选。

用户可以通过设置查询条件，如工作类型、地点、语言等，快速找到符合需求的职位信息。这一服务适用于**职业规划**、**招聘管理**以及企业用工需求分析，为用户提供高效的职场信息获取方式。系统支持实时更新和智能推荐，确保信息的时效性和准确性。

**可用工具：**
1. **job_search** - 搜索全球范围内的工作机会，支持高级过滤条件和分页功能
2. **search_companies** - 查询企业信息和招聘状态
3. **get_job_details** - 获取职位详细信息包括薪资福利
4. **save_job** - 收藏感兴趣的职位方便后续查看
5. **get_salary_info** - 查询特定职位的薪资范围和市场行情"

【❌ 错误示例】（绝对不要这样写）：
"这是一个

- **PyPI 包名**: bach-youtube
- **版本**: 1.0.0
- **传输协议**: stdio"

请生成以下 JSON 格式的内容（包含简体中文、繁体中文、英文三个版本）：

{{
  "name_cn": "MCP Server 的中文简体名称（简短、吸引人）",
  "name_tw": "MCP Server 的中文繁體名稱（請使用正確的繁體字）",
  "name_en": "English name of the MCP Server (concise and attractive)",
  "summary_cn": "⭐ 简洁介绍（非常重要！）：必须是一句话（20-50字），直接描述核心功能，例如：'提供实时职位搜索和企业信息查询的智能招聘助手' 或 '一站式社交媒体内容管理和分析工具'。禁止使用冗长描述！",
  "summary_tw": "⭐ 簡潔介紹：必須是一句話（20-50字），直接描述核心功能，使用正確繁體字",
  "summary_en": "⭐ Concise summary: Must be ONE sentence (20-50 words), directly describing core functionality",
  "description_cn": "完整的功能描述（简体中文，200-400字，使用 Markdown 格式）。\n\n格式要求（使用 Markdown，不要显示段落标题）：\n\n第1段（2-3句话）：\n这是一个用于[功能]的 MCP Server，提供[核心服务]。详细说明功能特点、适用场景、解决的问题。\n\n第2段（3-5句话）：\n详细描述主要功能和特性。说明使用场景和应用价值。突出优势和亮点。\n\n第3段 - 工具列表：\n**可用工具：**\n1. **工具名1** - 功能说明\n2. **工具名2** - 功能说明\n3. **工具名3** - 功能说明\n（列出所有工具，每个工具独占一行，使用有序列表）\n\n⚠️ 重要：不要在输出中包含「第一段」「第二段」「第三段」「功能概述」「详细功能」等段落标题！\n⚠️ Markdown 格式要求：\n- 段落之间用空行分隔\n- 重要内容用 **加粗**\n- 工具列表前加 **可用工具：** 标题\n- 工具列表使用有序列表（1. 2. 3.），工具名用 **加粗**\n- 整体排版清晰美观\n\n⚠️ 绝对禁止：包名、版本号、传输协议、安装命令等技术元信息",
  "description_tw": "完整的功能描述（繁體中文，200-400字，使用 Markdown 格式）。\n\n格式要求（使用 Markdown，不要顯示段落標題）：\n\n第1段（2-3句話）：\n這是一個用於[功能]的 MCP Server，提供[核心服務]。詳細說明功能特點、適用場景、解決的問題。\n\n第2段（3-5句話）：\n詳細描述主要功能和特性。說明使用場景和應用價值。突出優勢和亮點。\n\n第3段 - 工具列表：\n**可用工具：**\n1. **工具名1** - 功能說明\n2. **工具名2** - 功能說明\n3. **工具名3** - 功能說明\n（列出所有工具，每個工具獨占一行，使用有序列表）\n\n⚠️ 重要：不要在輸出中包含「第一段」「第二段」「第三段」「功能概述」「詳細功能」等段落標題！\n⚠️ Markdown 格式要求：\n- 段落之間用空行分隔\n- 重要內容用 **加粗**\n- 工具列表前加 **可用工具：** 標題\n- 工具列表使用有序列表（1. 2. 3.），工具名用 **加粗**\n- 整體排版清晰美觀\n\n⚠️ 絕對禁止：包名、版本號、傳輸協議、安裝命令等技術元信息\n⚠️ 請使用正確的繁體字",
  "description_en": "Complete functional description (English, 200-400 words, use Markdown format).\n\nFormat (use Markdown, NO section titles):\n\nParagraph 1 (2-3 sentences):\nThis is an MCP Server for [function], providing [core services]. Explain features, use cases, and problems it solves.\n\nParagraph 2 (3-5 sentences):\nDescribe main functionalities and characteristics. Explain usage scenarios and application value. Highlight advantages and key features.\n\nParagraph 3 - Tool list:\n**Available Tools:**\n1. **tool_name1** - description\n2. **tool_name2** - description\n3. **tool_name3** - description\n(List ALL tools, one per line, use ordered list)\n\n⚠️ IMPORTANT: Do NOT include section titles like \"Paragraph 1\", \"Overview\", \"Detailed Features\" in your output!\n⚠️ Markdown requirements:\n- Separate paragraphs with blank lines\n- Use **bold** for important content\n- Add **Available Tools:** title before tool list\n- Tool list using ordered list (1. 2. 3.), tool names in **bold**\n- Clean and beautiful layout\n\n⚠️ Strictly prohibited: package name, version, protocol, commands, etc.",
  "route_prefix": "建议的路由前缀（仅小写字母和数字，不能以数字开头，不超过10字符，如 filesearch）",
  "category_id": "⭐ 根据 README 内容选择最合适的分类 ID（非常重要！必须从上面分类列表中选择，认真分析 README 的功能描述来匹配最合适的分类）"
}}

**重要要求**：
1. 名称、简介、描述都要提供简体、繁体、英文三个版本
2. ⭐ **summary（简洁介绍）格式要求（非常重要！）**：
   - **必须只有一句话，20-50字**
   - **直接描述核心功能和用途**
   - ✅ 正确示例：
     * "提供实时职位搜索和企业信息查询的智能招聘助手"
     * "一站式社交媒体内容管理和分析工具"
     * "支持多平台数据抓取的电商价格监控服务"
   - ❌ 错误示例：
     * "这是一个用于..." (太冗长)
     * 包含包名、版本号等技术信息
     * 超过50字的长描述
3. ⭐ **category_id 分类选择规则（非常重要！）**：
   - **必须根据 README 的功能描述来选择最合适的分类**
   - **认真分析 README 中描述的主要用途、工具功能**
   - **从上面提供的分类列表中选择最匹配的 ID**
4. 繁体中文必须使用正确的繁体字，例如：
   - 数据 → 數據
   - 服务器 → 伺服器
   - 文件 → 檔案
   - 网络 → 網絡
   - 检索 → 檢索
   - 内容 → 內容
5. **特殊翻译规则**：
   - bachai → 巴赫 (不是巴凯)
   - bachstudio → 巴赫工作室
   - BACH → 巴赫
   例如：bachai-data-analysis-mcp → 巴赫数据分析服务器
6. **description（描述）格式要求（使用 Markdown）**：
   - 内容丰富详实，200-400字
   - **必须使用 Markdown 格式，增强可读性**
   - **必须严格按照三段式结构**：
     * 第一段（功能概述）：2-3句话介绍核心服务，重点词汇用 **加粗**
     * 第二段（详细功能）：3-5句话详细说明功能特点，重点内容用 **加粗**
     * 第三段（工具列表）：必须使用 Markdown 列表格式
   - ⚠️ Markdown 格式规范：
     * 段落之间用空行分隔（双换行）
     * 重要关键词用 **加粗**
     * 工具列表格式：**可用工具：** 后换行，每个工具用 - **工具名** - 功能说明
   - ⚠️ 工具列表要求：
     * 必须包含 README 中的所有工具，不要遗漏
     * 每个工具独占一行，格式统一
   - ⚠️ 禁止包含：安装步骤、运行命令、配置方法、环境要求、包名、版本号、传输协议等
7. route_prefix 规则：
   - 只能包含小写字母(a-z)和数字(0-9)
   - 不能以数字开头
   - 不超过10个字符
   - 不要使用横杠或下划线
   - 示例：filesearch, dataanaly, webparser
8. 所有文本要专业、流畅、吸引人
9. 必须返回有效的 JSON 格式
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
        
        # 获取或生成 Logo (使用即梦 API)
        print(f"\n🖼️ 开始生成 Logo...")
        print(f"   即梦 API 状态: {'已初始化' if self.jimeng_api else '未初始化'}")
        
        logo_url = self.logo_generator.get_or_generate_logo(
            package_info,
            package_type,
            generate_with_ai=self.enable_logo_generation,
            use_jimeng=True  # ✅ 启用即梦MCP生成Logo
        )
        
        print(f"✅ Logo URL: {logo_url}")
        
        # ⭐ 生成备用描述（如果 AI 生成的描述为空或格式错误）
        desc_cn = ai_result.get('description_cn', '')
        desc_tw = ai_result.get('description_tw', '')
        desc_en = ai_result.get('description_en', '')
        
        # ⭐ 清理段落标题（防止 AI 输出段落标题）
        import re
        unwanted_titles = [
            r'\*\*第[一二三1-3]段.*?\*\*[：:：\s]*',  # **第一段 - 功能概述**：
            r'第[一二三1-3]段.*?[：:：\s]*',  # 第一段：
            r'\*\*功能概述\*\*[：:：\s]*',
            r'\*\*详细功能\*\*[：:：\s]*',
            r'\*\*詳細功能\*\*[：:：\s]*',
            r'\*\*Overview\*\*[：:：\s]*',
            r'\*\*Detailed Features\*\*[：:：\s]*',
        ]
        
        for pattern in unwanted_titles:
            desc_cn = re.sub(pattern, '', desc_cn, flags=re.IGNORECASE)
            desc_tw = re.sub(pattern, '', desc_tw, flags=re.IGNORECASE)
            desc_en = re.sub(pattern, '', desc_en, flags=re.IGNORECASE)
        
        # 清理多余的空行
        desc_cn = re.sub(r'\n{3,}', '\n\n', desc_cn).strip()
        desc_tw = re.sub(r'\n{3,}', '\n\n', desc_tw).strip()
        desc_en = re.sub(r'\n{3,}', '\n\n', desc_en).strip()
        
        if not desc_cn or len(desc_cn) < 50:
            print(f"⚠️ 使用备用描述方案")
            # 从包名提取功能关键词
            clean_name = package_name.replace('bach-', '').replace('bachai-', '').replace('_', ' ').replace('-', ' ')
            desc_cn = f"这是一个用于 {clean_name} 的 MCP Server，提供相关的功能和服务接口。\n\n可用工具：请查看项目文档了解具体工具列表。"
            desc_tw = f"這是一個用於 {clean_name} 的 MCP Server，提供相關的功能和服務接口。\n\n可用工具：請查看項目文檔了解具體工具列表。"
            desc_en = f"This is an MCP Server for {clean_name}, providing related functionality and service interfaces.\n\nAvailable Tools: Please refer to the project documentation for the specific tool list."
        
        return {
            # 名称字段
            'name': ai_result.get('name_cn', ai_result.get('name', package_name)),
            'name_zh_cn': ai_result.get('name_cn', ai_result.get('name', package_name)),
            'name_zh_tw': ai_result.get('name_tw', ai_result.get('name_cn', package_name)),
            'name_en': ai_result.get('name_en', package_name),
            # 摘要字段（简短）
            'summary': ai_result.get('summary_cn', ai_result.get('summary', '')),
            'summary_zh_cn': ai_result.get('summary_cn', ai_result.get('summary', '')),
            'summary_zh_tw': ai_result.get('summary_tw', ai_result.get('summary_cn', '')),
            'summary_en': ai_result.get('summary_en', ''),
            # 描述字段（详细） - 使用验证后的描述
            'description': desc_cn,
            'description_zh_cn': desc_cn,
            'description_zh_tw': desc_tw,
            'description_en': desc_en,
            # 其他字段
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
            # 名称字段
            'name': name,
            'name_zh_cn': name,
            'name_zh_tw': name,  # 简单转换，不如LLM准确
            'name_en': package_name.replace('-', ' ').replace('_', ' ').title(),
            # 摘要字段（简短）
            'summary': summary,
            'summary_zh_cn': summary,
            'summary_zh_tw': summary,  # 简单转换
            'summary_en': info.get('summary', summary),  # 使用包的原始英文简介
            # 描述字段（详细）
            'description': description,
            'description_zh_cn': description,
            'description_zh_tw': description,  # 简单转换
            'description_en': info.get('description', description)[:1000],  # 使用包的原始英文描述
            # 其他字段
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


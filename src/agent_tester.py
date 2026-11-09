"""
Agent 平台测试器
自动创建 Agent、绑定 MCP、测试对话，最后关闭 EMCP 模板
"""

import requests
import json
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime

try:
    from src.signalr_chat_tester import SignalRChatTester
    SIGNALR_AVAILABLE = True
except ImportError:
    SIGNALR_AVAILABLE = False


class AgentTesterLogger:
    """Agent 测试日志记录器"""
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


class AgentPlatformClient:
    """Agent 平台客户端"""
    
    def __init__(self, base_url: str = "https://v5.kaleido.guru"):
        self.base_url = base_url
        self.session_key = None
        self.user_info = None
    
    def login(self, phone: str, validation_code: str, max_retries: int = 3) -> Dict:
        """
        登录 Agent 平台（带重试机制）
        
        Args:
            phone: 手机号
            validation_code: 验证码（格式 MMyyyydd，如 11202507）
            max_retries: 最大重试次数（默认3次）
        
        Returns:
            用户信息
        """
        import time
        
        url = f"{self.base_url}/api/authentication/verfiy_sms_validation_code_login?guest=true"
        
        payload = {
            "prefix": "+86",
            "guest": True,
            "phone": phone,
            "validation_code": validation_code
        }
        
        # 完整的请求头（参考浏览器请求）
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'Language': 'ch_cn',  # 重要：语言设置
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        AgentTesterLogger.log(f"   📤 POST {url}")
        AgentTesterLogger.log(f"   📱 手机号: {phone}")
        AgentTesterLogger.log(f"   🔑 验证码: {validation_code}")
        
        # ⭐ 打印等效的 curl 命令
        AgentTesterLogger.log(f"\n   🔧 等效 curl 命令:")
        import json
        curl_cmd = f"""curl -X POST '{url}' \\
  -H 'Accept: application/json, text/plain, */*' \\
  -H 'Content-Type: application/json;charset=UTF-8' \\
  -H 'Language: ch_cn' \\
  -H 'Cache-Control: no-cache' \\
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \\
  -d '{json.dumps(payload)}'"""
        AgentTesterLogger.log(f"{curl_cmd}\n")
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
                
                # 处理 502 Bad Gateway
                if response.status_code == 502:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3  # 递增等待时间：3秒、6秒、9秒
                        AgentTesterLogger.log(f"   ⚠️ 502 Bad Gateway，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        AgentTesterLogger.log(f"   ❌ 登录失败: {response.text}")
                        return None
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # ⭐ 打印完整响应以便调试
                    AgentTesterLogger.log(f"   📋 完整响应:")
                    AgentTesterLogger.log(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    # ⭐ 检查响应结构
                    if data.get('err_code') == 0:
                        # 标准格式：body 里面包含数据
                        body = data.get('body', {})
                        self.session_key = body.get('session_key')
                        self.user_info = body
                    else:
                        # 尝试直接获取
                        self.session_key = data.get('session_key')
                        self.user_info = data
                    
                    if self.session_key:
                        AgentTesterLogger.log(f"   ✅ 登录成功")
                        AgentTesterLogger.log(f"   👤 用户: {self.user_info.get('user_name', 'N/A')}")
                        AgentTesterLogger.log(f"   🆔 UID: {self.user_info.get('uid')}")
                        AgentTesterLogger.log(f"   🔑 Token: {self.session_key[:20]}...")
                        
                        return self.user_info
                    else:
                        AgentTesterLogger.log(f"   ❌ 响应中没有 session_key")
                        AgentTesterLogger.log(f"   💡 可能是验证码错误或账号问题")
                        return None
                else:
                    AgentTesterLogger.log(f"   ❌ 登录失败: {response.text}")
                    return None
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    AgentTesterLogger.log(f"   ⚠️ 请求超时，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    AgentTesterLogger.log(f"   ❌ 登录超时")
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    AgentTesterLogger.log(f"   ⚠️ 登录异常: {e}，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    AgentTesterLogger.log(f"   ❌ 登录异常: {e}")
                    return None
        
        return None
    
    def _get_headers(self) -> Dict:
        """获取请求 headers"""
        return {
            'Token': self.session_key,
            'Content-Type': 'application/json;charset=UTF-8'
        }
    
    def create_agent(
        self,
        name: str,
        description: str,
        logo: str = "",
        category_id: int = 261
    ) -> Optional[Dict]:
        """
        创建 Agent
        
        Args:
            name: Agent 名称
            description: Agent 描述
            logo: Logo URL
            category_id: 分类 ID
        
        Returns:
            创建结果
        """
        url = f"{self.base_url}/api/superAgent/create"
        
        payload = {
            "name": name,
            "logo": logo,
            "description": description,
            "super_agent_category_id": category_id,
            "manage_lable_ids": None,
            "editor_uids": []
        }
        
        AgentTesterLogger.log(f"   📤 POST {url}")
        AgentTesterLogger.log(f"   📝 名称: {name}")
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                body = data.get('body', {})
                agent_id = body.get('super_agent_setting_id')
                
                AgentTesterLogger.log(f"   ✅ Agent 已创建")
                AgentTesterLogger.log(f"   🆔 Agent ID: {agent_id}")
                
                return body
            else:
                AgentTesterLogger.log(f"   ❌ 创建失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 创建异常: {e}")
            return None
    
    def query_plugins(self, mcp_name: str = None) -> Optional[List[Dict]]:
        """
        查询插件列表
        
        Args:
            mcp_name: MCP 名称（用于查找）
        
        Returns:
            插件列表
        """
        url = f"{self.base_url}/api/plugin/query_plugin"
        
        payload = {
            "current_page": 1,
            "isPublish": True,
            "page_size": 9999,
            "category_id": None,
            "is_mcp_query": True
        }
        
        AgentTesterLogger.log(f"   📤 POST {url}")
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                plugins = data.get('body', [])
                AgentTesterLogger.log(f"   ✅ 找到 {len(plugins)} 个 MCP 插件")
                
                # 如果指定了 MCP 名称，查找匹配的
                if mcp_name:
                    matched = [p for p in plugins if mcp_name.lower() in p.get('name_for_model', '').lower()]
                    
                    if matched:
                        AgentTesterLogger.log(f"   ✅ 找到匹配的 MCP: {matched[0].get('name_for_model')}")
                        AgentTesterLogger.log(f"      ID: {matched[0].get('id')}")
                        AgentTesterLogger.log(f"      UUID: {matched[0].get('uuid')}")
                        return matched
                    else:
                        AgentTesterLogger.log(f"   ⚠️ 未找到匹配的 MCP: {mcp_name}")
                        AgentTesterLogger.log(f"      提示: 请确认 MCP 已发布到 EMCP 平台")
                        return []
                
                return plugins
            else:
                AgentTesterLogger.log(f"   ❌ 查询失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 查询异常: {e}")
            return None
    
    def update_agent(
        self,
        agent_id: int,
        name: str,
        description: str,
        plugin_ids: List[int],
        logo: str = "",
        system_message: str = "你是一个AI助手",
        category_id: int = 261
    ) -> bool:
        """
        更新 Agent（绑定 MCP 插件）
        
        Args:
            agent_id: Agent ID
            name: Agent 名称
            description: Agent 描述
            plugin_ids: 插件 ID 列表
            logo: Logo URL
            system_message: 系统消息
            category_id: 分类 ID
        
        Returns:
            是否成功
        """
        url = f"{self.base_url}/api/superAgent/update"
        
        payload = {
            "super_agent_setting_id": str(agent_id),
            "name": name,
            "logo": logo,
            "manage_lable_ids": [],
            "description": description,
            "super_agent_category_id": category_id,
            "user_tag_list": [],
            "system_message": system_message,
            "welcome_message": "",
            "plugin_ids": plugin_ids,  # ⭐ 绑定 MCP 插件
            "flow_ids": [],
            "knowledge_bases": [],
            "is_allow_upload_temp_document": None,
            "is_allow_attach_private_knowledge_base": None,
            "is_select_knowledge_must_chat_doc": 0,
            "pre_questions": [],
            "enable_follow_up_questions": None,
            "llm_request": [
                {
                    "type": 1,
                    "llm_model_name": "deepseek-chat",
                    "llm_provider": 6,
                    "llm_setting_name": "72e5c503-2c17-4167-863f-5b9e6b220332"
                },
                {
                    "type": 2,
                    "llm_model_name": "deepseek-chat",
                    "llm_provider": 6,
                    "llm_setting_name": "72e5c503-2c17-4167-863f-5b9e6b220332"
                }
            ],
            "vrm_ids": [],
            "enable_vrm": False,
            "use_fallback_ai": None,
            "send_history": None,
            "update_super_agent_knowledge_ck": {
                "similarity": 0,
                "limit": 0,
                "is_valid": False
            },
            "editor_uids": []
        }
        
        AgentTesterLogger.log(f"   📤 POST {url}")
        AgentTesterLogger.log(f"   🔗 绑定插件: {plugin_ids}")
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                AgentTesterLogger.log(f"   ✅ Agent 已更新")
                return True
            else:
                AgentTesterLogger.log(f"   ❌ 更新失败: {data.get('err_message')}")
                return False
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 更新异常: {e}")
            return False
    
    def get_workspaces(self) -> Optional[List[Dict]]:
        """
        获取工作区列表
        
        Returns:
            工作区列表
        """
        url = f"{self.base_url}/api/conversation/get_work_space_for_user"
        
        AgentTesterLogger.log(f"   📤 GET {url}")
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            data = response.json()
            
            AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                workspaces = data.get('body', [])
                AgentTesterLogger.log(f"   ✅ 找到 {len(workspaces)} 个工作区")
                
                return workspaces
            else:
                AgentTesterLogger.log(f"   ❌ 获取失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 请求异常: {e}")
            return None
    
    def create_or_get_workspace(self, workspace_name: str = "MCP 工厂") -> Optional[int]:
        """
        创建或获取工作区
        
        Args:
            workspace_name: 工作区名称
        
        Returns:
            工作区 ID
        """
        # 先查询是否已存在
        workspaces = self.get_workspaces()
        
        if workspaces:
            for ws in workspaces:
                if ws.get('name') == workspace_name:
                    ws_id = ws.get('id')
                    AgentTesterLogger.log(f"   ✅ 使用已有工作区: {workspace_name} (ID: {ws_id})")
                    return ws_id
        
        # 不存在，创建新的
        url = f"{self.base_url}/api/conversation/create_work_space"
        
        payload = {"name": workspace_name}
        
        AgentTesterLogger.log(f"   📤 POST {url}")
        AgentTesterLogger.log(f"   📝 创建工作区: {workspace_name}")
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            if data.get('err_code') == 0:
                ws_id = data.get('body', {}).get('id')
                AgentTesterLogger.log(f"   ✅ 工作区已创建, ID: {ws_id}")
                return ws_id
            else:
                AgentTesterLogger.log(f"   ❌ 创建失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 创建异常: {e}")
            return None
    
    def create_conversation(
        self,
        agent_id: int,
        workspace_id: int,
        conversation_name: str
    ) -> Optional[str]:
        """
        创建会话
        
        Args:
            agent_id: Agent ID
            workspace_id: 工作区 ID
            conversation_name: 会话名称
        
        Returns:
            会话 ID (conversation_id)
        """
        url = f"{self.base_url}/api/conversation/init?"
        
        payload = {
            "super_agent_setting_id": agent_id,
            "conversation_name": conversation_name,
            "work_space_id": workspace_id,
            "color": "#F67F00",
            "conversation_platform": 0,
            "type": 0
        }
        
        AgentTesterLogger.log(f"   📤 POST {url}")
        AgentTesterLogger.log(f"   📝 会话名称: {conversation_name}")
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                conv_id = data.get('body', {}).get('conversation_id')
                AgentTesterLogger.log(f"   ✅ 会话已创建")
                AgentTesterLogger.log(f"   🆔 会话ID: {conv_id}")
                
                return conv_id
            else:
                AgentTesterLogger.log(f"   ❌ 创建失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 创建异常: {e}")
            return None
    
    def get_agent_skills(self, agent_id: int, version: str = "v1.0.0") -> Optional[List[int]]:
        """
        获取 Agent 的技能（插件）列表
        
        Args:
            agent_id: Agent ID
            version: 版本号
        
        Returns:
            插件 ID 列表
        """
        url = f"{self.base_url}/api/superAgent/skill_detail"
        
        params = {
            "super_agent_setting_id": agent_id,
            "version": version
        }
        
        AgentTesterLogger.log(f"   📤 GET {url}")
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            data = response.json()
            
            AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            # ⭐ 从 body 中获取 plugins
            if data.get('err_code') == 0:
                body = data.get('body', {})
                plugins = body.get('plugins', [])
                
                if plugins:
                    plugin_ids = [p.get('id') for p in plugins]
                    
                    AgentTesterLogger.log(f"   ✅ 找到 {len(plugins)} 个插件")
                    for p in plugins:
                        AgentTesterLogger.log(f"      - {p.get('name_for_model')} (ID: {p.get('id')})")
                    
                    return plugin_ids
                else:
                    AgentTesterLogger.log(f"   ⚠️ plugins 列表为空")
                    return []
            else:
                AgentTesterLogger.log(f"   ❌ 响应错误: {data.get('err_message')}")
                return None
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 请求异常: {e}")
            return None
    
    def publish_agent(self, agent_id: int, description: str = "测试发布") -> Optional[Dict]:
        """
        发布 Agent
        
        Args:
            agent_id: Agent ID
            description: 发布描述
        
        Returns:
            发布结果
        """
        url = f"{self.base_url}/api/superAgent/publish/{agent_id}"
        
        payload = {
            "description": description,
            "upateAllAgentVersion": True
        }
        
        AgentTesterLogger.log(f"   📤 POST {url}")
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                body = data.get('body', {})
                publish_id = body.get('publish_id')
                
                AgentTesterLogger.log(f"   ✅ Agent 已发布")
                AgentTesterLogger.log(f"   🆔 发布ID: {publish_id}")
                AgentTesterLogger.log(f"   🔗 访问链接: {self.base_url}/chat?releaseId={publish_id}")
                
                return body
            else:
                AgentTesterLogger.log(f"   ❌ 发布失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 发布异常: {e}")
            return None


class AgentTester:
    """Agent + MCP 集成测试器"""
    
    def __init__(self, emcp_manager, ai_generator=None):
        """
        初始化 Agent 测试器
        
        Args:
            emcp_manager: EMCP 管理器
            ai_generator: AI 生成器（用于生成 Agent 描述）
        """
        self.emcp_manager = emcp_manager
        self.ai_generator = ai_generator
        self.agent_client = AgentPlatformClient()
    
    def test_agent_integration(
        self,
        template_id: str,
        mcp_name: str,
        mcp_description: str,
        phone: str = "17610785055"
    ) -> Dict:
        """
        完整的 Agent 集成测试流程
        
        Args:
            template_id: EMCP 模板 ID
            mcp_name: MCP 名称
            mcp_description: MCP 描述
            phone: Agent 平台登录手机号
        
        Returns:
            测试报告
        """
        AgentTesterLogger.log("\n" + "="*70)
        AgentTesterLogger.log("🤖 开始 Agent 平台集成测试")
        AgentTesterLogger.log("="*70)
        
        report = {
            "template_id": template_id,
            "mcp_name": mcp_name,
            "test_time": datetime.now().isoformat(),
            "steps": [],
            "success": False,
            "error": None
        }
        
        try:
            # 步骤 1: 登录 Agent 平台
            AgentTesterLogger.log("\n📋 步骤 1/7: 登录 Agent 平台...")
            
            # 生成验证码（格式 MMyyyydd = 月+年+日）
            validation_code = datetime.now().strftime("%m%Y%d")  # ⭐ 修正：只有一个 %d
            
            login_result = self.agent_client.login(phone, validation_code)
            report['steps'].append({"step": 1, "name": "登录Agent平台", "success": login_result is not None})
            
            if not login_result:
                raise Exception("登录 Agent 平台失败")
            
            AgentTesterLogger.log("   ✅ 登录成功")
            
            # 步骤 2: 创建 Agent
            AgentTesterLogger.log("\n📋 步骤 2/7: 创建测试 Agent...")
            
            # 使用 LLM 生成 Agent 名称和描述
            agent_name, agent_desc = self._generate_agent_info(mcp_name, mcp_description)
            
            agent_result = self.agent_client.create_agent(
                name=agent_name,
                description=agent_desc
            )
            
            report['steps'].append({"step": 2, "name": "创建Agent", "success": agent_result is not None})
            
            if not agent_result:
                raise Exception("创建 Agent 失败")
            
            agent_id = agent_result.get('super_agent_setting_id')
            report['agent_id'] = agent_id
            
            AgentTesterLogger.log(f"   ✅ Agent 已创建")
            AgentTesterLogger.log(f"   🆔 Agent ID: {agent_id}")
            
            # 步骤 3: 查询插件列表，检查 MCP 是否存在
            AgentTesterLogger.log("\n📋 步骤 3/7: 查询 MCP 插件...")
            
            plugins = self.agent_client.query_plugins(mcp_name)
            report['steps'].append({"step": 3, "name": "查询MCP插件", "success": plugins is not None and len(plugins) > 0})
            
            if not plugins or len(plugins) == 0:
                raise Exception(f"未找到 MCP 插件: {mcp_name}\n\n请确认 MCP 已成功发布到 EMCP 平台！")
            
            mcp_plugin = plugins[0]
            mcp_plugin_id = mcp_plugin.get('id')
            
            AgentTesterLogger.log(f"   ✅ 找到 MCP 插件")
            AgentTesterLogger.log(f"   🆔 插件 ID: {mcp_plugin_id}")
            report['mcp_plugin_id'] = mcp_plugin_id
            
            # 步骤 4: 更新 Agent，绑定 MCP
            AgentTesterLogger.log("\n📋 步骤 4/7: 绑定 MCP 到 Agent...")
            
            update_result = self.agent_client.update_agent(
                agent_id=agent_id,
                name=agent_name,
                description=agent_desc,
                plugin_ids=[mcp_plugin_id]  # ⭐ 绑定 MCP
            )
            
            report['steps'].append({"step": 4, "name": "绑定MCP", "success": update_result})
            
            if not update_result:
                raise Exception("绑定 MCP 失败")
            
            AgentTesterLogger.log(f"   ✅ MCP 已绑定到 Agent")
            
            # 步骤 5: 发布 Agent
            AgentTesterLogger.log("\n📋 步骤 5/7: 发布 Agent...")
            
            publish_result = self.agent_client.publish_agent(
                agent_id=agent_id,
                description="自动化测试发布"
            )
            
            report['steps'].append({"step": 5, "name": "发布Agent", "success": publish_result is not None})
            
            if not publish_result:
                raise Exception("发布 Agent 失败")
            
            publish_id = publish_result.get('publish_id')
            report['publish_id'] = publish_id
            report['agent_url'] = f"{self.agent_client.base_url}/chat?releaseId={publish_id}"
            
            AgentTesterLogger.log(f"   ✅ Agent 已发布")
            AgentTesterLogger.log(f"   🔗 访问链接: {report['agent_url']}")
            
            # 步骤 6: 完成（不需要对话测试和关闭模板）
            AgentTesterLogger.log("\n   ✅ Agent 集成已完成")
            
            # 测试完成
            report['success'] = True
            
            AgentTesterLogger.log("\n" + "="*70)
            AgentTesterLogger.log("✅ Agent 集成测试完成！")
            AgentTesterLogger.log("="*70)
            AgentTesterLogger.log(f"\n🔗 Agent 访问链接: {report['agent_url']}")
            AgentTesterLogger.log(f"💡 请访问链接测试 Agent 是否能正常使用 MCP 工具")
            
            return report
            
        except Exception as e:
            report['error'] = str(e)
            AgentTesterLogger.log(f"\n❌ 测试失败: {e}")
            return report
    
    def _generate_agent_info(self, mcp_name: str, mcp_description: str) -> tuple:
        """
        使用 LLM 生成 Agent 名称和描述
        
        Args:
            mcp_name: MCP 名称
            mcp_description: MCP 描述
        
        Returns:
            (agent_name, agent_description)
        """
        # 生成名称（MCP名称+测试）
        agent_name = f"{mcp_name} 测试"
        
        # 生成描述
        if self.ai_generator and hasattr(self.ai_generator, 'client'):
            try:
                AgentTesterLogger.log(f"   🤖 使用 LLM 生成 Agent 描述...")
                
                prompt = f"""
基于以下 MCP 服务信息，生成一个简洁专业的 Agent 描述（50-100字）：

MCP 名称：{mcp_name}
MCP 描述：{mcp_description}

要求：
1. 说明这是一个集成了该 MCP 的 AI Agent
2. 突出 MCP 的核心功能
3. 语言简洁专业
4. 50-100字

直接返回描述，不要其他内容。
"""
                
                response = self.ai_generator.client.chat.completions.create(
                    model=self.ai_generator.deployment_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                agent_desc = response.choices[0].message.content.strip()
                AgentTesterLogger.log(f"   ✅ LLM 生成描述: {agent_desc[:50]}...")
                
                return agent_name, agent_desc
                
            except Exception as e:
                AgentTesterLogger.log(f"   ⚠️ LLM 生成失败: {e}")
        
        # 降级方案
        agent_desc = f"集成了 {mcp_name} MCP 服务的 AI Agent。{mcp_description[:80]}"
        AgentTesterLogger.log(f"   ℹ️ 使用默认描述")
        
        return agent_name, agent_desc
    
    def _close_emcp_template(self, template_id: str) -> bool:
        """
        关闭 EMCP 模板（改为状态1）
        
        Args:
            template_id: 模板 ID
        
        Returns:
            是否成功
        """
        url = f"{self.emcp_manager.base_url}/api/Template/publish_mcp_template/{template_id}/1"
        
        headers = {
            'token': self.emcp_manager.session_key,
            'language': 'ch_cn'
        }
        
        AgentTesterLogger.log(f"   📤 PUT {url}")
        AgentTesterLogger.log(f"   📝 修改为: 关闭状态(1)")
        
        try:
            response = requests.put(url, headers=headers, timeout=30)
            data = response.json()
            
            AgentTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                return True
            else:
                AgentTesterLogger.log(f"   ❌ 错误: {data.get('err_message')}")
                return False
                
        except Exception as e:
            AgentTesterLogger.log(f"   ❌ 请求失败: {e}")
            return False


# 便捷函数
def test_agent_with_mcp(
    emcp_manager,
    template_id: str,
    mcp_name: str,
    mcp_description: str,
    ai_generator=None,
    phone: str = "17610785055"
) -> Dict:
    """
    测试 Agent + MCP 集成
    
    Args:
        emcp_manager: EMCP 管理器
        template_id: EMCP 模板 ID
        mcp_name: MCP 名称
        mcp_description: MCP 描述
        ai_generator: AI 生成器
        phone: Agent 平台手机号
    
    Returns:
        测试报告
    """
    tester = AgentTester(emcp_manager, ai_generator)
    report = tester.test_agent_integration(template_id, mcp_name, mcp_description, phone)
    
    return report


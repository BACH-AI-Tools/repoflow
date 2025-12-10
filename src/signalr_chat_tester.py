"""
SignalR 对话测试器
使用 SignalR 实现自动化 Agent 对话测试
"""

import json
import time
import uuid
from datetime import datetime
from signalrcore.hub_connection_builder import HubConnectionBuilder
from typing import Dict, Optional


class SignalRChatTester:
    """SignalR 对话测试器"""
    
    def __init__(self, base_url: str = "https://v5.kaleido.guru"):
        self.base_url = base_url
        self.hub_url = f"{base_url}/hubs/superagent"
        self.connection = None
        self.connection_token = None
        self.received_messages = []
        self.is_complete = False
        self.log_func = None
    
    def set_log_function(self, log_func):
        """设置日志函数"""
        self.log_func = log_func
    
    def log(self, message):
        """记录日志"""
        if self.log_func:
            self.log_func(message)
        else:
            print(message)
    
    def test_conversation_with_tools(
        self,
        agent_token: str,
        conversation_id: str,
        agent_id: int,
        mcp_name: str,
        template_id: str,
        plugin_ids: list,
        emcp_base_url: str,
        emcp_token: str,
        emcp_manager=None,
        ai_generator=None
    ) -> Dict:
        """
        测试 Agent 对话 - 测试所有 MCP 工具
        
        Args:
            agent_token: Agent 平台 token
            conversation_id: 会话 ID
            agent_id: Agent ID
            mcp_name: MCP 名称
            template_id: EMCP 模板 ID（用于获取工具列表）⭐
            plugin_ids: 插件 ID 列表
            emcp_base_url: EMCP 平台地址 ⭐
            emcp_token: EMCP token ⭐
            ai_generator: AI 生成器（用于生成测试问题）
        
        Returns:
            测试结果
        """
        self.log("\n" + "="*70)
        self.log("💬 开始 SignalR 对话测试 - 测试所有工具")
        self.log("="*70)
        
        result = {
            "success": False,
            "conversation_id": conversation_id,
            "tools_tested": [],
            "total_tools": 0,
            "passed_tools": 0,
            "failed_tools": 0,
            "error": None
        }
        
        try:
            # 步骤 0: 从 EMCP 获取 MCP 工具列表 ⭐
            self.log("\n📋 步骤 0: 从 EMCP 获取 MCP 工具列表...")
            self.log(f"   📋 模板ID: {template_id}")
            
            tools = self._get_mcp_tools_from_emcp(
                template_id,
                emcp_base_url,
                emcp_token,
                emcp_manager  # ⭐ 传递 emcp_manager 用于401重登录
            )
            
            if not tools:
                raise Exception("无法从 EMCP 获取 MCP 工具列表")
            
            result['total_tools'] = len(tools)
            self.log(f"   ✅ 找到 {len(tools)} 个工具")
            for i, tool in enumerate(tools, 1):
                display_name = tool.get('display_name') or tool.get('name')
                self.log(f"      {i}. {display_name}")
            
            # 步骤 1: 建立 SignalR 连接
            self.log("\n📋 步骤 1: 建立 SignalR 连接...")
            
            if not self._connect_signalr():
                raise Exception("SignalR 连接失败")
            
            self.log("   ✅ SignalR 连接已建立")
            time.sleep(1)
            
            # 步骤 2: 连接到 Agent
            self.log("\n📋 步骤 2: 连接到 Agent...")
            
            if not self._connect_to_agent(agent_token, conversation_id):
                raise Exception("连接到 Agent 失败")
            
            self.log(f"   ✅ 已连接到 Agent")
            
            # 步骤 3: 测试每个工具
            self.log("\n📋 步骤 3: 逐个测试 MCP 工具...")
            self.log("="*70)
            
            for i, tool in enumerate(tools, 1):
                tool_name = tool.get('name')  # API 名称
                display_name = tool.get('display_name') or tool_name  # 显示名称
                tool_desc = tool.get('description', '')
                
                self.log(f"\n🔧 测试 {i}/{len(tools)}: {display_name}")
                self.log(f"   API: {tool_name}")
                self.log(f"   描述: {tool_desc[:60]}...")
                
                # 生成测试问题
                test_question = self._generate_tool_test_question(
                    mcp_name,
                    tool,
                    ai_generator,
                    is_first=(i == 1)
                )
                
                self.log(f"   📝 测试问题: {test_question}")
                
                # 发送消息并等待响应
                test_result = self._send_and_receive(
                    conversation_id,
                    test_question,
                    plugin_ids,
                    tool_name  # ⭐ 期望的工具名称（API名称）
                )
                
                if test_result['success']:
                    self.log(f"   ✅ 测试通过")
                    result['passed_tools'] += 1
                else:
                    self.log(f"   ❌ 测试失败: {test_result.get('error', '未知')}")
                    result['failed_tools'] += 1
                
                result['tools_tested'].append({
                    "tool_name": tool_name,
                    "display_name": display_name,  # ⭐ 添加显示名称
                    "test_question": test_question,
                    "success": test_result['success'],
                    "response": test_result.get('response', ''),
                    "skills_used": test_result.get('skills_used', []),
                    "function_calls": test_result.get('function_calls', []),  # ⭐ 函数调用列表
                    "error": test_result.get('error')
                })
                
                # 等待一下，避免消息太快
                time.sleep(2)
            
            # 关闭连接
            if self.connection:
                self.connection.stop()
            
            # 计算成功率
            if result['total_tools'] > 0:
                success_rate = (result['passed_tools'] / result['total_tools']) * 100
                result['success_rate'] = success_rate
                result['success'] = success_rate >= 80  # 80%以上算成功
            
            self.log("\n" + "="*70)
            self.log("📊 测试统计")
            self.log("="*70)
            self.log(f"   总工具数: {result['total_tools']}")
            self.log(f"   ✅ 通过: {result['passed_tools']}")
            self.log(f"   ❌ 失败: {result['failed_tools']}")
            self.log(f"   📊 成功率: {success_rate:.1f}%")
            
            self.log("\n" + "="*70)
            self.log("✅ SignalR 对话测试完成！")
            self.log("="*70)
            
            # ⭐ 自动生成 HTML 测试报告
            if result['total_tools'] > 0:
                self.log("\n📄 生成测试报告...")
                
                report_file = f"agent_chat_test_{conversation_id[:8]}.html"
                self.generate_chat_test_report(result, report_file)
                
                result['report_file'] = report_file
            
            return result
            
        except Exception as e:
            self.log(f"\n❌ SignalR 测试异常: {e}")
            result['error'] = str(e)
            
            if self.connection:
                try:
                    self.connection.stop()
                except:
                    pass
            
            return result
    
    def test_conversation(
        self,
        agent_token: str,
        conversation_id: str,
        agent_id: int,
        mcp_name: str,
        plugin_ids: list,
        test_question: str = None
    ) -> Dict:
        """
        测试 Agent 对话
        
        Args:
            agent_token: Agent 平台 token
            conversation_id: 会话 ID
            agent_id: Agent ID
            mcp_name: MCP 名称
            plugin_ids: 插件 ID 列表
            test_question: 测试问题（可选）
        
        Returns:
            测试结果
        """
        self.log("\n" + "="*70)
        self.log("💬 开始 SignalR 自动化对话测试")
        self.log("="*70)
        
        result = {
            "success": False,
            "conversation_id": conversation_id,
            "messages": [],
            "error": None
        }
        
        try:
            # 步骤 1: 建立 SignalR 连接
            self.log("\n📋 步骤 1/4: 建立 SignalR 连接...")
            self.log(f"   🔗 Hub URL: {self.hub_url}")
            
            self.connection = HubConnectionBuilder() \
                .with_url(self.hub_url) \
                .with_automatic_reconnect({
                    "type": "interval",
                    "intervals": [0, 2, 10, 30]
                }) \
                .build()
            
            # 注册接收消息的处理器
            self.connection.on("receive", self._handle_receive_message)
            
            # 启动连接
            self.connection.start()
            
            self.log("   ✅ SignalR 连接已建立")
            time.sleep(1)  # 等待连接稳定
            
            # 步骤 2: 连接到 Agent
            self.log("\n📋 步骤 2/4: 连接到 Agent...")
            self.log(f"   🆔 会话ID: {conversation_id}")
            
            # 发送 connect_single_agent
            self.connection.send(
                "connect_single_agent",
                [agent_token, conversation_id]
            )
            
            self.log("   📤 已发送连接请求")
            
            # 等待连接响应
            time.sleep(2)
            
            if not self.connection_token:
                # 从接收到的消息中提取
                for msg in self.received_messages:
                    if isinstance(msg, dict):
                        content = msg.get('Content')
                        if content and len(content) > 30:  # UUID 格式
                            self.connection_token = content
                            break
            
            if self.connection_token:
                self.log(f"   ✅ 已连接到 Agent")
                self.log(f"   🔑 连接Token: {self.connection_token[:20]}...")
            else:
                raise Exception("未获取到连接 Token")
            
            # 步骤 3: 发送测试消息
            self.log("\n📋 步骤 3/4: 发送测试消息...")
            
            # 生成测试问题
            if not test_question:
                test_question = f"@{mcp_name} 你有什么功能？请介绍一下你的工具。"
            
            self.log(f"   📝 测试问题: {test_question}")
            
            # 构建消息
            dialog_id = str(uuid.uuid4())
            
            message_data = {
                "ContentText": test_question,
                "DialogID": dialog_id,
                "ConversationID": conversation_id,
                "FromName": "自动化测试",
                "EnumInvodeType": 1,
                "SelectReferenceInfos": [],
                "SkillMode": 1,
                "ContentImages": None,
                "IsVisible": False,
                "FunctionName": "",
                "Arguments": "",
                "TaskNumber": None,
                "EnableCanvas": False,
                "SelectSkills": [str(plugin_ids[0])] if plugin_ids else [],  # 选中第一个插件
                "HistoryCount": 0
            }
            
            # 发送消息
            self.connection.send(
                "send_text_message",
                [message_data, self.connection_token]
            )
            
            self.log("   ✅ 测试消息已发送")
            
            # 步骤 4: 接收响应
            self.log("\n📋 步骤 4/4: 接收 Agent 响应...")
            self.log("   ⏳ 等待 Agent 处理...")
            
            # 等待响应完成
            max_wait = 60  # 最多等待60秒
            start_time = time.time()
            
            while not self.is_complete and (time.time() - start_time) < max_wait:
                time.sleep(0.5)
            
            if self.is_complete:
                self.log("\n   ✅ Agent 响应完成")
                
                # 提取完整回答
                full_content = ""
                for msg in self.received_messages:
                    if isinstance(msg, dict):
                        if msg.get('MessageType') == 'AgentPartialTextMessage':
                            content = msg.get('FullContent', '')
                            if content and len(content) > len(full_content):
                                full_content = content
                        elif msg.get('MessageType') == 'AgentTextMessage':
                            content = msg.get('Content', '')
                            if content:
                                full_content = content
                
                if full_content:
                    self.log("\n   📝 Agent 完整回答:")
                    self.log("   " + "="*66)
                    # 显示前500字符
                    display_content = full_content[:500]
                    if len(full_content) > 500:
                        display_content += "..."
                    
                    for line in display_content.split('\n'):
                        self.log(f"   {line}")
                    
                    self.log("   " + "="*66)
                    
                    # 检查是否调用了 MCP
                    skills_used = []
                    for msg in self.received_messages:
                        if isinstance(msg, dict):
                            skills = msg.get('Skills', [])
                            if skills:
                                for skill in skills:
                                    skill_name = skill.get('SkillName')
                                    if skill_name and skill_name not in skills_used:
                                        skills_used.append(skill_name)
                    
                    if skills_used:
                        self.log(f"\n   ✅ Agent 调用了 MCP 工具:")
                        for skill in skills_used:
                            self.log(f"      - {skill}")
                    else:
                        self.log(f"\n   ⚠️ Agent 未调用 MCP 工具")
                    
                    result['success'] = True
                    result['full_content'] = full_content
                    result['skills_used'] = skills_used
                    result['messages'] = self.received_messages
                else:
                    self.log("\n   ⚠️ 未获取到完整回答")
                    result['success'] = False
                    result['messages'] = self.received_messages
            else:
                self.log(f"\n   ⚠️ 等待超时（{max_wait}秒）")
                result['success'] = False
                result['error'] = "响应超时"
            
            # 关闭连接
            self.connection.stop()
            
            self.log("\n" + "="*70)
            if result['success']:
                self.log("✅ SignalR 对话测试完成！")
            else:
                self.log("⚠️ SignalR 对话测试未完全成功")
            self.log("="*70)
            
            return result
            
        except Exception as e:
            self.log(f"\n❌ SignalR 测试异常: {e}")
            result['error'] = str(e)
            
            if self.connection:
                try:
                    self.connection.stop()
                except:
                    pass
            
            return result
    
    def _get_mcp_tools_from_emcp(
        self,
        template_id: str,
        emcp_base_url: str,
        emcp_token: str,
        emcp_manager=None
    ) -> list:
        """
        从 EMCP 平台获取 MCP 工具列表（支持401自动重登录）
        
        流程：template_id → server_id → 工具列表
        
        Args:
            template_id: EMCP 模板 ID
            emcp_base_url: EMCP 平台地址
            emcp_token: EMCP token
            emcp_manager: EMCP 管理器（用于401重登录）
        
        Returns:
            工具列表
        """
        try:
            import requests
            
            # ⭐ 步骤 0.1: 先获取 server_id
            self.log(f"   📋 步骤 0.1: 获取 Server ID...")
            
            server_id_url = f"{emcp_base_url}/api/Service/get_mcp_main_server_id/{template_id}"
            
            headers = {
                'token': emcp_token,
                'language': 'ch_cn'
            }
            
            self.log(f"   📤 GET {server_id_url}")
            
            server_id_resp = requests.get(server_id_url, headers=headers, timeout=30)
            
            self.log(f"   📥 响应: {server_id_resp.status_code}")
            
            # 检查 401
            if server_id_resp.status_code == 401 and emcp_manager:
                self.log(f"   ⚠️ 收到 401 - EMCP Token 已过期")
                self.log(f"   🔄 重新登录 EMCP...")
                
                from config_manager import ConfigManager
                config_mgr = ConfigManager()
                creds = config_mgr.load_emcp_credentials()
                
                if creds and emcp_manager.login(creds['phone_number'], creds['validation_code']):
                    self.log(f"   ✅ 重新登录成功")
                    headers['token'] = emcp_manager.session_key
                    server_id_resp = requests.get(server_id_url, headers=headers, timeout=30)
                    self.log(f"   📥 响应: {server_id_resp.status_code}")
                else:
                    return None
            
            server_id_data = server_id_resp.json()
            
            if server_id_data.get('err_code') != 0:
                self.log(f"   ❌ 获取 Server ID 失败: {server_id_data.get('err_message')}")
                return None
            
            server_id = server_id_data.get('body')
            
            if not server_id:
                self.log(f"   ❌ Server ID 为空")
                return None
            
            self.log(f"   ✅ Server ID: {server_id}")
            
            # ⭐ 步骤 0.2: 使用 server_id 获取工具列表
            self.log(f"   📋 步骤 0.2: 获取工具列表...")
            
            url = f"{emcp_base_url}/api/Service/get_mcp_test_tools/{server_id}"  # ⭐ 使用 server_id
            
            # 使用最新的 token（可能在步骤0.1中刷新过）
            if emcp_manager and hasattr(emcp_manager, 'session_key'):
                headers['token'] = emcp_manager.session_key
            
            self.log(f"   📤 GET {url}")
            
            response = requests.get(url, headers=headers, timeout=30)
            
            self.log(f"   📥 响应: {response.status_code}")
            
            data = response.json()
            
            if data.get('err_code') == 0:
                tools_data = data.get('body', [])
                
                # 转换为统一格式
                tools = []
                for tool in tools_data:
                    tools.append({
                        'name': tool.get('functionApi'),  # API 名称
                        'display_name': tool.get('functionName'),  # 显示名称
                        'description': tool.get('functionName', ''),  # 使用显示名称作为描述
                        'parameters': tool.get('parameters', [])
                    })
                
                self.log(f"   ✅ 成功获取 {len(tools)} 个工具")
                return tools
            else:
                self.log(f"   ❌ 获取失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            self.log(f"   ❌ 获取工具列表失败: {e}")
            return None
    
    def _connect_signalr(self) -> bool:
        """建立 SignalR 连接"""
        try:
            from signalrcore.hub_connection_builder import HubConnectionBuilder
            
            self.connection = HubConnectionBuilder() \
                .with_url(self.hub_url) \
                .with_automatic_reconnect({
                    "type": "interval",
                    "intervals": [0, 2, 10, 30]
                }) \
                .build()
            
            self.connection.on("receive", self._handle_receive_message)
            self.connection.start()
            
            return True
        except Exception as e:
            self.log(f"   ❌ SignalR 连接失败: {e}")
            return False
    
    def _connect_to_agent(self, agent_token: str, conversation_id: str) -> bool:
        """连接到 Agent"""
        try:
            self.connection.send(
                "connect_single_agent",
                [agent_token, conversation_id]
            )
            
            # 等待连接响应
            time.sleep(2)
            
            # 从消息中提取连接 Token
            for msg in self.received_messages:
                if isinstance(msg, dict):
                    content = msg.get('Content')
                    if content and len(content) > 30:
                        self.connection_token = content
                        self.log(f"   🔑 连接Token: {content[:20]}...")
                        return True
            
            return False
        except Exception as e:
            self.log(f"   ❌ 连接失败: {e}")
            return False
    
    def _generate_tool_test_question(
        self,
        mcp_name: str,
        tool: dict,
        ai_generator=None,
        is_first: bool = False
    ) -> str:
        """为工具生成测试问题"""
        tool_name = tool.get('display_name') or tool.get('name')  # 使用显示名称
        tool_desc = tool.get('description', '')
        
        # 如果是第一个工具，先打招呼
        if is_first:
            if ai_generator:
                try:
                    prompt = f"""
生成一个自然、口语化的测试问题，模拟真实用户场景。

MCP名称：{mcp_name}
工具名称：{tool_name}
工具描述：{tool_desc}

要求：
1. **像真实用户一样自然提问**，不要像测试脚本
2. 首次对话，可以简单打招呼（可选）
3. 直接提出具体需求，例如：
   - "帮我查一下北京的 Python 开发职位"
   - "我想了解一下微软公司的薪资水平"
   - "能帮我搜索一下最近的招聘信息吗"
4. 使用口语化表达，贴近日常对话
5. 包含具体的测试数据（城市名、职位名、公司名等）
6. 20-40字

直接返回问题，不要引号或其他修饰。
"""
                    
                    response = ai_generator.client.chat.completions.create(
                        model=ai_generator.deployment_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.9,  # 提高温度，更自然
                        max_tokens=150
                    )
                    
                    question = response.choices[0].message.content.strip().strip('"').strip("'")
                    self.log(f"   🤖 AI 生成问题: {question}")
                    return question
                except Exception as e:
                    self.log(f"   ⚠️ AI 生成失败: {e}")
            
            # 智能降级方案：根据工具描述生成自然问题
            return self._generate_smart_question(tool_name, tool_desc, is_first=True)
        
        # 后续工具，基于上下文提问
        if ai_generator:
            try:
                prompt = f"""
生成一个自然、口语化的测试问题，模拟真实用户场景。

MCP名称：{mcp_name}
工具名称：{tool_name}
工具描述：{tool_desc}

要求：
1. **像真实用户一样自然提问**，这是对话中的后续问题
2. 使用自然的承接语，例如：
   - "好的，那帮我查一下..."
   - "明白了，我想看看..."
   - "那我再试试..."
   - 或者直接提问
3. 包含具体的测试数据（城市名、职位名、公司名等）
4. 口语化表达，贴近日常对话
5. 15-35字

直接返回问题，不要引号或其他修饰。
"""
                
                response = ai_generator.client.chat.completions.create(
                    model=ai_generator.deployment_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.9,
                    max_tokens=150
                )
                
                question = response.choices[0].message.content.strip().strip('"').strip("'")
                self.log(f"   🤖 AI 生成问题: {question}")
                return question
            except Exception as e:
                self.log(f"   ⚠️ AI 生成失败: {e}")
        
        # 智能降级方案
        return self._generate_smart_question(tool_name, tool_desc, is_first=False)
    
    def _generate_smart_question(self, tool_name: str, tool_desc: str, is_first: bool = False) -> str:
        """
        智能生成测试问题（无需 AI）
        根据工具名称和描述，生成贴近真实用户的问题
        """
        # 转换为小写便于匹配
        name_lower = tool_name.lower()
        desc_lower = tool_desc.lower()
        
        # 构建承接语
        prefix = "" if is_first else ["好的，那", "明白了，", "那我", ""][__import__('random').randint(0, 3)]
        
        # 根据工具类型智能生成问题
        
        # 1. 搜索/查询类
        if any(keyword in name_lower or keyword in desc_lower for keyword in ['search', 'find', 'query', '搜索', '查询', '查找']):
            if 'job' in name_lower or 'job' in desc_lower or '职位' in desc_lower or '招聘' in desc_lower:
                questions = [
                    f"{prefix}帮我找一下北京的 Python 开发工程师职位",
                    f"{prefix}搜索一下上海的数据分析师岗位",
                    f"{prefix}查一下深圳有没有产品经理的招聘",
                    f"{prefix}我想看看杭州的前端工程师职位"
                ]
            elif 'company' in name_lower or '公司' in desc_lower:
                questions = [
                    f"{prefix}查一下腾讯公司的基本信息",
                    f"{prefix}我想了解一下字节跳动",
                    f"{prefix}搜索一下阿里巴巴公司"
                ]
            else:
                questions = [
                    f"{prefix}帮我搜索一下相关信息",
                    f"{prefix}查一下这方面的内容",
                    f"{prefix}找找看有什么结果"
                ]
        
        # 2. 获取详情类
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ['detail', 'get', 'info', '详情', '获取', '信息']):
            if 'job' in name_lower or '职位' in desc_lower:
                questions = [
                    f"{prefix}看一下这个职位的详细信息",
                    f"{prefix}我想了解这个岗位的具体要求",
                    f"{prefix}详细介绍一下这个工作"
                ]
            elif 'salary' in name_lower or 'pay' in name_lower or '薪资' in desc_lower or '工资' in desc_lower:
                questions = [
                    f"{prefix}查一下软件工程师在北京的薪资水平",
                    f"{prefix}我想知道产品经理的工资大概多少",
                    f"{prefix}帮我看看数据分析师的薪酬情况"
                ]
            else:
                questions = [
                    f"{prefix}获取一下详细信息",
                    f"{prefix}帮我看看具体内容",
                    f"{prefix}了解一下详情"
                ]
        
        # 3. 分析/统计类
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ['analy', 'statistic', 'report', '分析', '统计', '报告']):
            questions = [
                f"{prefix}分析一下互联网行业的就业趋势",
                f"{prefix}给我看看技术岗位的数据统计",
                f"{prefix}帮我做个行业薪资分析"
            ]
        
        # 4. 计算/估算类
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ['calculat', 'estimat', 'comput', '计算', '估算']):
            questions = [
                f"{prefix}算一下税后收入大概多少",
                f"{prefix}帮我估算一下年薪",
                f"{prefix}计算一下综合薪酬"
            ]
        
        # 5. 比较类
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ['compar', 'vs', 'versus', '比较', '对比']):
            questions = [
                f"{prefix}比较一下北京和上海的薪资水平",
                f"{prefix}对比一下不同公司的待遇",
                f"{prefix}看看哪个城市的机会更多"
            ]
        
        # 6. 推荐类
        elif any(keyword in name_lower or keyword in desc_lower for keyword in ['recommend', 'suggest', '推荐', '建议']):
            questions = [
                f"{prefix}推荐几个适合我的职位",
                f"{prefix}给我建议一些好的公司",
                f"{prefix}有什么合适的工作推荐吗"
            ]
        
        # 7. 通用功能
        else:
            questions = [
                f"{prefix}试试 {tool_name} 功能",
                f"{prefix}帮我用一下 {tool_name}",
                f"{prefix}测试一下 {tool_name} 看看"
            ]
        
        # 随机选择一个问题
        import random
        question = random.choice(questions)
        
        self.log(f"   💡 智能生成问题: {question}")
        return question
    
    def _send_and_receive(
        self,
        conversation_id: str,
        question: str,
        plugin_ids: list,
        expect_tool: str = None
    ) -> dict:
        """发送消息并接收响应"""
        try:
            # 重置状态
            self.is_complete = False
            self.received_messages = []
            
            # 构建消息
            dialog_id = str(uuid.uuid4())
            
            message_data = {
                "ContentText": question,
                "DialogID": dialog_id,
                "ConversationID": conversation_id,
                "FromName": "自动化测试",
                "EnumInvodeType": 1,
                "SelectReferenceInfos": [],
                "SkillMode": 1,
                "ContentImages": None,
                "IsVisible": False,
                "FunctionName": "",
                "Arguments": "",
                "TaskNumber": None,
                "EnableCanvas": False,
                "SelectSkills": [str(plugin_ids[0])] if plugin_ids else [],
                "HistoryCount": 0
            }
            
            # 发送消息
            self.connection.send(
                "send_text_message",
                [message_data, self.connection_token]
            )
            
            # 等待响应
            max_wait = 30
            start_time = time.time()
            
            while not self.is_complete and (time.time() - start_time) < max_wait:
                time.sleep(0.5)
            
            # 提取结果
            full_content = ""
            skills_used = []
            function_calls = []  # ⭐ 记录函数调用
            
            for msg in self.received_messages:
                if isinstance(msg, dict):
                    # 提取完整内容
                    if msg.get('MessageOrder') == -1:  # 完整消息标识
                        full_content = msg.get('FullContent', '')
                    
                    # ⭐ 检查工具调用消息（最重要的标识）
                    if msg.get('MessageType') == 'AgentFunctionCallMessage':
                        function_name = msg.get('FunctionName', '')
                        if function_name and function_name not in function_calls:
                            function_calls.append(function_name)
                    
                    # 提取技能标识
                    skills = msg.get('Skills', [])
                    for skill in skills:
                        skill_name = skill.get('SkillName')
                        if skill_name and skill_name not in skills_used:
                            skills_used.append(skill_name)
            
            # ⭐ 判断成功（更严格）
            success = (
                self.is_complete and  # 对话完成
                len(full_content) > 0  # 有回答
            )
            
            # ⭐ 如果期望特定工具，必须检查 FunctionName
            if expect_tool:
                # 智能匹配：支持带/不带 API_ 前缀的匹配
                # 例如：expect_tool = "API_job_search", FunctionName 可能是 "job_search" 或 "API_job_search"
                expect_tool_clean = expect_tool.lower().replace('api_', '')
                
                tool_called = False
                matched_function = None
                
                for fn in function_calls:
                    fn_clean = fn.lower().replace('api_', '')
                    # 双向匹配：expect包含fn 或 fn包含expect
                    if expect_tool_clean in fn_clean or fn_clean in expect_tool_clean:
                        tool_called = True
                        matched_function = fn
                        break
                
                if not tool_called:
                    self.log(f"   ❌ 期望工具 {expect_tool} 未被调用")
                    self.log(f"   📋 实际调用: {function_calls}")
                    success = False  # ⭐ 标记为失败
                else:
                    self.log(f"   ✅ 确认调用工具: {expect_tool} (匹配到: {matched_function})")
            
            return {
                "success": success,
                "response": full_content,
                "skills_used": skills_used,
                "function_calls": function_calls,  # ⭐ 返回函数调用列表
                "error": None if success else ("期望工具未被调用" if expect_tool and not tool_called else "响应超时或为空")
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "skills_used": [],
                "error": str(e)
            }
    
    def generate_chat_test_report(self, result: dict, output_file: str = "agent_chat_test_report.html"):
        """生成对话测试报告"""
        # 获取当前时间
        test_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Agent 对话测试报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #0066cc; }}
        .summary {{ background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .success {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #0066cc; color: white; }}
        .badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; color: white; }}
        .badge-success {{ background: #28a745; }}
        .badge-failed {{ background: #dc3545; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Agent 对话测试报告</h1>
        
        <div class="summary">
            <h2>📊 测试概览</h2>
            <p><strong>会话ID:</strong> {result.get('conversation_id')}</p>
            <p><strong>测试时间:</strong> {test_time}</p>
            <p><strong>总工具数:</strong> {result.get('total_tools', 0)}</p>
            <p><strong class="success">✅ 通过:</strong> {result.get('passed_tools', 0)}</p>
            <p><strong class="failed">❌ 失败:</strong> {result.get('failed_tools', 0)}</p>
            <p><strong>成功率:</strong> {result.get('success_rate', 0):.1f}%</p>
        </div>
        
        <h2>🔧 工具测试详情</h2>
        <table>
            <tr>
                <th>序号</th>
                <th>工具名称</th>
                <th>状态</th>
                <th>测试问题</th>
                <th>Agent回答</th>
                <th>函数调用 ⭐</th>
            </tr>
"""
        
        for i, tool_test in enumerate(result.get('tools_tested', []), 1):
            badge = '<span class="badge badge-success">✅ 通过</span>' if tool_test['success'] else '<span class="badge badge-failed">❌ 失败</span>'
            response = tool_test.get('response', '')[:200]
            if len(tool_test.get('response', '')) > 200:
                response += "..."
            
            skills = ', '.join(tool_test.get('skills_used', [])) or '无'
            
            # ⭐ 显示函数调用（AgentFunctionCallMessage）
            function_calls = tool_test.get('function_calls', [])
            functions_text = ', '.join(function_calls) if function_calls else '<span style="color:#dc3545;">未调用</span>'
            
            # 使用显示名称，API名称作为副标题
            display_name = tool_test.get('display_name') or tool_test.get('tool_name')
            api_name = tool_test.get('tool_name')
            
            html += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{display_name}</strong><br><small style="color:#666;">API: {api_name}</small></td>
                <td>{badge}</td>
                <td>{tool_test['test_question']}</td>
                <td><pre>{response}</pre></td>
                <td>{functions_text}</td>
            </tr>
"""
        
        html += f"""
        </table>
        
        <footer style="margin-top: 40px; text-align: center; color: #999;">
            <p>Generated by EMCPFlow - Agent 对话测试</p>
            <p>Made with ❤️ by 巴赫工作室</p>
        </footer>
    </div>
</body>
</html>
"""
        
        # 保存文件到 outputs/reports 目录
        import os
        from pathlib import Path
        
        # 确保 outputs/reports 目录存在
        reports_dir = Path("outputs/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果 output_file 没有路径前缀，添加 outputs/reports/
        output_path = Path(output_file)
        if not output_path.parent or output_path.parent == Path('.'):
            output_path = reports_dir / output_file
        
        abs_path = output_path.absolute()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.log(f"\n💾 对话测试报告已保存")
        self.log(f"   📂 文件: {abs_path}")
        
        return output_file
    
    def _handle_receive_message(self, data):
        """处理接收到的消息"""
        try:
            if isinstance(data, list) and len(data) > 0:
                msg = data[0]
                
                # 保存消息
                self.received_messages.append(msg)
                
                # 提取连接 Token
                if not self.connection_token:
                    content = msg.get('Content')
                    if content and len(content) > 30:  # UUID 格式
                        self.connection_token = content
                        self.log(f"   🔑 获取连接Token: {content[:20]}...")
                
                # 检查消息类型
                msg_type = msg.get('MessageType', '')
                
                if msg_type == 'AgentPartialTextMessage':
                    # 部分文本消息（流式输出）
                    partial = msg.get('Content', '')
                    if partial:
                        self.log(f"   💬 [{msg_type}] {partial[:50]}...")
                
                elif msg_type == 'AgentTextMessage':
                    # 完整文本消息
                    content = msg.get('Content', '')
                    self.log(f"   📝 [完整消息] {content[:80]}...")
                
                elif msg_type == 'SystemMessage':
                    # 系统消息
                    self.log(f"   ℹ️ [系统] {msg.get('Content', '')[:50]}...")
                
                elif msg_type == 'AgentFunctionCallMessage':  # ⭐ 工具调用消息
                    # 这才是真正的工具调用标识
                    function_name = msg.get('FunctionName', '')
                    response = msg.get('Response', '')
                    self.log(f"   🔧 [工具调用] 函数: {function_name}")
                    if response:
                        self.log(f"      响应: {response[:100]}...")
                
                # 检查是否完成
                process = msg.get('SuperAgentProcess', 0)
                if process == 1000:
                    self.log(f"   ✅ 对话处理完成 (SuperAgentProcess: 1000)")
                    self.is_complete = True
                
                # 检查技能调用（Skills 字段）
                skills = msg.get('Skills', [])
                if skills:
                    for skill in skills:
                        skill_name = skill.get('SkillName')
                        self.log(f"   🏷️ 技能标识: {skill_name}")
                
        except Exception as e:
            self.log(f"   ⚠️ 消息处理异常: {e}")


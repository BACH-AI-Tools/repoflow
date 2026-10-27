#!/usr/bin/env python3
"""
Agent 平台 API 调用示例
演示如何使用 Agent 平台的完整接口进行测试

Author: BACH Studio
Date: 2025-12-01
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional


class AgentPlatformDemo:
    """Agent 平台 API 示例客户端"""
    
    def __init__(self, base_url: str = "https://v5.kaleido.guru"):
        """
        初始化客户端
        
        Args:
            base_url: Agent 平台地址
        """
        self.base_url = base_url
        self.session_key = None
        self.user_info = None
    
    def _print_separator(self, title: str = ""):
        """打印分隔符"""
        print("\n" + "="*70)
        if title:
            print(f"  {title}")
            print("="*70)
    
    def _print_request(self, method: str, url: str, data: dict = None):
        """打印请求信息"""
        print(f"\n📤 {method} {url}")
        if data:
            print(f"📝 请求数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _print_response(self, status_code: int, data: dict):
        """打印响应信息"""
        print(f"\n📥 响应状态: {status_code}")
        print(f"📋 响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    def _get_headers(self) -> Dict:
        """获取请求头"""
        return {
            'Token': self.session_key,
            'Content-Type': 'application/json;charset=UTF-8',
            'Language': 'ch_cn'
        }
    
    # ==================== 1. 用户认证 ====================
    
    def login(self, phone: str, validation_code: str) -> Optional[Dict]:
        """
        登录 Agent 平台
        
        Args:
            phone: 手机号
            validation_code: 验证码（格式：MMyyyydd，如 11202507）
        
        Returns:
            用户信息字典，包含 session_key、user_name、uid
        """
        self._print_separator("接口 1: 登录 Agent 平台")
        
        url = f"{self.base_url}/api/authentication/verfiy_sms_validation_code_login?guest=true"
        
        payload = {
            "prefix": "+86",
            "guest": True,
            "phone": phone,
            "validation_code": validation_code
        }
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'Language': 'ch_cn',
            'Cache-Control': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self._print_request("POST", url, payload)
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                body = data.get('body', {})
                self.session_key = body.get('session_key')
                self.user_info = body
                
                print(f"\n✅ 登录成功!")
                print(f"   👤 用户: {body.get('user_name')}")
                print(f"   🆔 UID: {body.get('uid')}")
                print(f"   🔑 Token: {self.session_key[:30]}...")
                
                return body
            else:
                print(f"\n❌ 登录失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return None
    
    # ==================== 2. Agent 管理 ====================
    
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
            创建结果，包含 super_agent_setting_id
        """
        self._print_separator("接口 2: 创建 Agent")
        
        url = f"{self.base_url}/api/superAgent/create"
        
        payload = {
            "name": name,
            "logo": logo,
            "description": description,
            "super_agent_category_id": category_id,
            "manage_lable_ids": None,
            "editor_uids": []
        }
        
        self._print_request("POST", url, payload)
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                body = data.get('body', {})
                agent_id = body.get('super_agent_setting_id')
                
                print(f"\n✅ Agent 创建成功!")
                print(f"   🆔 Agent ID: {agent_id}")
                
                return body
            else:
                print(f"\n❌ 创建失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return None
    
    def query_plugins(self, mcp_name: str = None) -> Optional[List[Dict]]:
        """
        查询 MCP 插件列表
        
        Args:
            mcp_name: MCP 名称（用于过滤）
        
        Returns:
            插件列表
        """
        self._print_separator("接口 3: 查询 MCP 插件")
        
        url = f"{self.base_url}/api/plugin/query_plugin"
        
        payload = {
            "current_page": 1,
            "isPublish": True,
            "page_size": 9999,
            "category_id": None,
            "is_mcp_query": True  # ⭐ 只查询 MCP 插件
        }
        
        self._print_request("POST", url, payload)
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                plugins = data.get('body', [])
                
                print(f"\n✅ 查询成功!")
                print(f"   📦 找到 {len(plugins)} 个 MCP 插件")
                
                # 如果指定了 MCP 名称，进行过滤
                if mcp_name:
                    matched = [p for p in plugins if mcp_name.lower() in p.get('name_for_model', '').lower()]
                    
                    if matched:
                        print(f"\n   🎯 匹配的 MCP:")
                        for p in matched:
                            print(f"      • {p.get('name_for_model')}")
                            print(f"        ID: {p.get('id')}")
                            print(f"        UUID: {p.get('uuid')}")
                        return matched
                    else:
                        print(f"\n   ⚠️ 未找到匹配 '{mcp_name}' 的 MCP")
                        return []
                
                # 显示前 5 个插件
                print(f"\n   📋 插件列表（前5个）:")
                for i, p in enumerate(plugins[:5], 1):
                    print(f"      {i}. {p.get('name_for_model')} (ID: {p.get('id')})")
                
                return plugins
            else:
                print(f"\n❌ 查询失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
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
            plugin_ids: 要绑定的插件 ID 列表 ⭐
            logo: Logo URL
            system_message: 系统消息
            category_id: 分类 ID
        
        Returns:
            是否成功
        """
        self._print_separator("接口 4: 更新 Agent（绑定 MCP）")
        
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
            "plugin_ids": plugin_ids,  # ⭐ 绑定的 MCP 插件 ID 列表
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
        
        self._print_request("POST", url, payload)
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                print(f"\n✅ Agent 更新成功!")
                print(f"   🔗 已绑定 {len(plugin_ids)} 个插件")
                return True
            else:
                print(f"\n❌ 更新失败: {data.get('err_message')}")
                return False
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return False
    
    def publish_agent(self, agent_id: int, description: str = "测试发布") -> Optional[Dict]:
        """
        发布 Agent
        
        Args:
            agent_id: Agent ID
            description: 发布描述
        
        Returns:
            发布结果，包含 publish_id
        """
        self._print_separator("接口 5: 发布 Agent")
        
        url = f"{self.base_url}/api/superAgent/publish/{agent_id}"
        
        payload = {
            "description": description,
            "upateAllAgentVersion": True
        }
        
        self._print_request("POST", url, payload)
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                body = data.get('body', {})
                publish_id = body.get('publish_id')
                agent_url = f"{self.base_url}/chat?releaseId={publish_id}"
                
                print(f"\n✅ Agent 发布成功!")
                print(f"   🆔 发布 ID: {publish_id}")
                print(f"   🔗 访问链接: {agent_url}")
                
                return body
            else:
                print(f"\n❌ 发布失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
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
        self._print_separator("接口 6: 获取 Agent 技能")
        
        url = f"{self.base_url}/api/superAgent/skill_detail"
        
        params = {
            "super_agent_setting_id": agent_id,
            "version": version
        }
        
        print(f"\n📤 GET {url}")
        print(f"📝 查询参数: {params}")
        
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                body = data.get('body', {})
                plugins = body.get('plugins', [])
                
                if plugins:
                    plugin_ids = [p.get('id') for p in plugins]
                    
                    print(f"\n✅ 获取成功!")
                    print(f"   🔧 找到 {len(plugins)} 个技能:")
                    for p in plugins:
                        print(f"      • {p.get('name_for_model')} (ID: {p.get('id')})")
                    
                    return plugin_ids
                else:
                    print(f"\n   ℹ️ Agent 暂无绑定的技能")
                    return []
            else:
                print(f"\n❌ 获取失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return None
    
    # ==================== 3. 会话管理 ====================
    
    def get_workspaces(self) -> Optional[List[Dict]]:
        """
        获取工作区列表
        
        Returns:
            工作区列表
        """
        self._print_separator("接口 7: 获取工作区列表")
        
        url = f"{self.base_url}/api/conversation/get_work_space_for_user"
        
        print(f"\n📤 GET {url}")
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                workspaces = data.get('body', [])
                
                print(f"\n✅ 获取成功!")
                print(f"   📁 找到 {len(workspaces)} 个工作区:")
                for ws in workspaces:
                    print(f"      • {ws.get('name')} (ID: {ws.get('id')})")
                
                return workspaces
            else:
                print(f"\n❌ 获取失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return None
    
    def create_workspace(self, workspace_name: str) -> Optional[int]:
        """
        创建工作区
        
        Args:
            workspace_name: 工作区名称
        
        Returns:
            工作区 ID
        """
        self._print_separator("接口 8: 创建工作区")
        
        url = f"{self.base_url}/api/conversation/create_work_space"
        
        payload = {"name": workspace_name}
        
        self._print_request("POST", url, payload)
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                ws_id = data.get('body', {}).get('id')
                
                print(f"\n✅ 工作区创建成功!")
                print(f"   🆔 工作区 ID: {ws_id}")
                
                return ws_id
            else:
                print(f"\n❌ 创建失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
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
        self._print_separator("接口 9: 创建会话")
        
        url = f"{self.base_url}/api/conversation/init?"
        
        payload = {
            "super_agent_setting_id": agent_id,
            "conversation_name": conversation_name,
            "work_space_id": workspace_id,
            "color": "#F67F00",
            "conversation_platform": 0,
            "type": 0
        }
        
        self._print_request("POST", url, payload)
        
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            data = response.json()
            
            self._print_response(response.status_code, data)
            
            if data.get('err_code') == 0:
                conv_id = data.get('body', {}).get('conversation_id')
                
                print(f"\n✅ 会话创建成功!")
                print(f"   🆔 会话 ID: {conv_id}")
                
                return conv_id
            else:
                print(f"\n❌ 创建失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return None


# ==================== 完整测试流程示例 ====================

def demo_complete_workflow():
    """
    演示完整的 Agent 测试工作流程
    """
    print("\n" + "="*70)
    print("  🚀 Agent 平台 API 完整测试流程演示")
    print("="*70)
    
    # 初始化客户端
    demo = AgentPlatformDemo()
    
    # 配置参数（请根据实际情况修改）
    PHONE = "YOUR_PHONE_NUMBER"
    VALIDATION_CODE = datetime.now().strftime("%m%Y%d")  # 格式：MMyyyydd
    MCP_NAME = "测试MCP"  # 要查找的 MCP 名称
    AGENT_NAME = f"{MCP_NAME} 测试 Agent"
    AGENT_DESC = f"这是一个集成了 {MCP_NAME} 的测试 Agent"
    
    print(f"\n📋 配置信息:")
    print(f"   📱 手机号: {PHONE}")
    print(f"   🔑 验证码: {VALIDATION_CODE}")
    print(f"   📦 MCP 名称: {MCP_NAME}")
    print(f"   🤖 Agent 名称: {AGENT_NAME}")
    
    try:
        # 步骤 1: 登录
        print("\n" + "-"*70)
        print("步骤 1/9: 登录 Agent 平台")
        print("-"*70)
        
        user_info = demo.login(PHONE, VALIDATION_CODE)
        if not user_info:
            print("\n❌ 登录失败，终止流程")
            return
        
        # 步骤 2: 创建 Agent
        print("\n" + "-"*70)
        print("步骤 2/9: 创建 Agent")
        print("-"*70)
        
        agent_result = demo.create_agent(AGENT_NAME, AGENT_DESC)
        if not agent_result:
            print("\n❌ 创建 Agent 失败，终止流程")
            return
        
        agent_id = agent_result.get('super_agent_setting_id')
        
        # 步骤 3: 查询 MCP 插件
        print("\n" + "-"*70)
        print("步骤 3/9: 查询 MCP 插件")
        print("-"*70)
        
        plugins = demo.query_plugins(MCP_NAME)
        if not plugins or len(plugins) == 0:
            print(f"\n❌ 未找到 MCP '{MCP_NAME}'，终止流程")
            return
        
        mcp_plugin_id = plugins[0].get('id')
        
        # 步骤 4: 绑定 MCP 到 Agent
        print("\n" + "-"*70)
        print("步骤 4/9: 绑定 MCP 到 Agent")
        print("-"*70)
        
        update_success = demo.update_agent(
            agent_id=agent_id,
            name=AGENT_NAME,
            description=AGENT_DESC,
            plugin_ids=[mcp_plugin_id]
        )
        
        if not update_success:
            print("\n❌ 绑定 MCP 失败，终止流程")
            return
        
        # 步骤 5: 发布 Agent
        print("\n" + "-"*70)
        print("步骤 5/9: 发布 Agent")
        print("-"*70)
        
        publish_result = demo.publish_agent(agent_id)
        if not publish_result:
            print("\n❌ 发布 Agent 失败，终止流程")
            return
        
        publish_id = publish_result.get('publish_id')
        agent_url = f"{demo.base_url}/chat?releaseId={publish_id}"
        
        # 步骤 6: 获取 Agent 技能
        print("\n" + "-"*70)
        print("步骤 6/9: 获取 Agent 技能")
        print("-"*70)
        
        plugin_ids = demo.get_agent_skills(agent_id)
        
        # 步骤 7: 获取工作区
        print("\n" + "-"*70)
        print("步骤 7/9: 获取工作区")
        print("-"*70)
        
        workspaces = demo.get_workspaces()
        
        # 使用第一个工作区，或创建新的
        if workspaces and len(workspaces) > 0:
            workspace_id = workspaces[0].get('id')
            print(f"\n   ✅ 使用已有工作区: {workspaces[0].get('name')} (ID: {workspace_id})")
        else:
            print("\n   ℹ️ 没有工作区，创建新的...")
            workspace_id = demo.create_workspace("MCP 工厂")
            if not workspace_id:
                print("\n❌ 创建工作区失败，终止流程")
                return
        
        # 步骤 8: 创建会话
        print("\n" + "-"*70)
        print("步骤 8/9: 创建测试会话")
        print("-"*70)
        
        conv_name = f"{MCP_NAME} 自动测试 - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conversation_id = demo.create_conversation(agent_id, workspace_id, conv_name)
        
        if not conversation_id:
            print("\n❌ 创建会话失败")
        
        # 步骤 9: 总结
        print("\n" + "="*70)
        print("  ✅ 完整流程执行成功!")
        print("="*70)
        print(f"\n📊 测试结果汇总:")
        print(f"   🤖 Agent ID: {agent_id}")
        print(f"   📋 发布 ID: {publish_id}")
        print(f"   🔗 Agent 链接: {agent_url}")
        print(f"   💬 会话 ID: {conversation_id}")
        print(f"\n💡 下一步:")
        print(f"   1. 访问 Agent 链接进行测试")
        print(f"   2. 在会话中发送测试消息")
        print(f"   3. 验证 MCP 工具是否正常调用")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ 流程执行失败: {e}")
        import traceback
        print(traceback.format_exc())


# ==================== 单独接口测试示例 ====================

def demo_individual_apis():
    """
    演示单独测试各个接口
    """
    print("\n" + "="*70)
    print("  📖 单独接口调用示例")
    print("="*70)
    
    demo = AgentPlatformDemo()
    
    # 示例 1: 只登录
    print("\n【示例 1】仅登录")
    print("-"*70)
    phone = "YOUR_PHONE_NUMBER"
    validation_code = datetime.now().strftime("%m%Y%d")
    demo.login(phone, validation_code)
    
    # 示例 2: 查询所有 MCP 插件
    if demo.session_key:
        print("\n【示例 2】查询所有 MCP 插件")
        print("-"*70)
        demo.query_plugins()
    
    # 示例 3: 查询特定 MCP
    if demo.session_key:
        print("\n【示例 3】查询特定 MCP")
        print("-"*70)
        demo.query_plugins(mcp_name="巴赫")
    
    print("\n" + "="*70 + "\n")


# ==================== 主函数 ====================

def main():
    """主函数"""
    print("\n" + "="*70)
    print("  🎯 Agent 平台 API 示例程序")
    print("="*70)
    print("\n请选择运行模式:")
    print("  1. 完整测试流程 (推荐)")
    print("  2. 单独接口测试")
    print("  3. 退出")
    
    choice = input("\n请输入选项 (1-3): ").strip()
    
    if choice == "1":
        demo_complete_workflow()
    elif choice == "2":
        demo_individual_apis()
    elif choice == "3":
        print("\n👋 再见!")
    else:
        print("\n❌ 无效选项")


if __name__ == "__main__":
    # 直接运行完整流程（如需交互式选择，请取消注释下一行）
    # main()
    
    # 默认运行完整流程
    demo_complete_workflow()

















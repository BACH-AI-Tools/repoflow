#!/usr/bin/env python3
"""
即梦 MCP 工具测试脚本
用于连接即梦 MCP 服务器并生成 logo
"""

import requests
import json
import time
import threading
import sseclient

class JimengMCPClient:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.session_id = None
        self.message_endpoint = None
        self.sse_client = None
        self.sse_thread = None
        self.responses = {}
        self.running = False
        
    def connect(self):
        """建立 SSE 连接"""
        print("正在连接到即梦 MCP 服务器...")
        try:
            response = requests.get(self.base_url, headers=self.headers, stream=True, timeout=30)
            self.sse_client = sseclient.SSEClient(response)
            
            # 先获取 endpoint 事件
            for event in self.sse_client.events():
                if event.event == 'endpoint':
                    self.message_endpoint = event.data
                    if '?sessionId=' in self.message_endpoint:
                        self.session_id = self.message_endpoint.split('?sessionId=')[1]
                    print(f"✅ 连接成功! Session ID: {self.session_id}")
                    print(f"消息端点: {self.message_endpoint}")
                    
                    # 启动后台线程监听 SSE 消息
                    self.running = True
                    self.sse_thread = threading.Thread(target=self._listen_sse, daemon=True)
                    self.sse_thread.start()
                    
                    return True
                    
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def _listen_sse(self):
        """后台监听 SSE 消息"""
        try:
            for event in self.sse_client.events():
                if not self.running:
                    break
                    
                if event.event == 'message':
                    try:
                        data = json.loads(event.data)
                        msg_id = data.get('id')
                        if msg_id:
                            self.responses[msg_id] = data
                            print(f"\n📩 收到响应 (ID: {msg_id})")
                            print(f"内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"无法解析 SSE 消息: {event.data}")
        except Exception as e:
            print(f"SSE 监听错误: {e}")
    
    def send_request(self, method, params=None, wait_timeout=10):
        """发送 MCP 请求并等待响应"""
        if not self.message_endpoint:
            print("❌ 未建立连接,请先调用 connect()")
            return None
            
        url = f"{self.base_url.replace('/sse', '')}{self.message_endpoint}"
        
        msg_id = int(time.time() * 1000)
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": msg_id
        }
        
        if params:
            payload["params"] = params
            
        print(f"\n📤 发送请求: {method}")
        print(f"请求 ID: {msg_id}")
        print(f"参数: {json.dumps(params, ensure_ascii=False, indent=2) if params else 'null'}")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            print(f"HTTP 状态码: {response.status_code}")
            
            if response.status_code == 202:
                print("⏳ 请求已接受,等待 SSE 响应...")
                
                # 等待响应
                start_time = time.time()
                while time.time() - start_time < wait_timeout:
                    if msg_id in self.responses:
                        return self.responses[msg_id]
                    time.sleep(0.1)
                
                print(f"⚠️ 等待超时 ({wait_timeout}秒)")
                return None
            elif response.status_code == 200:
                # 直接返回的响应
                result = response.json()
                print(f"✅ 直接响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result
            else:
                print(f"❌ 请求失败,状态码: {response.status_code}")
                print(f"响应: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    def list_tools(self):
        """获取可用工具列表"""
        return self.send_request("tools/list", wait_timeout=15)
    
    def call_tool(self, tool_name, arguments):
        """调用工具"""
        return self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        }, wait_timeout=60)
    
    def close(self):
        """关闭连接"""
        self.running = False
        if self.sse_thread:
            self.sse_thread.join(timeout=2)


def main():
    # 从配置文件读取即梦 MCP 配置
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    from src.unified_config_manager import UnifiedConfigManager
    
    config_mgr = UnifiedConfigManager()
    jimeng_cfg = config_mgr.get_jimeng_config()
    
    if not jimeng_cfg.get("emcp_key") or not jimeng_cfg.get("emcp_usercode"):
        print("❌ 错误：请先在配置文件中设置 jimeng.emcp_key 和 jimeng.emcp_usercode")
        print("   配置文件位置：config.json")
        print("   参考模板：config_template.json")
        sys.exit(1)
    
    # 即梦 MCP 配置
    config = {
        "base_url": jimeng_cfg.get("mcp_url", "http://mcptest013.sitmcp.kaleido.guru/sse"),
        "headers": {
            "emcp-key": jimeng_cfg.get("emcp_key"),
            "emcp-usercode": jimeng_cfg.get("emcp_usercode")
        }
    }
    
    # 创建客户端
    client = JimengMCPClient(config['base_url'], config['headers'])
    
    # 建立连接
    if not client.connect():
        return
    
    # 等待 SSE 监听器启动
    time.sleep(1)
    
    try:
        # 1. 获取工具列表
        print("\n" + "="*60)
        print("步骤 1: 获取工具列表")
        print("="*60)
        
        tools_result = client.list_tools()
        
        if not tools_result:
            print("❌ 无法获取工具列表")
            return
        
        # 检查结果结构
        if 'result' in tools_result:
            tools = tools_result['result'].get('tools', [])
            print(f"\n✅ 找到 {len(tools)} 个工具:")
            for i, tool in enumerate(tools, 1):
                print(f"\n{i}. {tool.get('name')}")
                print(f"   描述: {tool.get('description', '无描述')}")
                if 'inputSchema' in tool:
                    print(f"   参数: {json.dumps(tool['inputSchema'], ensure_ascii=False, indent=6)}")
            
            # 2. 查找并调用 logo 生成工具
            print("\n" + "="*60)
            print("步骤 2: 生成 EMCPFlow Logo")
            print("="*60)
            
            # 查找图片生成相关的工具
            image_tools = [t for t in tools if any(keyword in t.get('name', '').lower() 
                          for keyword in ['image', 'logo', 'generate', 'create', 'draw', 'paint', '生成', '图片', '绘制'])]
            
            if not image_tools:
                print("❌ 未找到图片生成相关工具")
                print("可用工具:")
                for tool in tools:
                    print(f"  - {tool.get('name')}")
                return
            
            # 使用第一个匹配的工具
            tool = image_tools[0]
            tool_name = tool.get('name')
            
            print(f"\n🎨 使用工具: {tool_name}")
            print(f"描述: {tool.get('description', '')}")
            
            # 准备参数
            prompt = "EMCPFlow logo - 一个现代化的 MCP 包管理工具,简洁专业的设计,包含流动的数据元素和连接符号,蓝色调,扁平化风格"
            
            # 根据工具的 inputSchema 构建参数
            schema = tool.get('inputSchema', {})
            properties = schema.get('properties', {})
            
            arguments = {}
            
            # 智能填充参数
            for prop_name, prop_info in properties.items():
                if 'prompt' in prop_name.lower() or 'description' in prop_name.lower() or '描述' in prop_name:
                    arguments[prop_name] = prompt
                elif 'size' in prop_name.lower() or '尺寸' in prop_name:
                    arguments[prop_name] = "1024x1024"
                elif 'style' in prop_name.lower() or '风格' in prop_name:
                    arguments[prop_name] = "minimalist"
                elif 'quality' in prop_name.lower() or '质量' in prop_name:
                    arguments[prop_name] = "high"
            
            print(f"\n参数: {json.dumps(arguments, ensure_ascii=False, indent=2)}")
            
            # 调用工具
            result = client.call_tool(tool_name, arguments)
            
            if result and 'result' in result:
                print("\n" + "="*60)
                print("✅ Logo 生成成功!")
                print("="*60)
                print(json.dumps(result['result'], ensure_ascii=False, indent=2))
                
                # 如果有图片 URL,保存到文件
                content = result['result'].get('content', [])
                for item in content:
                    if item.get('type') == 'image':
                        img_data = item.get('data')
                        if img_data:
                            # 保存为文件
                            import base64
                            with open('emcpflow_logo.png', 'wb') as f:
                                if img_data.startswith('data:image'):
                                    # 处理 data URL
                                    img_data = img_data.split(',')[1]
                                f.write(base64.b64decode(img_data))
                            print("\n💾 Logo 已保存为: emcpflow_logo.png")
                    elif item.get('type') == 'text':
                        if 'url' in item.get('text', '').lower():
                            print(f"\n🔗 图片 URL: {item.get('text')}")
            else:
                print("\n❌ Logo 生成失败")
                
        else:
            print(f"❌ 意外的响应格式: {json.dumps(tools_result, ensure_ascii=False, indent=2)}")
            
    finally:
        # 关闭连接
        print("\n关闭连接...")
        client.close()


if __name__ == "__main__":
    main()

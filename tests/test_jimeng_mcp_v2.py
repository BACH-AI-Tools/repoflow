#!/usr/bin/env python3
"""
即梦 MCP 工具测试脚本 V2
使用独立的 SSE 连接接收响应
"""

import requests
import json
import time
import threading
import queue

class JimengMCPClient:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.session_id = None
        self.message_endpoint = None
        self.response_queue = queue.Queue()
        self.running = False
        
    def start_sse_listener(self):
        """启动 SSE 监听器线程"""
        print("🔌 启动 SSE 监听器...")
        self.running = True
        thread = threading.Thread(target=self._sse_listener, daemon=True)
        thread.start()
        return thread
    
    def _sse_listener(self):
        """SSE 监听器线程"""
        try:
            print("📡 正在连接 SSE 流...")
            response = requests.get(self.base_url, headers=self.headers, stream=True, timeout=None)
            
            print(f"SSE 连接状态: {response.status_code}")
            
            # 逐行读取 SSE 流
            for line in response.iter_lines():
                if not self.running:
                    break
                
                if line:
                    line = line.decode('utf-8')
                    
                    # 解析 SSE 格式
                    if line.startswith('event:'):
                        event_type = line[6:].strip()
                        
                    elif line.startswith('data:'):
                        data = line[5:].strip()
                        
                        # endpoint 事件
                        if data.startswith('/message?sessionId='):
                            self.message_endpoint = data
                            self.session_id = data.split('=')[1]
                            print(f"✅ 获得 Session ID: {self.session_id}")
                        
                        # 尝试解析为 JSON
                        else:
                            try:
                                json_data = json.loads(data)
                                print(f"\n📩 收到 SSE 消息:")
                                print(json.dumps(json_data, ensure_ascii=False, indent=2))
                                self.response_queue.put(json_data)
                            except json.JSONDecodeError:
                                print(f"📝 SSE 数据: {data}")
                                
        except Exception as e:
            print(f"❌ SSE 监听错误: {e}")
            import traceback
            traceback.print_exc()
    
    def wait_for_session(self, timeout=10):
        """等待获取 session ID"""
        start = time.time()
        while not self.session_id and time.time() - start < timeout:
            time.sleep(0.1)
        return self.session_id is not None
    
    def send_request(self, method, params=None, wait_timeout=30):
        """发送请求"""
        if not self.message_endpoint:
            print("❌ 未获得消息端点")
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
        print(f"URL: {url}")
        print(f"请求 ID: {msg_id}")
        if params:
            print(f"参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            print(f"HTTP 状态: {response.status_code} - {response.text[:100]}")
            
            if response.status_code == 202:
                print(f"⏳ 等待响应 (最多 {wait_timeout} 秒)...")
                
                # 等待匹配的响应
                start = time.time()
                while time.time() - start < wait_timeout:
                    try:
                        msg = self.response_queue.get(timeout=0.5)
                        if msg.get('id') == msg_id:
                            return msg
                        else:
                            # 放回队列
                            self.response_queue.put(msg)
                    except queue.Empty:
                        continue
                
                print("⚠️ 等待超时")
                return None
            
            elif response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def list_tools(self):
        """列出工具"""
        return self.send_request("tools/list", wait_timeout=30)
    
    def call_tool(self, name, arguments):
        """调用工具"""
        return self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        }, wait_timeout=60)
    
    def stop(self):
        """停止"""
        self.running = False


def main():
    print("="*70)
    print("即梦 MCP - Logo 生成测试")
    print("="*70)
    
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
    
    # 配置
    config = {
        "base_url": jimeng_cfg.get("mcp_url", "http://mcptest013.sitmcp.kaleido.guru/sse"),
        "headers": {
            "emcp-key": jimeng_cfg.get("emcp_key"),
            "emcp-usercode": jimeng_cfg.get("emcp_usercode")
        }
    }
    
    client = JimengMCPClient(config['base_url'], config['headers'])
    
    # 启动 SSE 监听
    sse_thread = client.start_sse_listener()
    
    # 等待 session
    print("\n⏳ 等待 session...")
    if not client.wait_for_session(timeout=15):
        print("❌ 无法获取 session")
        return
    
    print(f"✅ Session 就绪: {client.session_id}")
    
    # 等待连接稳定
    time.sleep(2)
    
    try:
        # 1. 获取工具列表
        print("\n" + "="*70)
        print("步骤 1: 获取可用工具")
        print("="*70)
        
        tools_result = client.list_tools()
        
        if not tools_result:
            print("❌ 无法获取工具列表")
            return
        
        print(f"\n完整响应: {json.dumps(tools_result, ensure_ascii=False, indent=2)}")
        
        # 提取工具列表
        if 'result' in tools_result:
            tools = tools_result['result'].get('tools', [])
        elif 'tools' in tools_result:
            tools = tools_result['tools']
        else:
            print("❌ 无法解析工具列表")
            return
        
        print(f"\n✅ 找到 {len(tools)} 个工具:\n")
        
        for i, tool in enumerate(tools, 1):
            name = tool.get('name', '未知')
            desc = tool.get('description', '无描述')
            print(f"{i}. [{name}]")
            print(f"   {desc}")
            
            # 显示参数
            schema = tool.get('inputSchema', {})
            if schema:
                props = schema.get('properties', {})
                if props:
                    print(f"   参数:")
                    for prop_name, prop_info in props.items():
                        prop_type = prop_info.get('type', 'any')
                        prop_desc = prop_info.get('description', '')
                        print(f"     - {prop_name} ({prop_type}): {prop_desc}")
            print()
        
        # 2. 查找图片生成工具
        print("="*70)
        print("步骤 2: 查找图片生成工具")
        print("="*70)
        
        keywords = ['image', 'logo', 'generate', 'create', 'draw', 'paint', 'picture', 
                   '生成', '图片', '绘制', '图像', 'dalle', 'diffusion', 'stability']
        
        image_tools = []
        for tool in tools:
            tool_name = tool.get('name', '').lower()
            tool_desc = tool.get('description', '').lower()
            
            if any(kw in tool_name or kw in tool_desc for kw in keywords):
                image_tools.append(tool)
        
        if not image_tools:
            print("\n⚠️ 未找到图片生成工具")
            print("\n可用工具列表:")
            for tool in tools:
                print(f"  - {tool.get('name')}")
            return
        
        print(f"\n✅ 找到 {len(image_tools)} 个图片生成工具:")
        for tool in image_tools:
            print(f"  - {tool.get('name')}: {tool.get('description', '')}")
        
        # 使用第一个
        selected_tool = image_tools[0]
        tool_name = selected_tool['name']
        
        # 3. 生成 Logo
        print("\n" + "="*70)
        print(f"步骤 3: 使用 [{tool_name}] 生成 Logo")
        print("="*70)
        
        # 分析参数
        schema = selected_tool.get('inputSchema', {})
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        print(f"\n工具参数:")
        for prop in properties:
            is_req = " [必需]" if prop in required else ""
            print(f"  - {prop}{is_req}: {properties[prop].get('description', '')}")
        
        # 构建参数
        prompt = "EMCPFlow - 一个现代化的 MCP 包管理和发布工具的 logo 图标,简洁专业,包含流动的数据和连接元素,蓝色渐变,扁平化设计风格,白色背景"
        
        arguments = {}
        
        # 智能填充
        for prop_name in properties:
            prop_lower = prop_name.lower()
            
            if 'prompt' in prop_lower or 'description' in prop_lower or '描述' in prop_name or 'text' in prop_lower:
                arguments[prop_name] = prompt
            elif 'size' in prop_lower or '尺寸' in prop_name or 'dimension' in prop_lower:
                arguments[prop_name] = "1024x1024"
            elif 'width' in prop_lower:
                arguments[prop_name] = 1024
            elif 'height' in prop_lower:
                arguments[prop_name] = 1024
            elif 'style' in prop_lower or '风格' in prop_name:
                arguments[prop_name] = "minimalist"
            elif 'quality' in prop_lower or '质量' in prop_name:
                arguments[prop_name] = "hd"
            elif 'model' in prop_lower or '模型' in prop_name:
                arguments[prop_name] = "dall-e-3"
        
        print(f"\n生成参数:")
        print(json.dumps(arguments, ensure_ascii=False, indent=2))
        
        print(f"\n🎨 开始生成 Logo...")
        
        result = client.call_tool(tool_name, arguments)
        
        if not result:
            print("❌ 生成失败")
            return
        
        print("\n" + "="*70)
        print("✅ 生成完成!")
        print("="*70)
        
        print(f"\n完整结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 提取并保存图片
        if 'result' in result:
            result_data = result['result']
            
            # MCP 工具调用结果通常在 content 中
            if isinstance(result_data, dict) and 'content' in result_data:
                content_items = result_data['content']
                
                for item in content_items:
                    item_type = item.get('type')
                    
                    if item_type == 'image':
                        # 图片内容
                        img_data = item.get('data', '')
                        
                        if img_data:
                            import base64
                            
                            # 处理 base64 或 data URL
                            if img_data.startswith('data:image'):
                                img_data = img_data.split(',', 1)[1]
                            
                            try:
                                img_bytes = base64.b64decode(img_data)
                                filename = 'emcpflow_logo_jimeng.png'
                                with open(filename, 'wb') as f:
                                    f.write(img_bytes)
                                print(f"\n💾 Logo 已保存: {filename}")
                            except Exception as e:
                                print(f"保存图片失败: {e}")
                    
                    elif item_type == 'text':
                        text = item.get('text', '')
                        print(f"\n📝 文本信息: {text}")
                        
                        # 检查是否包含 URL
                        if 'http' in text:
                            print(f"\n🔗 图片 URL: {text}")
            
            # 直接包含 URL 的情况
            elif isinstance(result_data, str) and 'http' in result_data:
                print(f"\n🔗 图片 URL: {result_data}")
        
    finally:
        print("\n关闭连接...")
        client.stop()
        time.sleep(1)


if __name__ == "__main__":
    main()


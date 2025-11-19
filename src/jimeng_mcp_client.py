"""即梦MCP客户端 - 用于生成图片（SSE方式）"""

import requests
import json
from typing import Optional
import time
import uuid

try:
    from sseclient import SSEClient
    HAS_SSE_CLIENT = True
except ImportError:
    HAS_SSE_CLIENT = False
    print("⚠️ sseclient-py 未安装，运行: pip install sseclient-py")


class JimengLogger:
    """即梦MCP日志记录器"""
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


class JimengMCPClient:
    """即梦MCP服务客户端 - 通过SSE协议调用"""
    
    def __init__(
        self,
        sse_url: str,
        emcp_key: str,
        emcp_usercode: str
    ):
        """
        初始化即梦MCP客户端
        
        Args:
            sse_url: SSE服务地址
            emcp_key: EMCP密钥（必须在配置文件中设置）
            emcp_usercode: EMCP用户码（必须在配置文件中设置）
        """
        if not emcp_key or not emcp_usercode:
            raise ValueError("emcp_key 和 emcp_usercode 不能为空，请在配置文件中设置")
        
        self.sse_url = sse_url
        self.headers = {
            "emcp-key": emcp_key,
            "emcp-usercode": emcp_usercode,
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache"
        }
        self.session = None
    
    def call_mcp_tool(self, tool_name: str, arguments: dict, timeout: int = 120) -> Optional[dict]:
        """
        通过SSE调用MCP工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            timeout: 超时时间（秒）
        
        Returns:
            工具返回结果或None
        """
        try:
            JimengLogger.log(f"\n{'='*70}")
            JimengLogger.log(f"📤 通过SSE调用即梦MCP工具: {tool_name}")
            JimengLogger.log(f"📋 SSE URL: {self.sse_url}")
            JimengLogger.log(f"📋 参数: {json.dumps(arguments, ensure_ascii=False)}")
            JimengLogger.log(f"{'='*70}\n")
            
            # 生成请求ID
            request_id = str(uuid.uuid4())
            
            # 构建MCP工具调用消息
            mcp_message = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            JimengLogger.log(f"📤 MCP消息: {json.dumps(mcp_message, ensure_ascii=False, indent=2)}")
            
            # 建立SSE连接并发送消息
            result = self._send_sse_request(mcp_message, timeout)
            
            if result:
                JimengLogger.log(f"✅ 工具调用成功")
                return result
            else:
                JimengLogger.log(f"⚠️ 工具调用失败或超时")
                return None
                
        except Exception as e:
            JimengLogger.log(f"❌ 即梦MCP调用异常: {e}")
            return None
    
    def _send_sse_request(self, mcp_message: dict, timeout: int) -> Optional[dict]:
        """
        使用 SSEClient 发送请求并等待响应
        
        Args:
            mcp_message: MCP消息
            timeout: 超时时间
        
        Returns:
            响应结果或None
        """
        if not HAS_SSE_CLIENT:
            JimengLogger.log(f"❌ sseclient-py 未安装，请运行: pip install sseclient-py")
            return None
        
        try:
            start_time = time.time()
            
            JimengLogger.log(f"📡 建立SSE连接: {self.sse_url}")
            
            # 方法1: 先POST发送消息，然后监听SSE
            # 尝试发送初始化消息
            init_response = requests.post(
                self.sse_url,
                headers={**self.headers, 'Content-Type': 'application/json'},
                json={'method': 'initialize', 'params': {}},
                timeout=10
            )
            
            JimengLogger.log(f"初始化响应: {init_response.status_code}")
            
            # 使用 SSEClient 建立连接
            client = SSEClient(
                self.sse_url,
                headers=self.headers
            )
            
            JimengLogger.log(f"✅ SSE客户端已创建，开始监听事件...")
            
            # 发送工具调用请求（通过POST到特定端点或通过SSE消息）
            # 尝试通过另一个端点发送
            call_url = self.sse_url.replace('/sse', '/call')
            try:
                JimengLogger.log(f"📤 发送工具调用到: {call_url}")
                call_response = requests.post(
                    call_url,
                    headers={**self.headers, 'Content-Type': 'application/json'},
                    json=mcp_message,
                    timeout=5
                )
                JimengLogger.log(f"   调用响应: {call_response.status_code}")
            except:
                pass
            
            # 监听SSE事件
            for event in client.events():
                # 检查超时
                if time.time() - start_time > timeout:
                    JimengLogger.log(f"⚠️ 超时 ({timeout}秒)")
                    client.close()
                    break
                
                JimengLogger.log(f"📨 收到事件 [{event.event}]: {event.data[:200]}")
                
                try:
                    # 解析事件数据
                    event_data = json.loads(event.data)
                    
                    # 检查是否是工具调用的响应
                    if event_data.get('id') == mcp_message['id']:
                        result = event_data.get('result')
                        if result:
                            JimengLogger.log(f"✅ 获得工具响应")
                            client.close()
                            return result
                    
                    # 或者检查其他可能的响应格式
                    if 'content' in event_data or 'image_url' in event_data:
                        JimengLogger.log(f"✅ 获得图片响应")
                        client.close()
                        return event_data
                        
                except json.JSONDecodeError:
                    JimengLogger.log(f"⚠️ JSON解析失败: {event.data[:100]}")
                except Exception as e:
                    JimengLogger.log(f"⚠️ 事件处理异常: {e}")
            
            return None
            
        except Exception as e:
            JimengLogger.log(f"❌ SSE连接异常: {e}")
            return None
    
    def generate_logo(
        self,
        prompt: str,
        package_name: str = "MCP"
    ) -> Optional[str]:
        """
        使用即梦MCP生成Logo图片
        
        Args:
            prompt: 图片生成提示词
            package_name: 包名（用于默认提示词）
        
        Returns:
            生成的图片URL或None（注意：这是即梦返回的URL，还需要上传到EMCP）
        """
        try:
            # 构建提示词
            if not prompt:
                prompt = f"""
Create a modern, minimalist, professional logo for software package "{package_name}".
Requirements:
- Style: flat design, simple, clean
- Theme: technology, software, modern
- Colors: 2-3 colors, professional color scheme
- Format: square 512x512, transparent or white background
- Icon should represent the package purpose
- Must be simple and recognizable
"""
            
            JimengLogger.log(f"\n🎨 使用即梦MCP生成Logo...")
            JimengLogger.log(f"   提示词: {prompt[:100]}...")
            
            # 调用即梦图片生成工具
            result = self.call_mcp_tool(
                tool_name="jimeng-v40-generate",  # ✅ 正确的工具名
                arguments={
                    "prompt": prompt
                },
                timeout=90  # 图片生成可能需要较长时间
            )
            
            if result:
                JimengLogger.log(f"   📋 即梦MCP返回数据: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")
                
                # 提取图片URL（尝试多种可能的字段）
                image_url = None
                
                # 常见的响应格式
                if 'content' in result:
                    # MCP标准响应格式
                    content = result.get('content', [])
                    if isinstance(content, list) and len(content) > 0:
                        first_item = content[0]
                        if isinstance(first_item, dict):
                            # 可能在 text 或 data 字段
                            image_url = first_item.get('text') or first_item.get('data') or first_item.get('url')
                
                # 其他可能的字段
                if not image_url:
                    image_url = (
                        result.get('image_url') or 
                        result.get('url') or 
                        result.get('data', {}).get('url') or
                        result.get('result', {}).get('url')
                    )
                
                if image_url:
                    JimengLogger.log(f"   ✅ 图片生成成功: {image_url}")
                    return image_url
                else:
                    JimengLogger.log(f"   ⚠️ 响应中未找到图片URL")
                    JimengLogger.log(f"   完整响应: {json.dumps(result, ensure_ascii=False)}")
            
            JimengLogger.log(f"   ⚠️ 即梦MCP生成失败")
            return None
            
        except Exception as e:
            JimengLogger.log(f"   ❌ 即梦MCP异常: {e}")
            return None
    
    def generate_package_logo(
        self,
        package_name: str,
        package_type: str,
        description: str = ""
    ) -> Optional[str]:
        """
        为包生成专属Logo
        
        Args:
            package_name: 包名
            package_type: 包类型 (pypi/npm/docker)
            description: 包描述
        
        Returns:
            图片URL或None
        """
        # 根据包类型和描述构建更精准的提示词
        type_themes = {
            'pypi': 'Python, snake, data science, blue and yellow',
            'npm': 'JavaScript, Node.js, red, modern',
            'docker': 'Container, whale, blue, DevOps'
        }
        
        theme = type_themes.get(package_type, 'technology, modern')
        
        prompt = f"""
Create a professional logo for "{package_name}" - a {package_type} package.
Description: {description[:100] if description else 'Software tool'}
Theme: {theme}
Style: flat design, minimalist, modern
Colors: professional color scheme (2-3 colors)
Format: square 512x512, clean background
Must include: simple icon representing the package purpose
"""
        
        return self.generate_logo(prompt, package_name)


# 测试代码
if __name__ == '__main__':
    client = JimengMCPClient()
    
    # 测试生成Logo
    logo_url = client.generate_package_logo(
        package_name="test-package",
        package_type="pypi",
        description="A test package for data analysis"
    )
    
    if logo_url:
        print(f"生成的Logo: {logo_url}")
    else:
        print("生成失败")


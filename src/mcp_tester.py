"""
MCP 模板测试器
自动测试 MCP 服务的所有工具，生成测试报告
"""

import requests
import json
import time
import threading
import queue
from typing import Dict, List, Optional
from datetime import datetime


class MCPTesterLogger:
    """测试日志记录器"""
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


class MCPClient:
    """MCP 客户端 - SSE 通信"""
    
    def __init__(self, sse_url: str, headers: Dict):
        self.sse_url = sse_url
        self.headers = headers
        self.session_id = None
        self.message_endpoint = None
        self.response_queue = queue.Queue()
        self.running = False
        
    def start_sse_listener(self):
        """启动 SSE 监听器"""
        self.running = True
        thread = threading.Thread(target=self._sse_listener, daemon=True)
        thread.start()
        return thread
    
    def _sse_listener(self):
        """SSE 监听器线程"""
        try:
            response = requests.get(self.sse_url, headers=self.headers, stream=True, timeout=None)
            
            for line in response.iter_lines():
                if not self.running:
                    break
                
                if line:
                    line = line.decode('utf-8')
                    
                    if line.startswith('data:'):
                        data = line[5:].strip()
                        
                        if data.startswith('/message?sessionId='):
                            self.message_endpoint = data
                            self.session_id = data.split('=')[1]
                        else:
                            try:
                                json_data = json.loads(data)
                                self.response_queue.put(json_data)
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            MCPTesterLogger.log(f"   ❌ SSE 错误: {e}")
    
    def wait_for_session(self, timeout=10):
        """等待获取 session ID"""
        start = time.time()
        while not self.session_id and time.time() - start < timeout:
            time.sleep(0.1)
        return self.session_id is not None
    
    def send_request(self, method, params=None, wait_timeout=30):
        """发送 MCP 请求"""
        if not self.message_endpoint:
            return None
        
        url = f"{self.sse_url.replace('/sse', '')}{self.message_endpoint}"
        
        msg_id = int(time.time() * 1000)
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": msg_id
        }
        
        if params:
            payload["params"] = params
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 202:
                start = time.time()
                while time.time() - start < wait_timeout:
                    try:
                        msg = self.response_queue.get(timeout=0.5)
                        if msg.get('id') == msg_id:
                            return msg
                        else:
                            self.response_queue.put(msg)
                    except queue.Empty:
                        continue
                return None
            elif response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            return None
    
    def list_tools(self):
        """获取工具列表"""
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


class MCPTester:
    """MCP 模板测试器"""
    
    def __init__(self, emcp_manager, ai_generator=None):
        """
        初始化测试器
        
        Args:
            emcp_manager: EMCP 管理器实例
            ai_generator: AITemplateGenerator 实例（包含 client 和 deployment_name）
        """
        self.emcp_manager = emcp_manager
        self.ai_generator = ai_generator
        
        # 提取 OpenAI 客户端和 deployment
        if ai_generator:
            self.openai_client = getattr(ai_generator, 'client', None)
            self.deployment_name = getattr(ai_generator, 'deployment_name', 'gpt-4')
        else:
            self.openai_client = None
            self.deployment_name = None
    
    def test_template(
        self,
        template_id: str,
        user_id: int = 51
    ) -> Dict:
        """
        完整测试流程
        
        Args:
            template_id: 模板 ID
            user_id: 用户 ID
        
        Returns:
            测试报告
        """
        MCPTesterLogger.log("\n" + "="*70)
        MCPTesterLogger.log("🧪 开始 MCP 模板测试流程")
        MCPTesterLogger.log("="*70)
        
        report = {
            "template_id": template_id,
            "test_time": datetime.now().isoformat(),
            "steps": [],
            "success": False,
            "error": None
        }
        
        try:
            # 步骤 1: 启动模板，创建 pod server
            MCPTesterLogger.log("\n📋 步骤 1/6: 启动模板，创建 Pod Server...")
            server_result = self._create_mcp_server(template_id, user_id)
            report['steps'].append({"step": 1, "name": "创建服务器", "success": server_result is not None})
            
            if not server_result:
                raise Exception("创建 MCP Server 失败")
            
            MCPTesterLogger.log("   ✅ Pod Server 已创建")
            
            # 步骤 2: 修改模板进入测试状态
            MCPTesterLogger.log("\n📋 步骤 2/6: 修改模板进入测试状态...")
            publish_result = self._set_template_status(template_id, 3)  # 3=测试状态
            report['steps'].append({"step": 2, "name": "进入测试状态", "success": publish_result})
            
            if not publish_result:
                raise Exception("修改模板状态失败")
            
            MCPTesterLogger.log("   ✅ 模板已进入测试状态")
            
            # 步骤 3: 获取 pod server id
            MCPTesterLogger.log("\n📋 步骤 3/6: 获取 Pod Server ID...")
            server_id = self._get_mcp_server_id(template_id)
            report['server_id'] = server_id
            report['steps'].append({"step": 3, "name": "获取服务器ID", "success": server_id is not None})
            
            if not server_id:
                raise Exception("获取 Server ID 失败")
            
            MCPTesterLogger.log(f"   ✅ Server ID: {server_id}")
            
            # 步骤 4: 获取 MCP 连接配置
            MCPTesterLogger.log("\n📋 步骤 4/6: 获取 MCP 连接配置...")
            mcp_config = self._get_mcp_config(server_id)
            report['mcp_config'] = mcp_config
            report['steps'].append({"step": 4, "name": "获取连接配置", "success": mcp_config is not None})
            
            if not mcp_config:
                raise Exception("获取 MCP 配置失败")
            
            MCPTesterLogger.log(f"   ✅ URL: {mcp_config['url']}")
            
            # 步骤 4.5: 健康检查 - 等待服务启动并验证可访问
            MCPTesterLogger.log("\n📋 步骤 4.5/6: 健康检查 - 等待服务启动...")
            if not self._wait_for_server_ready(mcp_config, template_id, server_id):
                raise Exception("MCP Server 启动失败或无法连接")
            
            MCPTesterLogger.log("   ✅ Server 已就绪")
            
            # 步骤 5: 测试所有工具
            MCPTesterLogger.log("\n📋 步骤 5/6: 测试所有 MCP 工具...")
            tools_report = self._test_all_tools(mcp_config)
            report['tools_report'] = tools_report
            report['steps'].append({
                "step": 5,
                "name": "测试工具",
                "success": tools_report['success'],
                "tested": tools_report['total_tools'],
                "passed": tools_report['passed_tools']
            })
            
            # 步骤 6: 恢复发布状态
            MCPTesterLogger.log("\n📋 步骤 6/6: 恢复模板发布状态...")
            publish_result = self._set_template_status(template_id, 2)  # 2=发布状态
            report['steps'].append({"step": 6, "name": "恢复发布状态", "success": publish_result})
            
            if publish_result:
                MCPTesterLogger.log("   ✅ 模板已恢复发布状态")
            
            # 测试完成
            if tools_report.get('success'):
                report['success'] = True
            
            MCPTesterLogger.log("\n" + "="*70)
            MCPTesterLogger.log("✅ 测试完成！")
            MCPTesterLogger.log("="*70)
            
            return report
            
        except Exception as e:
            report['error'] = str(e)
            MCPTesterLogger.log(f"\n❌ 测试失败: {e}")
            return report
    
    def _create_mcp_server(self, template_id: str, user_id: int) -> Optional[Dict]:
        """创建 MCP Server"""
        url = f"{self.emcp_manager.base_url}/api/Service/create_mcp_server"
        
        headers = {
            'token': self.emcp_manager.session_key,
            'language': 'ch_cn',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "template_id": template_id,
            "publish_type": 1,  # Preset
            "uid": user_id
        }
        
        MCPTesterLogger.log(f"   📤 POST {url}")
        MCPTesterLogger.log(f"   📦 Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()
            
            MCPTesterLogger.log(f"   📥 响应: {response.status_code}")
            MCPTesterLogger.log(f"   📋 {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if data.get('err_code') == 0:
                return data
            else:
                MCPTesterLogger.log(f"   ❌ 错误: {data.get('err_message')}")
                return None
                
        except Exception as e:
            MCPTesterLogger.log(f"   ❌ 请求失败: {e}")
            return None
    
    def _set_template_status(self, template_id: str, status: int) -> bool:
        """
        设置模板状态
        
        Args:
            template_id: 模板 ID
            status: 2=Dummy(实时/发布), 3=测试
        """
        url = f"{self.emcp_manager.base_url}/api/Template/publish_mcp_template/{template_id}/{status}"
        
        headers = {
            'token': self.emcp_manager.session_key,
            'language': 'ch_cn'
        }
        
        status_name = {2: "发布状态(Dummy)", 3: "测试状态"}
        MCPTesterLogger.log(f"   📤 PUT {url}")
        MCPTesterLogger.log(f"   📝 修改为: {status_name.get(status, str(status))}")
        
        try:
            response = requests.put(url, headers=headers, timeout=30)
            data = response.json()
            
            MCPTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                return True
            else:
                MCPTesterLogger.log(f"   ❌ 错误: {data.get('err_message')}")
                return False
                
        except Exception as e:
            MCPTesterLogger.log(f"   ❌ 请求失败: {e}")
            return False
    
    def _get_mcp_server_id(self, template_id: str) -> Optional[str]:
        """获取 MCP Server ID"""
        url = f"{self.emcp_manager.base_url}/api/Service/get_mcp_main_server_id/{template_id}"
        
        headers = {
            'token': self.emcp_manager.session_key,
            'language': 'ch_cn'
        }
        
        MCPTesterLogger.log(f"   📤 GET {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            data = response.json()
            
            MCPTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                server_id = data.get('body')
                return server_id
            else:
                MCPTesterLogger.log(f"   ❌ 错误: {data.get('err_message')}")
                return None
                
        except Exception as e:
            MCPTesterLogger.log(f"   ❌ 请求失败: {e}")
            return None
    
    def _get_mcp_config(self, server_id: str) -> Optional[Dict]:
        """获取 MCP 连接配置"""
        url = f"{self.emcp_manager.base_url}/api/Service/generate_mcp_server/{server_id}"
        
        headers = {
            'token': self.emcp_manager.session_key,
            'language': 'ch_cn'
        }
        
        MCPTesterLogger.log(f"   📤 GET {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            data = response.json()
            
            MCPTesterLogger.log(f"   📥 响应: {response.status_code}")
            
            if data.get('err_code') == 0:
                body = data.get('body', {})
                # body 结构: {"server_name": {"transport": "sse", "url": "...", "headers": {...}}}
                for key, config in body.items():
                    if isinstance(config, dict) and 'url' in config:
                        return config
                return None
            else:
                MCPTesterLogger.log(f"   ❌ 错误: {data.get('err_message')}")
                return None
                
        except Exception as e:
            MCPTesterLogger.log(f"   ❌ 请求失败: {e}")
            return None
    
    def _wait_for_server_ready(self, mcp_config: Dict, template_id: str, server_id: str, max_wait_seconds: int = 60) -> bool:
        """
        等待 MCP Server 启动并就绪
        
        Args:
            mcp_config: MCP 连接配置
            template_id: 模板 ID
            server_id: Server ID
            max_wait_seconds: 最大等待秒数
        
        Returns:
            True 如果服务就绪，False 如果失败
        """
        MCPTesterLogger.log(f"   ⏳ 最多等待 {max_wait_seconds} 秒...")
        
        retry_count = 0
        max_retries = max_wait_seconds // 5  # 每5秒重试一次
        
        while retry_count < max_retries:
            retry_count += 1
            wait_time = retry_count * 5
            
            MCPTesterLogger.log(f"   ⏳ 尝试连接 ({wait_time}/{max_wait_seconds}秒)...")
            time.sleep(5)
            
            try:
                # 尝试连接
                client = MCPClient(mcp_config['url'], mcp_config.get('headers', {}))
                client.start_sse_listener()
                
                if client.wait_for_session(timeout=10):
                    MCPTesterLogger.log(f"   ✅ 连接成功!")
                    client.stop()
                    return True
                else:
                    MCPTesterLogger.log(f"   ⚠️ 连接超时，继续重试...")
                    client.stop()
            except Exception as e:
                MCPTesterLogger.log(f"   ⚠️ 连接错误: {e}")
        
        # 所有重试都失败了
        MCPTesterLogger.log(f"\n   ❌ Server 在 {max_wait_seconds} 秒内未能启动")
        MCPTesterLogger.log(f"   💡 可能原因:")
        MCPTesterLogger.log(f"      1. 包名错误或包不存在")
        MCPTesterLogger.log(f"      2. npm/pypi 安装失败")
        MCPTesterLogger.log(f"      3. 启动命令错误")
        MCPTesterLogger.log(f"      4. 依赖安装失败")
        MCPTesterLogger.log(f"\n   🔍 建议检查:")
        MCPTesterLogger.log(f"      - 包是否已成功发布到 npm/pypi")
        MCPTesterLogger.log(f"      - 包名是否正确（无 @scope/ 前缀，除非真的有）")
        MCPTesterLogger.log(f"      - GitHub Actions 是否构建成功")
        
        return False
    
    def _test_all_tools(self, mcp_config: Dict) -> Dict:
        """测试所有 MCP 工具"""
        MCPTesterLogger.log(f"\n{'='*70}")
        MCPTesterLogger.log("🔧 开始测试 MCP 工具")
        MCPTesterLogger.log(f"{'='*70}")
        
        report = {
            "success": False,
            "total_tools": 0,
            "passed_tools": 0,
            "failed_tools": 0,
            "tools": []
        }
        
        try:
            # 创建 MCP 客户端
            client = MCPClient(mcp_config['url'], mcp_config.get('headers', {}))
            
            MCPTesterLogger.log("   🔌 连接 MCP 服务...")
            client.start_sse_listener()
            
            if not client.wait_for_session(timeout=15):
                MCPTesterLogger.log("   ❌ 连接失败")
                return report
            
            MCPTesterLogger.log(f"   ✅ 连接成功: {client.session_id}")
            time.sleep(1)
            
            # 获取工具列表
            MCPTesterLogger.log("\n   📋 获取工具列表...")
            tools_result = client.list_tools()
            
            if not tools_result or 'result' not in tools_result:
                MCPTesterLogger.log("   ❌ 无法获取工具列表")
                return report
            
            tools = tools_result['result'].get('tools', [])
            report['total_tools'] = len(tools)
            
            MCPTesterLogger.log(f"   ✅ 找到 {len(tools)} 个工具")
            
            # ⭐ 检测并记录 LLM 配置（只显示一次）
            if self.openai_client:
                MCPTesterLogger.log(f"\n   🤖 LLM 配置检测:")
                try:
                    from openai import AzureOpenAI
                    if isinstance(self.openai_client, AzureOpenAI):
                        MCPTesterLogger.log(f"      ✅ 类型: Azure OpenAI")
                        
                        if hasattr(self.openai_client, '_base_url'):
                            endpoint = str(self.openai_client._base_url)
                            MCPTesterLogger.log(f"      📍 Endpoint: {endpoint}")
                        
                        if hasattr(self.openai_client, 'api_key'):
                            key = str(self.openai_client.api_key)
                            MCPTesterLogger.log(f"      🔑 API Key: {key[:10]}...{key[-4:] if len(key) > 14 else ''}")
                        
                        # 检查 deployment 名称
                        deployment = None
                        for attr in ['deployment_name', 'model', '_deployment_name']:
                            if hasattr(self.openai_client, attr):
                                deployment = getattr(self.openai_client, attr)
                                break
                        
                        if deployment:
                            MCPTesterLogger.log(f"      🎯 Deployment: {deployment}")
                        else:
                            MCPTesterLogger.log(f"      ⚠️ Deployment: 未设置（可能导致 404 错误）")
                        
                        MCPTesterLogger.log(f"      💡 如果遇到 404 DeploymentNotFound 错误:")
                        MCPTesterLogger.log(f"         1. 检查 Azure OpenAI deployment 是否存在")
                        MCPTesterLogger.log(f"         2. 确认 deployment 名称拼写正确")
                        MCPTesterLogger.log(f"         3. 确认 endpoint URL 正确")
                    else:
                        MCPTesterLogger.log(f"      ℹ️ 类型: {type(self.openai_client).__name__}")
                except Exception as e:
                    MCPTesterLogger.log(f"      ⚠️ 配置检测失败: {e}")
            else:
                MCPTesterLogger.log(f"\n   ℹ️ 未配置 LLM，将使用简单默认值生成测试参数")
            
            # 测试每个工具
            for i, tool in enumerate(tools, 1):
                tool_name = tool.get('name')
                tool_desc = tool.get('description', '')
                
                MCPTesterLogger.log(f"\n   🔧 测试 {i}/{len(tools)}: {tool_name}")
                MCPTesterLogger.log(f"      描述: {tool_desc[:60]}...")
                
                # 生成测试参数
                test_args = self._generate_test_arguments(tool, self.openai_client)
                
                if test_args is None:
                    MCPTesterLogger.log(f"      ⚠️ 跳过（无法生成测试参数）")
                    report['tools'].append({
                        "name": tool_name,
                        "status": "skipped",
                        "reason": "无法生成测试参数"
                    })
                    continue
                
                MCPTesterLogger.log(f"      📝 测试参数: {json.dumps(test_args, ensure_ascii=False)[:80]}...")
                
                # 调用工具
                MCPTesterLogger.log(f"      ⏳ 调用中...")
                result = client.call_tool(tool_name, test_args)
                
                # 检查结果
                if not result:
                    # 超时或无响应
                    MCPTesterLogger.log(f"      ⚠️ 超时或无响应")
                    report['failed_tools'] += 1
                    report['tools'].append({
                        "name": tool_name,
                        "status": "timeout",
                        "arguments": test_args
                    })
                elif 'error' in result:
                    # 有错误
                    error_msg = result['error'].get('message', str(result['error']))
                    MCPTesterLogger.log(f"      ❌ 测试失败: {error_msg[:80]}")
                    report['failed_tools'] += 1
                    report['tools'].append({
                        "name": tool_name,
                        "status": "failed",
                        "arguments": test_args,
                        "error": result['error']
                    })
                elif 'result' in result:
                    # 有返回结果 - 进一步检查结果内容
                    result_content = result['result']
                    
                    # 检查结果中是否包含错误标识
                    result_str = str(result_content).lower()
                    error_indicators = ['error', 'exception', 'failed', 'not found', '错误', '失败', '未找到']
                    
                    has_error = any(indicator in result_str for indicator in error_indicators)
                    
                    if has_error and len(str(result_content)) < 200:  # 短错误消息
                        MCPTesterLogger.log(f"      ⚠️ 可能有错误: {str(result_content)[:80]}")
                        MCPTesterLogger.log(f"      📝 标记为部分通过")
                        report['passed_tools'] += 0.5  # 算半个通过
                        report['tools'].append({
                            "name": tool_name,
                            "status": "partial",  # 部分通过
                            "arguments": test_args,
                            "result": result_content,
                            "warning": "结果中可能包含错误信息"
                        })
                    else:
                        MCPTesterLogger.log(f"      ✅ 测试通过")
                        report['passed_tools'] += 1
                        report['tools'].append({
                            "name": tool_name,
                            "status": "passed",
                            "arguments": test_args,
                            "result": result_content
                        })
                else:
                    # 未知响应格式
                    MCPTesterLogger.log(f"      ⚠️ 未知响应格式")
                    report['failed_tools'] += 1
                    report['tools'].append({
                        "name": tool_name,
                        "status": "unknown",
                        "arguments": test_args,
                        "raw_result": result
                    })
            
            # 停止客户端
            client.stop()
            
            # 计算成功率
            if report['total_tools'] > 0:
                success_rate = (report['passed_tools'] / report['total_tools']) * 100
                report['success_rate'] = success_rate
                report['success'] = success_rate >= 50  # 50%以上算成功
                
                MCPTesterLogger.log(f"\n{'='*70}")
                MCPTesterLogger.log(f"📊 测试统计")
                MCPTesterLogger.log(f"{'='*70}")
                MCPTesterLogger.log(f"   总工具数: {report['total_tools']}")
                MCPTesterLogger.log(f"   ✅ 通过: {report['passed_tools']}")
                MCPTesterLogger.log(f"   ❌ 失败: {report['failed_tools']}")
                MCPTesterLogger.log(f"   📊 成功率: {success_rate:.1f}%")
            
            return report
            
        except Exception as e:
            report['error'] = str(e)
            MCPTesterLogger.log(f"\n❌ 测试异常: {e}")
            return report
    
    def _generate_test_arguments(self, tool: Dict, openai_client) -> Optional[Dict]:
        """
        生成工具的测试参数
        
        使用 LLM 根据工具的 inputSchema 生成合理的测试参数
        """
        schema = tool.get('inputSchema', {})
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        # 如果没有必需参数，返回空字典
        if not required:
            return {}
        
        # 尝试使用 LLM 生成
        if openai_client:
            try:
                prompt = f"""
Generate test arguments for an MCP tool.

Tool name: {tool.get('name')}
Tool description: {tool.get('description', '')}

Input schema:
{json.dumps(schema, indent=2)}

Required parameters: {', '.join(required)}

Please generate reasonable test values for all required parameters.
Return ONLY a JSON object with the parameter values, no explanation.

Example format:
{{"param1": "test value", "param2": 123}}
"""
                
                # 使用正确的 deployment_name ⭐
                model_name = self.deployment_name if self.deployment_name else 'gpt-4'
                
                response = openai_client.chat.completions.create(
                    model=model_name,  # ⭐ 使用正确的 deployment
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates test data."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                content = response.choices[0].message.content.strip()
                # 提取 JSON
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0].strip()
                
                test_args = json.loads(content)
                return test_args
                
            except Exception as e:
                MCPTesterLogger.log(f"      ⚠️ LLM 生成失败: {e}")
        
        # 回退方案：使用简单的默认值
        test_args = {}
        for param_name in required:
            param_info = properties.get(param_name, {})
            param_type = param_info.get('type', 'string')
            
            if param_type == 'string':
                test_args[param_name] = "test"
            elif param_type == 'number' or param_type == 'integer':
                test_args[param_name] = 1
            elif param_type == 'boolean':
                test_args[param_name] = True
            elif param_type == 'array':
                test_args[param_name] = []
            elif param_type == 'object':
                test_args[param_name] = {}
        
        return test_args if test_args else None
    
    def generate_test_report_html(self, report: Dict, output_file: str = "mcp_test_report.html", share_to_edgeone: bool = True):
        """
        生成 HTML 测试报告
        
        Args:
            report: 测试报告
            output_file: 本地保存路径
            share_to_edgeone: 是否分享到 EdgeOne Pages (生成公开链接)
        """
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP 测试报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #0066cc; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .summary {{ background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .failed {{ color: #dc3545; font-weight: bold; }}
        .skipped {{ color: #ffc107; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #0066cc; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .status-badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; }}
        .badge-passed {{ background: #28a745; color: white; }}
        .badge-failed {{ background: #dc3545; color: white; }}
        .badge-skipped {{ background: #ffc107; color: white; }}
        .badge-partial {{ background: #ff9800; color: white; }}
        .badge-unknown {{ background: #9e9e9e; color: white; }}
        .progress-bar {{ background: #e0e0e0; height: 30px; border-radius: 15px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ background: linear-gradient(to right, #28a745, #0066cc); height: 100%; text-align: center; line-height: 30px; color: white; font-weight: bold; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 MCP 模板测试报告</h1>
        
        <div class="summary">
            <h2>📊 测试概览</h2>
            <p><strong>模板 ID:</strong> {report.get('template_id', 'N/A')}</p>
            <p><strong>测试时间:</strong> {report.get('test_time', 'N/A')}</p>
            <p><strong>Server ID:</strong> {report.get('server_id', 'N/A')}</p>
            <p><strong>总体状态:</strong> <span class="{'success' if report.get('success') else 'failed'}">{'✅ 通过' if report.get('success') else '❌ 失败'}</span></p>
            
            <h3>工具测试统计</h3>
            <p><strong>总工具数:</strong> {report.get('tools_report', {}).get('total_tools', 0)}</p>
            <p><strong class="success">✅ 通过:</strong> {report.get('tools_report', {}).get('passed_tools', 0)}</p>
            <p><strong class="failed">❌ 失败:</strong> {report.get('tools_report', {}).get('failed_tools', 0)}</p>
            <p><strong>成功率:</strong> {report.get('tools_report', {}).get('success_rate', 0):.1f}%</p>
            
            <div class="progress-bar">
                <div class="progress-fill" style="width: {report.get('tools_report', {}).get('success_rate', 0)}%">
                    {report.get('tools_report', {}).get('success_rate', 0):.1f}%
                </div>
            </div>
        </div>
        
        <h2>📋 测试步骤</h2>
        <table>
            <tr>
                <th>步骤</th>
                <th>名称</th>
                <th>状态</th>
                <th>详情</th>
            </tr>
"""
        
        for step in report.get('steps', []):
            status = '✅ 成功' if step.get('success') else '❌ 失败'
            badge_class = 'badge-passed' if step.get('success') else 'badge-failed'
            details = ''
            if 'tested' in step:
                details = f"测试: {step['tested']}, 通过: {step['passed']}"
            
            html += f"""
            <tr>
                <td>{step['step']}</td>
                <td>{step['name']}</td>
                <td><span class="status-badge {badge_class}">{status}</span></td>
                <td>{details}</td>
            </tr>
"""
        
        html += """
        </table>
        
        <h2>🔧 工具测试详情</h2>
        <table>
            <tr>
                <th>工具名称</th>
                <th>状态</th>
                <th>测试参数</th>
                <th>结果/错误</th>
            </tr>
"""
        
        for tool in report.get('tools_report', {}).get('tools', []):
            status = tool.get('status')
            if status == 'passed':
                badge = '<span class="status-badge badge-passed">✅ 通过</span>'
            elif status == 'failed':
                badge = '<span class="status-badge badge-failed">❌ 失败</span>'
            elif status == 'partial':
                badge = '<span class="status-badge badge-partial">⚠️ 部分通过</span>'
            elif status == 'unknown':
                badge = '<span class="status-badge badge-unknown">❓ 未知</span>'
            else:
                badge = '<span class="status-badge badge-skipped">⏭️ 跳过</span>'
            
            args_json = json.dumps(tool.get('arguments', {}), ensure_ascii=False)[:100]
            
            result_text = ''
            if 'error' in tool:
                result_text = f"错误: {tool['error'].get('message', '')[:100]}"
            elif 'result' in tool:
                result_text = "成功"
            elif 'reason' in tool:
                result_text = tool['reason']
            
            html += f"""
            <tr>
                <td><strong>{tool.get('name')}</strong></td>
                <td>{badge}</td>
                <td><pre>{args_json}</pre></td>
                <td>{result_text}</td>
            </tr>
"""
        
        html += f"""
        </table>
        
        <h2>📝 MCP 连接配置</h2>
        <pre>{json.dumps(report.get('mcp_config', {}), indent=2, ensure_ascii=False)}</pre>
        
        <footer style="margin-top: 40px; text-align: center; color: #999; font-size: 12px;">
            <p>Generated by EMCPFlow - MCP 测试工具</p>
            <p>Made with ❤️ by 巴赫工作室 (BACH Studio)</p>
        </footer>
    </div>
</body>
</html>
"""
        
        # 保存 HTML 文件到 outputs/reports 目录
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
        
        MCPTesterLogger.log(f"\n💾 测试报告已保存到本地")
        MCPTesterLogger.log(f"   📂 文件路径: {abs_path}")
        MCPTesterLogger.log(f"   💡 可以用浏览器打开查看")
        
        # 尝试分享到 EdgeOne Pages (可选)
        if share_to_edgeone:
            MCPTesterLogger.log(f"\n🌐 尝试分享测试报告到 EdgeOne Pages...")
            edgeone_url = self._share_to_edgeone(html, output_file)
            
            if edgeone_url:
                MCPTesterLogger.log(f"   ✅ 报告已分享")
                MCPTesterLogger.log(f"   🔗 公开链接: {edgeone_url}")
                MCPTesterLogger.log(f"   💡 可以直接分享这个链接给他人")
                report['edgeone_url'] = edgeone_url
            else:
                MCPTesterLogger.log(f"   ⚠️ EdgeOne 分享失败（本地文件仍可用）")
        
        return report
    
    def _share_to_edgeone(self, html_content: str, filename: str) -> Optional[str]:
        """
        分享 HTML 到 EdgeOne Pages
        
        使用 EdgeOne Pages MCP 的 API 快速部署 HTML 内容
        参考: https://pages.edgeone.ai/zh/document/pages-mcp
        
        Args:
            html_content: HTML 内容
            filename: 文件名（用于生成友好的URL）
        
        Returns:
            公开访问链接 或 None
        """
        try:
            # EdgeOne Pages MCP API
            edgeone_api = "https://mcp-on-edge.edgeone.app/kv/set"
            
            # 从文件名提取标识（用于URL）
            import re
            file_id = re.sub(r'[^a-z0-9]', '', filename.lower().replace('.html', ''))
            
            # 添加时间戳确保唯一性
            import time
            timestamp = str(int(time.time()))[-6:]
            file_id = f"{file_id}{timestamp}"
            
            payload = {
                "key": file_id,
                "value": html_content
            }
            
            MCPTesterLogger.log(f"      📤 POST {edgeone_api}")
            MCPTesterLogger.log(f"      🔑 Key: {file_id}")
            MCPTesterLogger.log(f"      📦 大小: {len(html_content):,} 字符")
            
            # 尝试请求（忽略代理）
            response = requests.post(
                edgeone_api,
                json=payload,
                timeout=10,
                proxies={}  # ⭐ 禁用代理（使用空字典）
            )
            
            MCPTesterLogger.log(f"      📥 响应: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                MCPTesterLogger.log(f"      📋 {json.dumps(data, ensure_ascii=False)}")
                
                # EdgeOne 返回的访问链接
                if 'url' in data:
                    return data['url']
                elif 'key' in data:
                    return f"https://mcp-on-edge.edgeone.app/kv/get?key={data['key']}"
                else:
                    # 使用我们的 key 构建链接
                    return f"https://mcp-on-edge.edgeone.app/kv/get?key={file_id}"
            else:
                MCPTesterLogger.log(f"      ❌ EdgeOne 返回错误: {response.text[:200]}")
                return None
                
        except requests.exceptions.ProxyError as e:
            MCPTesterLogger.log(f"   ⚠️ 代理连接错误: {e}")
            MCPTesterLogger.log(f"   💡 可能需要关闭代理或配置网络")
            return None
        except requests.exceptions.Timeout:
            MCPTesterLogger.log(f"   ⚠️ 请求超时（网络问题）")
            return None
        except Exception as e:
            MCPTesterLogger.log(f"   ⚠️ EdgeOne 分享异常: {e}")
            MCPTesterLogger.log(f"   💡 本地文件仍然可用，可以手动分享")
            return None


# 便捷函数
def test_mcp_template(
    emcp_manager,
    template_id: str,
    user_id: int = 51,
    openai_client = None
) -> Dict:
    """
    测试 MCP 模板
    
    Args:
        emcp_manager: EMCP 管理器
        template_id: 模板 ID
        user_id: 用户 ID
        openai_client: Azure OpenAI 客户端（可选）
    
    Returns:
        测试报告
    """
    tester = MCPTester(emcp_manager, openai_client)
    report = tester.test_template(template_id, user_id)
    
    # 生成 HTML 报告
    tester.generate_test_report_html(report)
    
    return report


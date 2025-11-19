#!/usr/bin/env python3
"""
即梦 MCP Logo 生成器 - 完整集成版
根据包地址生成 Logo 并上传到 EMCP
"""

import requests
import json
import time
import threading
import queue
import base64
from typing import Optional, Dict
from src.package_fetcher import PackageFetcher


class JimengMCPClient:
    """即梦 MCP 客户端"""
    
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.session_id = None
        self.message_endpoint = None
        self.response_queue = queue.Queue()
        self.running = False
        
    def start_sse_listener(self):
        """启动 SSE 监听器线程"""
        self.running = True
        thread = threading.Thread(target=self._sse_listener, daemon=True)
        thread.start()
        return thread
    
    def _sse_listener(self):
        """SSE 监听器线程"""
        try:
            response = requests.get(self.base_url, headers=self.headers, stream=True, timeout=None)
            
            # 逐行读取 SSE 流
            for line in response.iter_lines():
                if not self.running:
                    break
                
                if line:
                    line = line.decode('utf-8')
                    
                    if line.startswith('data:'):
                        data = line[5:].strip()
                        
                        # endpoint 事件
                        if data.startswith('/message?sessionId='):
                            self.message_endpoint = data
                            self.session_id = data.split('=')[1]
                        
                        # JSON 消息
                        else:
                            try:
                                json_data = json.loads(data)
                                self.response_queue.put(json_data)
                            except json.JSONDecodeError:
                                pass
                                
        except Exception as e:
            print(f"❌ SSE 监听错误: {e}")
    
    def wait_for_session(self, timeout=10):
        """等待获取 session ID"""
        start = time.time()
        while not self.session_id and time.time() - start < timeout:
            time.sleep(0.1)
        return self.session_id is not None
    
    def send_request(self, method, params=None, wait_timeout=30):
        """发送请求"""
        if not self.message_endpoint:
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
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 202:
                # 等待匹配的响应
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
    
    def call_tool(self, name, arguments, wait_timeout=120):
        """调用工具"""
        return self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        }, wait_timeout=wait_timeout)
    
    def stop(self):
        """停止"""
        self.running = False


class JimengLogoGenerator:
    """即梦 MCP Logo 生成器"""
    
    def __init__(self, jimeng_config: Dict):
        """
        初始化
        
        Args:
            jimeng_config: {
                "base_url": "http://mcptest013.sitmcp.kaleido.guru/sse",
                "headers": {
                    "emcp-key": "xxx",
                    "emcp-usercode": "xxx"
                }
            }
        """
        self.jimeng_config = jimeng_config
        self.package_fetcher = PackageFetcher()
        
    def generate_logo_from_package(
        self,
        package_url: str,
        emcp_base_url: str = "https://sit-emcp.kaleido.guru",
        use_v40: bool = True,
        fallback_description: str = None
    ) -> Dict:
        """
        从包地址生成 Logo 并上传到 EMCP
        
        Args:
            package_url: 包地址 (PyPI/NPM/Docker)
            emcp_base_url: EMCP 平台地址
            use_v40: 是否使用即梦 4.0 (推荐)
            fallback_description: 降级描述（当包不存在时使用）
        
        Returns:
            {
                "success": True/False,
                "logo_url": "EMCP logo URL",
                "package_info": {...},
                "error": "错误信息"
            }
        """
        print("="*70)
        print("🎨 即梦 MCP Logo 生成器")
        print("="*70)
        
        try:
            # 步骤 1: 获取包信息
            print(f"\n📦 步骤 1/4: 获取包信息...")
            print(f"包地址: {package_url}")
            
            package_info = self.package_fetcher.detect_package_type(package_url)
            
            if package_info['type'] == 'unknown':
                # 不直接失败，使用降级方案
                print(f"⚠️ 包不存在或未发布，使用降级方案生成 Logo")
                if fallback_description:
                    # 构造虚拟的 package_info 用于生成
                    package_info = {
                        'type': 'npm',  # 默认类型
                        'package_name': package_url,
                        'url': '',
                        'info': {
                            'name': package_url,
                            'summary': fallback_description[:200],
                            'description': fallback_description
                        }
                    }
                    print(f"✅ 使用降级描述: {fallback_description[:100]}...")
                else:
                    return {
                        "success": False,
                        "error": f"无法识别包类型且无降级描述: {package_url}"
                    }
            
            print(f"✅ 包类型: {package_info['type']}")
            print(f"✅ 包名: {package_info['package_name']}")
            
            info = package_info.get('info', {})
            description = info.get('summary') or info.get('description') or info.get('name', '')
            
            print(f"✅ 描述: {description[:100]}...")
            
            # 步骤 2: 生成提示词
            print(f"\n🎯 步骤 2/4: 生成 Logo 提示词...")
            
            prompt = self._create_logo_prompt(package_info)
            print(f"提示词: {prompt[:200]}...")
            
            # 步骤 3: 使用即梦 MCP 生成 Logo
            print(f"\n🎨 步骤 3/4: 使用即梦 MCP 生成 Logo...")
            
            jimeng_image_url = self._generate_with_jimeng(prompt, use_v40=use_v40)
            
            if not jimeng_image_url:
                return {
                    "success": False,
                    "error": "即梦 MCP 生成失败"
                }
            
            print(f"✅ 即梦生成成功: {jimeng_image_url[:80]}...")
            
            # 步骤 4: 下载并保存到本地
            print(f"\n💾 步骤 4/5: 下载并保存 Logo...")
            
            local_file = self._save_logo_locally(
                jimeng_image_url, 
                package_info['package_name']
            )
            
            if local_file:
                print(f"✅ 本地文件: {local_file}")
            
            # 步骤 5: 尝试上传到 EMCP (可选)
            print(f"\n⬆️ 步骤 5/5: 上传到 EMCP (可选)...")
            
            emcp_logo_url = self._upload_to_emcp(jimeng_image_url, emcp_base_url)
            
            if emcp_logo_url:
                print(f"✅ EMCP URL: {emcp_logo_url}")
                final_logo_url = emcp_logo_url
            else:
                print(f"⚠️ EMCP 上传失败，使用即梦 URL")
                final_logo_url = jimeng_image_url
            
            print("\n" + "="*70)
            print("🎉 Logo 生成成功!")
            print("="*70)
            
            return {
                "success": True,
                "logo_url": final_logo_url,
                "emcp_url": emcp_logo_url,
                "jimeng_url": jimeng_image_url,
                "local_file": local_file,
                "package_info": package_info,
                "prompt": prompt
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_logo_prompt(self, package_info: Dict) -> str:
        """根据包信息创建 Logo 生成提示词"""
        info = package_info.get('info', {})
        
        package_name = package_info['package_name']
        package_type = package_info['type']
        
        # 获取描述（优先使用完整 README）
        readme = info.get('readme', info.get('description', ''))
        summary = info.get('summary', '')
        
        # 使用更详细的描述（最多500字符）
        if readme and len(readme) > 100:
            description = readme[:500]  # ✅ 使用更长的描述
            print(f"   📖 使用 README 生成提示词 ({len(readme)} 字符)")
        elif summary:
            description = summary[:300]
            print(f"   📝 使用简介生成提示词")
        else:
            description = f"{package_name} - {package_type} package"
            print(f"   ⚠️  使用默认描述")
        
        # 清理描述（移除 Markdown 标记，保留文字）
        import re
        description = re.sub(r'#+\s*', '', description)  # 移除标题标记
        description = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', description)  # 移除链接但保留文字
        description = re.sub(r'```.*?```', '', description, flags=re.DOTALL)  # 移除代码块
        description = description.strip()
        
        # 根据包类型选择图标元素
        type_elements = {
            'pypi': '蟒蛇、代码、Python标志',
            'npm': 'JavaScript、Node.js、包管理',
            'docker': '容器、鲸鱼、云平台'
        }
        
        elements = type_elements.get(package_type, '代码、工具、软件')
        
        # 构建提示词
        prompt = f"""{package_name} Logo 设计:
一个专业的 {package_type.upper()} 包管理工具标志

包描述: {description}

设计要求:
- 主题: 蓝色渐变色调
- 元素: {elements}
- 风格: 扁平化、现代、简洁、专业
- 布局: 方形图标，白色或透明背景
- 文字: 可包含包名 {package_name}

要求: 干净清晰的现代科技 logo，适合软件包标识使用"""
        
        return prompt
    
    def _generate_with_jimeng(self, prompt: str, use_v40: bool = True) -> Optional[str]:
        """使用即梦 MCP 生成图片"""
        client = JimengMCPClient(
            self.jimeng_config['base_url'],
            self.jimeng_config['headers']
        )
        
        try:
            # 启动 SSE 监听
            print("   🔌 连接即梦 MCP...")
            client.start_sse_listener()
            
            if not client.wait_for_session(timeout=15):
                print("   ❌ 连接失败")
                return None
            
            print(f"   ✅ 连接成功: {client.session_id}")
            time.sleep(1)
            
            # 选择工具
            tool_name = "jimeng-v40-generate" if use_v40 else "jimeng-t2i-v31"
            
            arguments = {
                "prompt": prompt,
                "size": 2048 if use_v40 else None,
                "width": None if use_v40 else 1024,
                "height": None if use_v40 else 1024
            }
            
            # 移除 None 值
            arguments = {k: v for k, v in arguments.items() if v is not None}
            
            print(f"   🎨 使用工具: {tool_name}")
            print(f"   ⏳ 生成中...")
            
            result = client.call_tool(tool_name, arguments, wait_timeout=120)
            
            if not result:
                print("   ❌ 生成超时")
                return None
            
            # 检查错误
            if 'error' in result:
                print(f"   ❌ 生成失败: {result['error']}")
                return None
            
            # 提取图片 URL
            image_url = self._extract_image_url(result)
            
            return image_url
            
        finally:
            client.stop()
    
    def _extract_image_url(self, result: Dict) -> Optional[str]:
        """从即梦 MCP 响应中提取图片 URL"""
        if 'result' not in result:
            return None
        
        result_data = result['result']
        
        # 检查 content
        if isinstance(result_data, dict) and 'content' in result_data:
            content_items = result_data['content']
            
            for item in content_items:
                if item.get('type') == 'text':
                    text = item.get('text', '')
                    
                    # 尝试解析 JSON
                    try:
                        text_json = json.loads(text)
                        
                        if 'data' in text_json:
                            data = text_json['data']
                            
                            # 提取第一个 URL
                            if 'image_url' in data:
                                return data['image_url']
                            
                            if 'image_urls' in data and isinstance(data['image_urls'], list):
                                if data['image_urls']:
                                    return data['image_urls'][0]
                    
                    except json.JSONDecodeError:
                        pass
        
        return None
    
    def _save_logo_locally(self, image_url: str, package_name: str) -> Optional[str]:
        """保存 Logo 到本地文件"""
        try:
            # 下载图片
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            # 清理文件名中的非法字符（/, \, :, *, ?, ", <, >, |, @）
            import re
            from pathlib import Path
            
            # 确保 outputs/logos 目录存在
            logos_dir = Path("outputs/logos")
            logos_dir.mkdir(parents=True, exist_ok=True)
            
            safe_name = re.sub(r'[/\\:*?"<>|@]', '_', package_name)
            filename = logos_dir / f"logo_{safe_name}.png"
            
            with open(filename, 'wb') as f:
                f.write(image_data)
            
            print(f"   ✅ 已保存到: {filename.absolute()}")
            print(f"   📦 文件大小: {len(image_data):,} 字节")
            
            return str(filename)
            
        except Exception as e:
            print(f"   ❌ 保存失败: {e}")
            return None
    
    def _upload_to_emcp(self, image_url: str, base_url: str) -> Optional[str]:
        """
        下载图片并上传到 EMCP
        
        Args:
            image_url: 即梦图片 URL
            base_url: EMCP 平台地址
        
        Returns:
            EMCP logo URL (如 /api/proxyStorage/NoAuth/xxx.png)
        """
        try:
            # 步骤 1: 从即梦 URL 下载图片
            print(f"   ⬇️ 下载图片: {image_url[:60]}...")
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            image_data = response.content
            
            print(f"   ✅ 下载完成: {len(image_data):,} 字节")
            
            # 步骤 2: 构建文件流并上传到 EMCP
            upload_url = f"{base_url}/api/proxyStorage/NoAuth/upload_file"
            
            # 构建 multipart/form-data 文件流
            files = {
                'file': ('logo.png', image_data, 'image/png')
            }
            
            print(f"   📤 上传文件流到 EMCP...")
            print(f"      URL: {upload_url}")
            print(f"      文件名: logo.png")
            print(f"      大小: {len(image_data):,} 字节")
            
            # 发送 multipart/form-data 请求
            response = requests.post(upload_url, files=files, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 步骤 3: 提取 fileUrl
            if data.get('err_code') == 0:
                logo_url = data.get('body', {}).get('fileUrl')
                print(f"   ✅ 上传成功")
                print(f"   📋 fileUrl: {logo_url}")
                return logo_url
            else:
                print(f"   ❌ 上传失败: {data.get('err_message')}")
                return None
                
        except Exception as e:
            print(f"   ❌ 上传错误: {e}")
            return None


def main():
    """主函数 - 命令行使用示例"""
    import sys
    
    # 即梦 MCP 配置
    jimeng_config = {
        "base_url": "http://mcptest013.sitmcp.kaleido.guru/sse",
        "headers": {
            "emcp-key": "PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n",
            "emcp-usercode": "VGSdDTgj"
        }
    }
    
    # 创建生成器
    generator = JimengLogoGenerator(jimeng_config)
    
    # 从命令行参数获取包地址
    if len(sys.argv) > 1:
        package_url = sys.argv[1]
    else:
        # 默认测试包
        package_url = input("请输入包地址 (PyPI/NPM/Docker): ").strip()
        if not package_url:
            package_url = "requests"  # 默认测试
    
    # 生成 Logo
    result = generator.generate_logo_from_package(
        package_url=package_url,
        emcp_base_url="https://sit-emcp.kaleido.guru",
        use_v40=True
    )
    
    # 输出结果
    print("\n" + "="*70)
    print("📊 生成结果")
    print("="*70)
    
    if result['success']:
        print(f"\n✅ 成功!")
        print(f"\n📦 包信息:")
        print(f"   类型: {result['package_info']['type']}")
        print(f"   名称: {result['package_info']['package_name']}")
        
        print(f"\n🎨 Logo:")
        print(f"   即梦 URL: {result['jimeng_url']}")
        if result.get('emcp_url'):
            print(f"   EMCP URL: {result['emcp_url']}")
        else:
            print(f"   EMCP URL: (上传失败)")
        print(f"   最终 URL: {result['logo_url']}")
        if result.get('local_file'):
            print(f"   本地文件: {result['local_file']}")
        
        print(f"\n💡 提示词:")
        print(f"   {result['prompt'][:200]}...")
        
        # 保存结果
        result_file = f"logo_result_{result['package_info']['package_name']}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存: {result_file}")
        
        print(f"\n📝 使用说明:")
        print(f"   1. 即梦 URL 可直接使用 (有效期约 24 小时)")
        print(f"   2. 本地文件可手动上传到 EMCP")
        print(f"   3. 如需长期使用，建议将图片保存到自己的服务器")
    else:
        print(f"\n❌ 失败: {result.get('error')}")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即梦AI图像生成Python客户端

使用火山引擎即梦AI的图像生成服务，支持：
- 即梦4.0图片生成 (jimeng_t2i_v40) - 文生图、图像编辑、多图组合
- 即梦图生图3.0 (jimeng_i2i_v30) - 基于图片的智能编辑
- 即梦文生图3.1 (jimeng_t2i_v31) - 画面效果升级版
- 即梦文生图3.0 (jimeng_t2i_v30) - 文字响应准确版

使用方法:
1. 设置环境变量:
   export JIMENG_ACCESS_KEY=你的火山引擎访问密钥
   export JIMENG_SECRET_KEY=你的火山引擎密钥

2. 运行脚本:
   python jimeng_image_generator.py "一只可爱的熊猫在竹林中"

作者: 参考 jimeng4.0-mcp-steve 项目
"""

import os
import sys
import json
import time
import hmac
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlencode
from typing import Optional, List, Dict, Any
import requests


class JimengClient:
    """即梦AI客户端 - 使用火山引擎V4签名算法"""
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        endpoint: str = "https://visual.volcengineapi.com",
        host: str = "visual.volcengineapi.com",
        region: str = "cn-north-1",
        service: str = "cv",
        debug: bool = False,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        初始化即梦AI客户端
        
        Args:
            access_key: 火山引擎访问密钥，默认从环境变量 JIMENG_ACCESS_KEY 获取
            secret_key: 火山引擎密钥，默认从环境变量 JIMENG_SECRET_KEY 获取
            endpoint: API端点
            host: API主机名
            region: 区域，默认 cn-north-1
            service: 服务名，默认 cv
            debug: 是否开启调试模式
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.access_key = access_key or os.environ.get("JIMENG_ACCESS_KEY", "")
        self.secret_key = secret_key or os.environ.get("JIMENG_SECRET_KEY", "")
        self.endpoint = endpoint
        self.host = host
        self.region = region
        self.service = service
        self.debug = debug
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.access_key or not self.secret_key:
            raise ValueError("缺少必要的配置: access_key 和 secret_key。请设置环境变量 JIMENG_ACCESS_KEY 和 JIMENG_SECRET_KEY")
        
        if self.debug:
            print(f"JimengClient 初始化完成:")
            print(f"- 端点: {self.endpoint}")
            print(f"- 区域: {self.region}")
            print(f"- 服务: {self.service}")
            print(f"- AccessKey: {self.access_key[:8]}...")
    
    def _get_signature_key(self, key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
        """生成签名密钥"""
        k_date = hmac.new(key.encode('utf-8'), date_stamp.encode('utf-8'), hashlib.sha256).digest()
        k_region = hmac.new(k_date, region_name.encode('utf-8'), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service_name.encode('utf-8'), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, b'request', hashlib.sha256).digest()
        return k_signing
    
    def _format_query(self, parameters: Dict[str, str]) -> str:
        """格式化查询参数"""
        sorted_keys = sorted(parameters.keys())
        return '&'.join([f"{key}={parameters[key]}" for key in sorted_keys])
    
    def _sign_v4_request(self, req_query: str, req_body: str, region: Optional[str] = None) -> Dict[str, Any]:
        """
        火山引擎V4签名算法
        
        Args:
            req_query: 查询字符串
            req_body: 请求体
            region: 区域（可选）
        
        Returns:
            包含headers和request_url的字典
        """
        t = datetime.now(timezone.utc)
        current_date = t.strftime('%Y%m%dT%H%M%SZ')
        datestamp = current_date[:8]
        used_region = region or self.region
        
        method = 'POST'
        canonical_uri = '/'
        canonical_querystring = req_query
        signed_headers = 'content-type;host;x-content-sha256;x-date'
        payload_hash = hashlib.sha256(req_body.encode('utf-8')).hexdigest()
        content_type = 'application/json'
        
        canonical_headers = '\n'.join([
            f'content-type:{content_type}',
            f'host:{self.host}',
            f'x-content-sha256:{payload_hash}',
            f'x-date:{current_date}'
        ]) + '\n'
        
        canonical_request = '\n'.join([
            method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash
        ])
        
        if self.debug:
            print(f"规范请求字符串:\n{canonical_request}")
        
        algorithm = 'HMAC-SHA256'
        credential_scope = f'{datestamp}/{used_region}/{self.service}/request'
        string_to_sign = '\n'.join([
            algorithm,
            current_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        ])
        
        if self.debug:
            print(f"待签名字符串:\n{string_to_sign}")
        
        signing_key = self._get_signature_key(self.secret_key, datestamp, used_region, self.service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        if self.debug:
            print(f"签名值: {signature}")
        
        authorization_header = f'{algorithm} Credential={self.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}'
        
        headers = {
            'X-Date': current_date,
            'Authorization': authorization_header,
            'X-Content-Sha256': payload_hash,
            'Content-Type': content_type,
            'Host': self.host
        }
        
        request_url = f'{self.endpoint}?{canonical_querystring}'
        
        return {'headers': headers, 'request_url': request_url}
    
    def submit_async_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        提交异步任务
        
        Args:
            params: 任务参数
        
        Returns:
            API响应
        """
        query_params = {
            'Action': 'CVSync2AsyncSubmitTask',
            'Version': '2022-08-31'
        }
        formatted_query = self._format_query(query_params)
        formatted_body = json.dumps(params, ensure_ascii=False)
        
        if self.debug:
            print(f"提交异步任务请求体: {formatted_body}")
        
        sign_result = self._sign_v4_request(formatted_query, formatted_body)
        headers = sign_result['headers']
        request_url = sign_result['request_url']
        
        if self.debug:
            print(f"提交异步任务请求URL: {request_url}")
        
        try:
            response = requests.post(
                request_url,
                headers=headers,
                data=formatted_body.encode('utf-8'),
                timeout=self.timeout
            )
            
            if self.debug:
                print(f"响应状态码: {response.status_code}")
                print(f"响应数据: {response.text}")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP错误! 状态码: {response.status_code}'
                }
            
            data = response.json()
            
            if data.get('code') != 10000:
                return {
                    'success': False,
                    'error': f"API错误: {data.get('message', '未知错误')} (错误码: {data.get('code')})"
                }
            
            task_id = data.get('data', {}).get('task_id')
            if task_id:
                return {
                    'success': True,
                    'task_id': task_id,
                    'raw_response': data
                }
            else:
                return {
                    'success': False,
                    'error': '提交任务失败或响应格式不正确',
                    'raw_response': data
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_async_task(self, req_key: str, task_id: str, req_json: Optional[str] = None) -> Dict[str, Any]:
        """
        查询异步任务结果
        
        Args:
            req_key: 服务标识
            task_id: 任务ID
            req_json: 额外的JSON配置（可选）
        
        Returns:
            API响应
        """
        query_params = {
            'Action': 'CVSync2AsyncGetResult',
            'Version': '2022-08-31'
        }
        formatted_query = self._format_query(query_params)
        
        body_params = {
            'req_key': req_key,
            'task_id': task_id
        }
        
        if req_json:
            body_params['req_json'] = req_json
        else:
            body_params['req_json'] = json.dumps({'return_url': True})
        
        formatted_body = json.dumps(body_params, ensure_ascii=False)
        
        if self.debug:
            print(f"查询异步任务请求体: {formatted_body}")
        
        sign_result = self._sign_v4_request(formatted_query, formatted_body)
        headers = sign_result['headers']
        request_url = sign_result['request_url']
        
        try:
            response = requests.post(
                request_url,
                headers=headers,
                data=formatted_body.encode('utf-8'),
                timeout=self.timeout
            )
            
            if self.debug:
                print(f"查询响应状态码: {response.status_code}")
                print(f"查询响应数据: {response.text}")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP错误! 状态码: {response.status_code}'
                }
            
            data = response.json()
            
            # 检查业务错误码
            if data.get('code') != 10000:
                # 特殊处理审核错误
                if data.get('code') in [50411, 50511, 50412, 50512, 50413]:
                    return {
                        'success': False,
                        'status': 'FAILED',
                        'error': data.get('message'),
                        'raw_response': data
                    }
                return {
                    'success': False,
                    'error': f"API错误: {data.get('message', '未知错误')} (错误码: {data.get('code')})"
                }
            
            task_data = data.get('data', {})
            task_status = task_data.get('status', '')
            
            # 标准化状态值
            status_map = {
                'in_queue': 'PENDING',
                'generating': 'RUNNING',
                'processing': 'RUNNING',
                'done': 'SUCCEEDED',
                'fail': 'FAILED',
                'failed': 'FAILED'
            }
            normalized_status = status_map.get(task_status, task_status.upper() if task_status else 'UNKNOWN')
            
            return {
                'success': True,
                'status': normalized_status,
                'data': task_data,
                'raw_response': data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_image_v40(
        self,
        prompt: str,
        image_urls: Optional[List[str]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        size: Optional[int] = None,
        scale: float = 0.5,
        force_single: bool = False,
        seed: int = -1,
        polling_interval: int = 5,
        max_attempts: int = 60
    ) -> Dict[str, Any]:
        """
        即梦4.0图片生成（同步方式，内部轮询）
        
        支持文生图、图像编辑及多图组合生成
        
        Args:
            prompt: 提示词
            image_urls: 输入图片URL列表（0-10张）
            width: 图片宽度
            height: 图片高度
            size: 图片面积（与width/height二选一）
            scale: 文本描述影响程度 [0, 1]
            force_single: 是否强制生成单图
            seed: 随机种子，-1表示随机
            polling_interval: 轮询间隔（秒）
            max_attempts: 最大轮询次数
        
        Returns:
            生成结果
        """
        # 构建参数
        params = {
            'req_key': 'jimeng_t2i_v40',
            'prompt': prompt
        }
        
        # width和height必须同时存在
        if width and height:
            area = width * height
            if area < 1024 * 1024 or area > 4096 * 4096:
                return {
                    'success': False,
                    'error': f'宽高乘积必须在[1048576, 16777216]范围内，当前值：{area}'
                }
            params['width'] = width
            params['height'] = height
        elif size:
            if size < 1024 * 1024:
                size = 1024 * 1024
            elif size > 4096 * 4096:
                size = 4096 * 4096
            params['size'] = size
        
        if image_urls:
            params['image_urls'] = image_urls
        if scale != 0.5:
            params['scale'] = scale
        if force_single:
            params['force_single'] = force_single
        if seed != -1:
            params['seed'] = seed
        
        print("即梦4.0图片生成中...")
        
        # 提交任务
        task_result = self.submit_async_task(params)
        if not task_result.get('success') or not task_result.get('task_id'):
            return {
                'success': False,
                'error': task_result.get('error', '提交任务失败')
            }
        
        task_id = task_result['task_id']
        print(f"任务提交成功，任务ID: {task_id}")
        print("开始轮询任务结果...")
        
        # 轮询查询结果
        for i in range(max_attempts):
            print(f"轮询任务结果 ({i + 1}/{max_attempts})...")
            
            result = self.query_async_task('jimeng_t2i_v40', task_id)
            
            if result.get('success'):
                status = result.get('status')
                if status == 'SUCCEEDED' and result.get('data'):
                    image_urls = result['data'].get('image_urls', [])
                    if image_urls:
                        print("图片生成成功!")
                        return {
                            'success': True,
                            'image_urls': image_urls,
                            'task_id': task_id,
                            'raw_response': result.get('raw_response')
                        }
                elif status == 'FAILED':
                    return {
                        'success': False,
                        'error': result.get('error', '图片生成任务失败'),
                        'task_id': task_id,
                        'raw_response': result.get('raw_response')
                    }
                elif status in ['PENDING', 'RUNNING']:
                    print(f"任务仍在进行中，状态: {status}，等待 {polling_interval} 秒后重试...")
                    time.sleep(polling_interval)
                    continue
            
            time.sleep(polling_interval)
        
        return {
            'success': False,
            'error': '轮询任务结果超时',
            'task_id': task_id
        }
    
    def generate_image_t2i_v31(
        self,
        prompt: str,
        use_pre_llm: bool = True,
        width: int = 1328,
        height: int = 1328,
        seed: int = -1,
        polling_interval: int = 5,
        max_attempts: int = 60
    ) -> Dict[str, Any]:
        """
        即梦文生图3.1（画面效果升级版）
        
        Args:
            prompt: 提示词
            use_pre_llm: 是否开启文本扩写
            width: 图片宽度 [512, 2048]
            height: 图片高度 [512, 2048]
            seed: 随机种子，-1表示随机
            polling_interval: 轮询间隔（秒）
            max_attempts: 最大轮询次数
        
        Returns:
            生成结果
        """
        params = {
            'req_key': 'jimeng_t2i_v31',
            'prompt': prompt,
            'use_pre_llm': use_pre_llm,
            'width': width,
            'height': height
        }
        
        if seed != -1:
            params['seed'] = seed
        
        print("即梦文生图3.1生成中...")
        
        # 提交任务
        task_result = self.submit_async_task(params)
        if not task_result.get('success') or not task_result.get('task_id'):
            return {
                'success': False,
                'error': task_result.get('error', '提交任务失败')
            }
        
        task_id = task_result['task_id']
        print(f"任务提交成功，任务ID: {task_id}")
        print("开始轮询任务结果...")
        
        # 轮询查询结果
        for i in range(max_attempts):
            print(f"轮询任务结果 ({i + 1}/{max_attempts})...")
            
            result = self.query_async_task('jimeng_t2i_v31', task_id)
            
            if result.get('success'):
                status = result.get('status')
                if status == 'SUCCEEDED' and result.get('data'):
                    image_urls = result['data'].get('image_urls', [])
                    if image_urls:
                        print("图片生成成功!")
                        return {
                            'success': True,
                            'image_urls': image_urls,
                            'task_id': task_id,
                            'raw_response': result.get('raw_response')
                        }
                elif status == 'FAILED':
                    return {
                        'success': False,
                        'error': result.get('error', '图片生成任务失败'),
                        'task_id': task_id,
                        'raw_response': result.get('raw_response')
                    }
                elif status in ['PENDING', 'RUNNING']:
                    print(f"任务仍在进行中，状态: {status}，等待 {polling_interval} 秒后重试...")
                    time.sleep(polling_interval)
                    continue
            
            time.sleep(polling_interval)
        
        return {
            'success': False,
            'error': '轮询任务结果超时',
            'task_id': task_id
        }
    
    def generate_image_t2i_v30(
        self,
        prompt: str,
        use_pre_llm: bool = True,
        width: int = 1328,
        height: int = 1328,
        seed: int = -1,
        polling_interval: int = 5,
        max_attempts: int = 60
    ) -> Dict[str, Any]:
        """
        即梦文生图3.0（文字响应准确版）
        
        适合生成带文字的海报等
        
        Args:
            prompt: 提示词
            use_pre_llm: 是否开启文本扩写
            width: 图片宽度 [512, 2048]
            height: 图片高度 [512, 2048]
            seed: 随机种子，-1表示随机
            polling_interval: 轮询间隔（秒）
            max_attempts: 最大轮询次数
        
        Returns:
            生成结果
        """
        params = {
            'req_key': 'jimeng_t2i_v30',
            'prompt': prompt,
            'use_pre_llm': use_pre_llm,
            'width': width,
            'height': height
        }
        
        if seed != -1:
            params['seed'] = seed
        
        print("即梦文生图3.0生成中...")
        
        # 提交任务
        task_result = self.submit_async_task(params)
        if not task_result.get('success') or not task_result.get('task_id'):
            return {
                'success': False,
                'error': task_result.get('error', '提交任务失败')
            }
        
        task_id = task_result['task_id']
        print(f"任务提交成功，任务ID: {task_id}")
        print("开始轮询任务结果...")
        
        # 轮询查询结果
        for i in range(max_attempts):
            print(f"轮询任务结果 ({i + 1}/{max_attempts})...")
            
            result = self.query_async_task('jimeng_t2i_v30', task_id)
            
            if result.get('success'):
                status = result.get('status')
                if status == 'SUCCEEDED' and result.get('data'):
                    image_urls = result['data'].get('image_urls', [])
                    if image_urls:
                        print("图片生成成功!")
                        return {
                            'success': True,
                            'image_urls': image_urls,
                            'task_id': task_id,
                            'raw_response': result.get('raw_response')
                        }
                elif status == 'FAILED':
                    return {
                        'success': False,
                        'error': result.get('error', '图片生成任务失败'),
                        'task_id': task_id,
                        'raw_response': result.get('raw_response')
                    }
                elif status in ['PENDING', 'RUNNING']:
                    print(f"任务仍在进行中，状态: {status}，等待 {polling_interval} 秒后重试...")
                    time.sleep(polling_interval)
                    continue
            
            time.sleep(polling_interval)
        
        return {
            'success': False,
            'error': '轮询任务结果超时',
            'task_id': task_id
        }
    
    def generate_image_i2i_v30(
        self,
        image_url: str,
        prompt: str,
        width: int = 1328,
        height: int = 1328,
        scale: float = 0.5,
        seed: int = -1,
        polling_interval: int = 5,
        max_attempts: int = 60
    ) -> Dict[str, Any]:
        """
        即梦图生图3.0（智能图像编辑）
        
        Args:
            image_url: 输入图片URL
            prompt: 编辑指令
            width: 图片宽度 [512, 2016]
            height: 图片高度 [512, 2016]
            scale: 文本描述影响程度 [0, 1]
            seed: 随机种子，-1表示随机
            polling_interval: 轮询间隔（秒）
            max_attempts: 最大轮询次数
        
        Returns:
            生成结果
        """
        params = {
            'req_key': 'jimeng_i2i_v30',
            'image_urls': [image_url],
            'prompt': prompt,
            'width': width,
            'height': height,
            'scale': scale
        }
        
        if seed != -1:
            params['seed'] = seed
        
        print("即梦图生图3.0编辑中...")
        
        # 提交任务
        task_result = self.submit_async_task(params)
        if not task_result.get('success') or not task_result.get('task_id'):
            return {
                'success': False,
                'error': task_result.get('error', '提交任务失败')
            }
        
        task_id = task_result['task_id']
        print(f"任务提交成功，任务ID: {task_id}")
        print("开始轮询任务结果...")
        
        # 轮询查询结果
        for i in range(max_attempts):
            print(f"轮询任务结果 ({i + 1}/{max_attempts})...")
            
            result = self.query_async_task('jimeng_i2i_v30', task_id)
            
            if result.get('success'):
                status = result.get('status')
                if status == 'SUCCEEDED' and result.get('data'):
                    image_urls = result['data'].get('image_urls', [])
                    if image_urls:
                        print("图片编辑成功!")
                        return {
                            'success': True,
                            'image_urls': image_urls,
                            'task_id': task_id,
                            'raw_response': result.get('raw_response')
                        }
                elif status == 'FAILED':
                    return {
                        'success': False,
                        'error': result.get('error', '图片编辑任务失败'),
                        'task_id': task_id,
                        'raw_response': result.get('raw_response')
                    }
                elif status in ['PENDING', 'RUNNING']:
                    print(f"任务仍在进行中，状态: {status}，等待 {polling_interval} 秒后重试...")
                    time.sleep(polling_interval)
                    continue
            
            time.sleep(polling_interval)
        
        return {
            'success': False,
            'error': '轮询任务结果超时',
            'task_id': task_id
        }


def download_image(url: str, save_path: str) -> bool:
    """
    下载图片到本地
    
    Args:
        url: 图片URL
        save_path: 保存路径
    
    Returns:
        是否成功
    """
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        print(f"下载图片失败: {e}")
        return False


class JimengAPIGenerator:
    """即梦 API Logo 生成器（从配置读取密钥）"""
    
    def __init__(self, access_key: str = None, secret_key: str = None):
        """
        初始化
        
        Args:
            access_key: 火山引擎 Access Key（可选，默认从配置读取）
            secret_key: 火山引擎 Secret Key（可选，默认从配置读取）
        """
        # 如果未传入，从配置读取
        if not access_key or not secret_key:
            try:
                from src.unified_config_manager import UnifiedConfigManager
                config_mgr = UnifiedConfigManager()
                ak, sk = config_mgr.get_jimeng_api_credentials()
                access_key = access_key or ak
                secret_key = secret_key or sk
            except Exception as e:
                print(f"⚠️ 无法从配置读取即梦密钥: {e}")
        
        if not access_key or not secret_key:
            raise ValueError("缺少即梦 API 密钥，请在设置中配置 Access Key 和 Secret Key")
        
        self.access_key = access_key
        self.secret_key = secret_key
        
        # 初始化客户端
        self.client = JimengClient(
            access_key=self.access_key,
            secret_key=self.secret_key,
            debug=False
        )
        print(f"✅ 即梦 API 初始化成功")
    
    def generate_logo(self, prompt: str, width: int = 1024, height: int = 1024) -> Dict[str, Any]:
        """
        生成 Logo
        
        Args:
            prompt: 图片描述
            width: 图片宽度
            height: 图片高度
            
        Returns:
            生成结果 {"success": True/False, "image_url": "..."}
        """
        print(f"\n🎨 即梦 API 生成 Logo...")
        print(f"   📝 提示词: {prompt[:100]}...")
        
        try:
            # 使用即梦 4.0 生成
            result = self.client.generate_image_v40(
                prompt=prompt,
                width=width,
                height=height,
                force_single=True,
                polling_interval=3,
                max_attempts=40
            )
            
            if result.get('success') and result.get('image_urls'):
                image_url = result['image_urls'][0]
                print(f"   ✅ 生成成功!")
                return {
                    "success": True,
                    "image_url": image_url
                }
            else:
                error = result.get('error', '未知错误')
                print(f"   ❌ 生成失败: {error}")
                return {"success": False, "error": error}
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def generate_logo_for_mcp(self, description: str, mcp_name: str = "") -> Dict[str, Any]:
        """
        为 MCP 服务生成 Logo
        
        Args:
            description: MCP 服务描述
            mcp_name: MCP 名称
            
        Returns:
            生成结果
        """
        # 从描述中提取核心功能
        core_function = self._extract_core_function(description, mcp_name)
        design_elements = self._get_design_elements(core_function, description)
        
        # 构建 Logo 提示词
        prompt = f"""设计一个专业的科技服务 Logo

服务功能: {core_function}
设计元素: {design_elements}

设计要求:
- 现代科技风格，蓝紫色渐变
- 扁平化、简约、专业
- 方形图标，简洁背景
- 体现该服务的功能特点
- 高端、智能、可靠的感觉"""

        return self.generate_logo(prompt, 1024, 1024)
    
    def _extract_core_function(self, description: str, name: str) -> str:
        """提取核心功能"""
        import re
        
        clean_name = name.replace('bach-', '').replace('bachai-', '')
        clean_name = clean_name.replace('-mcp', '').replace('_mcp', '')
        clean_name = clean_name.replace('-', ' ').replace('_', ' ')
        
        if description:
            patterns = [
                r'用于[「【]?([^」】,，。.]+)[」】]?的',
                r'提供[「【]?([^」】,，。.]+)[」】]?服务',
                r'一个[「【]?([^」】,，。.]+)[」】]?的',
            ]
            for pattern in patterns:
                match = re.search(pattern, description)
                if match:
                    extracted = match.group(1).strip()
                    if 2 < len(extracted) < 30:
                        return extracted
            
            first_sentence = description.split('。')[0].split('.')[0]
            if 5 < len(first_sentence) < 50:
                return first_sentence[:30]
        
        return clean_name if clean_name else "智能服务"
    
    def _get_design_elements(self, core_function: str, description: str) -> str:
        """获取设计元素"""
        text = f"{core_function} {description}".lower()
        
        element_map = {
            ('数据', 'data', '分析'): '数据图表、统计曲线、智能分析',
            ('搜索', 'search', '检索'): '搜索图标、放大镜、数据流',
            ('商品', '电商', 'amazon', 'walmart'): '购物车、商品标签、价格曲线',
            ('支付', 'pay', 'payment'): '金融符号、安全盾牌、交易流程',
            ('社交', 'social', '媒体'): '社交网络、连接节点、对话气泡',
            ('视频', 'video', 'youtube'): '播放按钮、视频帧、流媒体',
            ('地图', 'map', '位置'): '地图标记、定位图标、路线',
            ('房产', 'real', 'estate'): '建筑剪影、房屋图标、城市天际线',
            ('消息', 'message', 'whatsapp'): '消息气泡、通讯图标、连接线',
            ('翻译', 'translat', '语言'): '语言符号、翻译箭头、地球',
            ('天气', 'weather'): '天气图标、云朵、温度计',
            ('工作', 'job', '招聘'): '公文包、职业图标、人才网络',
            ('航班', 'flight', '旅行'): '飞机图标、地球、航线',
        }
        
        for keywords, elements in element_map.items():
            if any(kw in text for kw in keywords):
                return elements
        
        return '科技齿轮、数据节点、智能连接'


def main():
    """主函数 - 命令行示例"""
    # 解析命令行参数
    prompt = sys.argv[1] if len(sys.argv) > 1 else "一只可爱的熊猫，坐在竹林中，吃着竹子，阳光照射，高清细节，写实风格"
    model = sys.argv[2] if len(sys.argv) > 2 else "v40"  # v40, v31, v30
    
    print("=" * 50)
    print("即梦AI图像生成Python客户端")
    print("=" * 50)
    print(f"提示词: {prompt}")
    print(f"模型: {model}")
    print("=" * 50)
    
    try:
        # 创建客户端
        client = JimengClient(debug=False)
        
        start_time = time.time()
        
        # 根据模型选择不同的生成方法
        if model == "v40":
            result = client.generate_image_v40(
                prompt=prompt,
                width=2048,
                height=2048,
                force_single=True
            )
        elif model == "v31":
            result = client.generate_image_t2i_v31(
                prompt=prompt,
                width=2048,
                height=2048
            )
        elif model == "v30":
            result = client.generate_image_t2i_v30(
                prompt=prompt,
                width=1328,
                height=1328
            )
        else:
            print(f"不支持的模型: {model}")
            print("可用模型: v40, v31, v30")
            return
        
        end_time = time.time()
        print(f"\n生成耗时: {end_time - start_time:.2f}秒")
        
        if result.get('success') and result.get('image_urls'):
            print("\n图像生成成功!")
            print("图像URL:")
            for i, url in enumerate(result['image_urls'], 1):
                print(f"[{i}] {url}")
            
            # 可选：下载第一张图片
            # if result['image_urls']:
            #     save_path = f"output_{int(time.time())}.jpg"
            #     if download_image(result['image_urls'][0], save_path):
            #         print(f"\n图片已保存到: {save_path}")
        else:
            print(f"\n图像生成失败: {result.get('error', '未知错误')}")
    
    except ValueError as e:
        print(f"配置错误: {e}")
        print("\n请设置环境变量:")
        print("  export JIMENG_ACCESS_KEY=你的火山引擎访问密钥")
        print("  export JIMENG_SECRET_KEY=你的火山引擎密钥")
    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    main()


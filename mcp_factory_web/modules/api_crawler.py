"""
API爬取转换模块
整合RapidAPI爬取、百度API爬取、OpenAPI转换功能
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

# 尝试导入APItoMCP模块
try:
    api_to_mcp_path = Path("E:/code/APItoMCP")
    if api_to_mcp_path.exists():
        sys.path.insert(0, str(api_to_mcp_path))
        sys.path.insert(0, str(api_to_mcp_path / "src"))
        from api_to_mcp.platforms.rapidapi_auto import auto_extract_rapidapi, RapidAPIAutoExtractor
        from api_to_mcp.parsers import OpenAPIParser
        from api_to_mcp.generator import MCPGenerator
        from api_to_mcp.enhancer import DescriptionEnhancer
        API_TO_MCP_AVAILABLE = True
except ImportError:
    API_TO_MCP_AVAILABLE = False


def crawl_rapidapi_url(url: str, use_selenium: bool = False, name: Optional[str] = None) -> Dict[str, Any]:
    """
    爬取RapidAPI页面并提取API规范
    
    Args:
        url: RapidAPI页面URL
        use_selenium: 是否使用Selenium完整提取
        name: 自定义MCP名称
    
    Returns:
        包含OpenAPI规范和MCP生成结果的字典
    """
    if not API_TO_MCP_AVAILABLE:
        raise ImportError("APItoMCP模块不可用，请确保E:/code/APItoMCP目录存在")
    
    try:
        # 提取API名称
        match = re.search(r'/api/([^/?]+)', url)
        api_name = match.group(1) if match else 'api'
        
        if use_selenium:
            extractor = RapidAPIAutoExtractor()
            openapi_spec = extractor.auto_extract_with_selenium(url, headless=True)
        else:
            openapi_spec = auto_extract_rapidapi(url)
        
        # 保存OpenAPI规范
        output_dir = Path("generated_mcps")
        output_dir.mkdir(exist_ok=True)
        
        spec_file = output_dir / f"rapidapi_{api_name}_spec.json"
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        
        # 解析并生成MCP
        parser = OpenAPIParser()
        api_spec = parser.parse_dict(openapi_spec)
        
        generator = MCPGenerator(output_dir=str(output_dir))
        mcp_server = generator.generate(api_spec, custom_name=name or api_name)
        
        return {
            'success': True,
            'api_name': api_name,
            'spec_file': str(spec_file),
            'mcp_path': str(mcp_server.output_path),
            'mcp_name': mcp_server.name,
            'tools_count': len(mcp_server.tools),
            'openapi_spec': openapi_spec
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'api_name': api_name if 'api_name' in locals() else 'unknown'
        }


def crawl_baidu_api(max_products: int = 5, start_from: int = 1) -> Dict[str, Any]:
    """
    百度API自动化爬取
    
    Args:
        max_products: 最大处理产品数
        start_from: 起始位置
    
    Returns:
        处理结果
    """
    try:
        # 动态导入百度API爬取模块
        baidu_path = Path("E:/百度api爬取")
        if baidu_path.exists():
            sys.path.insert(0, str(baidu_path))
            
            # 由于百度API需要浏览器交互，这里返回启动信息
            return {
                'success': True,
                'message': '百度API自动化需要在独立窗口中运行',
                'command': f'python "{baidu_path}/auto_full.py"',
                'params': {
                    'max_products': max_products,
                    'start_from': start_from
                }
            }
        else:
            return {
                'success': False,
                'error': '百度API爬取模块不存在'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def convert_openapi_to_mcp(
    openapi_spec: Dict[str, Any],
    name: str,
    transport: str = 'stdio',
    enhance: bool = True
) -> Dict[str, Any]:
    """
    将OpenAPI规范转换为MCP服务器
    
    Args:
        openapi_spec: OpenAPI规范字典
        name: MCP服务器名称
        transport: 传输协议 (stdio/sse/streamable-http)
        enhance: 是否使用LLM增强描述
    
    Returns:
        生成结果
    """
    if not API_TO_MCP_AVAILABLE:
        raise ImportError("APItoMCP模块不可用")
    
    try:
        # 解析规范
        parser = OpenAPIParser()
        api_spec = parser.parse_dict(openapi_spec)
        
        # 增强描述
        if enhance:
            enhancer = DescriptionEnhancer()
            api_spec = enhancer.enhance_api_spec(api_spec)
        
        # 生成MCP
        output_dir = Path("generated_mcps")
        output_dir.mkdir(exist_ok=True)
        
        generator = MCPGenerator(output_dir=str(output_dir))
        mcp_server = generator.generate(api_spec, transport=transport, custom_name=name)
        
        return {
            'success': True,
            'mcp_path': str(mcp_server.output_path),
            'mcp_name': mcp_server.name,
            'version': mcp_server.version,
            'tools_count': len(mcp_server.tools),
            'transport': transport
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def batch_crawl_rapidapi(urls: List[str], use_selenium: bool = False) -> List[Dict[str, Any]]:
    """
    批量爬取RapidAPI
    
    Args:
        urls: RapidAPI URL列表
        use_selenium: 是否使用Selenium
    
    Returns:
        结果列表
    """
    results = []
    
    for url in urls:
        result = crawl_rapidapi_url(url, use_selenium)
        results.append(result)
    
    return results





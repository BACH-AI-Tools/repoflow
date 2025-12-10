"""
第三方平台发布模块
整合LobeHub、mcp.so等平台的发布功能
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 日志文件路径
LOBEHUB_LOG = Path(__file__).parent.parent / 'outputs' / 'lobehub_submit_log.json'
MCPSO_LOG = Path(__file__).parent.parent / 'outputs' / 'mcpso_submit_log.json'


def load_submit_log(log_file: Path) -> Dict[str, Any]:
    """加载提交日志"""
    try:
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    return {
        'last_updated': '',
        'submitted': [],
        'failed': [],
        'pending': []
    }


def save_submit_log(log_file: Path, data: Dict[str, Any]):
    """保存提交日志"""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    data['last_updated'] = datetime.now().isoformat()
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def submit_to_lobehub(repos: List[str], headless: bool = True) -> Dict[str, Any]:
    """
    批量提交到LobeHub平台
    
    Args:
        repos: GitHub仓库URL列表
        headless: 是否无头模式运行
    
    Returns:
        提交结果
    """
    results = {
        'total': len(repos),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    log_data = load_submit_log(LOBEHUB_LOG)
    
    try:
        # 尝试使用Playwright
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless, slow_mo=50)
            context = browser.new_context(viewport={"width": 1400, "height": 900})
            page = context.new_page()
            
            # 访问LobeHub MCP页面
            page.goto("https://lobehub.com/MCP", wait_until="domcontentloaded", timeout=120000)
            time.sleep(5)
            
            for repo_url in repos:
                repo_name = repo_url.rstrip('/').split('/')[-1]
                detail = {'url': repo_url, 'name': repo_name}
                
                try:
                    # 点击Submit MCP按钮
                    page.evaluate('''() => {
                        const buttons = document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if (btn.textContent.includes('Submit MCP') || 
                                btn.textContent.includes('提交 MCP')) {
                                btn.click();
                                return true;
                            }
                        }
                        return false;
                    }''')
                    time.sleep(2)
                    
                    # 等待对话框
                    page.wait_for_selector('[role="dialog"]', timeout=10000)
                    time.sleep(1)
                    
                    # 填写URL
                    page.evaluate(f'''(url) => {{
                        const dialog = document.querySelector('[role="dialog"]');
                        if (dialog) {{
                            const input = dialog.querySelector('input');
                            if (input) {{
                                input.value = url;
                                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            }}
                        }}
                    }}''', repo_url)
                    time.sleep(1)
                    
                    # 点击提交
                    page.evaluate('''() => {
                        const dialog = document.querySelector('[role="dialog"]');
                        if (dialog) {
                            const buttons = dialog.querySelectorAll('button');
                            for (let btn of buttons) {
                                if (btn.textContent.trim() === 'Submit' || 
                                    btn.textContent.trim() === '提交') {
                                    btn.click();
                                    return true;
                                }
                            }
                        }
                        return false;
                    }''')
                    time.sleep(3)
                    
                    detail['success'] = True
                    results['success'] += 1
                    log_data['submitted'].append({
                        'url': repo_url,
                        'time': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    detail['success'] = False
                    detail['error'] = str(e)
                    results['failed'] += 1
                    log_data['failed'].append({
                        'url': repo_url,
                        'time': datetime.now().isoformat(),
                        'error': str(e)
                    })
                
                results['details'].append(detail)
                
                # 刷新页面准备下一个
                page.reload(wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
            
            browser.close()
            
    except ImportError:
        return {
            'success': False,
            'error': 'Playwright未安装，请运行: pip install playwright && playwright install chromium'
        }
    except Exception as e:
        results['error'] = str(e)
    
    save_submit_log(LOBEHUB_LOG, log_data)
    return results


def submit_to_mcpso(repos: List[str], headless: bool = True) -> Dict[str, Any]:
    """
    批量提交到mcp.so平台
    
    Args:
        repos: GitHub仓库URL列表
        headless: 是否无头模式运行
    
    Returns:
        提交结果
    """
    results = {
        'total': len(repos),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    log_data = load_submit_log(MCPSO_LOG)
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # 使用持久化上下文保持登录
            user_data_dir = Path(__file__).parent.parent / 'browser_data' / 'mcpso'
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=headless,
                slow_mo=50,
                viewport={"width": 1400, "height": 900}
            )
            page = context.new_page()
            
            for repo_url in repos:
                repo_name = repo_url.rstrip('/').split('/')[-1]
                detail = {'url': repo_url, 'name': repo_name}
                
                try:
                    # 访问提交页面
                    page.goto("https://mcp.so/submit", wait_until="domcontentloaded", timeout=60000)
                    time.sleep(3)
                    
                    # 填写表单
                    name_input = page.locator('input[name="name"]').first
                    if name_input.is_visible():
                        name_input.fill(repo_name)
                    
                    url_input = page.locator('input[name="url"]').first
                    if url_input.is_visible():
                        url_input.fill(repo_url)
                    
                    time.sleep(1)
                    
                    # 提交
                    submit_btn = page.locator('button[type="submit"]').first
                    if submit_btn.is_visible():
                        submit_btn.click()
                        time.sleep(3)
                    
                    detail['success'] = True
                    results['success'] += 1
                    log_data['submitted'].append({
                        'name': repo_name,
                        'url': repo_url,
                        'time': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    detail['success'] = False
                    detail['error'] = str(e)
                    results['failed'] += 1
                    log_data['failed'].append({
                        'name': repo_name,
                        'url': repo_url,
                        'time': datetime.now().isoformat(),
                        'error': str(e)
                    })
                
                results['details'].append(detail)
                time.sleep(2)
            
            context.close()
            
    except ImportError:
        return {
            'success': False,
            'error': 'Playwright未安装'
        }
    except Exception as e:
        results['error'] = str(e)
    
    save_submit_log(MCPSO_LOG, log_data)
    return results


def batch_submit_platforms(
    repos: List[str],
    platforms: List[str] = ['lobehub', 'mcpso'],
    headless: bool = True
) -> Dict[str, Any]:
    """
    批量发布到多个平台
    
    Args:
        repos: GitHub仓库URL列表
        platforms: 目标平台列表
        headless: 是否无头模式
    
    Returns:
        发布结果
    """
    results = {
        'platforms': {}
    }
    
    if 'lobehub' in platforms:
        results['platforms']['lobehub'] = submit_to_lobehub(repos, headless)
    
    if 'mcpso' in platforms:
        results['platforms']['mcpso'] = submit_to_mcpso(repos, headless)
    
    # 统计总体结果
    total_success = sum(
        p.get('success', 0) 
        for p in results['platforms'].values() 
        if isinstance(p, dict)
    )
    total_failed = sum(
        p.get('failed', 0) 
        for p in results['platforms'].values() 
        if isinstance(p, dict)
    )
    
    results['summary'] = {
        'total_success': total_success,
        'total_failed': total_failed
    }
    
    return results


def get_submit_status(platform: str) -> Dict[str, Any]:
    """
    获取平台提交状态
    
    Args:
        platform: 平台名称 (lobehub/mcpso)
    
    Returns:
        提交状态统计
    """
    log_file = LOBEHUB_LOG if platform == 'lobehub' else MCPSO_LOG
    log_data = load_submit_log(log_file)
    
    return {
        'platform': platform,
        'last_updated': log_data.get('last_updated', ''),
        'submitted_count': len(log_data.get('submitted', [])),
        'failed_count': len(log_data.get('failed', [])),
        'pending_count': len(log_data.get('pending', []))
    }


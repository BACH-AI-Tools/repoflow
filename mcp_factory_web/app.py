"""
MCP工厂 - Web界面
完整的MCP生产流水线：API爬取 → 转换 → 发布 → 上架
"""

import os
import sys
import json
import queue
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from modules.logger import log, get_logger
from modules.config import config, get_config, set_config
from modules.database import db

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'mcp-factory-secret-key'
app.config['JSON_AS_ASCII'] = False

log_queues = []

# ==================== 页面路由 ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pipeline')
def pipeline():
    return render_template('pipeline.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/api-crawler')
def api_crawler():
    return render_template('api_crawler.html')

@app.route('/mcp-publisher')
def mcp_publisher():
    return render_template('mcp_publisher.html')

@app.route('/platform-publisher')
def platform_publisher():
    return render_template('platform_publisher.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/logs')
def logs_page():
    return render_template('logs.html')

# ==================== 系统API ====================

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stats')
def api_stats():
    """获取统计信息"""
    stats = db.get_stats()
    return jsonify({'success': True, 'data': stats})

# ==================== 项目API ====================

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """列出所有项目"""
    status = request.args.get('status')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    projects = db.list_projects(status=status, limit=limit, offset=offset)
    return jsonify({'success': True, 'data': projects})

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """获取项目详情"""
    project = db.get_project(project_id)
    if project:
        return jsonify({'success': True, 'data': project})
    return jsonify({'success': False, 'error': '项目不存在'})

@app.route('/api/projects/create', methods=['POST'])
def create_project():
    """创建新项目"""
    data = request.get_json()
    source_type = data.get('source_type')
    source_url = data.get('source_url')
    name = data.get('name')
    start_step = data.get('start_step', 1)
    
    # 自动生成名称
    if not name:
        if source_type == 'rapidapi' and source_url:
            import re
            match = re.search(r'/api/([^/?]+)', source_url)
            name = match.group(1) if match else f'project_{datetime.now().strftime("%Y%m%d%H%M%S")}'
        else:
            name = f'project_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    
    logger = get_logger("项目管理")
    logger.info(f"创建项目: {name}")
    
    try:
        project_id = db.create_project(
            name=name,
            source_type=source_type,
            source_url=source_url,
            metadata={'start_step': start_step}
        )
        
        # 跳过前面的步骤
        if start_step > 1:
            step_names = ['crawl', 'convert', 'github', 'pypi', 'emcp', 'lobehub', 'mcpso', 'test']
            for i in range(start_step - 1):
                if i < len(step_names):
                    db.update_step(project_id, step_names[i], 'skipped')
        
        logger.success(f"项目创建成功: {name} (ID: {project_id})")
        db.add_log('create_project', f'创建项目: {name}', 'info', project_id)
        
        return jsonify({
            'success': True, 
            'data': {'id': project_id, 'name': name}
        })
        
    except Exception as e:
        logger.error(f"创建项目失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目"""
    data = request.get_json()
    db.update_project(project_id, **data)
    return jsonify({'success': True})

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    db.delete_project(project_id)
    log.info(f"删除项目: {project_id}", "项目管理")
    return jsonify({'success': True})

@app.route('/api/projects/<int:project_id>/test-reports', methods=['GET'])
def get_project_test_reports(project_id):
    """获取项目的测试报告"""
    test_type = request.args.get('type')
    reports = db.get_test_reports(project_id=project_id, test_type=test_type)
    return jsonify({'success': True, 'data': reports})

@app.route('/api/projects/<int:project_id>/test-reports', methods=['POST'])
def add_project_test_report(project_id):
    """添加测试报告"""
    data = request.get_json()
    
    report_id = db.add_test_report(
        project_id=project_id,
        test_type=data.get('test_type', 'local'),
        platform=data.get('platform'),
        status=data.get('status', 'success'),
        passed=data.get('passed', 0),
        failed=data.get('failed', 0),
        skipped=data.get('skipped', 0),
        duration_ms=data.get('duration_ms', 0),
        report_data=data.get('report_data'),
        error_message=data.get('error_message')
    )
    
    log.info(f"添加测试报告: {data.get('test_type')}", "测试")
    return jsonify({'success': True, 'data': {'id': report_id}})

@app.route('/api/projects/<int:project_id>/run-step', methods=['POST'])
def run_project_step(project_id):
    """执行项目的某个步骤"""
    data = request.get_json()
    step_name = data.get('step')
    
    project = db.get_project(project_id)
    if not project:
        return jsonify({'success': False, 'error': '项目不存在'})
    
    logger = get_logger(f"流水线-{step_name}")
    logger.info(f"开始执行步骤: {step_name} (项目: {project['name']})")
    
    # 更新步骤状态为运行中
    db.update_step(project_id, step_name, 'running')
    
    try:
        result = execute_step(project, step_name)
        
        if result.get('success'):
            db.update_step(project_id, step_name, 'success', result=result.get('data'))
            
            # 添加发布记录
            if step_name in ['github', 'pypi', 'emcp', 'lobehub', 'mcpso']:
                db.add_publish_record(
                    project_id=project_id,
                    target=step_name,
                    target_url=result.get('data', {}).get('url'),
                    package_name=result.get('data', {}).get('package_name'),
                    status='success'
                )
            
            logger.success(f"步骤完成: {step_name}")
            db.add_log(f'step_{step_name}', f'{step_name}执行成功', 'success', project_id, result.get('data'))
            
            return jsonify({'success': True, 'data': result.get('data')})
        else:
            db.update_step(project_id, step_name, 'failed', error_message=result.get('error'))
            logger.error(f"步骤失败: {result.get('error')}")
            db.add_log(f'step_{step_name}', f'{step_name}执行失败: {result.get("error")}', 'error', project_id)
            
            return jsonify({'success': False, 'error': result.get('error')})
            
    except Exception as e:
        db.update_step(project_id, step_name, 'failed', error_message=str(e))
        logger.error(f"步骤异常: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


def execute_step(project: dict, step_name: str) -> dict:
    """执行具体步骤"""
    
    if step_name == 'crawl':
        # API爬取
        source_type = project.get('source_type')
        source_url = project.get('source_url')
        
        if source_type == 'rapidapi':
            from modules.api_crawler import crawl_rapidapi_url
            return crawl_rapidapi_url(source_url)
        elif source_type == 'baidu':
            from modules.api_crawler import crawl_baidu_api
            return crawl_baidu_api()
        else:
            return {'success': True, 'data': {'message': '跳过爬取步骤'}}
    
    elif step_name == 'convert':
        # MCP转换
        from modules.api_crawler import convert_openapi_to_mcp
        metadata = project.get('metadata', {})
        openapi_spec = metadata.get('openapi_spec', {})
        return convert_openapi_to_mcp(openapi_spec, project['name'])
    
    elif step_name == 'github':
        # GitHub发布
        from modules.mcp_publisher import publish_to_github_org
        local_path = project.get('local_path', '')
        return publish_to_github_org(
            local_path, 
            get_config('github.org_name', 'BACH-AI-Tools')
        )
    
    elif step_name == 'pypi':
        # PyPI发布
        from modules.mcp_publisher import publish_to_pypi_registry
        local_path = project.get('local_path', '')
        return publish_to_pypi_registry(
            local_path, 
            get_config('pypi.use_test_pypi', True)
        )
    
    elif step_name == 'emcp':
        # EMCP发布（含平台测试）
        from modules.mcp_publisher import publish_to_emcp_platform
        import time
        
        local_path = project.get('local_path', '')
        
        # 检查是否通过本地测试
        if not db.has_passed_test(project['id'], 'local'):
            return {'success': False, 'error': '请先通过本地测试再上架市场'}
        
        start_time = time.time()
        result = publish_to_emcp_platform(local_path)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 保存EMCP平台测试报告
        if result.get('success'):
            emcp_test = result.get('data', {}).get('test_result', {})
            db.add_test_report(
                project_id=project['id'],
                test_type='platform',
                platform='emcp',
                status='success' if emcp_test.get('passed', True) else 'failed',
                passed=emcp_test.get('passed_count', 1),
                failed=emcp_test.get('failed_count', 0),
                duration_ms=duration_ms,
                report_data=emcp_test
            )
        
        return result
    
    elif step_name == 'lobehub':
        # LobeHub提交
        from modules.platform_publisher import submit_to_lobehub
        metadata = project.get('metadata', {})
        github_url = metadata.get('github_url', '')
        if github_url:
            return submit_to_lobehub([github_url])
        return {'success': False, 'error': '缺少GitHub URL'}
    
    elif step_name == 'mcpso':
        # mcp.so提交
        from modules.platform_publisher import submit_to_mcpso
        metadata = project.get('metadata', {})
        github_url = metadata.get('github_url', '')
        if github_url:
            return submit_to_mcpso([github_url])
        return {'success': False, 'error': '缺少GitHub URL'}
    
    elif step_name == 'online_test':
        # 线上测试（平台验证）
        from modules.mcp_publisher import test_online_mcp
        import time
        
        # 获取已上架的平台信息
        publish_records = db.get_publish_records(project_id=project['id'])
        platforms = [r['target'] for r in publish_records if r['target'] in ['emcp', 'lobehub', 'mcpso']]
        
        if not platforms:
            return {'success': False, 'error': '请先上架到至少一个市场平台'}
        
        start_time = time.time()
        results = []
        total_passed = 0
        total_failed = 0
        
        for platform in platforms:
            record = next((r for r in publish_records if r['target'] == platform), None)
            if record:
                result = test_online_mcp(platform, record.get('target_url'), record.get('package_name'))
                results.append({'platform': platform, 'result': result})
                
                if result.get('success'):
                    total_passed += 1
                else:
                    total_failed += 1
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 保存线上测试报告
        db.add_test_report(
            project_id=project['id'],
            test_type='online',
            status='success' if total_failed == 0 else 'failed',
            passed=total_passed,
            failed=total_failed,
            duration_ms=duration_ms,
            report_data={'platforms': results}
        )
        
        if total_failed == 0:
            return {'success': True, 'data': {'platforms': results, 'message': f'所有{len(platforms)}个平台测试通过'}}
        else:
            return {'success': False, 'error': f'{total_failed}个平台测试失败', 'data': {'platforms': results}}
    
    elif step_name == 'local_test':
        # 本地测试（上架前必须通过）
        from modules.mcp_publisher import test_mcp_server
        import time
        
        local_path = project.get('local_path', '')
        start_time = time.time()
        result = test_mcp_server(local_path)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 保存测试报告
        if result.get('success'):
            tests = result.get('data', {}).get('tests', [])
            passed = sum(1 for t in tests if t.get('passed'))
            failed = len(tests) - passed
            
            db.add_test_report(
                project_id=project['id'],
                test_type='local',
                status='success' if failed == 0 else 'failed',
                passed=passed,
                failed=failed,
                duration_ms=duration_ms,
                report_data=result.get('data')
            )
        else:
            db.add_test_report(
                project_id=project['id'],
                test_type='local',
                status='failed',
                failed=1,
                duration_ms=duration_ms,
                error_message=result.get('error')
            )
        
        return result
    
    return {'success': False, 'error': f'未知步骤: {step_name}'}

# ==================== 日志API ====================

@app.route('/api/logs')
def get_logs():
    limit = request.args.get('limit', 100, type=int)
    level = request.args.get('level')
    module = request.args.get('module')
    
    logs_list = log.get_logs(limit=limit, level=level, module=module)
    return jsonify({'success': True, 'data': logs_list})

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    log.clear()
    return jsonify({'success': True})

@app.route('/api/logs/stream')
def log_stream():
    def generate():
        q = queue.Queue()
        log_queues.append(q)
        
        try:
            while True:
                try:
                    entry = q.get(timeout=30)
                    yield f"data: {json.dumps(entry, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        finally:
            log_queues.remove(q)
    
    return Response(generate(), mimetype='text/event-stream')

def broadcast_log(entry):
    for q in log_queues:
        q.put(entry)

log.add_listener(broadcast_log)

# ==================== 配置API ====================

@app.route('/api/config')
def get_all_config():
    return jsonify({'success': True, 'data': config.get_all()})

@app.route('/api/config/<section>')
def get_config_section(section):
    return jsonify({'success': True, 'data': config.get_section(section)})

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.get_json()
    
    if 'path' in data and 'value' in data:
        set_config(data['path'], data['value'])
    elif 'section' in data and 'data' in data:
        config.set_section(data['section'], data['data'])
    else:
        for key, value in data.items():
            if isinstance(value, dict):
                config.set_section(key, value)
    
    log.info("配置已更新", "系统")
    return jsonify({'success': True})

@app.route('/api/config/reset', methods=['POST'])
def reset_config():
    config.reset()
    log.info("配置已重置为默认值", "系统")
    return jsonify({'success': True})

# ==================== 兼容旧API ====================

@app.route('/api/crawler/rapidapi', methods=['POST'])
def crawl_rapidapi():
    data = request.get_json()
    url = data.get('url', '')
    use_selenium = data.get('use_selenium', get_config('crawler.rapidapi.use_selenium', False))
    
    logger = get_logger("RapidAPI爬取")
    logger.info(f"开始爬取: {url}")
    
    try:
        from modules.api_crawler import crawl_rapidapi_url
        result = crawl_rapidapi_url(url, use_selenium)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"爬取异常: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/projects/list')
def list_projects_legacy():
    """兼容旧的项目列表API"""
    try:
        from modules.project_manager import list_mcp_projects, get_stats
        projects = list_mcp_projects()
        stats = get_stats()
        return jsonify({'success': True, 'data': projects, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/projects/github-org')
def list_github_org():
    org_name = request.args.get('org', get_config('github.org_name', 'BACH-AI-Tools'))
    
    try:
        from modules.project_manager import list_github_org_repos
        repos = list_github_org_repos(org_name)
        return jsonify({'success': True, 'data': repos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    log.info("MCP工厂 Web界面启动", "系统")
    print("\n" + "="*50)
    print("  🏭 MCP工厂 - 完整流水线")
    print("="*50)
    print(f"  📍 主页: http://localhost:5000")
    print(f"  🏭 流水线: http://localhost:5000/pipeline")
    print(f"  📦 项目记录: http://localhost:5000/projects")
    print(f"  ⚙️  配置: http://localhost:5000/settings")
    print(f"  📜 日志: http://localhost:5000/logs")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

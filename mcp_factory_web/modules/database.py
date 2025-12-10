"""
MCP工厂数据库模块
使用SQLite保存项目发布记录
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum
from contextlib import contextmanager


# 数据库文件路径
DB_PATH = Path(__file__).parent.parent / "data" / "mcp_factory.db"


class ProjectStatus(Enum):
    """项目状态"""
    CREATED = "created"           # 已创建
    CRAWLED = "crawled"           # 已爬取
    CONVERTED = "converted"       # 已转换为MCP
    GITHUB_PUBLISHED = "github"   # 已发布GitHub
    PYPI_PUBLISHED = "pypi"       # 已发布PyPI
    EMCP_PUBLISHED = "emcp"       # 已发布EMCP
    PLATFORM_SUBMITTED = "platform"  # 已提交第三方平台
    COMPLETED = "completed"       # 全部完成
    FAILED = "failed"             # 失败


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Database:
    """数据库管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 项目表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source_type TEXT,
                    source_url TEXT,
                    local_path TEXT,
                    status TEXT DEFAULT 'created',
                    current_step INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # 步骤记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pipeline_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    step_order INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result TEXT,
                    error_message TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            ''')
            
            # 发布记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS publish_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    target TEXT NOT NULL,
                    target_url TEXT,
                    package_name TEXT,
                    version TEXT,
                    status TEXT DEFAULT 'pending',
                    published_at TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            ''')
            
            # 操作日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    operation TEXT NOT NULL,
                    level TEXT DEFAULT 'info',
                    message TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            ''')
            
            # 测试报告表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    test_type TEXT NOT NULL,
                    platform TEXT,
                    status TEXT DEFAULT 'pending',
                    passed INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    skipped INTEGER DEFAULT 0,
                    duration_ms INTEGER,
                    report_data TEXT,
                    error_message TEXT,
                    tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            ''')
            
            conn.commit()
    
    # ========== 项目操作 ==========
    
    def create_project(self, name: str, source_type: str = None, source_url: str = None, 
                       local_path: str = None, metadata: dict = None) -> int:
        """创建新项目"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO projects (name, source_type, source_url, local_path, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, source_type, source_url, local_path, json.dumps(metadata or {})))
            
            project_id = cursor.lastrowid
            
            # 初始化流水线步骤
            steps = [
                ('crawl', 1),        # 爬取API
                ('convert', 2),      # 转换MCP
                ('github', 3),       # 发布GitHub
                ('pypi', 4),         # 发布包源 (PyPI/NPM)
                ('local_test', 5),   # 本地测试（上架前必须通过）
                ('emcp', 6),         # 上架EMCP市场
                ('lobehub', 7),      # 上架LobeHub市场
                ('mcpso', 8),        # 上架mcp.so市场
                ('online_test', 9),  # 线上测试（平台验证）
            ]
            
            for step_name, step_order in steps:
                cursor.execute('''
                    INSERT INTO pipeline_steps (project_id, step_name, step_order)
                    VALUES (?, ?, ?)
                ''', (project_id, step_name, step_order))
            
            return project_id
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """获取项目详情"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
            row = cursor.fetchone()
            
            if row:
                project = dict(row)
                project['metadata'] = json.loads(project['metadata'] or '{}')
                project['steps'] = self.get_project_steps(project_id)
                project['publish_records'] = self.get_publish_records(project_id)
                return project
            return None
    
    def get_project_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取项目"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM projects WHERE name = ?', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_projects(self, status: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """列出项目"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM projects WHERE status = ?
                    ORDER BY updated_at DESC LIMIT ? OFFSET ?
                ''', (status, limit, offset))
            else:
                cursor.execute('''
                    SELECT * FROM projects
                    ORDER BY updated_at DESC LIMIT ? OFFSET ?
                ''', (limit, offset))
            
            projects = []
            for row in cursor.fetchall():
                project = dict(row)
                project['metadata'] = json.loads(project['metadata'] or '{}')
                projects.append(project)
            
            return projects
    
    def update_project(self, project_id: int, **kwargs):
        """更新项目"""
        allowed_fields = ['name', 'source_type', 'source_url', 'local_path', 
                         'status', 'current_step', 'completed_at', 'metadata']
        
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f'{field} = ?')
                if field == 'metadata' and isinstance(value, dict):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
        
        if not updates:
            return
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        values.append(project_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE projects SET {', '.join(updates)} WHERE id = ?
            ''', values)
    
    def delete_project(self, project_id: int):
        """删除项目"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM pipeline_steps WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM publish_records WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM operation_logs WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    
    # ========== 步骤操作 ==========
    
    def get_project_steps(self, project_id: int) -> List[Dict]:
        """获取项目的所有步骤"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM pipeline_steps WHERE project_id = ?
                ORDER BY step_order
            ''', (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_step(self, project_id: int, step_name: str, status: str, 
                    result: dict = None, error_message: str = None):
        """更新步骤状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status == 'running':
                cursor.execute('''
                    UPDATE pipeline_steps 
                    SET status = ?, started_at = CURRENT_TIMESTAMP
                    WHERE project_id = ? AND step_name = ?
                ''', (status, project_id, step_name))
            elif status in ('success', 'failed'):
                cursor.execute('''
                    UPDATE pipeline_steps 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP,
                        result = ?, error_message = ?
                    WHERE project_id = ? AND step_name = ?
                ''', (status, json.dumps(result) if result else None, 
                      error_message, project_id, step_name))
            else:
                cursor.execute('''
                    UPDATE pipeline_steps SET status = ?
                    WHERE project_id = ? AND step_name = ?
                ''', (status, project_id, step_name))
    
    def get_step_status(self, project_id: int, step_name: str) -> Optional[str]:
        """获取步骤状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status FROM pipeline_steps 
                WHERE project_id = ? AND step_name = ?
            ''', (project_id, step_name))
            row = cursor.fetchone()
            return row['status'] if row else None
    
    # ========== 发布记录 ==========
    
    def add_publish_record(self, project_id: int, target: str, target_url: str = None,
                          package_name: str = None, version: str = None, 
                          status: str = 'success', metadata: dict = None) -> int:
        """添加发布记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO publish_records 
                (project_id, target, target_url, package_name, version, status, 
                 published_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (project_id, target, target_url, package_name, version, status,
                  json.dumps(metadata or {})))
            return cursor.lastrowid
    
    def get_publish_records(self, project_id: int = None, target: str = None) -> List[Dict]:
        """获取发布记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if project_id and target:
                cursor.execute('''
                    SELECT * FROM publish_records 
                    WHERE project_id = ? AND target = ?
                    ORDER BY published_at DESC
                ''', (project_id, target))
            elif project_id:
                cursor.execute('''
                    SELECT * FROM publish_records WHERE project_id = ?
                    ORDER BY published_at DESC
                ''', (project_id,))
            elif target:
                cursor.execute('''
                    SELECT * FROM publish_records WHERE target = ?
                    ORDER BY published_at DESC
                ''', (target,))
            else:
                cursor.execute('SELECT * FROM publish_records ORDER BY published_at DESC')
            
            records = []
            for row in cursor.fetchall():
                record = dict(row)
                record['metadata'] = json.loads(record['metadata'] or '{}')
                records.append(record)
            
            return records
    
    # ========== 操作日志 ==========
    
    def add_log(self, operation: str, message: str, level: str = 'info',
                project_id: int = None, details: dict = None):
        """添加操作日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operation_logs (project_id, operation, level, message, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (project_id, operation, level, message, json.dumps(details) if details else None))
    
    def get_logs(self, project_id: int = None, operation: str = None, 
                 limit: int = 100) -> List[Dict]:
        """获取操作日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            values = []
            
            if project_id:
                conditions.append('project_id = ?')
                values.append(project_id)
            if operation:
                conditions.append('operation = ?')
                values.append(operation)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            values.append(limit)
            
            cursor.execute(f'''
                SELECT * FROM operation_logs {where_clause}
                ORDER BY created_at DESC LIMIT ?
            ''', values)
            
            logs = []
            for row in cursor.fetchall():
                log = dict(row)
                log['details'] = json.loads(log['details'] or '{}') if log['details'] else None
                logs.append(log)
            
            return logs
    
    # ========== 测试报告 ==========
    
    def add_test_report(self, project_id: int, test_type: str, platform: str = None,
                       status: str = 'success', passed: int = 0, failed: int = 0,
                       skipped: int = 0, duration_ms: int = 0, 
                       report_data: dict = None, error_message: str = None) -> int:
        """添加测试报告"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO test_reports 
                (project_id, test_type, platform, status, passed, failed, skipped,
                 duration_ms, report_data, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (project_id, test_type, platform, status, passed, failed, skipped,
                  duration_ms, json.dumps(report_data) if report_data else None, error_message))
            return cursor.lastrowid
    
    def get_test_reports(self, project_id: int = None, test_type: str = None,
                        platform: str = None) -> List[Dict]:
        """获取测试报告"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            values = []
            
            if project_id:
                conditions.append('project_id = ?')
                values.append(project_id)
            if test_type:
                conditions.append('test_type = ?')
                values.append(test_type)
            if platform:
                conditions.append('platform = ?')
                values.append(platform)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            cursor.execute(f'''
                SELECT * FROM test_reports {where_clause}
                ORDER BY tested_at DESC
            ''', values)
            
            reports = []
            for row in cursor.fetchall():
                report = dict(row)
                report['report_data'] = json.loads(report['report_data'] or '{}') if report['report_data'] else None
                reports.append(report)
            
            return reports
    
    def get_latest_test_report(self, project_id: int, test_type: str = None) -> Optional[Dict]:
        """获取最新的测试报告"""
        reports = self.get_test_reports(project_id, test_type)
        return reports[0] if reports else None
    
    def has_passed_test(self, project_id: int, test_type: str) -> bool:
        """检查是否通过了指定类型的测试"""
        report = self.get_latest_test_report(project_id, test_type)
        return report is not None and report.get('status') == 'success' and report.get('failed', 0) == 0
    
    # ========== 统计 ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 项目统计
            cursor.execute('SELECT COUNT(*) as count FROM projects')
            total_projects = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status = 'completed'")
            completed_projects = cursor.fetchone()['count']
            
            # 发布统计
            cursor.execute("SELECT COUNT(*) as count FROM publish_records WHERE target = 'github'")
            github_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM publish_records WHERE target = 'pypi'")
            pypi_count = cursor.fetchone()['count']
            
            # 所有市场平台（EMCP、LobeHub、mcp.so）
            cursor.execute("SELECT COUNT(*) as count FROM publish_records WHERE target IN ('emcp', 'lobehub', 'mcpso')")
            platform_count = cursor.fetchone()['count']
            
            return {
                'total_projects': total_projects,
                'completed_projects': completed_projects,
                'github_published': github_count,
                'pypi_published': pypi_count,
                'platform_submitted': platform_count  # 包含EMCP、LobeHub、mcp.so
            }


# 全局数据库实例
db = Database()


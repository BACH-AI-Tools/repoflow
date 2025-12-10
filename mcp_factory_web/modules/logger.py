"""
统一日志管理系统
提供实时日志记录、WebSocket推送、日志存储
"""

import os
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from enum import Enum


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class LogEntry:
    """日志条目"""
    def __init__(self, level: LogLevel, message: str, module: str = "", details: Any = None):
        self.id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.timestamp = datetime.now().isoformat()
        self.time_str = datetime.now().strftime("%H:%M:%S")
        self.level = level.value
        self.message = message
        self.module = module
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "time": self.time_str,
            "level": self.level,
            "message": self.message,
            "module": self.module,
            "details": self.details
        }


class LogManager:
    """日志管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logs: deque = deque(maxlen=1000)  # 保留最近1000条
        self.listeners: List[Callable] = []
        self.log_file = Path(__file__).parent.parent / "outputs" / "factory.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置Python logging
        self.logger = logging.getLogger("MCPFactory")
        self.logger.setLevel(logging.DEBUG)
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        self.logger.addHandler(file_handler)
    
    def add_listener(self, callback: Callable):
        """添加日志监听器"""
        self.listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """移除日志监听器"""
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    def _notify_listeners(self, entry: LogEntry):
        """通知所有监听器"""
        for listener in self.listeners:
            try:
                listener(entry.to_dict())
            except:
                pass
    
    def log(self, level: LogLevel, message: str, module: str = "", details: Any = None):
        """记录日志"""
        entry = LogEntry(level, message, module, details)
        self.logs.append(entry)
        
        # 写入文件
        log_line = f"[{entry.time_str}] [{level.value.upper()}] [{module}] {message}"
        if details:
            log_line += f" | {json.dumps(details, ensure_ascii=False)}"
        
        if level == LogLevel.DEBUG:
            self.logger.debug(log_line)
        elif level == LogLevel.INFO:
            self.logger.info(log_line)
        elif level == LogLevel.SUCCESS:
            self.logger.info(f"✓ {log_line}")
        elif level == LogLevel.WARNING:
            self.logger.warning(log_line)
        elif level == LogLevel.ERROR:
            self.logger.error(log_line)
        
        # 通知监听器
        self._notify_listeners(entry)
        
        return entry
    
    def debug(self, message: str, module: str = "", details: Any = None):
        return self.log(LogLevel.DEBUG, message, module, details)
    
    def info(self, message: str, module: str = "", details: Any = None):
        return self.log(LogLevel.INFO, message, module, details)
    
    def success(self, message: str, module: str = "", details: Any = None):
        return self.log(LogLevel.SUCCESS, message, module, details)
    
    def warning(self, message: str, module: str = "", details: Any = None):
        return self.log(LogLevel.WARNING, message, module, details)
    
    def error(self, message: str, module: str = "", details: Any = None):
        return self.log(LogLevel.ERROR, message, module, details)
    
    def get_logs(self, limit: int = 100, level: Optional[str] = None, module: Optional[str] = None) -> List[Dict]:
        """获取日志列表"""
        logs = list(self.logs)
        
        if level:
            logs = [l for l in logs if l.level == level]
        if module:
            logs = [l for l in logs if l.module == module]
        
        # 返回最新的
        logs = logs[-limit:]
        return [l.to_dict() for l in logs]
    
    def clear(self):
        """清空日志"""
        self.logs.clear()
    
    def export_logs(self, filepath: Optional[str] = None) -> str:
        """导出日志到文件"""
        if filepath is None:
            filepath = self.log_file.parent / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        logs = [l.to_dict() for l in self.logs]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        return str(filepath)


# 全局日志实例
log = LogManager()


def get_logger(module: str = ""):
    """获取模块专用日志器"""
    class ModuleLogger:
        def __init__(self, module_name: str):
            self.module = module_name
        
        def debug(self, msg: str, details: Any = None):
            log.debug(msg, self.module, details)
        
        def info(self, msg: str, details: Any = None):
            log.info(msg, self.module, details)
        
        def success(self, msg: str, details: Any = None):
            log.success(msg, self.module, details)
        
        def warning(self, msg: str, details: Any = None):
            log.warning(msg, self.module, details)
        
        def error(self, msg: str, details: Any = None):
            log.error(msg, self.module, details)
    
    return ModuleLogger(module)


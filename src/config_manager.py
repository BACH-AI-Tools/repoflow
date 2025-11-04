"""配置管理模块"""

import json
from pathlib import Path


class ConfigManager:
    """管理 RepoFlow 配置"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.repoflow'
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(exist_ok=True)
    
    def load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_file.exists():
            return {}
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_config(self, config: dict):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default=None):
        """获取配置项"""
        config = self.load_config()
        return config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置项"""
        config = self.load_config()
        config[key] = value
        self.save_config(config)


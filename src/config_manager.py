"""配置管理模块"""

import json
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """管理 EMCPFlow 配置"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = Path.home() / '.emcpflow'
        self.config_file = self.config_dir / 'config.json'
        self.config_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self._config = self.load_config()
    
    def save_session(self, session_key: str, user_info: dict):
        """
        保存登录 Session
        
        Args:
            session_key: Session 密钥
            user_info: 用户信息
        """
        config = self.load_config()
        config['emcp_session'] = {
            'session_key': session_key,
            'user_info': user_info
        }
        self.save_config(config)
    
    def load_session(self) -> dict:
        """
        加载登录 Session
        
        Returns:
            Session 信息字典
        """
        config = self.load_config()
        return config.get('emcp_session', {})
    
    def save_config(self, config: dict):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"保存配置失败: {str(e)}")
    
    def load_config(self) -> dict:
        """加载配置"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def clear_session(self):
        """清除 Session"""
        config = self.load_config()
        if 'emcp_session' in config:
            del config['emcp_session']
            self.save_config(config)
    
    # ========== EMCP 用户凭据 ==========
    
    def save_emcp_credentials(self, phone_number: str, validation_code: str):
        """
        保存 EMCP 用户凭据
        
        Args:
            phone_number: 手机号
            validation_code: 验证码
        """
        self._config['emcp_credentials'] = {
            'phone_number': phone_number,
            'validation_code': validation_code
        }
        self.save_config(self._config)
    
    def load_emcp_credentials(self) -> Optional[Dict]:
        """
        加载 EMCP 用户凭据
        
        Returns:
            {'phone_number': str, 'validation_code': str} 或 None
        """
        return self._config.get('emcp_credentials')
    
    def has_emcp_credentials(self) -> bool:
        """检查是否配置了 EMCP 凭据"""
        creds = self.load_emcp_credentials()
        return creds is not None and creds.get('phone_number') and creds.get('validation_code')
    
    # ========== Azure OpenAI 配置 ==========
    
    def save_azure_openai_config(
        self,
        azure_endpoint: str,
        api_key: str,
        deployment_name: str = "gpt-4",
        api_version: str = "2024-02-15-preview"
    ):
        """
        保存 Azure OpenAI 配置
        
        Args:
            azure_endpoint: Azure OpenAI endpoint
            api_key: API key
            deployment_name: 部署名称
            api_version: API 版本
        """
        self._config['azure_openai'] = {
            'azure_endpoint': azure_endpoint,
            'api_key': api_key,
            'deployment_name': deployment_name,
            'api_version': api_version
        }
        self.save_config(self._config)
    
    def load_azure_openai_config(self) -> Optional[Dict]:
        """
        加载 Azure OpenAI 配置
        
        Returns:
            配置字典 或 None
        """
        return self._config.get('azure_openai')
    
    def has_azure_openai_config(self) -> bool:
        """检查是否配置了 Azure OpenAI"""
        config = self.load_azure_openai_config()
        return config is not None and config.get('azure_endpoint') and config.get('api_key')
    
    # ========== 通用配置 ==========
    
    def set_config(self, key: str, value):
        """设置配置项"""
        self._config[key] = value
        self.save_config(self._config)
    
    def get_config(self, key: str, default=None):
        """获取配置项"""
        return self._config.get(key, default)
    
    def clear_all_config(self):
        """清除所有配置"""
        self._config = {}
        if self.config_file.exists():
            self.config_file.unlink()




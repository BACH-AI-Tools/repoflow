#!/usr/bin/env python3
"""
统一配置管理器
管理 RepoFlow 和 EMCPFlow 的所有配置
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class UnifiedConfigManager:
    """统一配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = Path.home() / ".repoflow"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._get_default_config()
        return self._get_default_config()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def export_config(self, export_path: str) -> bool:
        """导出配置到指定路径"""
        try:
            config = self.load_config()
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """从指定路径导入配置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return self.save_config(config)
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # GitHub 配置
            "github": {
                "token": "",
                "org_name": "BACH-AI-Tools"
            },
            
            # EMCP 平台配置
            "emcp": {
                "base_url": "https://sit-emcp.kaleido.guru",
                "phone_number": "",
                "validation_code": ""
            },
            
            # Agent 平台配置
            "agent": {
                "base_url": "https://v5.kaleido.guru",
                "phone_number": "",
                "validation_code": ""
            },
            
            # Azure OpenAI 配置
            "azure_openai": {
                "endpoint": "",
                "api_key": "",
                "api_version": "2024-02-15-preview",
                "deployment_name": "gpt-4o"
            },
            
            # 即梦 AI 配置
            "jimeng": {
                "enabled": True,
                "mcp_url": "sse+https://jm-mcp.kaleido.guru/sse"
            },
            
            # EdgeOne 配置
            "edgeone": {
                "enabled": True,
                "api_url": "https://mcp-on-edge.edgeone.app/kv/set"
            },
            
            # PyPI 配置
            "pypi": {
                "mirror_url": "https://pypi.tuna.tsinghua.edu.cn/simple"
            },
            
            # 其他配置
            "other": {
                "auto_publish": True,
                "private_repo": False,
                "default_version": "1.0.0"
            },
            
            # 会话信息（运行时）
            "session": {
                "emcp_session_key": "",
                "emcp_user_info": {},
                "agent_session_key": "",
                "agent_user_info": {}
            }
        }
    
    # ===== GitHub 配置 =====
    
    def get_github_token(self) -> str:
        """获取 GitHub Token"""
        config = self.load_config()
        return config.get("github", {}).get("token", "")
    
    def set_github_token(self, token: str) -> bool:
        """设置 GitHub Token"""
        config = self.load_config()
        if "github" not in config:
            config["github"] = {}
        config["github"]["token"] = token
        return self.save_config(config)
    
    def get_github_org(self) -> str:
        """获取 GitHub 组织名"""
        config = self.load_config()
        return config.get("github", {}).get("org_name", "BACH-AI-Tools")
    
    def set_github_org(self, org_name: str) -> bool:
        """设置 GitHub 组织名"""
        config = self.load_config()
        if "github" not in config:
            config["github"] = {}
        config["github"]["org_name"] = org_name
        return self.save_config(config)
    
    # ===== EMCP 平台配置 =====
    
    def get_emcp_config(self) -> Dict[str, str]:
        """获取 EMCP 配置"""
        from datetime import datetime
        config = self.load_config()
        emcp_config = config.get("emcp", {})
        # 自动生成今日验证码
        emcp_config["validation_code"] = datetime.now().strftime("%m%Y%d")
        return emcp_config
    
    def set_emcp_config(self, base_url: str, phone: str, code: str) -> bool:
        """设置 EMCP 配置"""
        config = self.load_config()
        config["emcp"] = {
            "base_url": base_url,
            "phone_number": phone,
            "validation_code": code
        }
        return self.save_config(config)
    
    # ===== Agent 平台配置 =====
    
    def get_agent_config(self) -> Dict[str, str]:
        """获取 Agent 配置"""
        from datetime import datetime
        config = self.load_config()
        agent_config = config.get("agent", {})
        # 自动生成今日验证码
        agent_config["validation_code"] = datetime.now().strftime("%m%Y%d")
        return agent_config
    
    def set_agent_config(self, base_url: str, phone: str, code: str) -> bool:
        """设置 Agent 配置"""
        config = self.load_config()
        config["agent"] = {
            "base_url": base_url,
            "phone_number": phone,
            "validation_code": code
        }
        return self.save_config(config)
    
    # ===== Azure OpenAI 配置 =====
    
    def get_azure_openai_config(self) -> Dict[str, str]:
        """获取 Azure OpenAI 配置"""
        config = self.load_config()
        return config.get("azure_openai", {})
    
    def set_azure_openai_config(self, endpoint: str, api_key: str, 
                                 api_version: str, deployment_name: str) -> bool:
        """设置 Azure OpenAI 配置"""
        config = self.load_config()
        config["azure_openai"] = {
            "endpoint": endpoint,
            "api_key": api_key,
            "api_version": api_version,
            "deployment_name": deployment_name
        }
        return self.save_config(config)
    
    # ===== 即梦 AI 配置 =====
    
    def get_jimeng_config(self) -> Dict[str, Any]:
        """获取即梦 AI 配置"""
        config = self.load_config()
        return config.get("jimeng", {})
    
    def set_jimeng_enabled(self, enabled: bool) -> bool:
        """设置即梦 AI 启用状态"""
        config = self.load_config()
        if "jimeng" not in config:
            config["jimeng"] = {}
        config["jimeng"]["enabled"] = enabled
        return self.save_config(config)
    
    # ===== EdgeOne 配置 =====
    
    def get_edgeone_config(self) -> Dict[str, Any]:
        """获取 EdgeOne 配置"""
        config = self.load_config()
        return config.get("edgeone", {})
    
    def set_edgeone_enabled(self, enabled: bool) -> bool:
        """设置 EdgeOne 启用状态"""
        config = self.load_config()
        if "edgeone" not in config:
            config["edgeone"] = {}
        config["edgeone"]["enabled"] = enabled
        return self.save_config(config)
    
    # ===== PyPI 配置 =====
    
    def get_pypi_mirror(self) -> str:
        """获取 PyPI 镜像源"""
        config = self.load_config()
        return config.get("pypi", {}).get("mirror_url", "https://pypi.tuna.tsinghua.edu.cn/simple")
    
    def set_pypi_mirror(self, mirror_url: str) -> bool:
        """设置 PyPI 镜像源"""
        config = self.load_config()
        if "pypi" not in config:
            config["pypi"] = {}
        config["pypi"]["mirror_url"] = mirror_url
        return self.save_config(config)
    
    # ===== 会话管理 =====
    
    def get_emcp_session(self) -> Dict[str, Any]:
        """获取 EMCP 会话信息"""
        config = self.load_config()
        return config.get("session", {})
    
    def set_emcp_session(self, session_key: str, user_info: Dict) -> bool:
        """设置 EMCP 会话信息"""
        config = self.load_config()
        if "session" not in config:
            config["session"] = {}
        config["session"]["emcp_session_key"] = session_key
        config["session"]["emcp_user_info"] = user_info
        return self.save_config(config)
    
    def set_agent_session(self, session_key: str, user_info: Dict) -> bool:
        """设置 Agent 会话信息"""
        config = self.load_config()
        if "session" not in config:
            config["session"] = {}
        config["session"]["agent_session_key"] = session_key
        config["session"]["agent_user_info"] = user_info
        return self.save_config(config)
    
    # ===== 其他配置 =====
    
    def get_other_config(self) -> Dict[str, Any]:
        """获取其他配置"""
        config = self.load_config()
        return config.get("other", {})
    
    def get_config_file_path(self) -> str:
        """获取配置文件路径"""
        return str(self.config_file)


"""
MCP工厂配置管理模块
统一管理所有配置项
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional


CONFIG_FILE = Path(__file__).parent.parent / "config.json"

# 默认配置
DEFAULT_CONFIG = {
    # LLM配置 (Azure OpenAI) - 很多步骤都会用到
    "llm": {
        "azure_endpoint": "",
        "azure_api_key": "",
        "azure_deployment": "gpt-4o",
        "azure_api_version": "2024-10-21",
        "fallback_model": "gpt-3.5-turbo"
    },
    
    # GitHub配置
    "github": {
        "token": "",
        "org_name": "BACH-AI-Tools",
        "default_branch": "main",
        "private_repo": False,
        "add_workflows": True
    },
    
    # PyPI配置
    "pypi": {
        "token": "",
        "test_token": "",
        "use_test_pypi": True
    },
    
    # EMCP配置 (包含即梦Logo生成、Agent测试)
    "emcp": {
        "api_url": "https://sit-emcp.kaleido.guru/",
        "token": "",
        # 即梦 (Logo生成) - 需要 Access Key 和 Secret Key
        "jimeng_access_key": "",
        "jimeng_secret_key": "",
        "auto_generate_logo": True,
        "logo_prompt_template": "为MCP服务器项目"{name}"生成一个简洁现代的图标。这是一个{description}的AI工具接口。要求：1.图标要体现该API的核心功能和用途 2.扁平化设计风格 3.科技感、专业感 4.蓝绿色调为主 5.适合作为软件包的Logo",
        # Agent测试
        "agent_test_model": "gpt-4o",
        "agent_test_timeout": 60,
        "agent_test_enabled": True
    },
    
    # API爬取配置
    "crawler": {
        "rapidapi": {
            "api_key": "",
            "use_selenium": False
        },
        "baidu": {
            "cookie": "",
            "max_products": 5
        },
        # 描述增强 (使用LLM)
        "enhance_description": True,
        "enhance_prompt": """请为以下API生成三种语言的描述（简体中文、繁体中文、英文）：

API名称: {api_name}
原描述: {description}

要求：
1. 描述清晰准确，突出API的核心功能
2. 包含典型使用场景
3. 对AI Agent友好，便于理解和调用

请按以下格式输出：

【简体中文】
摘要: (一句话描述)
描述: (详细描述，包含功能、场景、注意事项)

【繁體中文】
摘要: (一句話描述)
描述: (詳細描述，包含功能、場景、注意事項)

【English】
Summary: (one-line description)
Description: (detailed description including features, use cases, notes)"""
    },
    
    # MCP生成配置
    "mcp": {
        "author": "bachai",
        "author_email": "contact@bachai.com",
        "transport": "stdio",
        "output_dir": "E:/code/generated_mcps",
        "add_tests": True,
        "add_readme": True,
        # EMCP平台引流话术
        "emcp_domain": "https://sit-emcp.kaleido.guru",
        "add_emcp_promo": True,
        "emcp_promo_zh": """## 🚀 使用 EMCP 平台快速体验

**[EMCP]({emcp_domain})** 是一个强大的 MCP 服务器管理平台，让您无需手动配置即可快速使用各种 MCP 服务器！

### 快速开始：

1. 🌐 访问 **[EMCP 平台]({emcp_domain})**
2. 📝 注册并登录账号
3. 🎯 进入 **MCP 广场**，浏览所有可用的 MCP 服务器
4. 🔍 搜索或找到本服务器（`{package_name}`）
5. 🎉 点击 **"安装 MCP"** 按钮
6. ✅ 完成！即可在您的应用中使用

### EMCP 平台优势：

- ✨ **零配置**：无需手动编辑配置文件
- 🎨 **可视化管理**：图形界面轻松管理所有 MCP 服务器
- 🔐 **安全可靠**：统一管理 API 密钥和认证信息
- 🚀 **一键安装**：MCP 广场提供丰富的服务器选择
- 📊 **使用统计**：实时查看服务调用情况

立即访问 **[EMCP 平台]({emcp_domain})** 开始您的 MCP 之旅！""",
        "emcp_promo_en": """## 🚀 Quick Start with EMCP Platform

**[EMCP]({emcp_domain})** is a powerful MCP server management platform that allows you to quickly use various MCP servers without manual configuration!

### Quick Start:

1. 🌐 Visit **[EMCP Platform]({emcp_domain})**
2. 📝 Register and login
3. 🎯 Go to **MCP Marketplace** to browse all available MCP servers
4. 🔍 Search or find this server (`{package_name}`)
5. 🎉 Click the **"Install MCP"** button
6. ✅ Done! You can now use it in your applications

### EMCP Platform Advantages:

- ✨ **Zero Configuration**: No need to manually edit config files
- 🎨 **Visual Management**: Easy-to-use GUI for managing all MCP servers
- 🔐 **Secure & Reliable**: Centralized API key and authentication management
- 🚀 **One-Click Install**: Rich selection of servers in MCP Marketplace
- 📊 **Usage Statistics**: Real-time service call monitoring

Visit **[EMCP Platform]({emcp_domain})** now to start your MCP journey!""",
        "emcp_promo_zh_tw": """## 🚀 使用 EMCP 平台快速體驗

**[EMCP]({emcp_domain})** 是一個強大的 MCP 伺服器管理平台，讓您無需手動配置即可快速使用各種 MCP 伺服器！

### 快速開始：

1. 🌐 造訪 **[EMCP 平台]({emcp_domain})**
2. 📝 註冊並登入帳號
3. 🎯 進入 **MCP 廣場**，瀏覽所有可用的 MCP 伺服器
4. 🔍 搜尋或找到本伺服器（`{package_name}`）
5. 🎉 點擊 **「安裝 MCP」** 按鈕
6. ✅ 完成！即可在您的應用中使用

### EMCP 平台優勢：

- ✨ **零配置**：無需手動編輯配置檔案
- 🎨 **視覺化管理**：圖形介面輕鬆管理所有 MCP 伺服器
- 🔐 **安全可靠**：統一管理 API 金鑰和認證資訊
- 🚀 **一鍵安裝**：MCP 廣場提供豐富的伺服器選擇
- 📊 **使用統計**：即時查看服務調用情況

立即造訪 **[EMCP 平台]({emcp_domain})** 開始您的 MCP 之旅！"""
    },
    
    # 第三方平台配置
    "platforms": {
        "lobehub": {
            "submit_url": "https://lobehub.com/submit",
            "enabled": True
        },
        "mcpso": {
            "submit_url": "https://mcp.so/submit",
            "user_data_dir": "",
            "enabled": True
        }
    },
    
    # Sonar配置
    "sonar": {
        "url": "",
        "token": "",
        "project_key_prefix": "mcp-",
        "enabled": False,
        "fail_on_issues": False
    }
}


class ConfigManager:
    """配置管理器"""
    
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
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 合并默认配置和已保存配置
                    return self._deep_merge(DEFAULT_CONFIG.copy(), loaded)
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()
    
    def _deep_merge(self, base: dict, override: dict) -> dict:
        """深度合并配置"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self):
        """保存配置到文件"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            path: 配置路径，如 "github.org_name"
            default: 默认值
        
        Returns:
            配置值
        """
        keys = path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, path: str, value: Any):
        """
        设置配置值
        
        Args:
            path: 配置路径
            value: 配置值
        """
        keys = path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self._save_config()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置区域"""
        return self._config.get(section, {})
    
    def set_section(self, section: str, data: Dict[str, Any]):
        """设置配置区域"""
        if section in self._config:
            self._config[section] = self._deep_merge(self._config[section], data)
        else:
            self._config[section] = data
        self._save_config()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def reset(self):
        """重置为默认配置"""
        self._config = DEFAULT_CONFIG.copy()
        self._save_config()
    
    def update(self, data: Dict[str, Any]):
        """批量更新配置"""
        self._config = self._deep_merge(self._config, data)
        self._save_config()


# 全局配置实例
config = ConfigManager()


# 便捷函数
def get_config(path: str, default: Any = None) -> Any:
    """获取配置值"""
    return config.get(path, default)


def set_config(path: str, value: Any):
    """设置配置值"""
    config.set(path, value)

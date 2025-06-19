"""
Configuration management for PodcastMCP
"""

import os
import json
from enum import Enum
from typing import Optional, Dict, Any
from pathlib import Path


class DeploymentMode(Enum):
    """部署模式枚举"""
    LOCAL = "local"       # 本地Gradio + Modal GPU endpoints
    MODAL = "modal"       # 完全在Modal平台运行
    HF_SPACES = "hf"      # Hugging Face Spaces部署


class AppConfig:
    """应用配置管理器"""
    
    def __init__(self):
        self._deployment_mode = self._detect_deployment_mode()
        self._cache_dir = self._get_cache_directory()
        self._endpoints = self._load_endpoints()
    
    @property
    def deployment_mode(self) -> DeploymentMode:
        """获取当前部署模式"""
        return self._deployment_mode
    
    @property
    def cache_dir(self) -> str:
        """获取缓存目录"""
        return self._cache_dir
    
    @property
    def is_local_mode(self) -> bool:
        """是否为本地模式"""
        return self._deployment_mode == DeploymentMode.LOCAL
    
    @property
    def is_modal_mode(self) -> bool:
        """是否为Modal模式"""
        return self._deployment_mode == DeploymentMode.MODAL
    
    @property
    def is_hf_spaces_mode(self) -> bool:
        """是否为HF Spaces模式"""
        return self._deployment_mode == DeploymentMode.HF_SPACES
    
    def get_transcribe_endpoint_url(self) -> Optional[str]:
        """获取转录endpoint URL"""
        return self._endpoints.get("transcribe_audio")
    
    def set_endpoint_url(self, service: str, url: str):
        """设置endpoint URL"""
        self._endpoints[service] = url
        self._save_endpoints()
    
    def _detect_deployment_mode(self) -> DeploymentMode:
        """自动检测部署模式"""
        # 检查环境变量
        mode = os.environ.get("DEPLOYMENT_MODE", "").lower()
        if mode == "modal":
            return DeploymentMode.MODAL
        elif mode == "hf":
            return DeploymentMode.HF_SPACES
        
        # 检查是否在HF Spaces环境
        if os.environ.get("SPACE_ID") or os.environ.get("SPACES_ZERO_GPU"):
            return DeploymentMode.HF_SPACES
        
        # 检查是否在Modal环境
        if os.environ.get("MODAL_TASK_ID") or os.environ.get("MODAL_IS_INSIDE_CONTAINER"):
            return DeploymentMode.MODAL
        
        # 默认为本地模式
        return DeploymentMode.LOCAL
    
    def _get_cache_directory(self) -> str:
        """获取缓存目录路径"""
        if self.is_modal_mode:
            return "/root/cache"
        else:
            # 本地模式和HF Spaces使用用户缓存目录
            home_dir = Path.home()
            cache_dir = home_dir / ".gradio_mcp_cache"
            cache_dir.mkdir(exist_ok=True)
            return str(cache_dir)
    
    def _load_endpoints(self) -> Dict[str, str]:
        """加载endpoint配置"""
        config_file = Path("endpoint_config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    endpoints = json.load(f)
                print(f"✅ Loaded endpoint configuration from {config_file}")
                return endpoints
            except Exception as e:
                print(f"⚠️ Failed to load endpoint config: {e}")
        else:
            print("⚠️ No endpoint configuration found. Run deployment first.")
        
        return {}
    
    def _save_endpoints(self):
        """保存endpoint配置"""
        config_file = Path("endpoint_config.json")
        try:
            with open(config_file, 'w') as f:
                json.dump(self._endpoints, f, indent=2)
            print(f"💾 Endpoint configuration saved to {config_file}")
        except Exception as e:
            print(f"⚠️ Failed to save endpoint config: {e}")


# 全局配置实例
app_config = AppConfig()

# 向后兼容的函数接口
def get_deployment_mode() -> str:
    """获取部署模式字符串"""
    return app_config.deployment_mode.value

def is_local_mode() -> bool:
    """是否为本地模式"""
    return app_config.is_local_mode

def is_modal_mode() -> bool:
    """是否为Modal模式"""
    return app_config.is_modal_mode

def get_cache_dir() -> str:
    """获取缓存目录"""
    return app_config.cache_dir

def get_transcribe_endpoint_url() -> Optional[str]:
    """获取转录endpoint URL"""
    return app_config.get_transcribe_endpoint_url()

def set_endpoint_url(service: str, url: str):
    """设置endpoint URL"""
    app_config.set_endpoint_url(service, url)


# 打印配置信息
print(f"🚀 Deployment mode: {app_config.deployment_mode.value}")
print(f"📁 Cache directory: {app_config.cache_dir}") 
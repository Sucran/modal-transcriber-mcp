"""
Deployment configuration for Gradio + MCP Server
Supports two deployment modes:
1. Local mode: Gradio runs locally, GPU functions call Modal endpoints
2. Modal mode: Gradio runs on Modal, GPU functions run locally on Modal
"""

import os
from enum import Enum
from typing import Optional

class DeploymentMode(Enum):
    LOCAL = "local"      # Local Gradio + Remote GPU (Modal endpoints)
    MODAL = "modal"      # Modal Gradio + Local GPU (Modal functions)

# Get deployment mode from environment variable
DEPLOYMENT_MODE = DeploymentMode(os.getenv("DEPLOYMENT_MODE", "local"))

# Modal endpoints configuration
MODAL_APP_NAME = "gradio-mcp-server"

# Load Modal configuration from environment variables
def get_modal_username() -> str:
    """Get Modal username from environment"""
    return os.getenv("MODAL_USERNAME", "richardsucran")

def get_modal_base_url() -> str:
    """Get Modal base URL from environment"""
    return os.getenv("MODAL_BASE_URL", "modal.run")

def build_modal_endpoint_url(endpoint_name: str) -> str:
    """Build Modal endpoint URL from configuration"""
    username = get_modal_username()
    base_url = get_modal_base_url()
    return f"https://{username}--{endpoint_name}.{base_url}"

def get_modal_transcribe_audio_endpoint() -> str:
    """Get transcribe audio endpoint URL"""
    return os.getenv(
        "MODAL_TRANSCRIBE_AUDIO_ENDPOINT",
        build_modal_endpoint_url("transcribe-audio-endpoint")
    )

def get_modal_transcribe_chunk_endpoint() -> str:
    """Get transcribe chunk endpoint URL"""
    return os.getenv(
        "MODAL_TRANSCRIBE_CHUNK_ENDPOINT", 
        build_modal_endpoint_url("transcribe-audio-chunk-endpoint")
    )

def get_modal_health_check_endpoint() -> str:
    """Get health check endpoint URL"""
    return os.getenv(
        "MODAL_HEALTH_CHECK_ENDPOINT",
        build_modal_endpoint_url("health-check-endpoint")
    )

def get_modal_gradio_ui_endpoint() -> str:
    """Get Gradio UI endpoint URL"""
    return os.getenv(
        "MODAL_GRADIO_UI_ENDPOINT",
        build_modal_endpoint_url("gradio-mcp-ui-app-entry")
    )

# Endpoint URLs (will be set when deployed)
ENDPOINTS = {
    "transcribe_audio": None,  # Will be filled with actual endpoint URL
}

def get_deployment_mode() -> DeploymentMode:
    """Get current deployment mode"""
    return DEPLOYMENT_MODE

def is_local_mode() -> bool:
    """Check if running in local mode"""
    return DEPLOYMENT_MODE == DeploymentMode.LOCAL

def is_modal_mode() -> bool:
    """Check if running in modal mode"""
    return DEPLOYMENT_MODE == DeploymentMode.MODAL

def set_endpoint_url(endpoint_name: str, url: str):
    """Set endpoint URL for local mode"""
    global ENDPOINTS
    ENDPOINTS[endpoint_name] = url

def get_endpoint_url(endpoint_name: str) -> Optional[str]:
    """Get endpoint URL for local mode"""
    return ENDPOINTS.get(endpoint_name)

def get_transcribe_endpoint_url() -> Optional[str]:
    """Get transcription endpoint URL"""
    return get_endpoint_url("transcribe_audio")

# Environment-specific cache directory
def get_cache_dir() -> str:
    """Get cache directory based on deployment mode"""
    if is_modal_mode():
        return "/root/cache"
    else:
        # Local mode - use user's home directory
        home_dir = os.path.expanduser("~")
        cache_dir = os.path.join(home_dir, ".gradio_mcp_cache")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

# Auto-load endpoint configuration in local mode
if is_local_mode():
    import json
    config_file = "endpoint_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            for endpoint_name, url in config.items():
                set_endpoint_url(endpoint_name, url)
            print(f"✅ Loaded endpoint configuration from {config_file}")
        except Exception as e:
            print(f"⚠️ Failed to load endpoint configuration: {e}")
    else:
        print(f"⚠️ No endpoint configuration found. Run 'python deploy_endpoints.py deploy' first.")

print(f"🚀 Deployment mode: {DEPLOYMENT_MODE.value}")
print(f"📁 Cache directory: {get_cache_dir()}")
print(f"🔗 Modal endpoints configured:")
print(f"   - Transcribe Audio: {get_modal_transcribe_audio_endpoint()}")
print(f"   - Transcribe Chunk: {get_modal_transcribe_chunk_endpoint()}")
print(f"   - Health Check: {get_modal_health_check_endpoint()}")
print(f"   - Gradio UI: {get_modal_gradio_ui_endpoint()}") 
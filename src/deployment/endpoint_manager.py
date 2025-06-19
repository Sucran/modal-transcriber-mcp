"""
Endpoint manager for handling Modal endpoints
"""

import json
import os
from typing import Dict, Optional

from ..utils.errors import ConfigurationError


class EndpointManager:
    """Manager for Modal endpoint configuration"""
    
    def __init__(self, config_file: str = "endpoint_config.json"):
        self.config_file = config_file
        self._endpoints = self._load_endpoints()
    
    def _load_endpoints(self) -> Dict[str, str]:
        """Load endpoints from configuration file"""
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load endpoint configuration: {e}")
            return {}
    
    def save_endpoints(self):
        """Save endpoints to configuration file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._endpoints, f, indent=2)
            print(f"💾 Endpoint configuration saved to {self.config_file}")
        except Exception as e:
            raise ConfigurationError(f"Failed to save endpoint configuration: {e}")
    
    def set_endpoint(self, name: str, url: str):
        """Set endpoint URL"""
        self._endpoints[name] = url
        self.save_endpoints()
        print(f"✅ Endpoint '{name}' set to: {url}")
    
    def get_endpoint(self, name: str) -> Optional[str]:
        """Get endpoint URL"""
        return self._endpoints.get(name)
    
    def remove_endpoint(self, name: str):
        """Remove endpoint"""
        if name in self._endpoints:
            del self._endpoints[name]
            self.save_endpoints()
            print(f"🗑️ Endpoint '{name}' removed")
        else:
            print(f"⚠️ Endpoint '{name}' not found")
    
    def list_endpoints(self) -> Dict[str, str]:
        """List all endpoints"""
        return self._endpoints.copy()
    
    def check_endpoint_health(self, name: str) -> bool:
        """Check if endpoint is healthy"""
        url = self.get_endpoint(name)
        if not url:
            return False
        
        try:
            import requests
            # Try a simple health check (adjust based on your endpoint)
            health_url = url.replace("/transcribe", "/health")
            response = requests.get(health_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False 
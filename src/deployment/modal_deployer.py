"""
Modal deployer for deploying transcription services
"""

import subprocess
from typing import Optional

from ..utils.config import AudioProcessingConfig
from ..utils.errors import DeploymentError
from .endpoint_manager import EndpointManager


class ModalDeployer:
    """Deployer for Modal transcription services"""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()
        self.endpoint_manager = EndpointManager()
    
    def deploy_transcription_service(self) -> Optional[str]:
        """Deploy transcription service to Modal"""
        
        print("🚀 Deploying transcription service to Modal...")
        
        try:
            # Deploy the Modal app
            print("🚀 Running modal deploy command...")
            result = subprocess.run(
                ["modal", "deploy", "modal_config.py"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Extract or construct endpoint URL
                endpoint_url = self._extract_endpoint_url(result.stdout)
                
                if endpoint_url:
                    # Save endpoint configuration
                    self.endpoint_manager.set_endpoint("transcribe_audio", endpoint_url)
                    print(f"✅ Transcription service deployed: {endpoint_url}")
                    return endpoint_url
                else:
                    print("⚠️ Could not extract endpoint URL from deployment output")
                    return None
            else:
                raise DeploymentError(
                    f"Modal deployment failed: {result.stderr}",
                    service="transcription"
                )
                
        except FileNotFoundError:
            raise DeploymentError(
                "Modal CLI not found. Please install Modal: pip install modal",
                service="transcription"
            )
        except Exception as e:
            raise DeploymentError(
                f"Failed to deploy transcription service: {str(e)}",
                service="transcription"
            )
    
    def _extract_endpoint_url(self, output: str) -> Optional[str]:
        """Extract endpoint URL from deployment output"""
        
        # Look for URL in output
        for line in output.split('\n'):
            if 'https://' in line and 'modal.run' in line:
                # Extract URL from line
                parts = line.split()
                for part in parts:
                    if part.startswith('https://') and 'modal.run' in part:
                        return part
        
        # Fallback to constructed URL
        return f"https://{self.config.modal_app_name}--transcribe-audio-endpoint.modal.run"
    
    def check_deployment_status(self) -> bool:
        """Check if transcription service is deployed and healthy"""
        
        endpoint_url = self.endpoint_manager.get_endpoint("transcribe_audio")
        if not endpoint_url:
            print("❌ No transcription endpoint configured")
            return False
        
        if self.endpoint_manager.check_endpoint_health("transcribe_audio"):
            print(f"✅ Transcription service is healthy: {endpoint_url}")
            return True
        else:
            print(f"❌ Transcription service is not responding: {endpoint_url}")
            return False
    
    def undeploy_transcription_service(self):
        """Remove transcription service endpoint"""
        self.endpoint_manager.remove_endpoint("transcribe_audio")
        print("🗑️ Transcription service endpoint removed from configuration")
        print("💡 Note: The actual Modal deployment may still be active. Use 'modal app stop' to stop it.") 
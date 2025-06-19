"""
Factory for creating transcription adapters
"""

import os
from typing import Optional

from ..interfaces.transcriber import ITranscriber
from ..utils.config import AudioProcessingConfig
from ..utils.errors import ConfigurationError
from .local_adapter import LocalTranscriptionAdapter
from .modal_adapter import ModalTranscriptionAdapter


class TranscriptionAdapterFactory:
    """Factory for creating appropriate transcription adapters"""
    
    @staticmethod
    def create_adapter(
        deployment_mode: str = "auto",
        config: Optional[AudioProcessingConfig] = None,
        endpoint_url: Optional[str] = None
    ) -> ITranscriber:
        """
        Create transcription adapter based on deployment mode
        
        Args:
            deployment_mode: "local", "modal", or "auto"
            config: Configuration object
            endpoint_url: Modal endpoint URL (for modal/auto mode)
            
        Returns:
            ITranscriber: Appropriate transcription adapter
        """
        
        config = config or AudioProcessingConfig()
        
        # Auto mode: decide based on environment and endpoint availability
        if deployment_mode == "auto":
            if endpoint_url:
                print(f"🌐 Auto mode: Using Modal adapter with endpoint {endpoint_url}")
                return ModalTranscriptionAdapter(config=config, endpoint_url=endpoint_url)
            else:
                print(f"🏠 Auto mode: Using Local adapter (no endpoint configured)")
                return LocalTranscriptionAdapter(config=config)
        
        # Explicit local mode
        elif deployment_mode == "local":
            print(f"🏠 Using Local transcription adapter")
            return LocalTranscriptionAdapter(config=config)
        
        # Explicit modal mode  
        elif deployment_mode == "modal":
            if not endpoint_url:
                raise ConfigurationError(
                    "Modal endpoint URL is required for modal mode",
                    config_key="endpoint_url"
                )
            print(f"🌐 Using Modal transcription adapter with endpoint {endpoint_url}")
            return ModalTranscriptionAdapter(config=config, endpoint_url=endpoint_url)
        
        else:
            raise ConfigurationError(
                f"Unsupported deployment mode: {deployment_mode}. Use 'local', 'modal', or 'auto'",
                config_key="deployment_mode"
            )
    
    @staticmethod
    def _detect_deployment_mode() -> str:
        """Auto-detect deployment mode based on environment"""
        import os
        
        # Check if running in Modal environment
        if os.environ.get("MODAL_TASK_ID"):
            return "local"  # We're inside Modal, use local processing
        else:
            return "modal"  # We're outside Modal, use remote endpoint 
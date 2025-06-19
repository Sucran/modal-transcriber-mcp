"""
Transcription API module
"""

import os
from typing import Optional, Dict, Any

from ..adapters import TranscriptionAdapterFactory
from ..services import TranscriptionService
from ..core import FFmpegAudioSplitter
from ..utils import AudioProcessingConfig, AudioProcessingError


class TranscriptionAPI:
    """High-level API for transcription operations"""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()
        self.transcription_service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize transcription service with appropriate adapter"""
        try:
            # Get endpoint URL from config file if available
            endpoint_url = self._get_endpoint_url()
            
            # Create appropriate adapter
            transcriber = TranscriptionAdapterFactory.create_adapter(
                deployment_mode="auto",
                config=self.config,
                endpoint_url=endpoint_url
            )
            
            # Create audio splitter
            audio_splitter = FFmpegAudioSplitter()
            
            # Create transcription service
            self.transcription_service = TranscriptionService(
                transcriber=transcriber,
                audio_splitter=audio_splitter,
                speaker_detector=None,  # TODO: Add speaker detector when implemented
                config=self.config
            )
            
        except Exception as e:
            print(f"⚠️ Failed to initialize transcription service: {e}")
            raise AudioProcessingError(f"Service initialization failed: {e}")
    
    def _get_endpoint_url(self) -> Optional[str]:
        """Get Modal endpoint URL from configuration"""
        try:
            import json
            config_file = "endpoint_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                return config.get("transcribe_audio")
        except Exception:
            pass
        return None
    
    async def transcribe_audio_file(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: Optional[str] = None,
        output_format: str = "srt",
        enable_speaker_diarization: bool = False
    ) -> Dict[str, Any]:
        """Transcribe audio file using the configured service"""
        
        if not self.transcription_service:
            raise AudioProcessingError("Transcription service not initialized")
        
        return await self.transcription_service.transcribe_audio_file(
            audio_file_path=audio_file_path,
            model_size=model_size,
            language=language,
            output_format=output_format,
            enable_speaker_diarization=enable_speaker_diarization
        )


# Create global API instance
_api_instance = None

def get_transcription_api() -> TranscriptionAPI:
    """Get global transcription API instance"""
    global _api_instance
    if _api_instance is None:
        _api_instance = TranscriptionAPI()
    return _api_instance

async def transcribe_audio_adaptive_sync(
    audio_file_path: str,
    model_size: str = "turbo", 
    language: str = None,
    output_format: str = "srt",
    enable_speaker_diarization: bool = False
) -> Dict[str, Any]:
    """
    Adaptive transcription function that routes to appropriate backend
    """
    api = get_transcription_api()
    return await api.transcribe_audio_file(
        audio_file_path=audio_file_path,
        model_size=model_size,
        language=language,
        output_format=output_format,
        enable_speaker_diarization=enable_speaker_diarization
    ) 
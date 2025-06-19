"""
Local transcription adapter for direct processing
"""

import asyncio
from typing import List, Optional

from ..interfaces.transcriber import ITranscriber, TranscriptionResult
from ..utils.config import AudioProcessingConfig
from ..utils.errors import TranscriptionError


class LocalTranscriptionAdapter(ITranscriber):
    """Adapter for local transcription processing"""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()
    
    async def transcribe(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False
    ) -> TranscriptionResult:
        """Transcribe audio using local processing"""
        
        try:
            # Use the new AudioProcessingService instead of old methods
            from ..services.audio_processing_service import AudioProcessingService
            from ..models.services import AudioProcessingRequest
            
            print(f"🔄 Starting local transcription for: {audio_file_path}")
            print(f"🚀 Running transcription with {model_size} model...")
            
            # Create service and request
            audio_service = AudioProcessingService()
            request = AudioProcessingRequest(
                audio_file_path=audio_file_path,
                model_size=model_size,
                language=language,
                output_format="json",
                enable_speaker_diarization=enable_speaker_diarization
            )
            
            # Process transcription
            result = audio_service.transcribe_full_audio(request)
            
            # Convert service result to adapter format
            return self._convert_service_result(result)
            
        except Exception as e:
            raise TranscriptionError(
                f"Local transcription failed: {str(e)}",
                model=model_size,
                audio_file=audio_file_path
            )
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported model sizes"""
        return list(self.config.whisper_models.keys())
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        # This would normally come from Whisper's supported languages
        return ["en", "zh", "ja", "ko", "es", "fr", "de", "ru", "auto"]
    
    def _convert_service_result(self, service_result) -> TranscriptionResult:
        """Convert service result format to TranscriptionResult"""
        from ..interfaces.transcriber import TranscriptionSegment
        
        # Extract segments from service result if available
        segments = []
        if hasattr(service_result, 'segments') and service_result.segments:
            for seg in service_result.segments:
                segments.append(TranscriptionSegment(
                    start=getattr(seg, 'start', 0),
                    end=getattr(seg, 'end', 0),
                    text=getattr(seg, 'text', ''),
                    speaker=getattr(seg, 'speaker', None)
                ))
        
        return TranscriptionResult(
            text=getattr(service_result, 'text', ''),
            segments=segments,
            language=getattr(service_result, 'language_detected', 'unknown'),
            model_used=getattr(service_result, 'model_used', 'unknown'),
            audio_duration=getattr(service_result, 'audio_duration', 0),
            processing_time=getattr(service_result, 'processing_time', 0),
            speaker_diarization_enabled=getattr(service_result, 'speaker_diarization_enabled', False),
            global_speaker_count=getattr(service_result, 'global_speaker_count', 0),
            error_message=getattr(service_result, 'error_message', None)
        ) 
"""
Modal transcription adapter for remote processing
"""

import requests
import base64
import pathlib
from typing import List, Optional

from ..interfaces.transcriber import ITranscriber, TranscriptionResult, TranscriptionSegment
from ..utils.config import AudioProcessingConfig
from ..utils.errors import TranscriptionError


class ModalTranscriptionAdapter(ITranscriber):
    """Adapter for Modal remote transcription processing"""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None, endpoint_url: Optional[str] = None):
        self.config = config or AudioProcessingConfig()
        self.endpoint_url = endpoint_url
    
    async def transcribe(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False
    ) -> TranscriptionResult:
        """Transcribe audio using Modal endpoint"""
        
        if not self.endpoint_url:
            raise TranscriptionError(
                "Modal endpoint URL not configured",
                model=model_size,
                audio_file=audio_file_path
            )
        
        try:
            # Read and encode audio file
            audio_path = pathlib.Path(audio_file_path)
            if not audio_path.exists():
                raise TranscriptionError(
                    f"Audio file not found: {audio_file_path}",
                    audio_file=audio_file_path
                )
            
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare request data
            request_data = {
                "audio_file_data": audio_base64,
                "audio_file_name": audio_path.name,
                "model_size": model_size,
                "language": language,
                "output_format": "json",
                "enable_speaker_diarization": enable_speaker_diarization
            }
            
            print(f"🔄 Sending transcription request to Modal endpoint")
            print(f"📁 File: {audio_file_path} ({len(audio_data) / (1024*1024):.2f} MB)")
            print(f"🔧 Model: {model_size}, Speaker diarization: {enable_speaker_diarization}")
            
            # Make request to Modal endpoint
            response = requests.post(
                self.endpoint_url,
                json=request_data,
                timeout=1800  # 30 minutes timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Modal transcription completed")
            
            # Convert result to TranscriptionResult format
            return self._convert_modal_result(result)
            
        except requests.exceptions.RequestException as e:
            raise TranscriptionError(
                f"Failed to call Modal endpoint: {str(e)}",
                model=model_size,
                audio_file=audio_file_path
            )
        except Exception as e:
            raise TranscriptionError(
                f"Modal transcription failed: {str(e)}",
                model=model_size,
                audio_file=audio_file_path
            )
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported model sizes"""
        return list(self.config.whisper_models.keys())
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return ["en", "zh", "ja", "ko", "es", "fr", "de", "ru", "auto"]
    
    def _convert_modal_result(self, modal_result: dict) -> TranscriptionResult:
        """Convert Modal result format to TranscriptionResult"""
        
        # Extract segments if available
        segments = []
        if "segments" in modal_result:
            for seg in modal_result["segments"]:
                segments.append(TranscriptionSegment(
                    start=seg.get("start", 0),
                    end=seg.get("end", 0),
                    text=seg.get("text", ""),
                    speaker=seg.get("speaker")
                ))
        
        return TranscriptionResult(
            text=modal_result.get("text", ""),
            segments=segments,
            language=modal_result.get("language_detected", "unknown"),
            model_used=modal_result.get("model_used", "unknown"),
            audio_duration=modal_result.get("audio_duration", 0),
            processing_time=modal_result.get("processing_time", 0),
            speaker_diarization_enabled=modal_result.get("speaker_diarization_enabled", False),
            global_speaker_count=modal_result.get("global_speaker_count", 0),
            error_message=modal_result.get("error_message")
        ) 
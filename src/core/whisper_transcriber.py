"""
Local Whisper transcriber implementation
"""

import whisper
import torch
import pathlib
import time
from typing import Optional, List

from ..interfaces.transcriber import ITranscriber, TranscriptionResult, TranscriptionSegment
from ..utils.config import AudioProcessingConfig
from ..utils.errors import TranscriptionError, ModelLoadError


class WhisperTranscriber(ITranscriber):
    """Local Whisper transcriber implementation"""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()
        self.model_cache = {}
        self.device = self._setup_device()
    
    def _setup_device(self) -> str:
        """Setup and return the best available device"""
        if torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    async def transcribe(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False
    ) -> TranscriptionResult:
        """Transcribe audio using local Whisper model"""
        
        try:
            # Validate audio file
            audio_path = pathlib.Path(audio_file_path)
            if not audio_path.exists():
                raise TranscriptionError(
                    f"Audio file not found: {audio_file_path}",
                    audio_file=audio_file_path
                )
            
            # Load model
            model = self._load_model(model_size)
            
            # Transcribe
            start_time = time.time()
            result = model.transcribe(
                str(audio_path),
                language=language,
                verbose=False
            )
            processing_time = time.time() - start_time
            
            # Convert to our format
            segments = []
            for seg in result.get("segments", []):
                segments.append(TranscriptionSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                    confidence=seg.get("avg_logprob")
                ))
            
            return TranscriptionResult(
                text=result.get("text", "").strip(),
                segments=segments,
                language=result.get("language", "unknown"),
                model_used=model_size,
                audio_duration=result.get("duration", 0),
                processing_time=processing_time,
                speaker_diarization_enabled=enable_speaker_diarization,
                global_speaker_count=0,
                error_message=None
            )
            
        except Exception as e:
            raise TranscriptionError(
                f"Whisper transcription failed: {str(e)}",
                model=model_size,
                audio_file=audio_file_path
            )
    
    def _load_model(self, model_size: str):
        """Load Whisper model with caching"""
        if model_size not in self.model_cache:
            try:
                print(f"📥 Loading Whisper model: {model_size}")
                self.model_cache[model_size] = whisper.load_model(
                    model_size,
                    device=self.device
                )
            except Exception as e:
                raise ModelLoadError(
                    f"Failed to load model {model_size}: {str(e)}",
                    model_name=model_size
                )
        
        return self.model_cache[model_size]
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported model sizes"""
        return list(self.config.whisper_models.keys())
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return ["en", "zh", "ja", "ko", "es", "fr", "de", "ru", "auto"] 
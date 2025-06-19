"""
Transcriber interface definition
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class TranscriptionSegment:
    """Transcription segment data class"""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class TranscriptionResult:
    """Transcription result data class"""
    text: str
    segments: List[TranscriptionSegment]
    language: str
    model_used: str
    audio_duration: float
    processing_time: float
    speaker_diarization_enabled: bool = False
    global_speaker_count: int = 0
    error_message: Optional[str] = None


class ITranscriber(ABC):
    """Interface for audio transcription"""
    
    @abstractmethod
    async def transcribe(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False
    ) -> TranscriptionResult:
        """
        Transcribe audio file
        
        Args:
            audio_file_path: Path to audio file
            model_size: Model size to use
            language: Language code (None for auto-detect)
            enable_speaker_diarization: Whether to enable speaker detection
            
        Returns:
            TranscriptionResult object
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Get list of supported model sizes"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        pass 
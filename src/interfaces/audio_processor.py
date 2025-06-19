"""
Audio processing interface definitions
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Iterator, Optional
from dataclasses import dataclass


@dataclass
class AudioSegment:
    """Audio segment representation"""
    start: float
    end: float
    file_path: str
    duration: float


class IAudioProcessor(ABC):
    """Interface for audio processing operations"""
    
    @abstractmethod
    async def split_audio_by_silence(
        self,
        audio_path: str,
        min_segment_length: float = 30.0,
        min_silence_length: float = 1.0
    ) -> List[AudioSegment]:
        """Split audio file by silence detection"""
        pass
    
    @abstractmethod
    async def process_audio_segment(
        self,
        segment: AudioSegment,
        model_name: str = "turbo",
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False
    ) -> Dict[str, Any]:
        """Process a single audio segment"""
        pass
    
    @abstractmethod
    async def process_complete_audio(
        self,
        audio_path: str,
        model_name: str = "turbo",
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False,
        min_segment_length: float = 30.0
    ) -> Dict[str, Any]:
        """Process complete audio file"""
        pass 
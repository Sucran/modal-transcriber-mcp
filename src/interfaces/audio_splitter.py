"""
Audio splitter interface definition
"""

from abc import ABC, abstractmethod
from typing import Iterator, Tuple
from dataclasses import dataclass


@dataclass
class AudioSegment:
    """Audio segment data class"""
    start: float
    end: float
    duration: float
    
    def __post_init__(self):
        if self.duration <= 0:
            self.duration = self.end - self.start


class IAudioSplitter(ABC):
    """Interface for audio splitting"""
    
    @abstractmethod
    def split_audio(
        self,
        audio_path: str,
        min_segment_length: float = 30.0,
        min_silence_length: float = 1.0
    ) -> Iterator[AudioSegment]:
        """
        Split audio into segments
        
        Args:
            audio_path: Path to audio file
            min_segment_length: Minimum segment length in seconds
            min_silence_length: Minimum silence length for splitting
            
        Yields:
            AudioSegment objects
        """
        pass
    
    @abstractmethod
    def get_audio_duration(self, audio_path: str) -> float:
        """Get total duration of audio file"""
        pass 
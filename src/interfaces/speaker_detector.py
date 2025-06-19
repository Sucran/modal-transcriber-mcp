"""
Speaker detector interface definition
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class SpeakerSegment:
    """Speaker segment data class"""
    start: float
    end: float
    speaker_id: str
    confidence: Optional[float] = None


@dataclass
class SpeakerProfile:
    """Speaker profile data class"""
    speaker_id: str
    embedding: np.ndarray
    segments: List[SpeakerSegment]
    total_duration: float


class ISpeakerDetector(ABC):
    """Interface for speaker detection and diarization"""
    
    @abstractmethod
    async def detect_speakers(
        self,
        audio_file_path: str,
        audio_segments: Optional[List] = None
    ) -> Dict[str, SpeakerProfile]:
        """
        Detect and identify speakers in audio
        
        Args:
            audio_file_path: Path to audio file
            audio_segments: Optional pre-segmented audio
            
        Returns:
            Dictionary mapping speaker IDs to SpeakerProfile objects
        """
        pass
    
    @abstractmethod
    def map_to_global_speakers(
        self,
        local_speakers: Dict[str, SpeakerProfile],
        source_file: str
    ) -> Dict[str, str]:
        """
        Map local speakers to global speaker identities
        
        Args:
            local_speakers: Local speaker profiles
            source_file: Source audio file path
            
        Returns:
            Mapping from local speaker ID to global speaker ID
        """
        pass
    
    @abstractmethod
    def get_speaker_summary(self) -> Dict:
        """Get summary of all detected speakers"""
        pass 
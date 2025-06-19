"""
Speaker identification and embedding management interfaces
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class SpeakerEmbedding:
    """Speaker embedding data structure"""
    speaker_id: str
    embedding: np.ndarray
    confidence: float
    source_files: List[str]
    sample_count: int
    created_at: str
    updated_at: str


@dataclass
class SpeakerSegment:
    """Speaker segment information"""
    start: float
    end: float
    speaker_id: str
    confidence: float


class ISpeakerEmbeddingManager(ABC):
    """Interface for speaker embedding management"""
    
    @abstractmethod
    async def find_matching_speaker(
        self,
        embedding: np.ndarray,
        source_file: str
    ) -> Optional[str]:
        """Find matching speaker from existing embeddings"""
        pass
    
    @abstractmethod
    async def add_or_update_speaker(
        self,
        embedding: np.ndarray,
        source_file: str,
        confidence: float = 1.0,
        original_label: Optional[str] = None
    ) -> str:
        """Add new speaker or update existing speaker"""
        pass
    
    @abstractmethod
    async def map_local_to_global_speakers(
        self,
        local_embeddings: Dict[str, np.ndarray],
        source_file: str
    ) -> Dict[str, str]:
        """Map local speaker labels to global speaker IDs"""
        pass
    
    @abstractmethod
    async def get_speaker_info(self, speaker_id: str) -> Optional[SpeakerEmbedding]:
        """Get speaker information by ID"""
        pass
    
    @abstractmethod
    async def get_all_speakers_summary(self) -> Dict[str, Any]:
        """Get summary of all speakers"""
        pass
    
    @abstractmethod
    async def save_speakers(self) -> None:
        """Save speaker data to storage"""
        pass
    
    @abstractmethod
    async def load_speakers(self) -> None:
        """Load speaker data from storage"""
        pass


class ISpeakerIdentificationService(ABC):
    """Interface for speaker identification operations"""
    
    @abstractmethod
    async def extract_speaker_embeddings(
        self,
        audio_path: str,
        segments: List[SpeakerSegment]
    ) -> Dict[str, np.ndarray]:
        """Extract speaker embeddings from audio segments"""
        pass
    
    @abstractmethod
    async def identify_speakers_in_audio(
        self,
        audio_path: str,
        transcription_segments: List[Dict[str, Any]]
    ) -> List[SpeakerSegment]:
        """Identify speakers in audio file"""
        pass
    
    @abstractmethod
    async def map_transcription_to_speakers(
        self,
        transcription_segments: List[Dict[str, Any]],
        speaker_segments: List[SpeakerSegment]
    ) -> List[Dict[str, Any]]:
        """Map transcription segments to speaker information"""
        pass 
"""
Interfaces for audio processing components
"""

from .transcriber import ITranscriber
from .speaker_detector import ISpeakerDetector
from .audio_splitter import IAudioSplitter
from .audio_processor import IAudioProcessor, AudioSegment
from .podcast_downloader import IPodcastDownloader, PodcastInfo, DownloadResult, PodcastPlatform
from .speaker_manager import (
    ISpeakerEmbeddingManager,
    ISpeakerIdentificationService,
    SpeakerEmbedding,
    SpeakerSegment
)

__all__ = [
    # Core interfaces
    "ITranscriber",
    "ISpeakerDetector", 
    "IAudioSplitter",
    
    # New service interfaces
    "IAudioProcessor",
    "IPodcastDownloader",
    "ISpeakerEmbeddingManager",
    "ISpeakerIdentificationService",
    
    # Data classes
    "AudioSegment",
    "PodcastInfo",
    "DownloadResult",
    "SpeakerEmbedding",
    "SpeakerSegment",
    
    # Enums
    "PodcastPlatform"
] 
"""
Podcast downloading interface definitions
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PodcastPlatform(Enum):
    """Podcast platform enumeration"""
    APPLE = "apple"
    XIAOYUZHOU = "xyz"
    SPOTIFY = "spotify"
    GENERIC = "generic"


@dataclass
class PodcastInfo:
    """Podcast episode information"""
    title: str
    audio_url: str
    episode_id: str
    platform: PodcastPlatform
    duration: Optional[float] = None
    description: Optional[str] = None


@dataclass
class DownloadResult:
    """Download operation result"""
    success: bool
    file_path: Optional[str]
    podcast_info: Optional[PodcastInfo]
    error_message: Optional[str] = None


class IPodcastDownloader(ABC):
    """Interface for podcast downloading operations"""
    
    @abstractmethod
    async def extract_podcast_info(self, url: str) -> PodcastInfo:
        """Extract podcast information from URL"""
        pass
    
    @abstractmethod
    async def download_podcast(
        self,
        url: str,
        output_folder: str = "downloads",
        convert_to_mp3: bool = False,
        keep_original: bool = False
    ) -> DownloadResult:
        """Download podcast from URL"""
        pass
    
    @abstractmethod
    def get_supported_platforms(self) -> list[PodcastPlatform]:
        """Get list of supported platforms"""
        pass
    
    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """Check if this downloader can handle the given URL"""
        pass 
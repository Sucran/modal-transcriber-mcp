"""
Download models
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

from .base import BaseRequest, BaseResponse, OperationStatus


class PodcastPlatform(str, Enum):
    """Supported podcast platforms"""
    APPLE_PODCAST = "apple_podcast"
    XIAOYUZHOU = "xiaoyuzhou"


@dataclass
class DownloadRequest(BaseRequest):
    """Request model for podcast download"""
    url: str
    platform: PodcastPlatform
    output_directory: Optional[str] = None
    auto_transcribe: bool = False
    enable_speaker_diarization: bool = False


@dataclass
class DownloadResponse(BaseResponse):
    """Response model for podcast download"""
    original_url: str = ""
    audio_file_path: Optional[str] = None
    file_size_mb: Optional[float] = None
    duration_seconds: Optional[float] = None
    
    @classmethod
    def success(
        cls,
        original_url: str,
        audio_file_path: str,
        file_size_mb: Optional[float] = None,
        duration_seconds: Optional[float] = None,
        message: str = "下载成功"
    ) -> "DownloadResponse":
        """Create successful response"""
        return cls(
            status=OperationStatus.SUCCESS,
            message=message,
            original_url=original_url,
            audio_file_path=audio_file_path,
            file_size_mb=file_size_mb,
            duration_seconds=duration_seconds
        )
    
    @classmethod
    def failed(
        cls,
        original_url: str,
        error_message: str,
        error_code: str = "DOWNLOAD_ERROR",
        error_details: Optional[Dict[str, Any]] = None
    ) -> "DownloadResponse":
        """Create failed response"""
        return cls(
            status=OperationStatus.FAILED,
            message=error_message,
            error_code=error_code,
            error_details=error_details,
            original_url=original_url
        ) 
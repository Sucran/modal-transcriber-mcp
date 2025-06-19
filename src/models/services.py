"""
Service layer specific data models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import numpy as np

from .base import BaseRequest, BaseResponse, OperationStatus


class AudioProcessingTask(Enum):
    """Audio processing task types"""
    TRANSCRIPTION = "transcription"
    SPEAKER_IDENTIFICATION = "speaker_identification"
    AUDIO_SEGMENTATION = "audio_segmentation"
    COMPLETE_PROCESSING = "complete_processing"


class FileOperationType(Enum):
    """File operation types"""
    SCAN = "scan"
    READ = "read"
    WRITE = "write"
    ORGANIZE = "organize"
    CONVERT = "convert"


@dataclass
class AudioProcessingRequest(BaseRequest):
    """Request for audio processing operations"""
    audio_path: str
    task: AudioProcessingTask
    model_name: str = "turbo"
    language: Optional[str] = None
    enable_speaker_diarization: bool = False
    min_segment_length: float = 30.0
    output_path: Optional[str] = None


@dataclass
class AudioProcessingResult:
    """Result of audio processing operations"""
    audio_path: str
    task: AudioProcessingTask
    text: str
    segments: List[Dict[str, Any]]
    audio_duration: float
    segment_count: int
    language_detected: str
    model_used: str
    speaker_diarization_enabled: bool
    status: OperationStatus = OperationStatus.SUCCESS
    processing_time: Optional[float] = None
    speakers_detected: Optional[int] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


@dataclass
class PodcastDownloadRequest(BaseRequest):
    """Request for podcast download operations"""
    url: str
    output_folder: str = "downloads"
    convert_to_mp3: bool = False
    keep_original: bool = False
    extract_info_only: bool = False


@dataclass
class PodcastDownloadResult:
    """Result of podcast download operations"""
    url: str
    title: str
    episode_id: str
    platform: str
    status: OperationStatus = OperationStatus.SUCCESS
    file_path: Optional[str] = None
    download_time: Optional[float] = None
    file_size: Optional[int] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


@dataclass
class SpeakerEmbeddingRequest(BaseRequest):
    """Request for speaker embedding operations"""
    audio_path: str
    speaker_segments: List[Dict[str, Any]]
    source_file: str
    update_global_speakers: bool = True


@dataclass
class SpeakerEmbeddingResult:
    """Result of speaker embedding operations"""
    audio_path: str
    speaker_embeddings: Dict[str, np.ndarray]
    speaker_mapping: Dict[str, str]  # local_id -> global_id
    speakers_created: int
    speakers_updated: int
    status: OperationStatus = OperationStatus.SUCCESS
    message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


@dataclass 
class FileManagementRequest(BaseRequest):
    """Request for file management operations"""
    operation: FileOperationType
    file_path: Optional[str] = None
    directory_path: Optional[str] = None
    content: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


@dataclass
class FileManagementResult:
    """Result of file management operations"""
    operation: FileOperationType
    status: OperationStatus = OperationStatus.SUCCESS
    file_path: Optional[str] = None
    directory_path: Optional[str] = None
    files_processed: int = 0
    total_files: int = 0
    content_length: int = 0
    file_size: int = 0
    message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


@dataclass
class ServiceError:
    """Service error information"""
    service_name: str
    error_code: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


@dataclass
class ServiceHealthCheck:
    """Service health check result"""
    service_name: str
    is_healthy: bool
    dependencies: Dict[str, bool]
    version: str
    uptime: float
    last_check: str
    status: OperationStatus = OperationStatus.SUCCESS
    message: Optional[str] = None
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None 
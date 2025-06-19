"""
Data models for audio processing
"""

from .base import BaseRequest, BaseResponse, OperationStatus
from .transcription import (
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionSegment,
    SpeakerInfo,
    TranscriptionFiles,
    TranscriptionMetrics,
    ModelSize
)
from .download import (
    DownloadRequest,
    DownloadResponse,
    PodcastPlatform
)
from .file_operations import (
    FileInfoRequest,
    FileInfoResponse,
    FileReadRequest,
    FileReadResponse,
    DirectoryListRequest,
    DirectoryListResponse,
    FileMetadata
)
from .services import (
    AudioProcessingTask,
    FileOperationType,
    AudioProcessingRequest,
    AudioProcessingResult,
    PodcastDownloadRequest,
    PodcastDownloadResult,
    SpeakerEmbeddingRequest,
    SpeakerEmbeddingResult,
    FileManagementRequest,
    FileManagementResult,
    ServiceError,
    ServiceHealthCheck
)
from .converters import (
    TranscriptionConverter,
    DownloadConverter,
    FileOperationConverter
)

__all__ = [
    # Base
    "BaseRequest",
    "BaseResponse", 
    "OperationStatus",
    
    # Transcription
    "TranscriptionRequest",
    "TranscriptionResponse",
    "TranscriptionSegment",
    "SpeakerInfo",
    "TranscriptionFiles",
    "TranscriptionMetrics",
    "ModelSize",
    
    # Download
    "DownloadRequest",
    "DownloadResponse",
    "PodcastPlatform",
    
    # File Operations
    "FileInfoRequest",
    "FileInfoResponse",
    "FileReadRequest",
    "FileReadResponse",
    "DirectoryListRequest",
    "DirectoryListResponse",
    "FileMetadata",
    
    # Service layer models
    "AudioProcessingTask",
    "FileOperationType",
    "AudioProcessingRequest",
    "AudioProcessingResult",
    "PodcastDownloadRequest",
    "PodcastDownloadResult",
    "SpeakerEmbeddingRequest",
    "SpeakerEmbeddingResult",
    "FileManagementRequest",
    "FileManagementResult",
    "ServiceError",
    "ServiceHealthCheck",
    
    # Converters
    "TranscriptionConverter",
    "DownloadConverter",
    "FileOperationConverter",
] 
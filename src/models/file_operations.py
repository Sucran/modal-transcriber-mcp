"""
File operation models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base import BaseRequest, BaseResponse, OperationStatus


@dataclass
class FileMetadata:
    """File metadata information"""
    filename: str
    full_path: str
    file_size: int
    file_size_mb: float
    created_time: datetime
    modified_time: datetime
    file_extension: str
    is_audio_file: bool = False


@dataclass
class FileInfoRequest(BaseRequest):
    """Request model for file information"""
    file_path: str


@dataclass 
class FileInfoResponse(BaseResponse):
    """Response model for file information"""
    file_path: str = ""
    file_exists: bool = False
    metadata: Optional[FileMetadata] = None
    
    @classmethod
    def success(
        cls,
        file_path: str,
        metadata: FileMetadata,
        message: str = "文件信息获取成功"
    ) -> "FileInfoResponse":
        """Create successful response"""
        return cls(
            status=OperationStatus.SUCCESS,
            message=message,
            file_path=file_path,
            file_exists=True,
            metadata=metadata
        )
    
    @classmethod
    def failed(
        cls,
        file_path: str,
        error_message: str,
        error_code: str = "FILE_ERROR",
        error_details: Optional[Dict[str, Any]] = None
    ) -> "FileInfoResponse":
        """Create failed response"""
        return cls(
            status=OperationStatus.FAILED,
            message=error_message,
            error_code=error_code,
            error_details=error_details,
            file_path=file_path,
            file_exists=False
        )


@dataclass
class FileReadRequest(BaseRequest):
    """Request model for file reading"""
    file_path: str
    chunk_size: int = 64 * 1024  # 64KB
    start_position: int = 0


@dataclass
class FileReadProgress:
    """File reading progress information"""
    current_position: int
    file_size: int
    bytes_read: int
    content_length: int
    progress_percentage: float
    end_of_file_reached: bool
    actual_boundary: str


@dataclass
class FileReadResponse(BaseResponse):
    """Response model for file reading"""
    file_path: str = ""
    content: str = ""
    progress: Optional[FileReadProgress] = None
    
    @classmethod
    def success(
        cls,
        file_path: str,
        content: str,
        progress: FileReadProgress,
        message: str = "文件读取成功"
    ) -> "FileReadResponse":
        """Create successful response"""
        return cls(
            status=OperationStatus.SUCCESS,
            message=message,
            file_path=file_path,
            content=content,
            progress=progress
        )
    
    @classmethod
    def failed(
        cls,
        file_path: str,
        error_message: str,
        error_code: str = "FILE_READ_ERROR",
        error_details: Optional[Dict[str, Any]] = None
    ) -> "FileReadResponse":
        """Create failed response"""
        return cls(
            status=OperationStatus.FAILED,
            message=error_message,
            error_code=error_code,
            error_details=error_details,
            file_path=file_path
        )


@dataclass
class DirectoryListRequest(BaseRequest):
    """Request model for directory listing"""
    directory: str
    file_extension_filter: Optional[str] = None  # e.g., ".mp3"


@dataclass
class DirectoryListResponse(BaseResponse):
    """Response model for directory listing"""
    directory: str = ""
    total_files: int = 0
    file_list: List[FileMetadata] = field(default_factory=list)
    
    @classmethod
    def success(
        cls,
        directory: str,
        file_list: List[FileMetadata],
        message: str = "目录扫描成功"
    ) -> "DirectoryListResponse":
        """Create successful response"""
        return cls(
            status=OperationStatus.SUCCESS,
            message=message,
            directory=directory,
            total_files=len(file_list),
            file_list=file_list
        )
    
    @classmethod
    def failed(
        cls,
        directory: str,
        error_message: str,
        error_code: str = "DIRECTORY_ERROR",
        error_details: Optional[Dict[str, Any]] = None
    ) -> "DirectoryListResponse":
        """Create failed response"""
        return cls(
            status=OperationStatus.FAILED,
            message=error_message,
            error_code=error_code,
            error_details=error_details,
            directory=directory
        ) 
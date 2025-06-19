"""
Model converters for transforming between different formats
"""

from typing import Dict, Any, List
from datetime import datetime
import os

from .transcription import (
    TranscriptionResponse, TranscriptionFiles, TranscriptionSegment,
    TranscriptionMetrics, SpeakerInfo, ModelSize, OutputFormat
)
from .download import DownloadResponse, PodcastPlatform
from .file_operations import (
    FileInfoResponse, FileReadResponse, DirectoryListResponse,
    FileMetadata, FileReadProgress
)
from .base import OperationStatus


class TranscriptionConverter:
    """Converter for transcription models"""
    
    @staticmethod
    def from_legacy_dict(data: Dict[str, Any]) -> TranscriptionResponse:
        """Convert legacy dictionary format to TranscriptionResponse"""
        
        # Parse files
        files = TranscriptionFiles(
            txt_file_path=data.get("txt_file_path"),
            srt_file_path=data.get("srt_file_path"),
            json_file_path=data.get("json_file_path")
        )
        
        # Parse segments
        segments = []
        if "segments" in data:
            for seg_data in data["segments"]:
                segments.append(TranscriptionSegment(
                    start=seg_data.get("start", 0),
                    end=seg_data.get("end", 0),
                    text=seg_data.get("text", ""),
                    speaker=seg_data.get("speaker"),
                    confidence=seg_data.get("confidence")
                ))
        
        # Parse metrics
        metrics = TranscriptionMetrics(
            audio_duration=data.get("audio_duration", 0),
            processing_time=data.get("processing_time", 0),
            segment_count=data.get("segment_count", 0),
            model_used=data.get("model_used", ""),
            language_detected=data.get("language_detected", "unknown")
        )
        
        # Parse speaker info
        speaker_info = SpeakerInfo(
            enabled=data.get("speaker_diarization_enabled", False),
            global_speaker_count=data.get("global_speaker_count", 0),
            speaker_mapping=data.get("speaker_summary", {}).get("speaker_mapping", {}),
            speaker_summary=data.get("speaker_summary", {})
        )
        
        # Determine status
        status = OperationStatus.SUCCESS if data.get("processing_status") == "success" else OperationStatus.FAILED
        
        return TranscriptionResponse(
            status=status,
            message=data.get("error_message") if status == OperationStatus.FAILED else "转录完成",
            audio_file=data.get("audio_file", ""),
            files=files,
            segments=segments,
            speaker_info=speaker_info,
            metrics=metrics
        )
    
    @staticmethod
    def to_legacy_dict(response: TranscriptionResponse) -> Dict[str, Any]:
        """Convert TranscriptionResponse to legacy dictionary format"""
        
        return {
            "txt_file_path": response.files.txt_file_path,
            "srt_file_path": response.files.srt_file_path,
            "audio_file": response.audio_file,
            "model_used": response.metrics.model_used,
            "segment_count": response.metrics.segment_count,
            "audio_duration": response.metrics.audio_duration,
            "processing_status": response.status.value,
            "processing_time": response.metrics.processing_time,
            "saved_files": response.files.all_files,
            "speaker_diarization_enabled": response.speaker_info.enabled,
            "global_speaker_count": response.speaker_info.global_speaker_count,
            "speaker_summary": response.speaker_info.speaker_summary,
            "language_detected": response.metrics.language_detected,
            "error_message": response.message if response.is_failed else None
        }


class DownloadConverter:
    """Converter for download models"""
    
    @staticmethod
    def from_legacy_dict(data: Dict[str, Any]) -> DownloadResponse:
        """Convert legacy dictionary format to DownloadResponse"""
        
        status = OperationStatus.SUCCESS if data.get("status") == "success" else OperationStatus.FAILED
        
        # Calculate file size if available
        file_size_mb = None
        if data.get("audio_file_path") and os.path.exists(data["audio_file_path"]):
            try:
                file_size_bytes = os.path.getsize(data["audio_file_path"])
                file_size_mb = file_size_bytes / (1024 * 1024)
            except:
                pass
        
        return DownloadResponse(
            status=status,
            message=data.get("error_message") if status == OperationStatus.FAILED else "下载成功",
            original_url=data.get("original_url", ""),
            audio_file_path=data.get("audio_file_path"),
            file_size_mb=file_size_mb
        )
    
    @staticmethod
    def to_legacy_dict(response: DownloadResponse) -> Dict[str, Any]:
        """Convert DownloadResponse to legacy dictionary format"""
        
        return {
            "status": response.status.value,
            "original_url": response.original_url,
            "audio_file_path": response.audio_file_path,
            "error_message": response.message if response.is_failed else None
        }


class FileOperationConverter:
    """Converter for file operation models"""
    
    @staticmethod
    def from_legacy_file_info(data: Dict[str, Any]) -> FileInfoResponse:
        """Convert legacy file info format to FileInfoResponse"""
        
        status = OperationStatus.SUCCESS if data.get("status") == "success" else OperationStatus.FAILED
        
        metadata = None
        if status == OperationStatus.SUCCESS:
            metadata = FileMetadata(
                filename=data.get("filename", ""),
                full_path=data.get("file_path", ""),
                file_size=data.get("file_size", 0),
                file_size_mb=data.get("file_size_mb", 0.0),
                created_time=datetime.fromtimestamp(data.get("created_time", 0)),
                modified_time=datetime.fromtimestamp(data.get("modified_time", 0)),
                file_extension=data.get("file_extension", ""),
                is_audio_file=data.get("file_extension", "").lower() in ['.mp3', '.wav', '.m4a', '.flac']
            )
        
        return FileInfoResponse(
            status=status,
            message=data.get("error_message") if status == OperationStatus.FAILED else "文件信息获取成功",
            file_path=data.get("file_path", ""),
            file_exists=data.get("file_exists", False),
            metadata=metadata
        )
    
    @staticmethod
    def from_legacy_file_read(data: Dict[str, Any]) -> FileReadResponse:
        """Convert legacy file read format to FileReadResponse"""
        
        status = OperationStatus.SUCCESS if data.get("status") == "success" else OperationStatus.FAILED
        
        progress = None
        if status == OperationStatus.SUCCESS:
            progress = FileReadProgress(
                current_position=data.get("current_position", 0),
                file_size=data.get("file_size", 0),
                bytes_read=data.get("bytes_read", 0),
                content_length=data.get("content_length", 0),
                progress_percentage=data.get("progress_percentage", 0.0),
                end_of_file_reached=data.get("end_of_file_reached", False),
                actual_boundary=data.get("actual_boundary", "")
            )
        
        return FileReadResponse(
            status=status,
            message=data.get("error_message") if status == OperationStatus.FAILED else "文件读取成功",
            file_path=data.get("file_path", ""),
            content=data.get("content", ""),
            progress=progress
        )
    
    @staticmethod
    def from_legacy_directory_list(data: Dict[str, Any]) -> DirectoryListResponse:
        """Convert legacy directory list format to DirectoryListResponse"""
        
        status = OperationStatus.SUCCESS if not data.get("error_message") else OperationStatus.FAILED
        
        file_list = []
        if "file_list" in data:
            for file_data in data["file_list"]:
                # Handle time format conversion - original format is string, not ISO format
                created_time_str = file_data.get("created_time", "")
                modified_time_str = file_data.get("modified_time", "")
                
                try:
                    # Try to parse as ISO format first
                    created_time = datetime.fromisoformat(created_time_str.replace("T", " ")) if created_time_str else datetime.fromtimestamp(0)
                except:
                    # Fallback to default time
                    created_time = datetime.fromtimestamp(0)
                    
                try:
                    modified_time = datetime.fromisoformat(modified_time_str.replace("T", " ")) if modified_time_str else datetime.fromtimestamp(0)
                except:
                    modified_time = datetime.fromtimestamp(0)
                
                file_list.append(FileMetadata(
                    filename=file_data.get("filename", ""),
                    full_path=file_data.get("full_path", ""),
                    file_size=file_data.get("file_size", 0),
                    file_size_mb=file_data.get("file_size_mb", 0.0),
                    created_time=created_time,
                    modified_time=modified_time,
                    file_extension=os.path.splitext(file_data.get("filename", ""))[1],
                    is_audio_file=file_data.get("filename", "").lower().endswith(('.mp3', '.wav', '.m4a', '.flac'))
                ))
        
        return DirectoryListResponse(
            status=status,
            message=data.get("error_message", "目录扫描成功"),
            directory=data.get("scanned_directory", ""),
            total_files=data.get("total_files", 0),
            file_list=file_list
        ) 
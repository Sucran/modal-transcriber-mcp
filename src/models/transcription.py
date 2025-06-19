"""
Transcription models
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .base import BaseRequest, BaseResponse, OperationStatus


class ModelSize(str, Enum):
    """Whisper model sizes"""
    TINY = "tiny"
    BASE = "base" 
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    TURBO = "turbo"


class OutputFormat(str, Enum):
    """Output formats"""
    TXT = "txt"
    SRT = "srt"
    JSON = "json"


@dataclass
class TranscriptionRequest(BaseRequest):
    """Request model for transcription"""
    audio_file_path: str
    model_size: ModelSize = ModelSize.TURBO
    language: Optional[str] = None
    output_format: OutputFormat = OutputFormat.SRT
    enable_speaker_diarization: bool = False


@dataclass
class TranscriptionSegment:
    """Individual transcription segment"""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class SpeakerInfo:
    """Speaker diarization information"""
    enabled: bool = False
    global_speaker_count: int = 0
    speaker_mapping: Dict[str, str] = field(default_factory=dict)
    speaker_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptionFiles:
    """Generated transcription files"""
    txt_file_path: Optional[str] = None
    srt_file_path: Optional[str] = None
    json_file_path: Optional[str] = None
    
    @property
    def all_files(self) -> List[str]:
        """Get all non-None file paths"""
        return [f for f in [self.txt_file_path, self.srt_file_path, self.json_file_path] if f]


@dataclass
class TranscriptionMetrics:
    """Transcription processing metrics"""
    audio_duration: float = 0.0
    processing_time: float = 0.0
    segment_count: int = 0
    model_used: str = ""
    language_detected: str = "unknown"


@dataclass 
class TranscriptionResponse(BaseResponse):
    """Response model for transcription"""
    audio_file: str = ""
    files: TranscriptionFiles = field(default_factory=TranscriptionFiles)
    segments: List[TranscriptionSegment] = field(default_factory=list)
    speaker_info: SpeakerInfo = field(default_factory=SpeakerInfo)
    metrics: TranscriptionMetrics = field(default_factory=TranscriptionMetrics)
    
    @classmethod
    def success(
        cls,
        audio_file: str,
        files: TranscriptionFiles,
        segments: List[TranscriptionSegment],
        metrics: TranscriptionMetrics,
        speaker_info: Optional[SpeakerInfo] = None,
        message: str = "转录完成"
    ) -> "TranscriptionResponse":
        """Create successful response"""
        return cls(
            status=OperationStatus.SUCCESS,
            message=message,
            audio_file=audio_file,
            files=files,
            segments=segments,
            speaker_info=speaker_info or SpeakerInfo(),
            metrics=metrics
        )
    
    @classmethod
    def failed(
        cls,
        audio_file: str,
        error_message: str,
        error_code: str = "TRANSCRIPTION_ERROR",
        error_details: Optional[Dict[str, Any]] = None
    ) -> "TranscriptionResponse":
        """Create failed response"""
        return cls(
            status=OperationStatus.FAILED,
            message=error_message,
            error_code=error_code,
            error_details=error_details,
            audio_file=audio_file
        ) 
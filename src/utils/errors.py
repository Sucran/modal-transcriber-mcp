"""
Custom error classes for audio processing
"""


class AudioProcessingError(Exception):
    """Base exception for audio processing errors"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "AUDIO_PROCESSING_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert error to dictionary format"""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class TranscriptionError(AudioProcessingError):
    """Exception for transcription-related errors"""
    
    def __init__(self, message: str, model: str = None, audio_file: str = None, **kwargs):
        super().__init__(message, error_code="TRANSCRIPTION_ERROR", **kwargs)
        if model:
            self.details["model"] = model
        if audio_file:
            self.details["audio_file"] = audio_file


class SpeakerDetectionError(AudioProcessingError):
    """Exception for speaker detection-related errors"""
    
    def __init__(self, message: str, audio_file: str = None, **kwargs):
        super().__init__(message, error_code="SPEAKER_DETECTION_ERROR", **kwargs)
        if audio_file:
            self.details["audio_file"] = audio_file


class SpeakerDiarizationError(AudioProcessingError):
    """Exception for speaker diarization-related errors"""
    
    def __init__(self, message: str, audio_file: str = None, **kwargs):
        super().__init__(message, error_code="SPEAKER_DIARIZATION_ERROR", **kwargs)
        if audio_file:
            self.details["audio_file"] = audio_file


class AudioSplittingError(AudioProcessingError):
    """Exception for audio splitting-related errors"""
    
    def __init__(self, message: str, audio_file: str = None, **kwargs):
        super().__init__(message, error_code="AUDIO_SPLITTING_ERROR", **kwargs)
        if audio_file:
            self.details["audio_file"] = audio_file


class FileProcessingError(AudioProcessingError):
    """Exception for file processing-related errors"""
    
    def __init__(self, message: str, file_path: str = None, **kwargs):
        super().__init__(message, error_code="FILE_PROCESSING_ERROR", **kwargs)
        if file_path:
            self.details["file_path"] = file_path


class ModelLoadError(AudioProcessingError):
    """Exception for model loading errors"""
    
    def __init__(self, message: str, model_name: str = None, **kwargs):
        super().__init__(message, error_code="MODEL_LOAD_ERROR", **kwargs)
        if model_name:
            self.details["model_name"] = model_name


class ConfigurationError(AudioProcessingError):
    """Exception for configuration-related errors"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)
        if config_key:
            self.details["config_key"] = config_key


class DeploymentError(AudioProcessingError):
    """Exception for deployment-related errors"""
    
    def __init__(self, message: str, service: str = None, **kwargs):
        super().__init__(message, error_code="DEPLOYMENT_ERROR", **kwargs)
        if service:
            self.details["service"] = service 
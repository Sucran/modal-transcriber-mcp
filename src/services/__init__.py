"""
Services layer for the podcast transcription system
Provides clean abstraction for business logic
"""

# Core transcription services
from .transcription_service import TranscriptionService
from .distributed_transcription_service import DistributedTranscriptionService

# Modal-specific services
from .modal_transcription_service import ModalTranscriptionService
# Note: ModalDownloadService removed - downloads now handled locally by PodcastDownloadService

# Download and media services
from .podcast_download_service import PodcastDownloadService

# System services
from .health_service import HealthService

# File and utility services
from .file_management_service import FileManagementService

# Speaker services (if speaker diarization is available)
try:
    from .speaker_embedding_service import SpeakerEmbeddingService
    SPEAKER_DIARIZATION_AVAILABLE = True
except ImportError:
    SPEAKER_DIARIZATION_AVAILABLE = False
    SpeakerEmbeddingService = None

# Deprecated services (kept for backward compatibility but should not be used)
# These services have been consolidated into other services or replaced
try:
    from .audio_processing_service import AudioProcessingService
    from .file_service import FileService
    DEPRECATED_SERVICES_AVAILABLE = True
except ImportError:
    DEPRECATED_SERVICES_AVAILABLE = False
    AudioProcessingService = None
    FileService = None

# Export active services
__all__ = [
    # Primary services for active use
    "TranscriptionService",
    "DistributedTranscriptionService", 
    "ModalTranscriptionService",
    "PodcastDownloadService",
    "HealthService",
    "FileManagementService",
    
    # Optional services
    "SpeakerEmbeddingService",
    
    # Availability flags
    "SPEAKER_DIARIZATION_AVAILABLE",
    "DEPRECATED_SERVICES_AVAILABLE",
    
    # Deprecated services (for backward compatibility only)
    "AudioProcessingService",  
    "FileService"
]

# Service registry for dynamic access
SERVICE_REGISTRY = {
    "transcription": TranscriptionService,
    "distributed_transcription": DistributedTranscriptionService,
    "modal_transcription": ModalTranscriptionService,
    "podcast_download": PodcastDownloadService,
    "health": HealthService,
    "file_management": FileManagementService,
}

if SPEAKER_DIARIZATION_AVAILABLE:
    SERVICE_REGISTRY["speaker_embedding"] = SpeakerEmbeddingService

if DEPRECATED_SERVICES_AVAILABLE:
    SERVICE_REGISTRY["audio_processing"] = AudioProcessingService
    SERVICE_REGISTRY["file"] = FileService


def get_service(service_name: str, *args, **kwargs):
    """
    Factory function to get service instances
    
    Args:
        service_name: Name of the service to get
        *args: Arguments to pass to service constructor
        **kwargs: Keyword arguments to pass to service constructor
        
    Returns:
        Service instance
        
    Raises:
        ValueError: If service name is not found
    """
    if service_name not in SERVICE_REGISTRY:
        available_services = list(SERVICE_REGISTRY.keys())
        raise ValueError(f"Service '{service_name}' not found. Available services: {available_services}")
    
    service_class = SERVICE_REGISTRY[service_name]
    return service_class(*args, **kwargs)


def list_available_services() -> dict:
    """
    Get list of all available services with their status
    
    Returns:
        Dictionary of service names and their availability status
    """
    services = {}
    
    # Active services
    for name in ["transcription", "distributed_transcription", "modal_transcription", 
                 "podcast_download", "health", "file_management"]:
        services[name] = {"status": "active", "available": True}
    
    # Optional services
    services["speaker_embedding"] = {
        "status": "optional", 
        "available": SPEAKER_DIARIZATION_AVAILABLE
    }
    
    # Deprecated services
    if DEPRECATED_SERVICES_AVAILABLE:
        services["audio_processing"] = {"status": "deprecated", "available": True}
        services["file"] = {"status": "deprecated", "available": True}
    else:
        services["audio_processing"] = {"status": "deprecated", "available": False}
        services["file"] = {"status": "deprecated", "available": False}
    
    return services 
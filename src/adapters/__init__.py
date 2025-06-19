"""
Adapters for different transcription backends
"""

from .transcription_adapter_factory import TranscriptionAdapterFactory
from .local_adapter import LocalTranscriptionAdapter
from .modal_adapter import ModalTranscriptionAdapter

__all__ = [
    "TranscriptionAdapterFactory",
    "LocalTranscriptionAdapter", 
    "ModalTranscriptionAdapter"
] 
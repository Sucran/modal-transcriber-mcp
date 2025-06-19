"""
Configuration management for audio processing
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import json


@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    params: str
    description: str = ""


@dataclass
class AudioProcessingConfig:
    """Centralized configuration for audio processing"""
    
    # Model configurations
    whisper_models: Dict[str, ModelConfig] = field(default_factory=lambda: {
        "tiny": ModelConfig("tiny", "39M", "Fastest, lowest accuracy"),
        "base": ModelConfig("base", "74M", "Fast, low accuracy"),
        "small": ModelConfig("small", "244M", "Medium speed, medium accuracy"),
        "medium": ModelConfig("medium", "769M", "Slow, high accuracy"),
        "large": ModelConfig("large", "1550M", "Slowest, highest accuracy"),
        "turbo": ModelConfig("turbo", "809M", "Balanced speed and accuracy")
    })
    
    # Default settings
    default_model: str = "turbo"
    default_language: Optional[str] = None
    min_segment_length: float = 30.0
    min_silence_length: float = 1.0
    
    # Processing settings
    max_parallel_segments: int = 10
    timeout_seconds: int = 600
    
    # File paths
    cache_dir: str = "./cache"
    model_dir: str = "./models"
    
    # Modal settings
    modal_app_name: str = "podcast-transcription"
    modal_gpu_type: str = "A10G"
    modal_memory: int = 10240
    modal_cpu: int = 4
    
    # Speaker diarization
    hf_token_env_var: str = "HF_TOKEN"
    speaker_embedding_model: str = "pyannote/embedding"
    speaker_diarization_model: str = "pyannote/speaker-diarization-3.1"
    
    # Output formats
    supported_output_formats: List[str] = field(default_factory=lambda: ["txt", "srt", "json"])
    
    @classmethod
    def from_file(cls, config_path: str) -> "AudioProcessingConfig":
        """Load configuration from JSON file"""
        if not os.path.exists(config_path):
            return cls()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # Convert model configs
        if 'whisper_models' in config_dict:
            models = {}
            for name, model_data in config_dict['whisper_models'].items():
                models[name] = ModelConfig(**model_data)
            config_dict['whisper_models'] = models
        
        return cls(**config_dict)
    
    def to_file(self, config_path: str):
        """Save configuration to JSON file"""
        config_dict = {}
        for key, value in self.__dict__.items():
            if key == 'whisper_models':
                config_dict[key] = {
                    name: model.__dict__ for name, model in value.items()
                }
            else:
                config_dict[key] = value
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get model configuration by name"""
        if model_name not in self.whisper_models:
            raise ValueError(f"Unsupported model: {model_name}")
        return self.whisper_models[model_name]
    
    @property
    def is_speaker_diarization_available(self) -> bool:
        """Check if speaker diarization is available"""
        return os.environ.get(self.hf_token_env_var) is not None
    
    @property
    def hf_token(self) -> Optional[str]:
        """Get Hugging Face token"""
        return os.environ.get(self.hf_token_env_var) 
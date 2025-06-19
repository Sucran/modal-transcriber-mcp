"""
Storage Configuration Management
Centralizes all storage path configurations for downloads and transcripts
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class StorageConfig:
    """Centralized storage configuration for podcast processing"""
    
    def __init__(self, config_file: str = "config.env"):
        """
        Initialize storage configuration
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self._load_config()
        self._ensure_directories()
    
    def _load_config(self):
        """Load configuration from environment file or Modal environment"""
        # Check if we're running in Modal environment
        is_modal_env = (
            os.getenv("MODAL_TASK_ID") or 
            os.getenv("MODAL_IS_INSIDE_CONTAINER") or 
            os.getenv("DEPLOYMENT_MODE") == "modal"
        )
        
        if is_modal_env:
            print("🔧 Using Modal environment configuration")
            # Use Modal defaults - don't load config files
            self.downloads_dir = Path("/root/downloads").resolve()
            self.transcripts_dir = Path("/root/transcripts").resolve()
            self.cache_dir = Path("/root/cache").resolve()
        else:
            print("🔧 Using local environment configuration")
            # Load from config file if it exists
            if os.path.exists(self.config_file):
                load_dotenv(self.config_file, override=False)
                print(f"📄 Loaded config from {self.config_file}")
            
            # Load from .env if it exists
            if os.path.exists(".env"):
                load_dotenv(".env", override=False)
                print("📄 Loaded config from .env")
            
            # Set defaults for local environment
            self.downloads_dir = Path(os.getenv("DOWNLOADS_DIR", "./downloads")).resolve()
            self.transcripts_dir = Path(os.getenv("TRANSCRIPTS_DIR", "./transcripts")).resolve()
            self.cache_dir = Path(os.getenv("CACHE_DIR", "./cache")).resolve()
        
        # Common settings (apply to both environments)
        self.download_quality = os.getenv("DOWNLOAD_QUALITY", "highest")
        self.convert_to_mp3 = os.getenv("CONVERT_TO_MP3", "true").lower() == "true"
        self.default_model_size = os.getenv("DEFAULT_MODEL_SIZE", "turbo")
        self.default_output_format = os.getenv("DEFAULT_OUTPUT_FORMAT", "srt")
        self.enable_speaker_diarization = os.getenv("ENABLE_SPEAKER_DIARIZATION", "false").lower() == "true"
        self.use_parallel_processing = os.getenv("USE_PARALLEL_PROCESSING", "true").lower() == "true"
        self.chunk_duration = int(os.getenv("CHUNK_DURATION", "60"))
        
        # Store environment type for reference
        self.is_modal_env = is_modal_env
        
    def _ensure_directories(self):
        """Ensure all configured directories exist"""
        for directory in [self.downloads_dir, self.transcripts_dir, self.cache_dir]:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                if self.is_modal_env:
                    print(f"📁 Modal storage directory ready: {directory}")
                else:
                    print(f"📁 Local storage directory ready: {directory}")
            except Exception as e:
                print(f"⚠️ Failed to create directory {directory}: {e}")
                # In Modal environment, some directories might be managed differently
                if not self.is_modal_env:
                    raise
    
    def get_download_path(self, filename: str) -> Path:
        """
        Get full path for downloaded audio file
        
        Args:
            filename: Audio filename
            
        Returns:
            Full path for downloaded file
        """
        return self.downloads_dir / filename
    
    def get_transcript_path(self, audio_filename: str, output_format: str = None) -> Path:
        """
        Get full path for transcript file
        
        Args:
            audio_filename: Original audio filename
            output_format: Output format (txt, srt, json)
            
        Returns:
            Full path for transcript file
        """
        if output_format is None:
            output_format = self.default_output_format
            
        # Remove audio extension and add transcript extension
        base_name = Path(audio_filename).stem
        transcript_filename = f"{base_name}.{output_format}"
        
        return self.transcripts_dir / transcript_filename
    
    def get_cache_path(self, filename: str) -> Path:
        """
        Get full path for cache file
        
        Args:
            filename: Cache filename
            
        Returns:
            Full path for cache file
        """
        return self.cache_dir / filename
    
    def get_audio_files(self) -> list[Path]:
        """
        Get list of all audio files in downloads directory
        
        Returns:
            List of audio file paths
        """
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg'}
        audio_files = []
        
        for file_path in self.downloads_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                audio_files.append(file_path)
        
        return sorted(audio_files)
    
    def get_transcript_files(self, audio_filename: str = None) -> dict[str, Path]:
        """
        Get paths for all transcript formats for a given audio file
        
        Args:
            audio_filename: Audio filename (optional)
            
        Returns:
            Dictionary mapping format to file path
        """
        if audio_filename:
            base_name = Path(audio_filename).stem
            return {
                'txt': self.get_transcript_path(audio_filename, 'txt'),
                'srt': self.get_transcript_path(audio_filename, 'srt'),
                'json': self.get_transcript_path(audio_filename, 'json')
            }
        else:
            # Return all transcript files
            transcript_files = {'txt': [], 'srt': [], 'json': []}
            for file_path in self.transcripts_dir.iterdir():
                if file_path.is_file():
                    ext = file_path.suffix[1:]  # Remove the dot
                    if ext in transcript_files:
                        transcript_files[ext].append(file_path)
            return transcript_files
    
    def cleanup_temp_files(self, pattern: str = "temp_*"):
        """
        Clean up temporary files in cache directory
        
        Args:
            pattern: File pattern to match for cleanup
        """
        import glob
        temp_files = glob.glob(str(self.cache_dir / pattern))
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
                print(f"🗑️ Cleaned up temp file: {temp_file}")
            except Exception as e:
                print(f"⚠️ Failed to cleanup {temp_file}: {e}")
    
    def get_storage_info(self) -> dict:
        """
        Get storage configuration information
        
        Returns:
            Dictionary with storage information
        """
        audio_files = self.get_audio_files()
        transcript_files = self.get_transcript_files()
        
        def get_dir_size(directory: Path) -> int:
            """Get total size of directory in bytes"""
            total_size = 0
            try:
                for file_path in directory.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            except Exception:
                pass
            return total_size
        
        return {
            "environment": "modal" if self.is_modal_env else "local",
            "downloads_dir": str(self.downloads_dir),
            "transcripts_dir": str(self.transcripts_dir),
            "cache_dir": str(self.cache_dir),
            "audio_files_count": len(audio_files),
            "transcript_txt_count": len(transcript_files.get('txt', [])),
            "transcript_srt_count": len(transcript_files.get('srt', [])),
            "transcript_json_count": len(transcript_files.get('json', [])),
            "downloads_size_mb": round(get_dir_size(self.downloads_dir) / (1024 * 1024), 2),
            "transcripts_size_mb": round(get_dir_size(self.transcripts_dir) / (1024 * 1024), 2),
            "cache_size_mb": round(get_dir_size(self.cache_dir) / (1024 * 1024), 2),
        }


# Global storage configuration instance
_storage_config: Optional[StorageConfig] = None


def get_storage_config() -> StorageConfig:
    """
    Get global storage configuration instance
    
    Returns:
        StorageConfig instance
    """
    global _storage_config
    if _storage_config is None:
        _storage_config = StorageConfig()
    return _storage_config


def get_downloads_dir() -> Path:
    """Get downloads directory path"""
    return get_storage_config().downloads_dir


def get_transcripts_dir() -> Path:
    """Get transcripts directory path"""
    return get_storage_config().transcripts_dir


def get_cache_dir() -> Path:
    """Get cache directory path"""
    return get_storage_config().cache_dir 
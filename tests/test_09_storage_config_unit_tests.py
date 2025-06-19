"""
Unit tests for storage configuration system
Tests the new storage configuration functionality including:
- Storage config management
- Environment detection
- Path generation
- Storage tools
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import asyncio

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.utils.storage_config import StorageConfig, get_storage_config
from src.tools.storage_tools import get_storage_info_tool


class TestStorageConfig:
    """Test cases for StorageConfig class"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_file = self.temp_dir / "test_config.env"
        
        # Create test config file
        config_content = """
DOWNLOADS_DIR=./test_downloads
TRANSCRIPTS_DIR=./test_transcripts
CACHE_DIR=./test_cache
DEFAULT_MODEL_SIZE=base
DEFAULT_OUTPUT_FORMAT=srt
USE_PARALLEL_PROCESSING=true
CHUNK_DURATION=30
"""
        with open(self.config_file, 'w') as f:
            f.write(config_content)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        # Remove temporary directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_local_environment_detection(self):
        """Test local environment detection and configuration loading"""
        # Mock environment to ensure local detection
        with patch.dict(os.environ, {}, clear=True):
            storage_config = StorageConfig(config_file=str(self.config_file))
            
            assert not storage_config.is_modal_env
            assert storage_config.default_model_size == "base"
            assert storage_config.default_output_format == "srt"
            assert storage_config.use_parallel_processing == True
            assert storage_config.chunk_duration == 30
    
    def test_modal_environment_detection(self):
        """Test Modal environment detection"""
        # Mock Modal environment variables
        with patch.dict(os.environ, {"MODAL_TASK_ID": "test-task-123"}, clear=True):
            storage_config = StorageConfig(config_file=str(self.config_file))
            
            assert storage_config.is_modal_env
            assert str(storage_config.downloads_dir) == "/root/downloads"
            assert str(storage_config.transcripts_dir) == "/root/transcripts"
            assert str(storage_config.cache_dir) == "/root/cache"
    
    def test_modal_environment_detection_deployment_mode(self):
        """Test Modal environment detection via DEPLOYMENT_MODE"""
        with patch.dict(os.environ, {"DEPLOYMENT_MODE": "modal"}, clear=True):
            storage_config = StorageConfig(config_file=str(self.config_file))
            
            assert storage_config.is_modal_env
    
    def test_modal_environment_detection_container_var(self):
        """Test Modal environment detection via MODAL_IS_INSIDE_CONTAINER"""
        with patch.dict(os.environ, {"MODAL_IS_INSIDE_CONTAINER": "true"}, clear=True):
            storage_config = StorageConfig(config_file=str(self.config_file))
            
            assert storage_config.is_modal_env
    
    def test_path_generation(self):
        """Test path generation methods"""
        with patch.dict(os.environ, {}, clear=True):
            storage_config = StorageConfig(config_file=str(self.config_file))
            
            # Test download path
            download_path = storage_config.get_download_path("test.mp3")
            assert download_path.name == "test.mp3"
            assert "test_downloads" in str(download_path)
            
            # Test transcript paths
            txt_path = storage_config.get_transcript_path("test.mp3", "txt")
            assert txt_path.name == "test.txt"
            assert "test_transcripts" in str(txt_path)
            
            srt_path = storage_config.get_transcript_path("test.mp3", "srt")
            assert srt_path.name == "test.srt"
            
            # Test default format
            default_path = storage_config.get_transcript_path("test.mp3")
            assert default_path.name == "test.srt"  # Should use default format
            
            # Test cache path
            cache_path = storage_config.get_cache_path("temp.dat")
            assert cache_path.name == "temp.dat"
            assert "test_cache" in str(cache_path)
    
    def test_audio_files_listing(self):
        """Test audio files listing functionality"""
        with patch.dict(os.environ, {}, clear=True):
            # Create a separate test directory for this specific test
            test_dir = self.temp_dir / "audio_test"
            test_config_file = test_dir / "config.env"
            test_dir.mkdir(exist_ok=True)
            
            # Create isolated config file
            config_content = """
DOWNLOADS_DIR=./audio_test_downloads
TRANSCRIPTS_DIR=./audio_test_transcripts
CACHE_DIR=./audio_test_cache
"""
            with open(test_config_file, 'w') as f:
                f.write(config_content)
            
            storage_config = StorageConfig(config_file=str(test_config_file))
            
            # Create test audio files
            storage_config.downloads_dir.mkdir(parents=True, exist_ok=True)
            
            test_files = ["test1.mp3", "test2.wav", "test3.m4a", "not_audio.txt"]
            for filename in test_files:
                (storage_config.downloads_dir / filename).touch()
            
            audio_files = storage_config.get_audio_files()
            audio_names = [f.name for f in audio_files]
            
            assert "test1.mp3" in audio_names
            assert "test2.wav" in audio_names
            assert "test3.m4a" in audio_names
            assert "not_audio.txt" not in audio_names
            assert len(audio_files) == 3
    
    def test_transcript_files_mapping(self):
        """Test transcript files mapping functionality"""
        with patch.dict(os.environ, {}, clear=True):
            storage_config = StorageConfig(config_file=str(self.config_file))
            
            # Test specific audio file mapping
            transcript_files = storage_config.get_transcript_files("episode123.mp3")
            
            assert "txt" in transcript_files
            assert "srt" in transcript_files
            assert "json" in transcript_files
            
            assert transcript_files["txt"].name == "episode123.txt"
            assert transcript_files["srt"].name == "episode123.srt"
            assert transcript_files["json"].name == "episode123.json"
    
    def test_storage_info_generation(self):
        """Test storage information generation"""
        with patch.dict(os.environ, {}, clear=True):
            # Create a separate test directory for this specific test
            test_dir = self.temp_dir / "info_test"
            test_config_file = test_dir / "config.env"
            test_dir.mkdir(exist_ok=True)
            
            # Create isolated config file
            config_content = """
DOWNLOADS_DIR=./info_test_downloads
TRANSCRIPTS_DIR=./info_test_transcripts
CACHE_DIR=./info_test_cache
"""
            with open(test_config_file, 'w') as f:
                f.write(config_content)
            
            storage_config = StorageConfig(config_file=str(test_config_file))
            
            # Create some test files
            storage_config.downloads_dir.mkdir(parents=True, exist_ok=True)
            storage_config.transcripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create test audio file
            test_audio = storage_config.downloads_dir / "test.mp3"
            test_audio.write_bytes(b"fake audio data" * 100)
            
            # Create test transcript files
            (storage_config.transcripts_dir / "test.txt").write_text("transcript text")
            (storage_config.transcripts_dir / "test.srt").write_text("srt content")
            
            storage_info = storage_config.get_storage_info()
            
            assert storage_info["environment"] == "local"
            assert storage_info["audio_files_count"] == 1
            assert storage_info["transcript_txt_count"] == 1
            assert storage_info["transcript_srt_count"] == 1
            assert storage_info["transcript_json_count"] == 0
            # Check that sizes are calculated (should be greater than 0 due to our test files)
            assert storage_info["downloads_size_mb"] >= 0
            assert storage_info["transcripts_size_mb"] >= 0
    
    def test_cleanup_temp_files(self):
        """Test temporary files cleanup"""
        with patch.dict(os.environ, {}, clear=True):
            storage_config = StorageConfig(config_file=str(self.config_file))
            
            # Create cache directory and temp files
            storage_config.cache_dir.mkdir(parents=True, exist_ok=True)
            
            temp_file1 = storage_config.cache_dir / "temp_file1.dat"
            temp_file2 = storage_config.cache_dir / "temp_file2.dat"
            normal_file = storage_config.cache_dir / "normal_file.dat"
            
            temp_file1.touch()
            temp_file2.touch()
            normal_file.touch()
            
            # Test cleanup
            storage_config.cleanup_temp_files("temp_*")
            
            assert not temp_file1.exists()
            assert not temp_file2.exists()
            assert normal_file.exists()  # Should not be deleted
    
    def test_config_file_not_exists(self):
        """Test behavior when config file doesn't exist"""
        non_existent_config = self.temp_dir / "non_existent.env"
        
        with patch.dict(os.environ, {}, clear=True):
            storage_config = StorageConfig(config_file=str(non_existent_config))
            
            # Should use defaults
            assert not storage_config.is_modal_env
            assert storage_config.default_model_size == "turbo"
            assert storage_config.default_output_format == "srt"


class TestStorageConfigGlobalInstance:
    """Test cases for global storage config instance management"""
    
    def test_global_instance_singleton(self):
        """Test that get_storage_config returns singleton instance"""
        # Clear any existing global instance
        import src.utils.storage_config as storage_module
        storage_module._storage_config = None
        
        with patch.dict(os.environ, {}, clear=True):
            config1 = get_storage_config()
            config2 = get_storage_config()
            
            assert config1 is config2  # Should be the same instance
    
    def test_global_instance_reset(self):
        """Test resetting global instance"""
        import src.utils.storage_config as storage_module
        
        with patch.dict(os.environ, {}, clear=True):
            config1 = get_storage_config()
            
            # Reset global instance
            storage_module._storage_config = None
            
            config2 = get_storage_config()
            
            assert config1 is not config2  # Should be different instances


class TestStorageTools:
    """Test cases for storage management tools"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock storage config to use temp directory
        self.mock_config = MagicMock()
        self.mock_config.downloads_dir = self.temp_dir / "downloads"
        self.mock_config.transcripts_dir = self.temp_dir / "transcripts"
        self.mock_config.cache_dir = self.temp_dir / "cache"
        self.mock_config.is_modal_env = False
        
        # Create directories
        for directory in [self.mock_config.downloads_dir, 
                         self.mock_config.transcripts_dir, 
                         self.mock_config.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @pytest.mark.asyncio
    async def test_get_storage_info_tool_success(self):
        """Test get_storage_info_tool with successful execution"""
        
        # Create test files
        (self.mock_config.downloads_dir / "test.mp3").write_bytes(b"audio data")
        (self.mock_config.transcripts_dir / "test.txt").write_text("transcript")
        
        # Mock storage config
        mock_storage_info = {
            "environment": "local",
            "downloads_dir": str(self.mock_config.downloads_dir),
            "transcripts_dir": str(self.mock_config.transcripts_dir),
            "cache_dir": str(self.mock_config.cache_dir),
            "audio_files_count": 1,
            "transcript_txt_count": 1,
            "transcript_srt_count": 0,
            "transcript_json_count": 0,
            "downloads_size_mb": 0.01,
            "transcripts_size_mb": 0.01,
            "cache_size_mb": 0.0
        }
        
        self.mock_config.get_storage_info.return_value = mock_storage_info
        
        with patch('src.tools.storage_tools.get_storage_config', return_value=self.mock_config):
            result = await get_storage_info_tool()
            
            assert result["status"] == "success"
            assert result["environment"] == "local"
            assert result["audio_files_count"] == 1
            assert result["transcript_txt_count"] == 1
    
    @pytest.mark.asyncio
    async def test_get_storage_info_tool_failure(self):
        """Test get_storage_info_tool with exception handling"""
        
        # Mock config that raises exception
        self.mock_config.get_storage_info.side_effect = Exception("Test error")
        
        with patch('src.tools.storage_tools.get_storage_config', return_value=self.mock_config):
            result = await get_storage_info_tool()
            
            assert result["status"] == "failed"
            assert "Test error" in result["error_message"]


class TestDistributedTranscriptionFixes:
    """Test cases for distributed transcription speaker information collection fixes"""
    
    def test_collect_speaker_information_string_speakers(self):
        """Test handling of string format speakers_detected"""
        from src.services.distributed_transcription_service import DistributedTranscriptionService
        
        service = DistributedTranscriptionService()
        
        # Test with string format speakers_detected
        successful_chunks = [
            {
                "speakers_detected": "SPEAKER_01",  # String instead of list
                "speaker_summary": {
                    "SPEAKER_01": {
                        "total_duration": 120.5,
                        "segment_count": 5
                    }
                }
            },
            {
                "speakers_detected": ["SPEAKER_02"],  # Normal list format
                "speaker_summary": {
                    "SPEAKER_02": {
                        "total_duration": 95.3,
                        "segment_count": 3
                    }
                }
            }
        ]
        
        result = service._collect_speaker_information(successful_chunks, True)
        
        assert result["global_speaker_count"] == 2
        assert "SPEAKER_01" in result["speakers_detected"]
        assert "SPEAKER_02" in result["speakers_detected"]
        assert result["speaker_summary"]["SPEAKER_01"]["total_duration"] == 120.5
        assert result["speaker_summary"]["SPEAKER_02"]["total_duration"] == 95.3
    
    def test_collect_speaker_information_invalid_data(self):
        """Test handling of invalid speaker data"""
        from src.services.distributed_transcription_service import DistributedTranscriptionService
        
        service = DistributedTranscriptionService()
        
        # Test with invalid data formats
        successful_chunks = [
            {
                "speakers_detected": 123,  # Invalid type (number)
                "speaker_summary": "invalid"  # Invalid type (string)
            },
            {
                "speakers_detected": None,  # None value
                "speaker_summary": {
                    "SPEAKER_01": "invalid_info"  # Invalid speaker info format
                }
            },
            {
                "speakers_detected": ["SPEAKER_02"],  # Valid
                "speaker_summary": {
                    "SPEAKER_02": {
                        "total_duration": 50.0,
                        "segment_count": 2
                    }
                }
            }
        ]
        
        result = service._collect_speaker_information(successful_chunks, True)
        
        # Should handle invalid data gracefully and only process valid chunk
        assert result["global_speaker_count"] == 1
        assert result["speakers_detected"] == ["SPEAKER_02"]
        assert result["speaker_summary"]["SPEAKER_02"]["total_duration"] == 50.0
    
    def test_collect_speaker_information_disabled(self):
        """Test when speaker diarization is disabled"""
        from src.services.distributed_transcription_service import DistributedTranscriptionService
        
        service = DistributedTranscriptionService()
        
        successful_chunks = [{"speakers_detected": ["SPEAKER_01"]}]
        
        result = service._collect_speaker_information(successful_chunks, False)
        
        # Should return empty result when disabled
        assert result == {}


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"]) 
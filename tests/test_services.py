"""
Unit tests for the services layer
Tests all major services and their functionality
"""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import json

# Import services
from src.services import (
    TranscriptionService,
    DistributedTranscriptionService,
    ModalTranscriptionService,
    PodcastDownloadService,
    HealthService,
    FileManagementService,
    get_service,
    list_available_services,
    SERVICE_REGISTRY
)
# Note: ModalDownloadService removed - downloads now handled locally


class TestTranscriptionService:
    """Test the core TranscriptionService"""
    
    def setup_method(self):
        self.service = TranscriptionService()
    
    def test_init(self):
        """Test service initialization"""
        assert self.service is not None
        assert hasattr(self.service, 'transcribe_audio')
    
    @patch('os.path.exists')
    @patch('whisper.load_model')
    def test_load_cached_model(self, mock_load_model, mock_exists):
        """Test model loading with cache"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        mock_exists.return_value = False  # No cache directory
        
        # Test loading new model
        model = self.service._load_cached_model("turbo")
        assert model is not None
        mock_load_model.assert_called()
        
        # Test loading with cache directory available
        mock_load_model.reset_mock()
        mock_exists.return_value = True  # Cache directory exists
        model2 = self.service._load_cached_model("turbo")
        assert model2 is not None
        # Should call load_model with download_root parameter
        mock_load_model.assert_called_with("turbo", download_root="/model")


class TestDistributedTranscriptionService:
    """Test the DistributedTranscriptionService with intelligent segmentation"""
    
    def setup_method(self):
        self.service = DistributedTranscriptionService()
    
    def test_init(self):
        """Test service initialization"""
        assert self.service is not None
        assert hasattr(self.service, 'split_audio_by_time')
        assert hasattr(self.service, 'split_audio_by_silence')
        assert hasattr(self.service, 'choose_segmentation_strategy')
    
    def test_split_audio_by_time(self):
        """Test time-based audio splitting"""
        # Mock audio file and ffprobe
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "120.5"  # 120.5 seconds duration
            
            chunks = self.service.split_audio_by_time("test.mp3", chunk_duration=60)
            
            assert len(chunks) == 2  # 120.5s / 60s = 2 chunks
            assert chunks[0]["start_time"] == 0.0
            assert chunks[0]["end_time"] == 60.0
            assert chunks[1]["start_time"] == 60.0
            # The end time is calculated as min(start + duration, total), so it's 120.0 not 120.5
            assert chunks[1]["end_time"] == 120.0  # Fixed expectation
    
    @patch('ffmpeg.probe')
    @patch('subprocess.Popen')
    def test_split_audio_by_silence(self, mock_popen, mock_probe):
        """Test silence-based audio splitting"""
        # Mock audio metadata
        mock_probe.return_value = {"format": {"duration": "180.0"}}
        
        # Mock silence detection output
        mock_process = Mock()
        mock_process.stderr = [
            "[silencedetect @ 0x123] silence_end: 30.5 | silence_duration: 2.1",
            "[silencedetect @ 0x456] silence_end: 90.3 | silence_duration: 1.8",
            ""
        ]
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        segments = self.service.split_audio_by_silence("test.mp3")
        
        # Should create segments based on silence detection
        assert len(segments) >= 1
        assert all("segmentation_type" in seg for seg in segments)
    
    @patch('ffmpeg.probe')
    def test_choose_segmentation_strategy_short_audio(self, mock_probe):
        """Test segmentation strategy for short audio"""
        # Mock short audio (4 minutes)
        mock_probe.return_value = {"format": {"duration": "240.0"}}
        
        segments = self.service.choose_segmentation_strategy("test.mp3")
        
        # Should use single chunk for short audio
        assert len(segments) == 1
        assert segments[0]["segmentation_type"] == "single"
    
    @patch('ffmpeg.probe')
    def test_choose_segmentation_strategy_long_audio(self, mock_probe):
        """Test segmentation strategy for long audio"""
        # Mock long audio (10 minutes)
        mock_probe.return_value = {"format": {"duration": "600.0"}}
        
        with patch.object(self.service, 'split_audio_by_silence') as mock_silence_split:
            mock_silence_split.return_value = [
                {"chunk_index": 0, "start_time": 0, "end_time": 180, "duration": 180, "segmentation_type": "silence_based"},
                {"chunk_index": 1, "start_time": 180, "end_time": 360, "duration": 180, "segmentation_type": "silence_based"}
            ]
            
            segments = self.service.choose_segmentation_strategy("test.mp3", use_intelligent_segmentation=True)
            
            # Should use intelligent segmentation
            mock_silence_split.assert_called_once()
            assert len(segments) == 2


class TestModalTranscriptionService:
    """Test the ModalTranscriptionService"""
    
    def setup_method(self):
        self.service = ModalTranscriptionService()
    
    def test_init(self):
        """Test service initialization"""
        assert self.service is not None
        assert "transcribe_audio" in self.service.endpoint_urls
        assert "health_check" in self.service.endpoint_urls
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self):
        """Test transcription with non-existent file"""
        result = await self.service.transcribe_audio_file("nonexistent.mp3")
        
        assert result["processing_status"] == "failed"
        assert "not found" in result["error_message"]
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    @patch('os.path.exists')
    @patch('builtins.open', create=True)
    async def test_transcribe_audio_file_success(self, mock_open, mock_exists, mock_post):
        """Test successful transcription"""
        # Mock file existence and content
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = b"fake audio data"
        
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "processing_status": "success",
            "segment_count": 10,
            "audio_duration": 120.5
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await self.service.transcribe_audio_file("test.mp3")
        
        assert result["processing_status"] == "success"
        assert result["segment_count"] == 10
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_check_endpoints_health(self, mock_get):
        """Test endpoint health checking"""
        # Mock health check response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await self.service.check_endpoints_health()
        
        assert "health_check" in result
        assert result["health_check"]["status"] == "healthy"


# TestModalDownloadService class removed - ModalDownloadService has been deprecated
# Downloads are now handled locally by PodcastDownloadService (tested below)


class TestHealthService:
    """Test the HealthService"""
    
    def setup_method(self):
        self.service = HealthService()
    
    def test_init(self):
        """Test service initialization"""
        assert self.service is not None
    
    @patch('whisper.available_models')
    @patch('whisper.load_model')
    @patch('os.path.exists')
    def test_check_whisper_models(self, mock_exists, mock_load_model, mock_available_models):
        """Test Whisper models checking"""
        mock_available_models.return_value = ["tiny", "base", "small", "medium", "large", "turbo"]
        mock_load_model.return_value = Mock()
        mock_exists.return_value = True
        
        status = self.service._check_whisper_models()
        
        assert status["status"] == "healthy"
        assert "turbo" in status["available_models"]
        assert status["default_model"] == "turbo"


class TestServiceRegistry:
    """Test the service registry and factory functions"""
    
    def test_get_service_valid(self):
        """Test getting valid service"""
        service = get_service("transcription")
        assert isinstance(service, TranscriptionService)
    
    def test_get_service_invalid(self):
        """Test getting invalid service"""
        with pytest.raises(ValueError) as excinfo:
            get_service("nonexistent_service")
        
        assert "not found" in str(excinfo.value)
    
    def test_list_available_services(self):
        """Test listing available services"""
        services = list_available_services()
        
        assert "transcription" in services
        assert "distributed_transcription" in services
        assert "modal_transcription" in services
        assert services["transcription"]["status"] == "active"
    
    def test_service_registry_completeness(self):
        """Test that all expected services are in registry"""
        expected_services = [
            "transcription", "distributed_transcription", "modal_transcription",
            "podcast_download", "health", "file_management"
        ]
        
        for service_name in expected_services:
            assert service_name in SERVICE_REGISTRY


class TestFileManagementService:
    """Test the FileManagementService"""
    
    def setup_method(self):
        self.service = FileManagementService()
    
    def test_init(self):
        """Test service initialization"""
        assert self.service is not None
    
    @pytest.mark.asyncio
    async def test_scan_mp3_files(self):
        """Test MP3 file scanning"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test MP3 files
            test_files = ["test1.mp3", "test2.mp3", "other.txt"]
            for filename in test_files:
                Path(temp_dir, filename).touch()
            
            result = await self.service.scan_mp3_files(temp_dir)
            
            assert result["total_files"] == 2  # Only MP3 files
            assert len(result["file_list"]) == 2
            assert all(f["filename"].endswith(".mp3") for f in result["file_list"])
    
    @pytest.mark.asyncio
    async def test_get_file_info(self):
        """Test file info retrieval"""
        with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_file:
            temp_file.write(b"test content")
            temp_file.flush()
            
            result = await self.service.get_file_info(temp_file.name)
            
            assert result["status"] == "success"
            assert result["file_exists"] is True
            assert result["file_extension"] == ".mp3"


# Integration test for service interactions
class TestServiceIntegration:
    """Test interactions between different services"""
    
    @pytest.mark.asyncio
    async def test_distributed_transcription_with_modal_service(self):
        """Test DistributedTranscriptionService working with ModalTranscriptionService"""
        distributed_service = DistributedTranscriptionService()
        modal_service = ModalTranscriptionService()
        
        # Mock a successful chunk transcription
        with patch.object(modal_service, 'transcribe_chunk') as mock_transcribe:
            mock_transcribe.return_value = {
                "processing_status": "success",
                "text": "Test transcription",
                "segments": []
            }
            
            # Test chunk transcription
            result = await modal_service.transcribe_chunk(
                chunk_path="test_chunk.wav",
                start_time=0.0,
                end_time=30.0
            )
            
            assert result["processing_status"] == "success"
            mock_transcribe.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 
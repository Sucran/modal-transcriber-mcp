"""
Test configuration and shared fixtures
"""

import pytest
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from typing import Generator, Dict, Any

from src.services.audio_processing_service import AudioProcessingService
from src.services.podcast_download_service import PodcastDownloadService
from src.services.file_management_service import FileManagementService
from src.services.speaker_embedding_service import SpeakerEmbeddingService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp(prefix="podcast_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_mp3_files(temp_dir: str) -> Dict[str, str]:
    """Create sample MP3 files for testing"""
    import ffmpeg
    
    files = {}
    for i, name in enumerate(["test1.mp3", "test2.mp3"]):
        file_path = os.path.join(temp_dir, name)
        # Create a short silence audio file for testing
        (
            ffmpeg
            .input('anullsrc=channel_layout=mono:sample_rate=16000', f='lavfi', t=5)
            .output(file_path, acodec='mp3')
            .overwrite_output()
            .run(quiet=True)
        )
        files[name] = file_path
    
    return files


@pytest.fixture
def podcast_download_service() -> PodcastDownloadService:
    """Create podcast download service instance"""
    return PodcastDownloadService()


@pytest.fixture
def file_management_service() -> FileManagementService:
    """Create file management service instance"""
    return FileManagementService()


@pytest.fixture
def apple_podcast_url() -> str:
    """Sample Apple Podcast URL for testing"""
    return "https://podcasts.apple.com/us/podcast/the-tim-ferriss-show/id863897795?i=1000640901376"


@pytest.fixture
def xiaoyuzhou_podcast_url() -> str:
    """Sample XiaoYuZhou Podcast URL for testing"""
    return "https://www.xiaoyuzhoufm.com/episode/654321"


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Test configuration"""
    return {
        "audio_processing": {
            "min_segment_length": 10.0,
            "min_silence_length": 0.5,
            "max_concurrent_segments": 2
        },
        "download": {
            "timeout": 30,
            "max_retries": 2
        },
        "transcription": {
            "model_name": "base",
            "language": "auto"
        }
    } 
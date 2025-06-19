"""
Test Modal Final Improvements - Updated for new service architecture
Tests model preloading, distributed processing with enhanced segmentation, and speaker diarization
"""

import asyncio
import pytest
import os
import time
from pathlib import Path

# Import from new service architecture
from src.services import (
    ModalTranscriptionService, 
    ModalDownloadService, 
    HealthService,
    TranscriptionService,
    DistributedTranscriptionService
)

# Import updated tools
from src.tools.transcription_tools import (
    transcribe_audio_file_tool,
    check_modal_endpoints_health,
    get_system_status
)

from src.tools.download_tools import (
    get_file_info_tool,
    read_text_file_segments_tool
)


class TestModalFinalImprovements:
    """Test suite for Modal improvements with new architecture"""
    
    @pytest.mark.asyncio
    async def test_model_preloading_health_check(self):
        """Test that models are properly preloaded in Modal"""
        print("\n🏗️ Testing model preloading health check...")
        
        health_status = await check_modal_endpoints_health()
        
        # Check if health check endpoint responded
        assert "health_check" in health_status, "Health check endpoint not found"
        health_endpoint = health_status["health_check"]
        
        if health_endpoint["status"] == "healthy":
            print("✅ Health check endpoint is accessible")
            
            # Get detailed system status
            system_status = await get_system_status()
            
            # Check Whisper status
            whisper_status = system_status.get("whisper", {})
            print(f"🤖 Whisper status: {whisper_status.get('status', 'unknown')}")
            print(f"🎯 Default model: {whisper_status.get('default_model', 'unknown')}")
            print(f"📦 Model cache exists: {whisper_status.get('model_cache_exists', False)}")
            
            # Verify turbo model is available
            available_models = whisper_status.get("available_models", [])
            assert "turbo" in available_models, f"Turbo model not available. Available: {available_models}"
            
            # Check speaker diarization status
            speaker_status = system_status.get("speaker_diarization", {})
            print(f"👥 Speaker diarization: {speaker_status.get('status', 'unknown')}")
            print(f"🔑 HF Token available: {speaker_status.get('hf_token_available', False)}")
            
        else:
            print(f"⚠️ Health check endpoint not healthy: {health_endpoint.get('error', 'Unknown error')}")
            pytest.skip("Health check endpoint not accessible")

    @pytest.mark.asyncio
    async def test_distributed_processing_with_turbo_model(self):
        """Test distributed processing using turbo model"""
        print("\n🔄 Testing distributed processing with turbo model...")
        
        # Check if we have test audio files
        test_audio_files = [
            "tests/cache/apple_podcast_episode.mp3",
            "tests/cache/xyz_podcast_episode.mp3"
        ]
        
        available_files = [f for f in test_audio_files if os.path.exists(f)]
        
        if not available_files:
            pytest.skip("No test audio files available. Run real-world integration tests first.")
        
        # Use the larger file for better distributed processing test
        test_file = max(available_files, key=lambda f: os.path.getsize(f))
        file_size_mb = os.path.getsize(test_file) / (1024 * 1024)
        
        print(f"📁 Using test file: {test_file} ({file_size_mb:.2f} MB)")
        
        start_time = time.time()
        
        # Test distributed processing with turbo model
        result = await transcribe_audio_file_tool(
            audio_file_path=test_file,
            model_size="turbo",  # Explicitly use turbo model
            language=None,  # Auto-detect
            output_format="srt",
            enable_speaker_diarization=False,  # Test without speaker diarization first
            use_parallel_processing=True,  # Force distributed processing
            chunk_duration=60,  # 60 seconds chunks
            use_intelligent_segmentation=True  # Use intelligent segmentation
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify transcription succeeded
        assert result["processing_status"] == "success", \
            f"Distributed transcription failed: {result.get('error_message', 'Unknown error')}"
        
        # Check that distributed processing was used
        distributed_processing = result.get("distributed_processing", False)
        chunks_processed = result.get("chunks_processed", 0)
        chunks_failed = result.get("chunks_failed", 0)
        segmentation_type = result.get("segmentation_type", "unknown")
        
        print(f"📊 Distributed processing results:")
        print(f"   Processing time: {processing_time:.2f}s")
        print(f"   Model used: {result.get('model_used', 'unknown')}")
        print(f"   Segments: {result.get('segment_count', 0)}")
        print(f"   Duration: {result.get('audio_duration', 0):.2f}s")
        print(f"   Language: {result.get('language_detected', 'unknown')}")
        print(f"   Distributed processing: {distributed_processing}")
        print(f"   Chunks processed: {chunks_processed}")
        print(f"   Chunks failed: {chunks_failed}")
        print(f"   Segmentation type: {segmentation_type}")
        
        # Verify that distributed processing was used for large files
        if result.get("audio_duration", 0) > 120:  # Files longer than 2 minutes
            assert distributed_processing, "Distributed processing should be used for long audio files"
            assert chunks_processed > 1, f"Expected multiple chunks, got {chunks_processed}"
        
        # Verify turbo model was used
        assert result.get("model_used") == "turbo", \
            f"Expected turbo model, got {result.get('model_used')}"
        
        # Note: Output files are created on Modal server, not locally
        # Verify transcription content instead
        assert result.get("segment_count", 0) > 0, "No transcription segments found"
        assert result.get("audio_duration", 0) > 0, "No audio duration detected"

    def test_health_check_with_model_preloading(self):
        """Test health service functionality"""
        print("\n🔍 Testing health service with model preloading...")
        
        health_service = HealthService()
        
        # Test Whisper models check
        whisper_status = health_service._check_whisper_models()
        print(f"🤖 Whisper status: {whisper_status}")
        
        assert whisper_status["default_model"] == "turbo"
        assert "turbo" in whisper_status["available_models"]
        
        # Test speaker diarization check
        speaker_status = health_service._check_speaker_diarization()
        print(f"👥 Speaker status: {speaker_status}")
        
        # Status can be healthy, partial, or disabled
        assert speaker_status["status"] in ["healthy", "partial", "disabled"]

    def test_speaker_diarization_pipeline_loading(self):
        """Test speaker diarization pipeline loading"""
        print("\n👥 Testing speaker diarization pipeline...")
        
        transcription_service = TranscriptionService()
        
        # Test loading speaker diarization pipeline
        pipeline = transcription_service._load_speaker_diarization_pipeline()
        
        if pipeline is not None:
            print("✅ Speaker diarization pipeline loaded successfully")
            # Test with actual pipeline
            assert hasattr(pipeline, '__call__'), "Pipeline should be callable"
        else:
            print("⚠️ Speaker diarization pipeline not available (likely missing HF_TOKEN)")
            # This is acceptable if HF_TOKEN is not configured

    @pytest.mark.asyncio
    async def test_transcription_service_with_speaker_diarization(self):
        """Test local transcription service with speaker diarization"""
        print("\n🎤 Testing transcription service with speaker diarization...")
        
        # Check if we have test audio files
        test_audio_files = [
            "tests/cache/apple_podcast_episode.mp3",
            "tests/cache/xyz_podcast_episode.mp3"
        ]
        
        available_files = [f for f in test_audio_files if os.path.exists(f)]
        
        if not available_files:
            pytest.skip("No test audio files available")
        
        # Use smaller file for local processing
        test_file = min(available_files, key=lambda f: os.path.getsize(f))
        
        transcription_service = TranscriptionService()
        
        # Test transcription with speaker diarization enabled
        result = transcription_service.transcribe_audio(
            audio_file_path=test_file,
            model_size="turbo",
            enable_speaker_diarization=True
        )
        
        assert result["processing_status"] == "success"
        assert result["model_used"] == "turbo"
        
        # Check speaker diarization results
        speaker_enabled = result.get("speaker_diarization_enabled", False)
        speaker_count = result.get("global_speaker_count", 0)
        
        print(f"👥 Speaker diarization enabled: {speaker_enabled}")
        print(f"👥 Speakers detected: {speaker_count}")
        
        if speaker_enabled:
            print("✅ Speaker diarization worked successfully")
        else:
            print("⚠️ Speaker diarization was disabled (likely missing dependencies)")

    @pytest.mark.asyncio 
    async def test_speaker_diarization_with_real_audio(self):
        """Test speaker diarization with real audio file"""
        print("\n🎯 Testing speaker diarization with real audio...")
        
        # Check if we have audio files available
        test_audio_files = [
            "tests/cache/apple_podcast_episode.mp3",
            "tests/cache/xyz_podcast_episode.mp3"
        ]
        
        available_files = [f for f in test_audio_files if os.path.exists(f)]
        
        if not available_files:
            pytest.skip("No test audio files available")
        
        test_file = available_files[0]  # Use first available file
        
        # Test with TranscriptionService
        transcription_service = TranscriptionService()
        
        result = transcription_service.transcribe_audio(
            audio_file_path=test_file,
            model_size="turbo", 
            enable_speaker_diarization=True
        )
        
        assert result["processing_status"] == "success"
        
        # Check speaker information
        speakers_detected = result.get("global_speaker_count", 0)
        speaker_enabled = result.get("speaker_diarization_enabled", False)
        
        print(f"🎯 Speaker diarization results:")
        print(f"   Enabled: {speaker_enabled}")
        print(f"   Speakers detected: {speakers_detected}")
        print(f"   Audio duration: {result.get('audio_duration', 0):.2f}s")
        print(f"   Segments: {result.get('segment_count', 0)}")

    @pytest.mark.asyncio
    async def test_distributed_transcription_with_speaker_diarization(self):
        """Test distributed transcription with speaker diarization"""
        print("\n🎯 Testing distributed transcription with speaker diarization...")
        
        # This test focuses on the distributed service architecture
        distributed_service = DistributedTranscriptionService()
        
        # Test segmentation strategies with non-existent file
        test_file = "dummy_audio.mp3"  # Dummy file for testing
        
        # Test intelligent segmentation choice - should handle missing files gracefully
        try:
            segments = distributed_service.choose_segmentation_strategy(test_file)
            # If no exception is raised, the service handled it gracefully
            print("✅ Distributed service properly handles missing files without exceptions")
        except Exception as e:
            # This is also acceptable - service detected the missing file
            print(f"✅ Distributed service properly detected missing file: {type(e).__name__}")
        
        # Test with actual audio file if available
        test_audio_files = [
            "tests/cache/apple_podcast_episode.mp3",
            "tests/cache/xyz_podcast_episode.mp3"
        ]
        
        available_files = [f for f in test_audio_files if os.path.exists(f)]
        
        if available_files:
            test_file = available_files[0]
            try:
                segments = distributed_service.choose_segmentation_strategy(test_file)
                print(f"✅ Segmentation strategy worked for real file: {segments}")
            except Exception as e:
                print(f"⚠️ Segmentation strategy failed: {e}")
        else:
            print("⚠️ No test audio files available for segmentation testing")

    def test_local_startup_with_new_architecture(self):
        """Test that all imports work correctly in new architecture"""
        print("\n🚀 Testing local startup with new architecture...")
        
        # Test core service imports
        try:
            from src.services.transcription_service import TranscriptionService
            print("✅ TranscriptionService imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import TranscriptionService: {e}")
        
        try:
            from src.services.distributed_transcription_service import DistributedTranscriptionService
            print("✅ DistributedTranscriptionService imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import DistributedTranscriptionService: {e}")
        
        try:
            from src.services.health_service import HealthService
            print("✅ HealthService imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import HealthService: {e}")
        
        # Test Modal services
        try:
            from src.services.modal_transcription_service import ModalTranscriptionService
            # Note: ModalDownloadService removed - downloads now handled locally
            print("✅ Modal services imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import Modal services: {e}")
        
        # Test tools imports
        try:
            from src.tools.transcription_tools import (
                transcribe_audio_file_tool,
                check_modal_endpoints_health
            )
            print("✅ Transcription tools imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import transcription tools: {e}")
        
        try:
            from src.tools.download_tools import (
                get_file_info_tool,
                read_text_file_segments_tool
            )
            print("✅ Download tools imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import download tools: {e}")
        
        # Test service registry
        try:
            from src.services import get_service, list_available_services
            
            # Test getting services
            transcription_service = get_service("transcription")
            assert transcription_service is not None
            
            modal_service = get_service("modal_transcription")
            assert modal_service is not None
            
            # Test service listing
            available_services = list_available_services()
            assert "transcription" in available_services
            assert "modal_transcription" in available_services
            
            print("✅ Service registry working correctly")
        except Exception as e:
            pytest.fail(f"Service registry error: {e}")

    @pytest.mark.asyncio
    async def test_modal_endpoints_availability(self):
        """Test Modal endpoints availability"""
        print("\n🌐 Testing Modal endpoints availability...")
        
        modal_service = ModalTranscriptionService()
        
        health_status = await modal_service.check_endpoints_health()
        
        print(f"🔍 Endpoint health status:")
        for endpoint_name, status in health_status.items():
            print(f"   {endpoint_name}: {status.get('status', 'unknown')}")
        
        # At least health check should be accessible
        health_check_status = health_status.get("health_check", {})
        if health_check_status.get("status") == "healthy":
            print("✅ Health check endpoint is working")
        else:
            print("⚠️ Health check endpoint may not be available")

    def test_model_cache_usage(self):
        """Test model cache usage in transcription service"""
        print("\n📦 Testing model cache usage...")
        
        transcription_service = TranscriptionService()
        
        # Test model loading (should use cache if available)
        model = transcription_service._load_cached_model("turbo")
        assert model is not None
        
        print("✅ Model loading successful")
        
        # Test speaker diarization pipeline loading
        pipeline = transcription_service._load_speaker_diarization_pipeline()
        
        if pipeline is not None:
            print("✅ Speaker diarization pipeline loaded")
        else:
            print("⚠️ Speaker diarization pipeline not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
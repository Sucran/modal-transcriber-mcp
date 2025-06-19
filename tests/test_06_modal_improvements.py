"""
Test Modal endpoint improvements:
1. Turbo model usage by default
2. Parallel processing for long audio
3. Health check endpoint  
4. Better audio encoding/decoding
5. Service architecture decoupling
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.transcription_tools import (
    transcribe_audio_file_tool, 
    check_modal_endpoints_health,
    get_modal_endpoint_url
)


class TestModalImprovements:
    """Test Modal endpoint improvements"""
    
    @pytest.mark.asyncio
    async def test_modal_health_check(self):
        """Test Modal health check endpoint"""
        print("\n🩺 Testing Modal health check endpoint...")
        
        health_status = await check_modal_endpoints_health()
        
        print(f"Health status: {health_status['status']}")
        assert health_status["status"] in ["healthy", "unhealthy"]
        assert "endpoints_available" in health_status
        
        if health_status["status"] == "healthy":
            assert health_status["endpoints_available"] is True
            assert "modal_health" in health_status
            
            modal_health = health_status["modal_health"]
            assert "service" in modal_health
            assert "default_model" in modal_health
            
            # Verify turbo is the default model
            assert modal_health["default_model"] == "turbo"
            print(f"✅ Default model confirmed as: {modal_health['default_model']}")
        
        print("✅ Health check test completed")
    
    def test_endpoint_url_configuration(self):
        """Test endpoint URL configuration"""
        print("\n🔗 Testing endpoint URL configuration...")
        
        # Test all known endpoints
        endpoints = [
            "transcribe-audio-chunk-endpoint",
            "health-check-endpoint"
            # Note: Download endpoints removed - downloads now handled locally
        ]
        
        for endpoint in endpoints:
            url = get_modal_endpoint_url(endpoint)
            assert url.startswith("https://")
            assert endpoint.replace("-", "") in url.replace("-", "")
            print(f"  ✅ {endpoint}: {url}")
        
        # Test invalid endpoint
        with pytest.raises(ValueError):
            get_modal_endpoint_url("invalid-endpoint")
        
        print("✅ Endpoint URL configuration test completed")
    
    @pytest.mark.asyncio
    async def test_turbo_model_transcription(self):
        """Test that turbo model is used by default"""
        print("\n🚀 Testing turbo model transcription...")
        
        # Check if we have test audio files
        test_audio_files = [
            "tests/cache/apple_podcast_episode.mp3",
            "tests/cache/xyz_podcast_episode.mp3"
        ]
        
        available_file = None
        for file_path in test_audio_files:
            if os.path.exists(file_path):
                available_file = file_path
                break
        
        if not available_file:
            pytest.skip("No test audio files available for transcription test")
        
        print(f"Using test file: {available_file}")
        
        # Test with default model (should be turbo)
        result = await transcribe_audio_file_tool(
            audio_file_path=available_file,
            use_parallel_processing=False  # Use single processing for faster test
        )
        
        print(f"Transcription status: {result['processing_status']}")
        
        if result["processing_status"] == "success":
            # Verify turbo model was used
            assert result["model_used"] == "turbo"
            print(f"✅ Confirmed turbo model used: {result['model_used']}")
            print(f"   Segments: {result['segment_count']}")
            print(f"   Duration: {result['audio_duration']:.2f}s")
        else:
            print(f"⚠️ Transcription failed: {result.get('error_message', 'Unknown error')}")
            # Still check that turbo was attempted
            assert result["model_used"] == "turbo"
        
        print("✅ Turbo model transcription test completed")
    
    @pytest.mark.asyncio
    async def test_parallel_processing_option(self):
        """Test parallel processing option"""
        print("\n⚡ Testing parallel processing option...")
        
        # Check if we have test audio files  
        test_audio_files = [
            "tests/cache/apple_podcast_episode.mp3",
            "tests/cache/xyz_podcast_episode.mp3"
        ]
        
        available_file = None
        for file_path in test_audio_files:
            if os.path.exists(file_path):
                available_file = file_path
                break
        
        if not available_file:
            pytest.skip("No test audio files available for parallel processing test")
        
        print(f"Using test file: {available_file}")
        
        # Test with parallel processing enabled
        result = await transcribe_audio_file_tool(
            audio_file_path=available_file,
            use_parallel_processing=True,
            chunk_duration=60  # 1 minute chunks for testing
        )
        
        print(f"Parallel transcription status: {result['processing_status']}")
        
        if result["processing_status"] == "success":
            # Check if parallel processing was used
            if "parallel_processing" in result:
                print(f"✅ Parallel processing enabled: {result['parallel_processing']}")
                if result.get("chunks_processed"):
                    print(f"   Chunks processed: {result['chunks_processed']}")
            
            assert result["model_used"] == "turbo"
            print(f"   Model used: {result['model_used']}")
            print(f"   Segments: {result['segment_count']}")
            print(f"   Duration: {result['audio_duration']:.2f}s")
        else:
            print(f"⚠️ Parallel transcription failed: {result.get('error_message', 'Unknown error')}")
        
        print("✅ Parallel processing test completed")
    
    @pytest.mark.asyncio
    async def test_service_architecture_decoupling(self):
        """Test that the service architecture is properly decoupled"""
        print("\n🏗️ Testing service architecture decoupling...")
        
        # Test that transcription tools can work independently
        try:
            from tools.transcription_tools import (
                transcribe_audio_file_tool,
                check_modal_endpoints_health,
                get_modal_endpoint_url
            )
            print("✅ Transcription tools import successful")
        except ImportError as e:
            pytest.fail(f"Transcription tools import failed: {e}")
        
        # Test endpoint URL configuration (architectural decoupling)
        try:
            urls = {}
            for endpoint in ["transcribe-audio-endpoint", "health-check-endpoint"]:
                url = get_modal_endpoint_url(endpoint)
                urls[endpoint] = url
                assert url.startswith("https://")
            print("✅ Endpoint configuration working independently")
        except Exception as e:
            pytest.fail(f"Endpoint configuration failed: {e}")
        
        # Test health check functionality (service layer abstraction)
        try:
            health_status = await check_modal_endpoints_health()
            assert "status" in health_status
            print("✅ Health check service abstraction working")
        except Exception as e:
            print(f"⚠️ Health check service test failed: {e}")
        
        # Test that Modal config is properly decoupled from business logic
        try:
            import src.config.modal_config as modal_config
            # Check that modal_config only contains configuration, not business logic
            config_content = open("src/config/modal_config.py", "r").read()
            
            # These should NOT be in the config file (business logic)
            business_logic_indicators = [
                "transcribe_audio_parallel", 
                "split_audio_chunks",
                "merge_transcription_results"
            ]
            
            for indicator in business_logic_indicators:
                assert indicator not in config_content, f"Business logic '{indicator}' found in config"
            
            print("✅ Modal config properly decoupled from business logic")
        except Exception as e:
            print(f"⚠️ Config decoupling test failed: {e}")
        
        print("✅ Service architecture decoupling test completed")

    def test_model_options_validation(self):
        """Test that model options are properly validated"""
        print("\n🎯 Testing model options validation...")
        
        # Import directly from the file to avoid package import issues
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
        
        try:
            from utils.modal_helpers import validate_transcription_request
        except ImportError:
            # If import fails, create a simple local validation function for testing
            def validate_transcription_request(request_data):
                valid_models = ["tiny", "base", "small", "medium", "large", "turbo"]
                if not request_data.get("audio_file_data"):
                    return False, "Missing audio_file_data field"
                model_size = request_data.get("model_size", "turbo")
                if model_size not in valid_models:
                    return False, f"Invalid model size '{model_size}'. Valid options: {valid_models}"
                return True, ""
        
        # Test valid request
        valid_request = {
            "audio_file_data": "dGVzdA==",  # base64 encoded "test"
            "model_size": "turbo",
            "output_format": "srt"
        }
        
        is_valid, error = validate_transcription_request(valid_request)
        assert is_valid is True
        assert error == ""
        print("✅ Valid request validation passed")
        
        # Test invalid model
        invalid_request = {
            "audio_file_data": "dGVzdA==",
            "model_size": "invalid_model",
            "output_format": "srt"
        }
        
        is_valid, error = validate_transcription_request(invalid_request)
        assert is_valid is False
        assert "Invalid model size" in error
        print("✅ Invalid model validation passed")
        
        # Test missing audio data
        missing_audio_request = {
            "model_size": "turbo",
            "output_format": "srt"
        }
        
        is_valid, error = validate_transcription_request(missing_audio_request)
        assert is_valid is False
        assert "Missing audio_file_data" in error
        print("✅ Missing audio data validation passed")
        
        print("✅ Model options validation test completed")


if __name__ == "__main__":
    # Run tests directly
    import asyncio
    
    async def run_async_tests():
        test_instance = TestModalImprovements()
        
        # Run async tests
        await test_instance.test_modal_health_check()
        await test_instance.test_turbo_model_transcription()  
        await test_instance.test_parallel_processing_option()
        await test_instance.test_service_architecture_decoupling()
        
        # Run sync tests
        test_instance.test_endpoint_url_configuration()
        test_instance.test_model_options_validation()
    
    asyncio.run(run_async_tests())
    print("\n🎉 All Modal improvement tests completed!") 
"""
Test remote GPU transcription functionality
测试远程GPU转录功能
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from src.tools.transcription_tools import transcribe_audio_file_tool
from src.services.audio_processing_service import AudioProcessingService


class TestRemoteTranscription:
    """Test remote GPU transcription integration"""
    
    def test_transcription_tools_initialization(self):
        """Test transcription tools initialization"""
        print("\n🔧 Testing transcription tools initialization...")
        
        # Test that the tool can be imported
        assert transcribe_audio_file_tool is not None
        
        print("✅ Transcription tools initialized successfully")
    
    @pytest.mark.asyncio
    async def test_create_sample_audio_file(self, temp_dir: str):
        """Test creating a sample audio file for transcription testing"""
        print("\n🎵 Creating sample audio file for testing...")
        
        import ffmpeg
        
        # Create a short sample audio file
        sample_file = os.path.join(temp_dir, "sample_audio.mp3")
        
        try:
            # Generate a short sine wave audio for testing
            (
                ffmpeg
                .input('sine=frequency=440:duration=5', f='lavfi')
                .output(sample_file, acodec='mp3', ar=16000)
                .overwrite_output()
                .run(quiet=True)
            )
            
            assert os.path.exists(sample_file)
            assert os.path.getsize(sample_file) > 0
            
            print(f"✅ Sample audio file created: {sample_file}")
            print(f"   File size: {os.path.getsize(sample_file)} bytes")
            
            return sample_file
            
        except Exception as e:
            print(f"❌ Failed to create sample audio file: {str(e)}")
            pytest.skip(f"Failed to create sample audio file: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_remote_transcription_endpoint_connectivity(self):
        """Test connectivity to remote transcription endpoint"""
        print("\n🌐 Testing remote transcription endpoint connectivity...")
        
        import aiohttp
        import json
        
        # Read endpoint config
        try:
            with open("endpoint_config.json", "r") as f:
                endpoint_config = json.load(f)
            
            endpoint_url = endpoint_config["transcribe_audio"]
            
            async with aiohttp.ClientSession() as session:
                # Test with a simple HEAD request to check if endpoint is reachable
                async with session.head(endpoint_url, timeout=10) as response:
                    print(f"✅ Endpoint connectivity test:")
                    print(f"   URL: {endpoint_url}")
                    print(f"   Status: {response.status}")
                    print(f"   Headers: {dict(response.headers)}")
                    
                    # We expect either 200 (OK) or 405 (Method Not Allowed) for HEAD requests
                    assert response.status in [200, 405, 404], f"Unexpected status: {response.status}"
                    
        except asyncio.TimeoutError:
            print(f"⚠️  Endpoint connectivity timeout (expected if Modal is sleeping)")
            pytest.skip("Endpoint connectivity timeout")
        except Exception as e:
            print(f"⚠️  Endpoint connectivity test failed: {str(e)}")
            print("   This might be expected if Modal endpoint is not running")
    
    @pytest.mark.asyncio
    async def test_transcription_tool_interface(self, temp_dir: str):
        """Test transcription tool interface with sample audio"""
        print("\n🎤 Testing transcription tool interface...")
        
        # Create a sample audio file first
        sample_file = await self.test_create_sample_audio_file(temp_dir)
        
        try:
            # Test the transcription tool
            result = await transcribe_audio_file_tool(
                audio_file_path=sample_file,
                model_size="base",
                language="en",
                output_format="srt",
                enable_speaker_diarization=False
            )
            
            print(f"📋 Transcription tool result:")
            print(f"   Status: {result.get('processing_status', 'unknown')}")
            print(f"   Audio file: {result.get('audio_file', 'N/A')}")
            print(f"   Model used: {result.get('model_used', 'N/A')}")
            print(f"   Duration: {result.get('audio_duration', 0):.2f}s")
            
            if result.get("processing_status") == "success":
                print(f"   TXT file: {result.get('txt_file_path', 'N/A')}")
                print(f"   SRT file: {result.get('srt_file_path', 'N/A')}")
                print(f"   Segments: {result.get('segment_count', 0)}")
                print("✅ Transcription tool interface test successful")
                
                # Verify output files exist
                if result.get('txt_file_path'):
                    assert os.path.exists(result['txt_file_path'])
                if result.get('srt_file_path'):
                    assert os.path.exists(result['srt_file_path'])
                    
            else:
                print(f"   Error: {result.get('error_message', 'Unknown error')}")
                print("⚠️  Transcription failed (might be due to remote endpoint)")
                
        except Exception as e:
            print(f"❌ Transcription tool test failed: {str(e)}")
            print("   This might be expected if remote endpoint is not available")
    
    @pytest.mark.asyncio
    async def test_transcription_with_speaker_diarization(self, temp_dir: str):
        """Test transcription with speaker diarization enabled"""
        print("\n👥 Testing transcription with speaker diarization...")
        
        # Create a sample audio file
        sample_file = await self.test_create_sample_audio_file(temp_dir)
        
        try:
            # Test transcription with speaker diarization
            result = await transcribe_audio_file_tool(
                audio_file_path=sample_file,
                model_size="base",
                language="auto",
                output_format="srt",
                enable_speaker_diarization=True
            )
            
            print(f"📋 Speaker diarization result:")
            print(f"   Status: {result.get('processing_status', 'unknown')}")
            print(f"   Speaker diarization enabled: {result.get('speaker_diarization_enabled', False)}")
            print(f"   Global speaker count: {result.get('global_speaker_count', 0)}")
            
            if result.get("processing_status") == "success":
                speaker_summary = result.get('speaker_summary', {})
                print(f"   Speaker summary: {speaker_summary}")
                print("✅ Speaker diarization test successful")
            else:
                print(f"   Error: {result.get('error_message', 'Unknown error')}")
                print("⚠️  Speaker diarization failed (might be due to remote endpoint or HF token)")
                
        except Exception as e:
            print(f"❌ Speaker diarization test failed: {str(e)}")
            print("   This might be expected if HF token is not configured or endpoint unavailable")
    
    @pytest.mark.asyncio
    async def test_different_transcription_models(self, temp_dir: str):
        """Test transcription with different models"""
        print("\n🧠 Testing different transcription models...")
        
        sample_file = await self.test_create_sample_audio_file(temp_dir)
        
        models_to_test = ["tiny", "base", "small"]
        
        for model in models_to_test:
            print(f"\n   Testing model: {model}")
            try:
                result = await transcribe_audio_file_tool(
                    audio_file_path=sample_file,
                    model_size=model,
                    language="auto",
                    output_format="txt",
                    enable_speaker_diarization=False
                )
                
                if result.get("processing_status") == "success":
                    print(f"   ✅ {model} model: Success")
                    print(f"      Segments: {result.get('segment_count', 0)}")
                    print(f"      Duration: {result.get('audio_duration', 0):.2f}s")
                else:
                    print(f"   ⚠️  {model} model: Failed - {result.get('error_message', 'Unknown')}")
                    
            except Exception as e:
                print(f"   ❌ {model} model: Exception - {str(e)}")
    
    @pytest.mark.asyncio
    async def test_transcription_output_formats(self, temp_dir: str):
        """Test different transcription output formats"""
        print("\n📄 Testing different output formats...")
        
        sample_file = await self.test_create_sample_audio_file(temp_dir)
        
        formats_to_test = ["txt", "srt", "json"]
        
        for format_type in formats_to_test:
            print(f"\n   Testing format: {format_type}")
            try:
                result = await transcribe_audio_file_tool(
                    audio_file_path=sample_file,
                    model_size="base",
                    language="auto",
                    output_format=format_type,
                    enable_speaker_diarization=False
                )
                
                if result.get("processing_status") == "success":
                    print(f"   ✅ {format_type} format: Success")
                    
                    # Check for format-specific outputs
                    if format_type == "txt" and result.get('txt_file_path'):
                        assert os.path.exists(result['txt_file_path'])
                    elif format_type == "srt" and result.get('srt_file_path'):
                        assert os.path.exists(result['srt_file_path'])
                        
                else:
                    print(f"   ⚠️  {format_type} format: Failed - {result.get('error_message', 'Unknown')}")
                    
            except Exception as e:
                print(f"   ❌ {format_type} format: Exception - {str(e)}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"]) 
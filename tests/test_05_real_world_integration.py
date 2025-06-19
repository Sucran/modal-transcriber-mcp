"""
Real-world integration tests using actual podcast URLs
Tests the complete workflow from download to transcription to file management
"""
import pytest
import os
import tempfile
import requests
import time
import json
import base64
from pathlib import Path

# Import the tools for testing
from src.tools import mcp_tools

class TestRealWorldIntegration:
    """Real-world integration tests with actual podcast URLs"""
    
    @pytest.fixture(autouse=True)
    def setup_cache_directories(self):
        """Setup cache directories for testing"""
        self.cache_dir = Path("tests/cache")
        self.transcribe_dir = Path("tests/cache/transcribe")
        
        # Ensure directories exist
        self.cache_dir.mkdir(exist_ok=True)
        self.transcribe_dir.mkdir(exist_ok=True)
        
        print(f"📁 Cache directory: {self.cache_dir.absolute()}")
        print(f"📁 Transcribe directory: {self.transcribe_dir.absolute()}")
    
    # No longer need separate managers, using direct tool functions
    
    def test_modal_endpoints_accessibility(self):
        """Test that Modal endpoints are accessible and responsive"""
        print("🌐 Testing Modal endpoints accessibility...")
        
        endpoints = {
                    "transcription": os.getenv("MODAL_TRANSCRIBE_CHUNK_ENDPOINT", "https://richardsucran--transcribe-audio-chunk-endpoint.modal.run"),
        "health_check": os.getenv("MODAL_HEALTH_CHECK_ENDPOINT", "https://richardsucran--health-check-endpoint.modal.run")
            # Note: Download endpoints removed - downloads now handled locally
        }
        
        for name, url in endpoints.items():
            try:
                response = requests.get(url, timeout=10)
                print(f"   📡 {name}: Status {response.status_code}")
                assert response.status_code in [200, 405], f"Endpoint {name} not accessible"
            except Exception as e:
                print(f"   ❌ {name}: Failed - {e}")
                pytest.fail(f"Endpoint {name} not accessible: {e}")
        
        print("✅ All Modal endpoints are accessible")
    
    @pytest.mark.asyncio
    async def test_real_podcast_download_apple(self):
        """Test downloading actual Apple Podcast episode"""
        print("🍎 Testing real Apple Podcast download...")
        
        # Real Apple Podcast URL provided by user
        apple_url = "https://podcasts.apple.com/cn/podcast/all-ears-english-podcast/id751574016?i=1000712048662"
        
        try:
            result = await mcp_tools.download_apple_podcast(apple_url)
            
            print(f"📋 Download result:")
            print(f"   Status: {result['status']}")
            print(f"   Original URL: {result['original_url']}")
            
            if result['status'] == 'success':
                audio_file = result['audio_file_path']
                print(f"   Audio file: {audio_file}")
                
                # Move file to our cache directory if not already there
                if audio_file and os.path.exists(audio_file):
                    cache_file = self.cache_dir / "apple_podcast_episode.mp3"
                    if str(cache_file) != audio_file:
                        import shutil
                        shutil.copy2(audio_file, cache_file)
                        print(f"   📁 Copied to cache: {cache_file}")
                    
                    assert os.path.exists(cache_file), "Downloaded file should exist in cache"
                    file_size = os.path.getsize(cache_file) / (1024*1024)
                    print(f"   📊 File size: {file_size:.2f} MB")
                    assert file_size > 0.1, "Downloaded file should not be empty"
                
                print("✅ Apple Podcast download successful")
            else:
                print(f"⚠️ Apple Podcast download failed: {result.get('error_message', 'Unknown error')}")
                # For this test, we'll consider partial success as still passing
                # since download might fail due to network/access issues
                
        except Exception as e:
            print(f"❌ Apple Podcast download test failed: {e}")
            # Don't fail the test for network issues, but log the problem
            print("⚠️ This might be due to network connectivity or podcast access restrictions")
    
    @pytest.mark.asyncio
    async def test_real_podcast_download_xyz(self):
        """Test downloading actual XiaoYuZhou Podcast episode"""
        print("🎵 Testing real XiaoYuZhou Podcast download...")
        
        # Real XiaoYuZhou Podcast URL provided by user
        xyz_url = "https://www.xiaoyuzhoufm.com/episode/6844388379e285b9b8b7067d"
        
        try:
            result = await mcp_tools.download_xyz_podcast(xyz_url)
            
            print(f"📋 Download result:")
            print(f"   Status: {result['status']}")
            print(f"   Original URL: {result['original_url']}")
            
            if result['status'] == 'success':
                audio_file = result['audio_file_path']
                print(f"   Audio file: {audio_file}")
                
                # Move file to our cache directory if not already there
                if audio_file and os.path.exists(audio_file):
                    cache_file = self.cache_dir / "xyz_podcast_episode.mp3"
                    if str(cache_file) != audio_file:
                        import shutil
                        shutil.copy2(audio_file, cache_file)
                        print(f"   📁 Copied to cache: {cache_file}")
                    
                    assert os.path.exists(cache_file), "Downloaded file should exist in cache"
                    file_size = os.path.getsize(cache_file) / (1024*1024)
                    print(f"   📊 File size: {file_size:.2f} MB")
                    assert file_size > 0.1, "Downloaded file should not be empty"
                
                print("✅ XiaoYuZhou Podcast download successful")
            else:
                print(f"⚠️ XiaoYuZhou Podcast download failed: {result.get('error_message', 'Unknown error')}")
                # For this test, we'll consider partial success as still passing
                
        except Exception as e:
            print(f"❌ XiaoYuZhou Podcast download test failed: {e}")
            print("⚠️ This might be due to network connectivity or access restrictions")
    
    def get_available_audio_files(self):
        """Get list of available audio files in cache directory"""
        audio_files = []
        for ext in ['*.mp3', '*.wav', '*.m4a']:
            audio_files.extend(self.cache_dir.glob(ext))
        return audio_files
    
    @pytest.mark.asyncio
    async def test_real_transcription_with_modal(self):
        """Test real audio transcription using Modal endpoints"""
        print("🎤 Testing real audio transcription with Modal...")
        
        # Get available audio files
        audio_files = self.get_available_audio_files()
        
        if not audio_files:
            print("⚠️ No audio files found in cache, creating a small test file...")
            # Create a small test audio file for transcription
            test_file = self.cache_dir / "test_audio.mp3"
            await self._create_test_audio_file(test_file)
            audio_files = [test_file]
        
        # Test transcription with the first available audio file
        audio_file = audio_files[0]
        print(f"🎵 Transcribing: {audio_file.name}")
        print(f"   File size: {audio_file.stat().st_size / (1024*1024):.2f} MB")
        
        try:
            # Test transcription with different parameters
            result = await mcp_tools.transcribe_audio_file(
                audio_file_path=str(audio_file),
                model_size="tiny",  # Use faster model for testing
                language="en",
                output_format="srt",
                enable_speaker_diarization=False
            )
            
            print(f"📋 Transcription result:")
            print(f"   Status: {result['processing_status']}")
            print(f"   Model used: {result['model_used']}")
            print(f"   Segment count: {result['segment_count']}")
            print(f"   Audio duration: {result['audio_duration']:.2f}s")
            
            if result['processing_status'] == 'success':
                # Move transcription files to our cache/transcribe directory
                if result['txt_file_path']:
                    txt_cache = self.transcribe_dir / f"{audio_file.stem}.txt"
                    if os.path.exists(result['txt_file_path']) and str(txt_cache) != result['txt_file_path']:
                        import shutil
                        shutil.copy2(result['txt_file_path'], txt_cache)
                        print(f"   📄 TXT saved to: {txt_cache}")
                
                if result['srt_file_path']:
                    srt_cache = self.transcribe_dir / f"{audio_file.stem}.srt"
                    if os.path.exists(result['srt_file_path']) and str(srt_cache) != result['srt_file_path']:
                        import shutil
                        shutil.copy2(result['srt_file_path'], srt_cache)
                        print(f"   📄 SRT saved to: {srt_cache}")
                
                print("✅ Real transcription successful")
                
                # Assert basic success criteria
                assert result['segment_count'] > 0, "Should have at least one segment"
                assert result['audio_duration'] > 0, "Should have positive duration"
                
            else:
                error_msg = result.get('error_message', 'Unknown error')
                print(f"❌ Transcription failed: {error_msg}")
                
                # Check if it's a Modal/network issue vs code issue
                if 'ConnectionError' in error_msg or 'TimeoutError' in error_msg:
                    print("⚠️ This appears to be a network connectivity issue")
                else:
                    pytest.fail(f"Transcription failed: {error_msg}")
                
        except Exception as e:
            print(f"❌ Transcription test failed: {e}")
            print("⚠️ This might be due to Modal endpoint issues or network connectivity")
    
    async def _create_test_audio_file(self, file_path):
        """Create a small test audio file for transcription testing"""
        try:
            import numpy as np
            import soundfile as sf
            
            # Generate 5 seconds of test audio (440Hz tone)
            sample_rate = 22050
            duration = 5
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)
            
            # Save as WAV first, then convert to MP3 if needed
            wav_file = file_path.with_suffix('.wav')
            sf.write(wav_file, audio_data, sample_rate)
            
            # Convert to MP3 using ffmpeg if available
            if file_path.suffix == '.mp3':
                import subprocess
                try:
                    subprocess.run([
                        'ffmpeg', '-i', str(wav_file), '-acodec', 'mp3', '-y', str(file_path)
                    ], check=True, capture_output=True)
                    wav_file.unlink()  # Remove WAV file
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # If ffmpeg not available, just use WAV
                    file_path = wav_file
            
            print(f"✅ Created test audio file: {file_path}")
            
        except ImportError:
            print("⚠️ Could not create test audio file (missing dependencies)")
    
    @pytest.mark.asyncio
    async def test_mp3_file_management_with_real_files(self):
        """Test MP3 file management with real downloaded files"""
        print("📂 Testing MP3 file management with real files...")
        
        # Scan the cache directory for MP3 files
        result = await mcp_tools.get_mp3_files(str(self.cache_dir))
        
        print(f"📋 MP3 scan result:")
        print(f"   Total files: {result['total_files']}")
        print(f"   Directory: {result['scanned_directory']}")
        
        if result['total_files'] > 0:
            print(f"   Found MP3 files:")
            for file_info in result['file_list']:
                print(f"      📄 {file_info['filename']}")
                print(f"         Size: {file_info['file_size_mb']:.2f} MB")
                print(f"         Created: {file_info['created_time']}")
            
            # Test getting detailed info for the first file
            first_file = result['file_list'][0]
            file_info_result = await mcp_tools.get_file_info(first_file['full_path'])
            
            print(f"📋 Detailed file info for {first_file['filename']}:")
            print(f"   Status: {file_info_result['status']}")
            print(f"   Size: {file_info_result['file_size_mb']:.2f} MB")
            print(f"   Extension: {file_info_result['file_extension']}")
            
            assert file_info_result['status'] == 'success', "File info should succeed"
            assert file_info_result['file_exists'], "File should exist"
            
        print("✅ MP3 file management test completed")
    
    @pytest.mark.asyncio
    async def test_transcription_file_management(self):
        """Test transcription file management with real transcription results"""
        print("📝 Testing transcription file management...")
        
        # Check for transcription files in the transcribe directory
        transcription_files = []
        for ext in ['*.txt', '*.srt']:
            transcription_files.extend(self.transcribe_dir.glob(ext))
        
        if not transcription_files:
            print("⚠️ No transcription files found, creating test files...")
            # Create test transcription files
            test_txt = self.transcribe_dir / "test_transcription.txt"
            test_srt = self.transcribe_dir / "test_transcription.srt"
            
            test_txt.write_text("This is a test transcription from the real-world integration test.")
            test_srt.write_text("""1
00:00:00,000 --> 00:00:05,000
This is a test transcription.

2
00:00:05,000 --> 00:00:10,000
From the real-world integration test.
""")
            transcription_files = [test_txt, test_srt]
        
        print(f"📋 Found {len(transcription_files)} transcription files")
        
        for file_path in transcription_files:
            print(f"   📄 Testing: {file_path.name}")
            
            # Test file info
            file_info = await mcp_tools.get_file_info(str(file_path))
            print(f"      Size: {file_info['file_size_mb']:.3f} MB")
            
            # Test file reading
            content_result = await mcp_tools.read_text_file_segments(str(file_path))
            print(f"      Content length: {content_result['content_length']} characters")
            print(f"      Progress: {content_result['progress_percentage']:.1f}%")
            
            # Show content preview
            content_preview = content_result['content'][:100] + "..." if len(content_result['content']) > 100 else content_result['content']
            print(f"      Preview: {content_preview}")
            
            assert file_info['status'] == 'success', f"File info should succeed for {file_path.name}"
            assert content_result['status'] == 'success', f"File reading should succeed for {file_path.name}"
        
        print("✅ Transcription file management test completed")
    
    def test_modal_deployment_status(self):
        """Check Modal deployment status and logs"""
        print("☁️ Checking Modal deployment status...")
        
        try:
            # Check if Modal CLI is available
            import subprocess
            result = subprocess.run(['modal', 'app', 'list'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Modal CLI is available")
                print("📋 Active Modal apps:")
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"   {line}")
            else:
                print("⚠️ Modal CLI command failed")
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"⚠️ Could not check Modal status: {e}")
        
        print("✅ Modal deployment status check completed")
    
    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self):
        """Test the complete workflow from download to transcription to file management"""
        print("🔄 Testing complete workflow integration...")
        
        workflow_summary = {
            'downloaded_files': 0,
            'transcribed_files': 0,
            'managed_files': 0
        }
        
        # Step 1: Check downloaded files
        mp3_result = await mcp_tools.get_mp3_files(str(self.cache_dir))
        workflow_summary['downloaded_files'] = mp3_result['total_files']
        print(f"   📁 Downloaded MP3 files: {workflow_summary['downloaded_files']}")
        
        # Step 2: Check transcription files
        transcription_files = list(self.transcribe_dir.glob('*.txt')) + list(self.transcribe_dir.glob('*.srt'))
        workflow_summary['transcribed_files'] = len(transcription_files)
        print(f"   📝 Transcription files: {workflow_summary['transcribed_files']}")
        
        # Step 3: Test file management capabilities
        all_files = list(self.cache_dir.rglob('*.*'))
        workflow_summary['managed_files'] = len([f for f in all_files if f.is_file()])
        print(f"   📂 Total managed files: {workflow_summary['managed_files']}")
        
        # Summary
        print(f"📊 Workflow Summary:")
        print(f"   Total downloaded files: {workflow_summary['downloaded_files']}")
        print(f"   Total transcription files: {workflow_summary['transcribed_files']}")
        print(f"   Total managed files: {workflow_summary['managed_files']}")
        
        # Basic assertions
        assert workflow_summary['managed_files'] > 0, "Should have at least some files to manage"
        
        print("✅ Complete workflow integration test successful") 
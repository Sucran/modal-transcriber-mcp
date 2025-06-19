"""
Modal Transcription Service - handles transcription via Modal endpoints
Enhanced to replace transcription_tools.py functions with proper service architecture
"""

import asyncio
import aiohttp
import base64
import os
from typing import Dict, Any
from pathlib import Path


class ModalTranscriptionService:
    """Service for audio transcription via Modal endpoints"""
    
    def __init__(self, endpoint_urls: Dict[str, str] = None, cache_dir: str = None, use_direct_modal_calls: bool = True):
        """
        Initialize Modal transcription service
        
        Args:
            endpoint_urls: Dictionary of endpoint URLs (used when use_direct_modal_calls=False)
            cache_dir: Cache directory path
            use_direct_modal_calls: Whether to use direct Modal function calls or HTTP endpoints
        """
        self.use_direct_modal_calls = use_direct_modal_calls
        
        # Import config functions
        from ..config.config import (
            get_modal_transcribe_audio_endpoint,
            get_modal_transcribe_chunk_endpoint,
            get_modal_health_check_endpoint
        )
        
        self.endpoint_urls = endpoint_urls or {
            "transcribe_audio": get_modal_transcribe_audio_endpoint(),
            "transcribe_chunk": get_modal_transcribe_chunk_endpoint(), 
            "health_check": get_modal_health_check_endpoint()
        }
        self.cache_dir = cache_dir or "/tmp"
        
        # Determine if we're running in Modal environment
        if self.use_direct_modal_calls:
            print("✅ Using direct function calls (no HTTP endpoints)")
    
    async def transcribe_audio_file(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: str = None,
        output_format: str = "srt",
        enable_speaker_diarization: bool = False,
        use_parallel_processing: bool = True,
        chunk_duration: int = 60,
        use_intelligent_segmentation: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Modal endpoints with intelligent processing
        
        Args:
            audio_file_path: Path to audio file
            model_size: Whisper model size
            language: Language code (None for auto-detect)
            output_format: Output format (srt, txt, json)
            enable_speaker_diarization: Whether to enable speaker diarization
            use_parallel_processing: Whether to use distributed processing
            chunk_duration: Duration of chunks for parallel processing
            use_intelligent_segmentation: Whether to use intelligent segmentation
            
        Returns:
            Transcription result dictionary
        """
        try:
            # Validate input file
            if not os.path.exists(audio_file_path):
                return {
                    "processing_status": "failed",
                    "error_message": f"Audio file not found: {audio_file_path}"
                }
            
            # Read and encode audio file
            with open(audio_file_path, "rb") as f:
                audio_data = f.read()
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare request data
            request_data = {
                "audio_file_data": audio_base64,
                "audio_file_name": os.path.basename(audio_file_path),
                "model_size": model_size,
                "language": language,
                "output_format": output_format,
                "enable_speaker_diarization": enable_speaker_diarization,
                "use_parallel_processing": use_parallel_processing,
                "chunk_duration": chunk_duration,
                "use_intelligent_segmentation": use_intelligent_segmentation
            }
            
            endpoint_url = self.endpoint_urls["transcribe_audio"]
            
            print(f"🎤 Starting transcription via Modal {'function call' if self.use_direct_modal_calls else 'endpoint'}...")
            print(f"   File: {audio_file_path}")
            print(f"   Size: {len(audio_data) / (1024*1024):.2f} MB")
            print(f"   Model: {model_size}")
            print(f"   Parallel processing: {use_parallel_processing}")
            print(f"   Intelligent segmentation: {use_intelligent_segmentation}")
            print(f"   Speaker diarization: {enable_speaker_diarization}")
            
            # Choose between direct function call or HTTP endpoint
            if self.use_direct_modal_calls:
                # Direct function call (when running inside Modal environment)
                try:
                    # Call the process_transcription_request method directly
                    result = await self.process_transcription_request(request_data)
                except Exception as e:
                    print(f"⚠️ Direct Modal call failed, falling back to HTTP: {e}")
                    self.use_direct_modal_calls = False
                    # Fall through to HTTP endpoint call
                else:
                    print(f"✅ Transcription completed successfully via direct function call")
                    self._log_transcription_results(result, enable_speaker_diarization)
                    return result
            
            if not self.use_direct_modal_calls:
                # HTTP endpoint call (fallback)
                endpoint_url = self.endpoint_urls["transcribe_audio"]
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        endpoint_url,
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=3600)  # 1 hour timeout
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ Transcription completed successfully via HTTP endpoint")
                            self._log_transcription_results(result, enable_speaker_diarization)
                            return result
                        else:
                            error_text = await response.text()
                            return {
                                "processing_status": "failed",
                                "error_message": f"HTTP {response.status}: {error_text}"
                            }
                        
        except Exception as e:
            return {
                "processing_status": "failed",
                "error_message": f"Transcription request failed: {e}"
            }
    
    async def transcribe_chunk(
        self,
        chunk_path: str,
        start_time: float,
        end_time: float,
        model_size: str = "turbo",
        language: str = None,
        enable_speaker_diarization: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe a single audio chunk using Modal chunk endpoint
        
        Args:
            chunk_path: Path to audio chunk file
            start_time: Start time of chunk in original audio
            end_time: End time of chunk in original audio
            model_size: Whisper model size
            language: Language code
            enable_speaker_diarization: Whether to enable speaker diarization
            
        Returns:
            Transcription result for the chunk
        """
        try:
            # Read and encode chunk file
            with open(chunk_path, "rb") as f:
                audio_data = f.read()
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare request data
            request_data = {
                "audio_file_data": audio_base64,
                "audio_file_name": os.path.basename(chunk_path),
                "model_size": model_size,
                "language": language,
                "output_format": "json",  # Use JSON for easier merging
                "enable_speaker_diarization": enable_speaker_diarization,
                "chunk_start_time": start_time,
                "chunk_end_time": end_time
            }
            
            # Choose between direct function call or HTTP endpoint
            if self.use_direct_modal_calls:
                # Direct function call
                try:
                    result = self.process_chunk_request(request_data)
                    result["chunk_start_time"] = start_time
                    result["chunk_end_time"] = end_time
                    result["chunk_file"] = chunk_path
                    return result
                except Exception as e:
                    print(f"⚠️ Direct chunk call failed, falling back to HTTP: {e}")
                    self.use_direct_modal_calls = False
                    # Fall through to HTTP endpoint call
            
            if not self.use_direct_modal_calls:
                # HTTP endpoint call (fallback)
                endpoint_url = self.endpoint_urls["transcribe_chunk"]
                # Configure timeout with more granular controls
                # Adjust timeout based on speaker diarization
                if enable_speaker_diarization:
                    timeout_config = aiohttp.ClientTimeout(
                        total=720,  # 12 minutes total for speaker diarization
                        connect=45,  # 45 seconds connection timeout
                        sock_read=300  # 5 minutes read timeout for speaker processing
                    )
                else:
                    timeout_config = aiohttp.ClientTimeout(
                        total=480,  # 8 minutes total for regular transcription
                        connect=30,  # 30 seconds connection timeout
                        sock_read=120  # 2 minutes read timeout for regular processing
                    )
                
                async with aiohttp.ClientSession(timeout=timeout_config) as session:
                    async with session.post(
                        endpoint_url,
                        json=request_data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            result["chunk_start_time"] = start_time
                            result["chunk_end_time"] = end_time
                            result["chunk_file"] = chunk_path
                            return result
                        else:
                            error_text = await response.text()
                            return {
                                "processing_status": "failed",
                                "error_message": f"HTTP {response.status}: {error_text}",
                                "chunk_start_time": start_time,
                                "chunk_end_time": end_time,
                                "chunk_file": chunk_path
                            }
                        
        except Exception as e:
            return {
                "processing_status": "failed",
                "error_message": str(e),
                "chunk_start_time": start_time,
                "chunk_end_time": end_time,
                "chunk_file": chunk_path
            }
    
    async def check_endpoints_health(self) -> Dict[str, Any]:
        """
        Check the health status of all Modal endpoints
        
        Returns:
            Health status dictionary for all endpoints
        """
        health_status = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint_name, endpoint_url in self.endpoint_urls.items():
                try:
                    if endpoint_name == "health_check":
                        # Health check endpoint supports GET
                        async with session.get(
                            endpoint_url,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            if response.status == 200:
                                response_data = await response.json()
                                health_status[endpoint_name] = {
                                    "status": "healthy",
                                    "response": response_data,
                                    "url": endpoint_url
                                }
                            else:
                                health_status[endpoint_name] = {
                                    "status": "unhealthy",
                                    "error": f"HTTP {response.status}",
                                    "url": endpoint_url
                                }
                    else:
                        # Other endpoints are POST-only, just check if they're accessible
                        async with session.get(
                            endpoint_url,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            # 405 Method Not Allowed is expected for POST-only endpoints
                            if response.status == 405:
                                health_status[endpoint_name] = {
                                    "status": "healthy",
                                    "response": "Endpoint accessible (POST-only)",
                                    "url": endpoint_url
                                }
                            else:
                                health_status[endpoint_name] = {
                                    "status": "unknown",
                                    "response": f"HTTP {response.status}",
                                    "url": endpoint_url
                                }
                                
                except Exception as e:
                    health_status[endpoint_name] = {
                        "status": "error",
                        "error": str(e),
                        "url": endpoint_url
                    }
        
        return health_status
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status including health checks
        
        Returns:
            System status dictionary
        """
        try:
            endpoint_url = self.endpoint_urls["health_check"]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint_url,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {
                            "status": "failed",
                            "error_message": f"HTTP {response.status}: {error_text}"
                        }
                        
        except Exception as e:
            return {
                "status": "failed", 
                "error_message": f"Health check failed: {e}"
            }
    
    def get_endpoint_url(self, endpoint_name: str) -> str:
        """
        Get URL for specific endpoint
        
        Args:
            endpoint_name: Name of the endpoint
            
        Returns:
            Endpoint URL
        """
        from ..config.config import build_modal_endpoint_url
        return self.endpoint_urls.get(endpoint_name, build_modal_endpoint_url(endpoint_name))
    
    # ==================== Modal Server-Side Methods ====================
    # These methods are used by Modal endpoints running on the server
    
    async def process_transcription_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process transcription request on Modal server
        This method runs on the Modal server, not the client
        """
        try:
            # Import services that are available on Modal server
            import sys
            import tempfile
            import base64
            from pathlib import Path
            
            # Import local services (available on Modal server)
            from src.services.distributed_transcription_service import DistributedTranscriptionService
            from src.services.transcription_service import TranscriptionService
            
            # Extract request parameters
            audio_file_data = request_data.get("audio_file_data")
            audio_file_name = request_data.get("audio_file_name", "audio.mp3")
            model_size = request_data.get("model_size", "turbo")
            language = request_data.get("language")
            output_format = request_data.get("output_format", "srt")
            enable_speaker_diarization = request_data.get("enable_speaker_diarization", False)
            use_parallel_processing = request_data.get("use_parallel_processing", True)
            chunk_duration = request_data.get("chunk_duration", 60)
            use_intelligent_segmentation = request_data.get("use_intelligent_segmentation", True)
            
            if not audio_file_data:
                return {
                    "processing_status": "failed",
                    "error_message": "No audio data provided"
                }
            
            # Decode audio data and save to temporary file
            audio_bytes = base64.b64decode(audio_file_data)
            temp_dir = Path(self.cache_dir)
            temp_dir.mkdir(exist_ok=True)
            
            temp_audio_path = temp_dir / audio_file_name
            with open(temp_audio_path, "wb") as f:
                f.write(audio_bytes)
            
            print(f"🎤 Processing audio on Modal server: {audio_file_name}")
            print(f"   Size: {len(audio_bytes) / (1024*1024):.2f} MB")
            print(f"   Model: {model_size}")
            print(f"   Parallel processing: {use_parallel_processing}")
            print(f"   Intelligent segmentation: {use_intelligent_segmentation}")
            
            # Choose processing strategy based on file size and settings
            file_size_mb = len(audio_bytes) / (1024 * 1024)
            
            if use_parallel_processing and file_size_mb > 10:  # Use distributed for files > 10MB
                print("🔄 Using distributed transcription service")
                service = DistributedTranscriptionService()
                
                result = await service.transcribe_audio_distributed(
                    audio_file_path=str(temp_audio_path),
                    model_size=model_size,
                    language=language,
                    output_format=output_format,
                    enable_speaker_diarization=enable_speaker_diarization,
                    chunk_duration=chunk_duration,
                    use_intelligent_segmentation=use_intelligent_segmentation
                )
            else:
                print("🎯 Using single transcription service")
                service = TranscriptionService()
                
                result = service.transcribe_audio(
                    audio_file_path=str(temp_audio_path),
                    model_size=model_size,
                    language=language,
                    output_format=output_format,
                    enable_speaker_diarization=enable_speaker_diarization
                )
            
            # Clean up temporary file
            try:
                temp_audio_path.unlink()
            except:
                pass
            
            print(f"✅ Transcription completed on Modal server")
            return result
            
        except Exception as e:
            print(f"❌ Error processing transcription request: {e}")
            return {
                "processing_status": "failed",
                "error_message": f"Server processing error: {str(e)}"
            }
    
    def process_chunk_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process chunk transcription request on Modal server
        This method runs on the Modal server, not the client
        """
        try:
            # Import services that are available on Modal server
            import base64
            import tempfile
            from pathlib import Path
            
            # Import local services (available on Modal server)
            from src.services.transcription_service import TranscriptionService
            
            # Extract request parameters
            audio_file_data = request_data.get("audio_file_data")
            audio_file_name = request_data.get("audio_file_name", "chunk.mp3")
            model_size = request_data.get("model_size", "turbo")
            language = request_data.get("language")
            enable_speaker_diarization = request_data.get("enable_speaker_diarization", False)
            chunk_start_time = request_data.get("chunk_start_time", 0)
            chunk_end_time = request_data.get("chunk_end_time", 0)
            
            if not audio_file_data:
                return {
                    "processing_status": "failed",
                    "error_message": "No audio data provided",
                    "chunk_start_time": chunk_start_time,
                    "chunk_end_time": chunk_end_time
                }
            
            # Decode audio data and save to temporary file
            audio_bytes = base64.b64decode(audio_file_data)
            temp_dir = Path(self.cache_dir)
            temp_dir.mkdir(exist_ok=True)
            
            temp_audio_path = temp_dir / audio_file_name
            with open(temp_audio_path, "wb") as f:
                f.write(audio_bytes)
            
            print(f"🎤 Processing chunk on Modal server: {audio_file_name}")
            print(f"   Time range: {chunk_start_time:.2f}s - {chunk_end_time:.2f}s")
            print(f"   Size: {len(audio_bytes) / (1024*1024):.2f} MB")
            
            # Use single transcription service for chunks
            service = TranscriptionService()
            
            result = service.transcribe_audio(
                audio_file_path=str(temp_audio_path),
                model_size=model_size,
                language=language,
                output_format="json",  # Always use JSON for chunks
                enable_speaker_diarization=enable_speaker_diarization
            )
            
            # Add chunk timing information
            if result.get("processing_status") == "success":
                result["chunk_start_time"] = chunk_start_time
                result["chunk_end_time"] = chunk_end_time
                result["chunk_file"] = audio_file_name
            
            # Clean up temporary file
            try:
                temp_audio_path.unlink()
            except:
                pass
            
            print(f"✅ Chunk transcription completed on Modal server")
            return result
            
        except Exception as e:
            print(f"❌ Error processing chunk request: {e}")
            return {
                "processing_status": "failed",
                "error_message": f"Server chunk processing error: {str(e)}",
                "chunk_start_time": request_data.get("chunk_start_time", 0),
                "chunk_end_time": request_data.get("chunk_end_time", 0)
            }
    
    def _log_transcription_results(self, result: Dict[str, Any], enable_speaker_diarization: bool = False):
        """
        Log transcription results in a consistent format
        
        Args:
            result: Transcription result dictionary
            enable_speaker_diarization: Whether speaker diarization was enabled
        """
        print(f"   Processing type: {'Distributed' if result.get('distributed_processing', False) else 'Single'}")
        print(f"   Segments: {result.get('segment_count', 0)}")
        print(f"   Duration: {result.get('audio_duration', 0):.2f}s")
        print(f"   Language: {result.get('language_detected', 'unknown')}")
        
        if result.get("distributed_processing", False):
            print(f"   Chunks processed: {result.get('chunks_processed', 0)}")
            print(f"   Chunks failed: {result.get('chunks_failed', 0)}")
            segmentation_type = result.get("segmentation_type", "time_based")
            print(f"   Segmentation: {segmentation_type}")
        
        if enable_speaker_diarization:
            speaker_count = result.get("global_speaker_count", 0)
            print(f"   Speakers detected: {speaker_count}") 
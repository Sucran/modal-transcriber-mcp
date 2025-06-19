"""
Health Service
Provides health check functionality for the transcription service
"""

import os
import whisper
from pathlib import Path
from typing import Dict, Any


class HealthService:
    """Service for health checks and status monitoring"""
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the service"""
        
        # Check Whisper models
        whisper_status = self._check_whisper_models()
        
        # Check speaker diarization
        speaker_status = self._check_speaker_diarization()
        
        # Overall health
        overall_health = "healthy" if (
            whisper_status["status"] == "healthy" and 
            speaker_status["status"] in ["healthy", "partial"]  # Speaker diarization is optional
        ) else "unhealthy"
        
        return {
            "status": overall_health,
            "timestamp": self._get_current_timestamp(),
            "whisper": whisper_status,
            "speaker_diarization": speaker_status,
            "version": "1.0.0"
        }
    
    def _check_whisper_models(self) -> Dict[str, Any]:
        """Check Whisper model availability"""
        try:
            # Check available models
            available_models = whisper.available_models()
            
            # Check if turbo model is available
            default_model = "turbo"
            
            # Check model cache directory
            model_cache_dir = "/model"
            cache_exists = os.path.exists(model_cache_dir)
            
            # Try to load the default model
            try:
                if cache_exists:
                    model = whisper.load_model(default_model, download_root=model_cache_dir)
                    model_loaded = True
                    load_source = "cache"
                else:
                    model = whisper.load_model(default_model)
                    model_loaded = True
                    load_source = "download"
            except Exception as e:
                model_loaded = False
                load_source = f"failed: {e}"
            
            return {
                "status": "healthy" if model_loaded else "unhealthy",
                "default_model": default_model,
                "available_models": available_models,
                "model_cache_exists": cache_exists,
                "model_cache_directory": model_cache_dir if cache_exists else None,
                "model_loaded": model_loaded,
                "load_source": load_source,
                "whisper_version": getattr(whisper, '__version__', 'unknown')
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "default_model": "turbo",
                "available_models": [],
                "model_cache_exists": False,
                "model_loaded": False
            }
    
    def _check_speaker_diarization(self) -> Dict[str, Any]:
        """Check speaker diarization functionality"""
        try:
            # Check if HF token is available
            hf_token = os.environ.get("HF_TOKEN")
            hf_token_available = hf_token is not None
            
            # Check speaker model cache
            speaker_cache_dir = "/model/speaker-diarization"
            cache_exists = os.path.exists(speaker_cache_dir)
            
            # Check config file
            config_file = os.path.join(speaker_cache_dir, "config.json")
            config_exists = os.path.exists(config_file)
            
            # Try to load speaker diarization pipeline
            pipeline_loaded = False
            pipeline_error = None
            
            if hf_token_available:
                try:
                    from pyannote.audio import Pipeline
                    
                    # Try to load pipeline
                    pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                    pipeline_loaded = True
                    
                except Exception as e:
                    pipeline_error = str(e)
            else:
                pipeline_error = "HF_TOKEN not available"
            
            # Determine status
            if pipeline_loaded:
                status = "healthy"
            elif hf_token_available:
                status = "partial"  # Token available but pipeline failed
            else:
                status = "disabled"  # No token, feature disabled
            
            return {
                "status": status,
                "hf_token_available": hf_token_available,
                "speaker_cache_exists": cache_exists,
                "speaker_cache_directory": speaker_cache_dir if cache_exists else None,
                "config_exists": config_exists,
                "pipeline_loaded": pipeline_loaded,
                "pipeline_error": pipeline_error,
                "model_name": "pyannote/speaker-diarization-3.1"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "hf_token_available": False,
                "speaker_cache_exists": False,
                "pipeline_loaded": False
            }
    
    def test_speaker_diarization(self, test_audio_path: str = None) -> Dict[str, Any]:
        """Test speaker diarization functionality with actual audio"""
        try:
            # Check if HF token is available
            hf_token = os.environ.get("HF_TOKEN")
            if not hf_token:
                return {
                    "status": "skipped",
                    "reason": "HF_TOKEN not available"
                }
            
            # Load speaker diarization pipeline
            from pyannote.audio import Pipeline
            
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            
            # If no test audio provided, return pipeline load success
            if not test_audio_path:
                return {
                    "status": "pipeline_loaded",
                    "message": "Speaker diarization pipeline loaded successfully"
                }
            
            # Test with actual audio file
            if not os.path.exists(test_audio_path):
                return {
                    "status": "failed",
                    "reason": f"Test audio file not found: {test_audio_path}"
                }
            
            # Run speaker diarization
            diarization_result = pipeline(test_audio_path)
            
            # Process results
            speakers = set()
            segments_count = 0
            total_speech_duration = 0
            
            for turn, _, speaker in diarization_result.itertracks(yield_label=True):
                speakers.add(speaker)
                segments_count += 1
                total_speech_duration += turn.end - turn.start
            
            return {
                "status": "success",
                "speakers_detected": len(speakers),
                "segments_count": segments_count,
                "total_speech_duration": total_speech_duration,
                "test_audio_path": test_audio_path,
                "speakers": list(speakers)
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "test_audio_path": test_audio_path
            }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z" 
"""
Speaker diarization implementation using pyannote.audio
"""

import os
import torch
from typing import Optional, List, Dict, Any

from ..interfaces.speaker_detector import ISpeakerDetector
from ..utils.config import AudioProcessingConfig
from ..utils.errors import SpeakerDiarizationError, ModelLoadError


class PyannoteSpeikerDetector(ISpeakerDetector):
    """Speaker diarization using pyannote.audio"""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        self.config = config or AudioProcessingConfig()
        self.device = self._setup_device()
        self.pipeline = None
        self.auth_token = os.environ.get(self.config.hf_token_env_var)
        
        if not self.auth_token:
            print("⚠️ No Hugging Face token found. Speaker diarization will be disabled.")
    
    def _setup_device(self) -> torch.device:
        """Setup and return the best available device"""
        if torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")
    
    async def detect_speakers(
        self,
        audio_file_path: str,
        num_speakers: Optional[int] = None,
        min_speakers: int = 1,
        max_speakers: int = 10
    ) -> Dict[str, Any]:
        """Detect speakers in audio file"""
        
        if not self.auth_token:
            raise SpeakerDiarizationError(
                "Speaker diarization requires Hugging Face token",
                audio_file=audio_file_path
            )
        
        try:
            # Load pipeline if not already loaded
            if self.pipeline is None:
                self.pipeline = self._load_pipeline()
            
            # Perform diarization
            diarization = self.pipeline(audio_file_path)
            
            # Convert to our format
            speakers = {}
            segments = []
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_id = f"SPEAKER_{speaker.split('_')[-1].zfill(2)}"
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker_id
                })
                
                if speaker_id not in speakers:
                    speakers[speaker_id] = {
                        "id": speaker_id,
                        "total_time": 0.0,
                        "segments": []
                    }
                
                speakers[speaker_id]["total_time"] += turn.end - turn.start
                speakers[speaker_id]["segments"].append({
                    "start": turn.start,
                    "end": turn.end
                })
            
            return {
                "speaker_count": len(speakers),
                "speakers": speakers,
                "segments": segments,
                "audio_file": audio_file_path
            }
            
        except Exception as e:
            raise SpeakerDiarizationError(
                f"Speaker detection failed: {str(e)}",
                audio_file=audio_file_path
            )
    
    def _load_pipeline(self):
        """Load pyannote speaker diarization pipeline"""
        try:
            # Suppress warnings
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning, module="pyannote")
            warnings.filterwarnings("ignore", category=UserWarning, module="pytorch_lightning")
            warnings.filterwarnings("ignore", category=FutureWarning, module="pytorch_lightning")
            
            from pyannote.audio import Pipeline
            
            print("📥 Loading speaker diarization pipeline...")
            pipeline = Pipeline.from_pretrained(
                self.config.speaker_diarization_model,
                use_auth_token=self.auth_token
            )
            pipeline.to(self.device)
            
            return pipeline
            
        except Exception as e:
            raise ModelLoadError(
                f"Failed to load speaker diarization pipeline: {str(e)}",
                model_name=self.config.speaker_diarization_model
            )
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported speaker diarization models"""
        return [self.config.speaker_diarization_model]
    
    def is_available(self) -> bool:
        """Check if speaker diarization is available"""
        return self.auth_token is not None 
"""
Speaker Embedding Service - manages global speaker embeddings and identification

This module provides advanced speaker identification and unification across distributed audio chunks
using pyannote.audio embedding models and cosine similarity calculations.

Key Features:
1. Global Speaker Management: Maintains a persistent database of speaker embeddings
2. Embedding Extraction: Uses pyannote.audio models to extract speaker embeddings from audio segments  
3. Speaker Unification: Identifies when speakers in different chunks are the same person
4. Distributed Processing Support: Unifies speakers across multiple transcription chunks

Usage in Modal Configuration:
- Speaker diarization models are preloaded in modal_config.py download_models() function
- Models include both diarization pipeline and embedding extraction models
- GPU acceleration is used for optimal performance

Usage in Distributed Transcription:
- DistributedTranscriptionService.merge_chunk_results() calls speaker unification
- Speaker embeddings are extracted for each speaker segment using inference.crop()
- Cosine distance calculations determine if speakers are the same across chunks
- Speaker IDs are unified to prevent duplicate speaker labeling

Example workflow:
1. Audio is split into chunks for distributed processing
2. Each chunk performs speaker diarization independently (e.g., SPEAKER_00, SPEAKER_01)
3. After all chunks complete, speaker embeddings are extracted for unification
4. Cosine similarity comparison identifies matching speakers across chunks
5. Local speaker IDs are mapped to global unified IDs (e.g., SPEAKER_GLOBAL_001)
6. Final transcription uses consistent speaker labels throughout

Technical Details:
- Uses pyannote/embedding model for feature extraction
- Cosine distance threshold of 0.3 for speaker matching (configurable)
- Supports both single-file and distributed transcription workflows
- Thread-safe speaker database operations
- Persistent storage in JSON format for speaker history
"""

import asyncio
import json
import pickle
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

import numpy as np
import torch
from scipy.spatial.distance import cosine

from ..interfaces.speaker_manager import (
    ISpeakerEmbeddingManager,
    ISpeakerIdentificationService,
    SpeakerEmbedding,
    SpeakerSegment
)
from ..utils.errors import SpeakerDiarizationError, ModelLoadError
from ..utils.config import AudioProcessingConfig


class SpeakerEmbeddingService(ISpeakerEmbeddingManager):
    """Global speaker embedding management service"""
    
    def __init__(
        self,
        storage_path: str = "global_speakers.json",
        similarity_threshold: float = 0.3
    ):
        self.storage_path = Path(storage_path)
        self.similarity_threshold = similarity_threshold
        self.speakers: Dict[str, SpeakerEmbedding] = {}
        self.speaker_counter = 0
        self.lock = threading.Lock()
        self._loaded = False
        
        # Don't load speakers in __init__ to avoid async issues
        # Loading will happen on first use via _ensure_loaded()
    
    async def _ensure_loaded(self) -> None:
        """Ensure speakers are loaded (called on first use)"""
        if not self._loaded:
            await self.load_speakers()
            self._loaded = True
    
    async def load_speakers(self) -> None:
        """Load speaker data from storage file"""
        
        if not self.storage_path.exists():
            return
        
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._read_speakers_file)
            
            self.speakers = {
                speaker_id: SpeakerEmbedding(
                    speaker_id=speaker_data["speaker_id"],
                    embedding=np.array(speaker_data["embedding"]),
                    confidence=speaker_data["confidence"],
                    source_files=speaker_data["source_files"],
                    sample_count=speaker_data["sample_count"],
                    created_at=speaker_data["created_at"],
                    updated_at=speaker_data["updated_at"]
                )
                for speaker_id, speaker_data in data.get("speakers", {}).items()
            }
            self.speaker_counter = data.get("speaker_counter", 0)
            
            print(f"✅ Loaded {len(self.speakers)} known speakers")
            
        except Exception as e:
            print(f"⚠️ Failed to load speaker data: {e}")
            self.speakers = {}
            self.speaker_counter = 0
    
    async def save_speakers(self) -> None:
        """Save speaker data to storage file"""
        
        try:
            data = {
                "speakers": {
                    speaker_id: {
                        "speaker_id": speaker.speaker_id,
                        "embedding": speaker.embedding.tolist(),
                        "confidence": speaker.confidence,
                        "source_files": speaker.source_files,
                        "sample_count": speaker.sample_count,
                        "created_at": speaker.created_at,
                        "updated_at": speaker.updated_at
                    }
                    for speaker_id, speaker in self.speakers.items()
                },
                "speaker_counter": self.speaker_counter,
                "updated_at": datetime.now().isoformat()
            }
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._write_speakers_file, data)
            
            print(f"💾 Speaker data saved: {len(self.speakers)} speakers")
            
        except Exception as e:
            print(f"❌ Failed to save speaker data: {e}")
    
    async def find_matching_speaker(
        self,
        embedding: np.ndarray,
        source_file: str
    ) -> Optional[str]:
        """Find matching speaker from existing embeddings"""
        
        await self._ensure_loaded()
        
        if not self.speakers:
            return None
        
        best_match_id = None
        best_similarity = float('inf')
        
        for speaker_id, speaker in self.speakers.items():
            # Calculate cosine distance
            distance = cosine(embedding, speaker.embedding)
            
            if distance < best_similarity:
                best_similarity = distance
                best_match_id = speaker_id
        
        # Check if similarity threshold is met
        if best_similarity <= self.similarity_threshold:
            print(f"🎯 Found matching speaker: {best_match_id} (distance: {best_similarity:.3f})")
            return best_match_id
        
        print(f"🆕 No matching speaker found (best distance: {best_similarity:.3f} > {self.similarity_threshold})")
        return None
    
    async def add_or_update_speaker(
        self,
        embedding: np.ndarray,
        source_file: str,
        confidence: float = 1.0,
        original_label: Optional[str] = None
    ) -> str:
        """Add new speaker or update existing speaker"""
        
        await self._ensure_loaded()
        
        with self.lock:
            # Find matching speaker
            matching_speaker_id = await self.find_matching_speaker(embedding, source_file)
            
            if matching_speaker_id:
                # Update existing speaker
                speaker = self.speakers[matching_speaker_id]
                
                # Update embedding vector using weighted average
                weight = 1.0 / (speaker.sample_count + 1)
                speaker.embedding = (speaker.embedding * (1 - weight) + embedding * weight)
                
                # Update other information
                if source_file not in speaker.source_files:
                    speaker.source_files.append(source_file)
                speaker.sample_count += 1
                speaker.confidence = max(speaker.confidence, confidence)
                speaker.updated_at = datetime.now().isoformat()
                
                print(f"🔄 Updated speaker {matching_speaker_id}: {speaker.sample_count} samples")
                return matching_speaker_id
            
            else:
                # Create new speaker
                self.speaker_counter += 1
                new_speaker_id = f"SPEAKER_GLOBAL_{self.speaker_counter:03d}"
                
                new_speaker = SpeakerEmbedding(
                    speaker_id=new_speaker_id,
                    embedding=embedding.copy(),
                    confidence=confidence,
                    source_files=[source_file],
                    sample_count=1,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                
                self.speakers[new_speaker_id] = new_speaker
                
                print(f"🆕 Created new speaker {new_speaker_id}")
                return new_speaker_id
    
    async def map_local_to_global_speakers(
        self,
        local_embeddings: Dict[str, np.ndarray],
        source_file: str
    ) -> Dict[str, str]:
        """Map local speaker labels to global speaker IDs"""
        
        mapping = {}
        
        for local_label, embedding in local_embeddings.items():
            global_id = await self.add_or_update_speaker(
                embedding=embedding,
                source_file=source_file,
                original_label=local_label
            )
            mapping[local_label] = global_id
        
        # Save updated speaker data
        await self.save_speakers()
        
        return mapping
    
    async def get_speaker_info(self, speaker_id: str) -> Optional[SpeakerEmbedding]:
        """Get speaker information by ID"""
        return self.speakers.get(speaker_id)
    
    async def get_all_speakers_summary(self) -> Dict[str, Any]:
        """Get summary of all speakers"""
        
        return {
            "total_speakers": len(self.speakers),
            "speakers": {
                speaker_id: {
                    "speaker_id": speaker.speaker_id,
                    "confidence": speaker.confidence,
                    "source_files_count": len(speaker.source_files),
                    "sample_count": speaker.sample_count,
                    "created_at": speaker.created_at,
                    "updated_at": speaker.updated_at
                }
                for speaker_id, speaker in self.speakers.items()
            }
        }
    
    def _read_speakers_file(self) -> Dict[str, Any]:
        """Read speakers file synchronously"""
        with open(self.storage_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _write_speakers_file(self, data: Dict[str, Any]) -> None:
        """Write speakers file synchronously"""
        # Atomic write
        temp_path = self.storage_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(self.storage_path)


class SpeakerIdentificationService(ISpeakerIdentificationService):
    """Speaker identification service using pyannote.audio"""
    
    def __init__(
        self,
        embedding_manager: ISpeakerEmbeddingManager,
        config: Optional[AudioProcessingConfig] = None
    ):
        self.embedding_manager = embedding_manager
        self.config = config or AudioProcessingConfig()
        self.auth_token = None
        self.pipeline = None
        self.embedding_model = None
        
        # Check for HF token
        import os
        self.auth_token = os.environ.get(self.config.hf_token_env_var)
        self.available = self.auth_token is not None
        
        if not self.available:
            print("⚠️ No Hugging Face token found. Speaker identification will be disabled.")
    
    async def extract_speaker_embeddings(
        self,
        audio_path: str,
        segments: List[SpeakerSegment]
    ) -> Dict[str, np.ndarray]:
        """Extract speaker embeddings from audio segments"""
        
        if not self.available:
            raise SpeakerDiarizationError("Speaker identification not available - missing HF token")
        
        try:
            # Load models if needed
            if self.embedding_model is None:
                await self._load_models()
            
            # Create inference object for embedding extraction
            from pyannote.audio.core.inference import Inference
            from pyannote.core import Segment
            import torchaudio
            
            inference = Inference(self.embedding_model, window="whole")
            
            # Load audio file
            waveform, sample_rate = torchaudio.load(audio_path)
            
            embeddings = {}
            
            # Extract embeddings for each unique speaker
            for segment in segments:
                if segment.speaker_id not in embeddings:
                    # Create audio segment for embedding extraction
                    audio_segment = Segment(segment.start, segment.end)
                    
                    # Extract embedding using inference.crop
                    embedding = inference.crop(waveform, audio_segment)
                    
                    # Convert to numpy array and store
                    if isinstance(embedding, torch.Tensor):
                        embedding_np = embedding.detach().cpu().numpy()
                    else:
                        embedding_np = embedding
                    
                    embeddings[segment.speaker_id] = embedding_np
                    print(f"🎯 Extracted embedding for {segment.speaker_id}: shape {embedding_np.shape}")
            
            return embeddings
            
        except Exception as e:
            raise SpeakerDiarizationError(f"Embedding extraction failed: {str(e)}")
    
    async def identify_speakers_in_audio(
        self,
        audio_path: str,
        transcription_segments: List[Dict[str, Any]]
    ) -> List[SpeakerSegment]:
        """Identify speakers in audio file"""
        
        if not self.available:
            print("⚠️ Speaker identification skipped - not available")
            return []
        
        try:
            # Load pipeline if needed
            if self.pipeline is None:
                await self._load_models()
            
            # Perform diarization
            loop = asyncio.get_event_loop()
            diarization = await loop.run_in_executor(
                None,
                self.pipeline,
                audio_path
            )
            
            # Convert to speaker segments
            speaker_segments = []
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_id = f"SPEAKER_{speaker.split('_')[-1].zfill(2)}"
                speaker_segments.append(SpeakerSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker_id=speaker_id,
                    confidence=1.0  # pyannote doesn't provide confidence
                ))
            
            return speaker_segments
            
        except Exception as e:
            raise SpeakerDiarizationError(f"Speaker identification failed: {str(e)}")
    
    async def map_transcription_to_speakers(
        self,
        transcription_segments: List[Dict[str, Any]],
        speaker_segments: List[SpeakerSegment]
    ) -> List[Dict[str, Any]]:
        """Map transcription segments to speaker information"""
        
        result_segments = []
        
        for trans_seg in transcription_segments:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            
            # Find overlapping speaker segment
            best_speaker = None
            best_overlap = 0
            
            for speaker_seg in speaker_segments:
                # Calculate overlap
                overlap_start = max(trans_start, speaker_seg.start)
                overlap_end = min(trans_end, speaker_seg.end)
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = speaker_seg.speaker_id
            
            # Add speaker information to transcription segment
            result_segment = trans_seg.copy()
            result_segment["speaker"] = best_speaker
            result_segments.append(result_segment)
        
        return result_segments
    
    async def unify_distributed_speakers(
        self,
        chunk_results: List[Dict[str, Any]],
        audio_file_path: str
    ) -> Dict[str, str]:
        """
        Unify speaker identifications across distributed chunks using embedding similarity
        
        Args:
            chunk_results: List of chunk transcription results with speaker information
            audio_file_path: Path to the original audio file for embedding extraction
            
        Returns:
            Mapping from local chunk speaker IDs to unified global speaker IDs
        """
        if not self.available:
            print("⚠️ Speaker unification skipped - embedding service not available")
            return {}
        
        try:
            # Load models if needed
            if self.embedding_model is None:
                await self._load_models()
            
            from pyannote.audio.core.inference import Inference
            from pyannote.core import Segment
            import torchaudio
            from scipy.spatial.distance import cosine
            
            inference = Inference(self.embedding_model, window="whole")
            waveform, sample_rate = torchaudio.load(audio_file_path)
            
            # Collect all speaker segments from chunks with their chunk context
            all_speaker_segments = []
            
            for chunk_idx, chunk in enumerate(chunk_results):
                if chunk.get("processing_status") != "success":
                    continue
                    
                chunk_start_time = chunk.get("chunk_start_time", 0)
                segments = chunk.get("segments", [])
                
                for segment in segments:
                    if "speaker" in segment and segment["speaker"]:
                        # Create unique chunk-local speaker ID
                        chunk_speaker_id = f"chunk_{chunk_idx}_{segment['speaker']}"
                        
                        all_speaker_segments.append({
                            "chunk_speaker_id": chunk_speaker_id,
                            "original_speaker_id": segment["speaker"],
                            "chunk_index": chunk_idx,
                            "start": segment["start"] + chunk_start_time,
                            "end": segment["end"] + chunk_start_time,
                            "text": segment.get("text", "")
                        })
            
            if not all_speaker_segments:
                return {}
            
            # Extract embeddings for each unique chunk speaker
            speaker_embeddings = {}
            
            for seg in all_speaker_segments:
                chunk_speaker_id = seg["chunk_speaker_id"]
                
                if chunk_speaker_id not in speaker_embeddings:
                    try:
                        # Create audio segment for embedding extraction
                        audio_segment = Segment(seg["start"], seg["end"])
                        
                        # Extract embedding using inference.crop
                        embedding = inference.crop(waveform, audio_segment)
                        
                        # Convert to numpy array
                        if hasattr(embedding, 'detach'):
                            embedding_np = embedding.detach().cpu().numpy()
                        else:
                            embedding_np = embedding
                            
                        speaker_embeddings[chunk_speaker_id] = embedding_np
                        print(f"🎯 Extracted embedding for {chunk_speaker_id}: shape {embedding_np.shape}")
                        
                    except Exception as e:
                        print(f"⚠️ Failed to extract embedding for {chunk_speaker_id}: {e}")
                        continue
            
            # Perform speaker clustering based on embedding similarity
            unified_mapping = {}
            global_speaker_counter = 1
            similarity_threshold = 0.3  # Cosine distance threshold
            
            for chunk_speaker_id, embedding in speaker_embeddings.items():
                best_match_id = None
                best_distance = float('inf')
                
                # Compare with existing unified speakers
                for existing_id, mapped_global_id in unified_mapping.items():
                    if existing_id != chunk_speaker_id and existing_id in speaker_embeddings:
                        existing_embedding = speaker_embeddings[existing_id]
                        
                        try:
                            # Calculate cosine distance
                            distance = cosine(embedding.flatten(), existing_embedding.flatten())
                            
                            if distance < best_distance:
                                best_distance = distance
                                best_match_id = mapped_global_id
                        except Exception as e:
                            print(f"⚠️ Error calculating distance: {e}")
                            continue
                
                # Assign speaker ID based on similarity
                if best_match_id and best_distance <= similarity_threshold:
                    unified_mapping[chunk_speaker_id] = best_match_id
                    print(f"🎯 Unified {chunk_speaker_id} -> {best_match_id} (distance: {best_distance:.3f})")
                else:
                    # Create new unified speaker ID
                    new_global_id = f"SPEAKER_GLOBAL_{global_speaker_counter:03d}"
                    unified_mapping[chunk_speaker_id] = new_global_id
                    global_speaker_counter += 1
                    print(f"🆕 New speaker {chunk_speaker_id} -> {new_global_id}")
            
            # Create final mapping from original speaker IDs to global IDs
            final_mapping = {}
            for seg in all_speaker_segments:
                chunk_speaker_id = seg["chunk_speaker_id"]
                original_id = seg["original_speaker_id"]
                
                if chunk_speaker_id in unified_mapping:
                    # Create a key that includes chunk context for uniqueness
                    mapping_key = f"chunk_{seg['chunk_index']}_{original_id}"
                    final_mapping[mapping_key] = unified_mapping[chunk_speaker_id]
            
            print(f"🎤 Speaker unification completed: {len(set(unified_mapping.values()))} global speakers from {len(speaker_embeddings)} chunk speakers")
            return final_mapping
            
        except Exception as e:
            print(f"❌ Speaker unification failed: {e}")
            return {}
    
    async def _load_models(self) -> None:
        """Load pyannote.audio models"""
        
        try:
            # Suppress warnings
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning, module="pyannote")
            warnings.filterwarnings("ignore", category=UserWarning, module="pytorch_lightning")
            warnings.filterwarnings("ignore", category=FutureWarning, module="pytorch_lightning")
            
            from pyannote.audio import Model, Pipeline
            from pyannote.audio.core.inference import Inference
            import torch
            
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Load embedding model
            loop = asyncio.get_event_loop()
            
            self.embedding_model = await loop.run_in_executor(
                None,
                Model.from_pretrained,
                "pyannote/embedding",
                self.auth_token
            )
            self.embedding_model.to(device)
            self.embedding_model.eval()
            
            # Load diarization pipeline
            self.pipeline = await loop.run_in_executor(
                None,
                Pipeline.from_pretrained,
                "pyannote/speaker-diarization-3.1",
                self.auth_token
            )
            self.pipeline.to(device)
            
            print("✅ Speaker identification models loaded")
            
        except Exception as e:
            raise ModelLoadError(f"Failed to load speaker models: {str(e)}") 
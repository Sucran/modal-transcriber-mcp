"""
Unit tests for Speaker Embedding Service
Tests the core functionality of speaker identification and embedding management
"""

import pytest
import asyncio
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import numpy as np
import torch

from src.services.speaker_embedding_service import (
    SpeakerEmbeddingService, 
    SpeakerIdentificationService
)
from src.interfaces.speaker_manager import SpeakerEmbedding, SpeakerSegment
from src.utils.config import AudioProcessingConfig
from src.utils.errors import SpeakerDiarizationError


class TestSpeakerEmbeddingService:
    """Test SpeakerEmbeddingService functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "test_speakers.json"
        self.service = SpeakerEmbeddingService(
            storage_path=str(self.storage_path),
            similarity_threshold=0.3
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test service initialization"""
        assert self.service.storage_path == self.storage_path
        assert self.service.similarity_threshold == 0.3
        assert self.service.speakers == {}
        assert self.service.speaker_counter == 0
        assert not self.service._loaded
    
    @pytest.mark.asyncio
    async def test_load_speakers_empty_file(self):
        """Test loading speakers when no file exists"""
        await self.service.load_speakers()
        assert self.service.speakers == {}
        assert self.service.speaker_counter == 0
    
    @pytest.mark.asyncio
    async def test_save_and_load_speakers(self):
        """Test saving and loading speaker data"""
        # Create test speaker
        embedding = np.random.rand(512)
        
        speaker_id = await self.service.add_or_update_speaker(
            embedding=embedding,
            source_file="test.wav",
            confidence=0.9
        )
        
        # Save speakers
        await self.service.save_speakers()
        
        # Verify file exists
        assert self.storage_path.exists()
        
        # Create new service and load data
        new_service = SpeakerEmbeddingService(storage_path=str(self.storage_path))
        await new_service.load_speakers()
        
        # Verify loaded data
        assert len(new_service.speakers) == 1
        assert speaker_id in new_service.speakers
        assert new_service.speaker_counter == 1
        
        loaded_speaker = new_service.speakers[speaker_id]
        assert loaded_speaker.speaker_id == speaker_id
        assert loaded_speaker.confidence == 0.9
        assert "test.wav" in loaded_speaker.source_files
        assert np.allclose(loaded_speaker.embedding, embedding)
    
    @pytest.mark.asyncio
    async def test_find_matching_speaker(self):
        """Test finding matching speakers"""
        # Add first speaker
        embedding1 = np.random.rand(512)
        speaker_id1 = await self.service.add_or_update_speaker(
            embedding=embedding1,
            source_file="test1.wav"
        )
        
        # Test finding exact match
        match_id = await self.service.find_matching_speaker(
            embedding=embedding1,
            source_file="test1.wav"
        )
        assert match_id == speaker_id1
        
        # Test with similar embedding (should match)
        similar_embedding = embedding1 + np.random.normal(0, 0.01, 512)
        match_id = await self.service.find_matching_speaker(
            embedding=similar_embedding,
            source_file="test2.wav"
        )
        assert match_id == speaker_id1
        
        # Test with very different embedding (create orthogonal vector)
        different_embedding = np.zeros(512)
        different_embedding[0] = 1.0  # Create a very different embedding
        match_id = await self.service.find_matching_speaker(
            embedding=different_embedding,
            source_file="test3.wav"
        )
        assert match_id is None
    
    @pytest.mark.asyncio
    async def test_add_or_update_speaker_new(self):
        """Test adding new speaker"""
        embedding = np.random.rand(512)
        
        speaker_id = await self.service.add_or_update_speaker(
            embedding=embedding,
            source_file="test.wav",
            confidence=0.95
        )
        
        assert speaker_id == "SPEAKER_GLOBAL_001"
        assert len(self.service.speakers) == 1
        assert self.service.speaker_counter == 1
        
        speaker = self.service.speakers[speaker_id]
        assert speaker.confidence == 0.95
        assert speaker.source_files == ["test.wav"]
        assert speaker.sample_count == 1
        assert np.allclose(speaker.embedding, embedding)
    
    @pytest.mark.asyncio
    async def test_add_or_update_speaker_existing(self):
        """Test updating existing speaker"""
        # Add first speaker
        embedding1 = np.random.rand(512)
        speaker_id = await self.service.add_or_update_speaker(
            embedding=embedding1,
            source_file="test1.wav",
            confidence=0.8
        )
        
        # Add similar speaker (should update existing)
        embedding2 = embedding1 + np.random.normal(0, 0.01, 512)
        updated_id = await self.service.add_or_update_speaker(
            embedding=embedding2,
            source_file="test2.wav",
            confidence=0.9
        )
        
        assert updated_id == speaker_id
        assert len(self.service.speakers) == 1  # Should still be only one speaker
        
        speaker = self.service.speakers[speaker_id]
        assert speaker.confidence == 0.9  # Updated to higher confidence
        assert "test1.wav" in speaker.source_files
        assert "test2.wav" in speaker.source_files
        assert speaker.sample_count == 2
    
    @pytest.mark.asyncio
    async def test_map_local_to_global_speakers(self):
        """Test mapping local speaker labels to global IDs"""
        # Create distinctly different embeddings to avoid false matches
        embedding1 = np.zeros(512)
        embedding1[0] = 1.0  # First embedding concentrated at index 0
        
        embedding2 = np.zeros(512) 
        embedding2[256] = 1.0  # Second embedding concentrated at index 256
        
        local_embeddings = {
            "SPEAKER_00": embedding1,
            "SPEAKER_01": embedding2
        }
        
        mapping = await self.service.map_local_to_global_speakers(
            local_embeddings=local_embeddings,
            source_file="test.wav"
        )
        
        assert len(mapping) == 2
        assert "SPEAKER_00" in mapping
        assert "SPEAKER_01" in mapping
        assert mapping["SPEAKER_00"] == "SPEAKER_GLOBAL_001"
        assert mapping["SPEAKER_01"] == "SPEAKER_GLOBAL_002"
        assert len(self.service.speakers) == 2
    
    @pytest.mark.asyncio
    async def test_get_speaker_info(self):
        """Test getting speaker information"""
        embedding = np.zeros(512)
        embedding[0] = 1.0
        speaker_id = await self.service.add_or_update_speaker(
            embedding=embedding,
            source_file="test.wav"
        )
        
        speaker_info = await self.service.get_speaker_info(speaker_id)
        assert speaker_info is not None
        assert speaker_info.speaker_id == speaker_id
        
        # Test non-existent speaker
        non_existent = await self.service.get_speaker_info("NONEXISTENT")
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_get_all_speakers_summary(self):
        """Test getting summary of all speakers"""
        # Add multiple speakers with very different embeddings
        embeddings = []
        for i in range(3):
            embedding = np.zeros(512)
            embedding[i * 100] = 1.0  # Place spike at different locations
            embeddings.append(embedding)
            await self.service.add_or_update_speaker(
                embedding=embedding,
                source_file=f"test{i}.wav"
            )
        
        summary = await self.service.get_all_speakers_summary()
        assert summary["total_speakers"] == 3
        assert len(summary["speakers"]) == 3


class TestSpeakerIdentificationService:
    """Test SpeakerIdentificationService functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = AudioProcessingConfig()
        self.embedding_manager = SpeakerEmbeddingService()
        self.service = SpeakerIdentificationService(
            embedding_manager=self.embedding_manager,
            config=self.config
        )
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_no_token(self):
        """Test initialization without HF token"""
        assert not self.service.available
        assert self.service.pipeline is None
        assert self.service.embedding_model is None
    
    @patch.dict('os.environ', {'HF_TOKEN': 'test_token'})
    def test_initialization_with_token(self):
        """Test initialization with HF token"""
        service = SpeakerIdentificationService(
            embedding_manager=self.embedding_manager,
            config=self.config
        )
        assert service.available
        assert service.auth_token == 'test_token'
    
    @pytest.mark.asyncio
    async def test_extract_speaker_embeddings_not_available(self):
        """Test embedding extraction when service not available"""
        segments = [
            SpeakerSegment(start=0.0, end=5.0, speaker_id="SPEAKER_00", confidence=1.0)
        ]
        
        with pytest.raises(SpeakerDiarizationError, match="not available"):
            await self.service.extract_speaker_embeddings("test.wav", segments)
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'HF_TOKEN': 'test_token'})
    async def test_extract_speaker_embeddings_success(self):
        """Test successful embedding extraction"""
        # Mock the service as available
        service = SpeakerIdentificationService(
            embedding_manager=self.embedding_manager,
            config=self.config
        )
        
        # Mock the models and inference
        mock_model = Mock()
        mock_inference = Mock()
        mock_waveform = torch.rand(1, 16000)  # 1 second of audio
        mock_embedding = torch.rand(512)
        
        service.embedding_model = mock_model
        
        segments = [
            SpeakerSegment(start=0.0, end=1.0, speaker_id="SPEAKER_00", confidence=1.0),
            SpeakerSegment(start=1.0, end=2.0, speaker_id="SPEAKER_01", confidence=1.0),
            SpeakerSegment(start=2.0, end=3.0, speaker_id="SPEAKER_00", confidence=1.0)  # Same speaker
        ]
        
        with patch('torchaudio.load', return_value=(mock_waveform, 16000)), \
             patch('pyannote.audio.core.inference.Inference', return_value=mock_inference):
            
            mock_inference.crop.return_value = mock_embedding
            
            embeddings = await service.extract_speaker_embeddings("test.wav", segments)
            
            # Should have embeddings for 2 unique speakers
            assert len(embeddings) == 2
            assert "SPEAKER_00" in embeddings
            assert "SPEAKER_01" in embeddings
            assert isinstance(embeddings["SPEAKER_00"], np.ndarray)
            assert isinstance(embeddings["SPEAKER_01"], np.ndarray)
    
    @pytest.mark.asyncio
    async def test_identify_speakers_in_audio_not_available(self):
        """Test speaker identification when service not available"""
        result = await self.service.identify_speakers_in_audio("test.wav", [])
        assert result == []
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'HF_TOKEN': 'test_token'})
    async def test_unify_distributed_speakers(self):
        """Test unifying speakers across distributed chunks"""
        # Mock the service as available
        service = SpeakerIdentificationService(
            embedding_manager=self.embedding_manager,
            config=self.config
        )
        
        # Mock models
        service.embedding_model = Mock()
        
        # Create mock chunk results with speaker information
        chunk_results = [
            {
                "processing_status": "success",
                "chunk_start_time": 0,
                "segments": [
                    {"start": 0, "end": 5, "text": "Hello", "speaker": "SPEAKER_00"},
                    {"start": 5, "end": 10, "text": "World", "speaker": "SPEAKER_01"}
                ]
            },
            {
                "processing_status": "success", 
                "chunk_start_time": 60,
                "segments": [
                    {"start": 0, "end": 5, "text": "Again", "speaker": "SPEAKER_00"},  # Same as chunk 0 SPEAKER_00
                    {"start": 5, "end": 10, "text": "Different", "speaker": "SPEAKER_01"}  # Same as chunk 0 SPEAKER_01
                ]
            }
        ]
        
        # Mock audio loading and inference
        mock_waveform = torch.rand(1, 160000)  # 10 seconds of audio
        
        # Create similar embeddings for same speakers, different for different speakers
        speaker_00_embedding = np.random.rand(512)
        speaker_01_embedding = np.random.rand(512)
        
        def mock_crop_side_effect(waveform, segment):
            # Return similar embeddings for same speakers across chunks
            if "chunk_0_SPEAKER_00" in str(segment) or "chunk_1_SPEAKER_00" in str(segment):
                return torch.tensor(speaker_00_embedding + np.random.normal(0, 0.01, 512))
            else:  # SPEAKER_01
                return torch.tensor(speaker_01_embedding + np.random.normal(0, 0.01, 512))
        
        mock_inference = Mock()
        mock_inference.crop.side_effect = mock_crop_side_effect
        
        with patch('torchaudio.load', return_value=(mock_waveform, 16000)), \
             patch('pyannote.audio.core.inference.Inference', return_value=mock_inference):
            
            mock_inference.crop.side_effect = mock_crop_side_effect
            
            mapping = await service.unify_distributed_speakers(chunk_results, "test.wav")
            
            # Should have mappings for all chunk speakers
            assert len(mapping) >= 4  # 2 speakers × 2 chunks
            
            # Verify that same speakers across chunks map to same global ID
            chunk_0_speaker_00 = mapping.get("chunk_0_SPEAKER_00")
            chunk_1_speaker_00 = mapping.get("chunk_1_SPEAKER_00") 
            
            chunk_0_speaker_01 = mapping.get("chunk_0_SPEAKER_01")
            chunk_1_speaker_01 = mapping.get("chunk_1_SPEAKER_01")
            
            # Same speakers should map to same global ID
            if chunk_0_speaker_00 and chunk_1_speaker_00:
                assert chunk_0_speaker_00 == chunk_1_speaker_00
            if chunk_0_speaker_01 and chunk_1_speaker_01:
                assert chunk_0_speaker_01 == chunk_1_speaker_01
    
    @pytest.mark.asyncio
    async def test_unify_distributed_speakers_not_available(self):
        """Test speaker unification when service not available"""
        chunk_results = [{"processing_status": "success", "segments": []}]
        
        mapping = await self.service.unify_distributed_speakers(chunk_results, "test.wav")
        assert mapping == {}


# Test fixtures and utilities
@pytest.fixture
def sample_audio_file():
    """Create a temporary audio file for testing"""
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_file.close()
    return temp_file.name


@pytest.fixture  
def mock_torch():
    """Mock torch tensor for testing"""
    return torch.rand(512)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
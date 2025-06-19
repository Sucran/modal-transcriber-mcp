"""
Integration tests for Speaker Embedding functionality
Tests the complete workflow of speaker unification in distributed transcription
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import torch

from src.services.distributed_transcription_service import DistributedTranscriptionService
from src.services.speaker_embedding_service import SpeakerEmbeddingService, SpeakerIdentificationService
from src.utils.config import AudioProcessingConfig


class TestSpeakerEmbeddingIntegration:
    """Integration tests for speaker embedding with distributed transcription"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.service = DistributedTranscriptionService(cache_dir=self.temp_dir)
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'HF_TOKEN': 'test_token'})
    async def test_merge_chunk_results_with_speaker_unification(self):
        """Test complete speaker unification workflow in merge_chunk_results"""
        
        # Create realistic chunk results with overlapping speakers
        chunk_results = [
            {
                "processing_status": "success",
                "chunk_start_time": 0.0,
                "audio_duration": 60.0,
                "language_detected": "en",
                "model_used": "turbo",
                "segments": [
                    {"start": 0.0, "end": 5.0, "text": "Hello everyone", "speaker": "SPEAKER_00"},
                    {"start": 5.0, "end": 10.0, "text": "How are you?", "speaker": "SPEAKER_01"},
                    {"start": 10.0, "end": 15.0, "text": "I'm doing well", "speaker": "SPEAKER_00"},
                ]
            },
            {
                "processing_status": "success",
                "chunk_start_time": 60.0,
                "audio_duration": 60.0,
                "language_detected": "en", 
                "model_used": "turbo",
                "segments": [
                    {"start": 0.0, "end": 5.0, "text": "Let's continue", "speaker": "SPEAKER_00"},  # Same as chunk 0 SPEAKER_00
                    {"start": 5.0, "end": 10.0, "text": "Great idea", "speaker": "SPEAKER_01"},    # Same as chunk 0 SPEAKER_01
                    {"start": 10.0, "end": 15.0, "text": "New person here", "speaker": "SPEAKER_02"}, # New speaker
                ]
            }
        ]
        
        with patch('src.services.speaker_embedding_service.SpeakerIdentificationService') as mock_service_class:
            # Configure the mock speaker service
            mock_service = Mock()
            mock_service.unify_distributed_speakers = AsyncMock()
            
            # Create a realistic speaker mapping
            mock_speaker_mapping = {
                "chunk_0_SPEAKER_00": "SPEAKER_GLOBAL_001",  # Person A
                "chunk_0_SPEAKER_01": "SPEAKER_GLOBAL_002",  # Person B
                "chunk_1_SPEAKER_00": "SPEAKER_GLOBAL_001",  # Person A (unified)
                "chunk_1_SPEAKER_01": "SPEAKER_GLOBAL_002",  # Person B (unified)
                "chunk_1_SPEAKER_02": "SPEAKER_GLOBAL_003",  # Person C (new)
            }
            
            mock_service.unify_distributed_speakers.return_value = mock_speaker_mapping
            mock_service_class.return_value = mock_service
            
            # Test the merge functionality
            result = await self.service.merge_chunk_results(
                chunk_results=chunk_results,
                output_format="srt",
                enable_speaker_diarization=True,
                audio_file_path="test_audio.wav"
            )
            
            # Verify the result
            assert result["processing_status"] == "success"
            assert result["speaker_diarization_enabled"] is True
            assert result["speaker_embedding_unified"] is True
            assert result["distributed_processing"] is True
            assert result["chunks_processed"] == 2
            assert result["chunks_failed"] == 0
            
            # Check speaker statistics
            assert result["global_speaker_count"] == 3  # Should be unified to 3 speakers
            expected_speakers = {"SPEAKER_GLOBAL_001", "SPEAKER_GLOBAL_002", "SPEAKER_GLOBAL_003"}
            assert set(result["speakers_detected"]) == expected_speakers
            
            # Check segments have unified speaker labels
            segments = result["segments"]
            assert len(segments) == 6  # Total segments across all chunks
            
            # Verify speaker mappings in segments
            for segment in segments:
                assert "speaker" in segment
                assert segment["speaker"] in expected_speakers
    
    @pytest.mark.asyncio
    async def test_merge_chunk_results_without_speaker_diarization(self):
        """Test merge_chunk_results when speaker diarization is disabled"""
        
        chunk_results = [
            {
                "processing_status": "success",
                "chunk_start_time": 0.0,
                "audio_duration": 60.0,
                "language_detected": "en",
                "model_used": "turbo",
                "segments": [
                    {"start": 0.0, "end": 5.0, "text": "Hello everyone"},
                    {"start": 5.0, "end": 10.0, "text": "How are you?"},
                ]
            }
        ]
        
        result = await self.service.merge_chunk_results(
            chunk_results=chunk_results,
            output_format="srt",
            enable_speaker_diarization=False,
            audio_file_path="test_audio.wav"
        )
        
        # Should not perform speaker unification
        assert result["processing_status"] == "success"
        assert result["speaker_diarization_enabled"] is False
        assert "speaker_embedding_unified" not in result or result["speaker_embedding_unified"] is False
        # Note: global_speaker_count may not be present when speaker diarization is disabled
    
    @pytest.mark.asyncio
    async def test_merge_chunk_results_speaker_unification_failure(self):
        """Test merge_chunk_results when speaker unification fails"""
        
        chunk_results = [
            {
                "processing_status": "success",
                "chunk_start_time": 0.0,
                "audio_duration": 60.0,
                "language_detected": "en",
                "model_used": "turbo",
                "segments": [
                    {"start": 0.0, "end": 5.0, "text": "Hello", "speaker": "SPEAKER_00"},
                ]
            }
        ]
        
        with patch('src.services.speaker_embedding_service.SpeakerIdentificationService') as mock_service_class:
            # Make the speaker service throw an exception
            mock_service = Mock()
            mock_service.unify_distributed_speakers = AsyncMock(side_effect=Exception("Model not available"))
            mock_service_class.return_value = mock_service
            
            result = await self.service.merge_chunk_results(
                chunk_results=chunk_results,
                output_format="srt",
                enable_speaker_diarization=True,
                audio_file_path="test_audio.wav"
            )
            
            # Should continue with original speaker labels
            assert result["processing_status"] == "success"
            assert result["speaker_diarization_enabled"] is True
            assert "speaker_embedding_unified" not in result or result["speaker_embedding_unified"] is False
            
            # Should have chunk-aware speaker labels when unification fails
            segments = result["segments"]
            assert len(segments) == 1
            assert segments[0]["speaker"] == "SPEAKER_CHUNK_0_SPEAKER_00"  # Chunk-aware label when unification fails

    @pytest.mark.asyncio
    async def test_merge_chunk_results_unknown_speaker_filtering(self):
        """Test that UNKNOWN speakers are properly filtered from output"""
        
        service = DistributedTranscriptionService()
        
        # Mock chunk results with mixed speaker types
        chunk_results = [
            {
                "processing_status": "success",
                "chunk_start_time": 0.0,
                "chunk_end_time": 30.0,
                "segments": [
                    {
                        "start": 0.0,
                        "end": 2.0,
                        "text": "Hello world",
                        "speaker": "SPEAKER_00"
                    },
                    {
                        "start": 2.0,
                        "end": 4.0,
                        "text": "This has no speaker",
                        # No speaker field - should become UNKNOWN
                    },
                    {
                        "start": 4.0,
                        "end": 6.0,
                        "text": "Another good segment",
                        "speaker": "SPEAKER_01"
                    }
                ]
            },
            {
                "processing_status": "success",
                "chunk_start_time": 30.0,
                "chunk_end_time": 60.0,
                "segments": [
                    {
                        "start": 0.0,
                        "end": 2.0,
                        "text": "",  # Empty text - should be filtered
                        "speaker": "SPEAKER_00"
                    },
                    {
                        "start": 2.0,
                        "end": 4.0,
                        "text": "Good segment from chunk 2",
                        "speaker": "SPEAKER_00"
                    }
                ]
            }
        ]
        
        # Mock speaker embedding service (not available)
        with patch('src.services.distributed_transcription_service.SpeakerIdentificationService', create=True) as mock_service_class:
            with patch('src.services.distributed_transcription_service.SpeakerEmbeddingService', create=True) as mock_manager_class:
                
                result = await service.merge_chunk_results(
                    chunk_results=chunk_results,
                    output_format="srt",
                    enable_speaker_diarization=False,  # Disable to focus on filtering logic
                    audio_file_path="test.wav"
                )
                
                # Verify basic result structure
                assert result["processing_status"] == "success"
                assert result["chunks_processed"] == 2
                assert result["chunks_failed"] == 0
                
                # Verify filtering statistics
                assert "total_segments_collected" in result
                assert "unknown_segments_filtered" in result
                assert result["total_segments_collected"] == 5  # Total segments before filtering (4 with data + 1 empty)
                assert result["unknown_segments_filtered"] == 1  # One segment with no speaker
                assert result["segment_count"] == 4  # Known speaker segments after first filtering (including empty text)
                
                # Verify segments content (this will be the final filtered segments)
                segments = result["segments"]
                assert len(segments) == 4  # Known speaker segments (including empty text ones)
                
                # Check that all segments have speakers (but may have empty text)
                for segment in segments:
                    assert "speaker" in segment
                    assert segment["speaker"] != "UNKNOWN"
                    # Note: segments array includes all known-speaker segments,
                    # but full_text and output files filter empty text
                
                # Verify text content (should not include UNKNOWN segment)
                full_text = result["text"]
                assert "This has no speaker" not in full_text  # UNKNOWN segment filtered
                assert "Hello world" in full_text
                assert "Another good segment" in full_text
                assert "Good segment from chunk 2" in full_text


class TestSpeakerEmbeddingWorkflow:
    """Test complete workflow scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    @patch.dict('os.environ', {'HF_TOKEN': 'test_token'})
    async def test_end_to_end_speaker_unification(self):
        """Test complete end-to-end speaker unification workflow"""
        
        # Setup services
        embedding_service = SpeakerEmbeddingService(
            storage_path=str(Path(self.temp_dir) / "speakers.json")
        )
        speaker_service = SpeakerIdentificationService(embedding_service)
        
        # Mock the models
        speaker_service.embedding_model = Mock()
        
        # Create test chunk results representing a conversation between 2 people
        # but each chunk detects them as different local speakers
        chunk_results = [
            {
                "processing_status": "success",
                "chunk_start_time": 0,
                "segments": [
                    {"start": 0, "end": 3, "text": "Hi there", "speaker": "SPEAKER_00"},
                    {"start": 3, "end": 6, "text": "Hello", "speaker": "SPEAKER_01"},
                ]
            },
            {
                "processing_status": "success",
                "chunk_start_time": 60,
                "segments": [
                    {"start": 0, "end": 3, "text": "How are things?", "speaker": "SPEAKER_00"},  # Same person as chunk 0 SPEAKER_00
                    {"start": 3, "end": 6, "text": "Going well", "speaker": "SPEAKER_01"},      # Same person as chunk 0 SPEAKER_01
                ]
            }
        ]
        
        # Create consistent embeddings for same speakers
        person_a_base = np.zeros(512)
        person_a_base[0] = 1.0  # Person A concentrated at index 0
        
        person_b_base = np.zeros(512)
        person_b_base[256] = 1.0  # Person B concentrated at index 256
        
        def mock_crop_side_effect(waveform, segment):
            # Return consistent embeddings for same speakers across chunks
            segment_start = float(segment.start)
            if segment_start < 3 or (segment_start >= 60 and segment_start < 63):
                # Person A in both chunks
                return torch.tensor(person_a_base + np.random.normal(0, 0.005, 512))
            else:
                # Person B in both chunks  
                return torch.tensor(person_b_base + np.random.normal(0, 0.005, 512))
        
        mock_inference = Mock()
        mock_inference.crop.side_effect = mock_crop_side_effect
        mock_waveform = torch.rand(1, 96000)  # 6 seconds at 16kHz
        
        with patch('torchaudio.load', return_value=(mock_waveform, 16000)), \
             patch('pyannote.audio.core.inference.Inference', return_value=mock_inference):
            
            # Perform speaker unification
            mapping = await speaker_service.unify_distributed_speakers(
                chunk_results, "test_audio.wav"
            )
            
            # Verify mapping results
            assert len(mapping) == 4  # 2 speakers × 2 chunks
            
            # Same speakers should map to same global IDs
            chunk_0_speaker_00 = mapping["chunk_0_SPEAKER_00"]
            chunk_1_speaker_00 = mapping["chunk_1_SPEAKER_00"]
            chunk_0_speaker_01 = mapping["chunk_0_SPEAKER_01"]
            chunk_1_speaker_01 = mapping["chunk_1_SPEAKER_01"]
            
            # Verify unification worked
            assert chunk_0_speaker_00 == chunk_1_speaker_00  # Same person A
            assert chunk_0_speaker_01 == chunk_1_speaker_01  # Same person B
            assert chunk_0_speaker_00 != chunk_0_speaker_01  # Different people
            
            # Verify global speaker IDs are properly formatted
            assert chunk_0_speaker_00.startswith("SPEAKER_GLOBAL_")
            assert chunk_0_speaker_01.startswith("SPEAKER_GLOBAL_")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
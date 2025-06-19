"""
Test segmentation fallback logic for long audio with single segment
"""

import pytest
from unittest.mock import patch, Mock
from src.services.distributed_transcription_service import DistributedTranscriptionService


class TestSegmentationFallback:
    """Test the new segmentation fallback logic"""
    
    def setup_method(self):
        """Setup test environment"""
        self.service = DistributedTranscriptionService()
    
    @patch('ffmpeg.probe')
    @patch.object(DistributedTranscriptionService, 'split_audio_by_silence')
    @patch.object(DistributedTranscriptionService, 'split_audio_by_time')
    def test_fallback_for_long_audio_single_segment(self, mock_time_split, mock_silence_split, mock_probe):
        """Test fallback to time-based segmentation when silence detection creates only 1 segment for long audio"""
        
        # Mock 23-minute audio (1380 seconds > 3 minutes)
        mock_probe.return_value = {"format": {"duration": "1380.0"}}
        
        # Mock silence-based segmentation returning only 1 segment (failed segmentation)
        mock_silence_split.return_value = [
            {
                "chunk_index": 0,
                "start_time": 0.0,
                "end_time": 1380.0,
                "duration": 1380.0,
                "filename": "silence_chunk_000.wav",
                "segmentation_type": "silence_based"
            }
        ]
        
        # Mock time-based segmentation with 3-minute chunks
        mock_time_split.return_value = [
            {"chunk_index": 0, "start_time": 0.0, "end_time": 180.0, "duration": 180.0, "segmentation_type": "time_based"},
            {"chunk_index": 1, "start_time": 180.0, "end_time": 360.0, "duration": 180.0, "segmentation_type": "time_based"},
            {"chunk_index": 2, "start_time": 360.0, "end_time": 540.0, "duration": 180.0, "segmentation_type": "time_based"},
            {"chunk_index": 3, "start_time": 540.0, "end_time": 720.0, "duration": 180.0, "segmentation_type": "time_based"},
            {"chunk_index": 4, "start_time": 720.0, "end_time": 900.0, "duration": 180.0, "segmentation_type": "time_based"},
            {"chunk_index": 5, "start_time": 900.0, "end_time": 1080.0, "duration": 180.0, "segmentation_type": "time_based"},
            {"chunk_index": 6, "start_time": 1080.0, "end_time": 1260.0, "duration": 180.0, "segmentation_type": "time_based"},
            {"chunk_index": 7, "start_time": 1260.0, "end_time": 1380.0, "duration": 120.0, "segmentation_type": "time_based"}
        ]
        
        # Execute the segmentation strategy
        segments = self.service.choose_segmentation_strategy(
            "test_long_audio.mp3",
            use_intelligent_segmentation=True,
            chunk_duration=60  # Original chunk duration, but fallback uses 180s
        )
        
        # Verify that silence segmentation was tried first
        mock_silence_split.assert_called_once()
        
        # Verify that time-based segmentation was called with 3-minute chunks as fallback
        mock_time_split.assert_called_once_with("test_long_audio.mp3", chunk_duration=180)
        
        # Verify the returned segments are from time-based segmentation
        assert len(segments) == 8  # 1380s / 180s = 7.67 ≈ 8 chunks
        assert segments[0]["segmentation_type"] == "time_based"
        assert segments[0]["duration"] == 180.0  # 3-minute chunks
    
    @patch('ffmpeg.probe')
    @patch.object(DistributedTranscriptionService, 'split_audio_by_silence')
    def test_no_fallback_for_short_audio_single_segment(self, mock_silence_split, mock_probe):
        """Test that fallback is NOT triggered for short audio even with single segment"""
        
        # Mock 2-minute audio (120 seconds < 3 minutes)
        mock_probe.return_value = {"format": {"duration": "120.0"}}
        
        # Mock silence-based segmentation returning only 1 segment
        mock_silence_split.return_value = [
            {
                "chunk_index": 0,
                "start_time": 0.0,
                "end_time": 120.0,
                "duration": 120.0,
                "filename": "silence_chunk_000.wav",
                "segmentation_type": "silence_based"
            }
        ]
        
        # Execute the segmentation strategy
        segments = self.service.choose_segmentation_strategy(
            "test_short_audio.mp3",
            use_intelligent_segmentation=True,
            chunk_duration=60
        )
        
        # Verify that silence segmentation was used and no fallback occurred
        mock_silence_split.assert_called_once()
        
        # Verify the returned segments are from silence-based segmentation (no fallback)
        assert len(segments) == 1
        assert segments[0]["segmentation_type"] == "silence_based"
        assert segments[0]["duration"] == 120.0
    
    @patch('ffmpeg.probe')
    @patch.object(DistributedTranscriptionService, 'split_audio_by_silence')
    def test_no_fallback_for_long_audio_multiple_segments(self, mock_silence_split, mock_probe):
        """Test that fallback is NOT triggered for long audio with multiple segments"""
        
        # Mock 10-minute audio (600 seconds > 3 minutes)
        mock_probe.return_value = {"format": {"duration": "600.0"}}
        
        # Mock silence-based segmentation returning multiple segments (successful segmentation)
        mock_silence_split.return_value = [
            {"chunk_index": 0, "start_time": 0.0, "end_time": 150.0, "duration": 150.0, "segmentation_type": "silence_based"},
            {"chunk_index": 1, "start_time": 150.0, "end_time": 320.0, "duration": 170.0, "segmentation_type": "silence_based"},
            {"chunk_index": 2, "start_time": 320.0, "end_time": 480.0, "duration": 160.0, "segmentation_type": "silence_based"},
            {"chunk_index": 3, "start_time": 480.0, "end_time": 600.0, "duration": 120.0, "segmentation_type": "silence_based"}
        ]
        
        # Execute the segmentation strategy
        segments = self.service.choose_segmentation_strategy(
            "test_multi_segment_audio.mp3",
            use_intelligent_segmentation=True,
            chunk_duration=60
        )
        
        # Verify that silence segmentation was used and no fallback occurred
        mock_silence_split.assert_called_once()
        
        # Verify the returned segments are from silence-based segmentation (no fallback)
        assert len(segments) == 4
        assert all(seg["segmentation_type"] == "silence_based" for seg in segments)
    
    @patch('ffmpeg.probe')
    def test_fallback_threshold_exactly_3_minutes(self, mock_probe):
        """Test the exact threshold behavior at 3 minutes (180 seconds)"""
        
        # Mock exactly 3-minute audio (180 seconds)
        mock_probe.return_value = {"format": {"duration": "180.0"}}
        
        with patch.object(self.service, 'split_audio_by_silence') as mock_silence_split, \
             patch.object(self.service, 'split_audio_by_time') as mock_time_split:
            
            # Mock silence-based segmentation returning only 1 segment
            mock_silence_split.return_value = [
                {"chunk_index": 0, "start_time": 0.0, "end_time": 180.0, "duration": 180.0, "segmentation_type": "silence_based"}
            ]
            
            mock_time_split.return_value = [
                {"chunk_index": 0, "start_time": 0.0, "end_time": 180.0, "duration": 180.0, "segmentation_type": "time_based"}
            ]
            
            # Execute the segmentation strategy
            segments = self.service.choose_segmentation_strategy("test_180s_audio.mp3")
            
            # At exactly 180s, the condition is duration > 180, so no fallback should occur
            mock_silence_split.assert_called_once()
            mock_time_split.assert_not_called()
            
            assert len(segments) == 1
            assert segments[0]["segmentation_type"] == "silence_based"
    
    @patch('ffmpeg.probe')
    def test_fallback_threshold_just_over_3_minutes(self, mock_probe):
        """Test the fallback behavior just over 3 minutes (180.1 seconds)"""
        
        # Mock just over 3-minute audio (180.1 seconds)
        mock_probe.return_value = {"format": {"duration": "180.1"}}
        
        with patch.object(self.service, 'split_audio_by_silence') as mock_silence_split, \
             patch.object(self.service, 'split_audio_by_time') as mock_time_split:
            
            # Mock silence-based segmentation returning only 1 segment
            mock_silence_split.return_value = [
                {"chunk_index": 0, "start_time": 0.0, "end_time": 180.1, "duration": 180.1, "segmentation_type": "silence_based"}
            ]
            
            mock_time_split.return_value = [
                {"chunk_index": 0, "start_time": 0.0, "end_time": 180.1, "duration": 180.1, "segmentation_type": "time_based"}
            ]
            
            # Execute the segmentation strategy
            segments = self.service.choose_segmentation_strategy("test_180_1s_audio.mp3")
            
            # Just over 180s should trigger fallback
            mock_silence_split.assert_called_once()
            mock_time_split.assert_called_once_with("test_180_1s_audio.mp3", chunk_duration=180)
            
            assert len(segments) == 1
            assert segments[0]["segmentation_type"] == "time_based"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
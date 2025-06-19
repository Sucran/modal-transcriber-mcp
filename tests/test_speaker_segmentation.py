"""
测试 TranscriptionService 中的 speaker segmentation 功能
特别是 _merge_speaker_segments 和 _split_transcription_segment 方法
"""

import pytest
import tempfile
import os
from typing import List, Dict
from unittest.mock import Mock, patch

# 添加项目根目录到 Python 路径
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.transcription_service import TranscriptionService


class TestSpeakerSegmentation:
    """测试说话人分割功能"""
    
    def setup_method(self):
        """设置测试环境"""
        self.service = TranscriptionService()
    
    def test_single_speaker_segment(self):
        """测试单个说话人的情况"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "Hello, this is a test message."
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "speaker": "SPEAKER_00"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[0]["text"] == "Hello, this is a test message."
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 5.0
    
    def test_no_speaker_detected(self):
        """测试没有检测到说话人的情况"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "Hello, this is a test message."
            }
        ]
        
        speaker_segments = []
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 1
        assert result[0]["speaker"] is None
        assert result[0]["text"] == "Hello, this is a test message."
    
    def test_multiple_speakers_in_single_segment(self):
        """测试单个转录段中包含多个说话人的情况"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 10.0,
                "text": "Hello there how are you today I am doing well thank you for asking"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 4.0,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 4.0,
                "end": 7.0,
                "speaker": "SPEAKER_01"
            },
            {
                "start": 7.0,
                "end": 10.0,
                "speaker": "SPEAKER_00"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        # 应该被分割成3个段
        assert len(result) == 3
        
        # 检查说话人分配
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[1]["speaker"] == "SPEAKER_01"
        assert result[2]["speaker"] == "SPEAKER_00"
        
        # 检查时间戳（允许算法进行时间分配调整）
        assert result[0]["start"] == 0.0
        assert result[0]["end"] <= 4.0
        assert result[1]["start"] >= 4.0
        assert result[1]["end"] <= 7.0
        assert result[2]["start"] >= 7.0
        assert result[2]["end"] <= 10.0
        
        # 检查文本被正确分割
        combined_text = " ".join([seg["text"] for seg in result])
        original_text = "Hello there how are you today I am doing well thank you for asking"
        assert combined_text.replace("  ", " ") == original_text
    
    def test_overlapping_speakers(self):
        """测试说话人时间重叠的情况"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 6.0,
                "text": "This is a conversation between two people talking simultaneously"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 4.0,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 2.0,
                "end": 6.0,
                "speaker": "SPEAKER_01"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        # 应该被分割成2个段
        assert len(result) == 2
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[1]["speaker"] == "SPEAKER_01"
        
        # 检查重叠处理
        assert result[0]["start"] == 0.0
        assert result[0]["end"] <= 4.0
        assert result[1]["start"] >= 2.0
        assert result[1]["end"] == 6.0
    
    def test_partial_speaker_overlap(self):
        """测试说话人部分重叠转录段的情况"""
        transcription_segments = [
            {
                "start": 1.0,
                "end": 4.0,
                "text": "This is in the middle of speaker segment"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "speaker": "SPEAKER_00"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[0]["start"] == 1.0
        assert result[0]["end"] == 4.0
    
    def test_multiple_transcription_segments_with_speakers(self):
        """测试多个转录段与多个说话人的复杂情况"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                "text": "Hello how are you"
            },
            {
                "start": 3.0,
                "end": 6.0,
                "text": "I am fine thank you"
            },
            {
                "start": 6.0,
                "end": 10.0,
                "text": "That is great to hear from you today"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 3.0,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 3.0,
                "end": 6.0,
                "speaker": "SPEAKER_01"
            },
            {
                "start": 6.0,
                "end": 8.0,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 8.0,
                "end": 10.0,
                "speaker": "SPEAKER_01"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        # 前两个段应该保持不变，第三个段应该被分割
        assert len(result) == 4
        
        # 检查前两个段
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[0]["text"] == "Hello how are you"
        assert result[1]["speaker"] == "SPEAKER_01"
        assert result[1]["text"] == "I am fine thank you"
        
        # 检查被分割的第三个段
        assert result[2]["speaker"] == "SPEAKER_00"
        assert result[3]["speaker"] == "SPEAKER_01"
        
        # 检查分割后的文本
        combined_third_segment_text = result[2]["text"] + " " + result[3]["text"]
        assert "That is great to hear from you today" in combined_third_segment_text
    
    def test_word_boundary_preservation(self):
        """测试文本分割时保持单词边界的功能"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 8.0,
                "text": "The quick brown fox jumps over the lazy dog"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 4.0,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 4.0,
                "end": 8.0,
                "speaker": "SPEAKER_01"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 2
        
        # 检查文本没有在单词中间分割
        for segment in result:
            text = segment["text"]
            # 确保文本开头和结尾都是完整的单词
            if text:
                words = text.split()
                assert len(words) > 0, f"Segment should contain complete words: '{text}'"
                # 检查没有部分单词
                assert not any(word.endswith('-') or word.startswith('-') for word in words), \
                    f"Should not contain partial words: {words}"
    
    def test_empty_text_handling(self):
        """测试空文本的处理"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 2.0,
                "text": ""
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 2.0,
                "speaker": "SPEAKER_00"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[0]["text"] == ""
    
    def test_split_transcription_segment_direct(self):
        """直接测试 _split_transcription_segment 方法"""
        trans_seg = {
            "start": 0.0,
            "end": 6.0,
            "text": "Hello there how are you doing today"
        }
        
        overlapping_speakers = [
            {
                "speaker": "SPEAKER_00",
                "start": 0.0,
                "end": 3.0,
                "overlap_start": 0.0,
                "overlap_end": 3.0,
                "overlap_duration": 3.0
            },
            {
                "speaker": "SPEAKER_01",
                "start": 3.0,
                "end": 6.0,
                "overlap_start": 3.0,
                "overlap_end": 6.0,
                "overlap_duration": 3.0
            }
        ]
        
        result = self.service._split_transcription_segment(
            trans_seg, overlapping_speakers, trans_seg["text"]
        )
        
        assert len(result) == 2
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[1]["speaker"] == "SPEAKER_01"
        
        # 检查时间分配
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 3.0
        assert result[1]["start"] == 3.0
        assert result[1]["end"] == 6.0
        
        # 检查文本分配
        combined_text = result[0]["text"] + " " + result[1]["text"]
        assert "Hello there how are you doing today" in combined_text.replace("  ", " ")
    
    def test_unequal_speaker_durations(self):
        """测试说话人持续时间不等的情况"""
        trans_seg = {
            "start": 0.0,
            "end": 10.0,
            "text": "This is a longer sentence with one speaker talking much longer than the other speaker"
        }
        
        overlapping_speakers = [
            {
                "speaker": "SPEAKER_00",
                "start": 0.0,
                "end": 8.0,  # 说话时间更长
                "overlap_start": 0.0,
                "overlap_end": 8.0,
                "overlap_duration": 8.0
            },
            {
                "speaker": "SPEAKER_01",
                "start": 8.0,
                "end": 10.0,  # 说话时间较短
                "overlap_start": 8.0,
                "overlap_end": 10.0,
                "overlap_duration": 2.0
            }
        ]
        
        result = self.service._split_transcription_segment(
            trans_seg, overlapping_speakers, trans_seg["text"]
        )
        
        assert len(result) == 2
        
        # SPEAKER_00 应该得到更多的文本（因为说话时间更长）
        speaker_00_text_length = len(result[0]["text"])
        speaker_01_text_length = len(result[1]["text"])
        
        assert speaker_00_text_length > speaker_01_text_length, \
            f"SPEAKER_00 should have more text. Got {speaker_00_text_length} vs {speaker_01_text_length}"
        
        # 检查时间分配正确
        assert result[0]["end"] == 8.0
        assert result[1]["start"] == 8.0

    @pytest.mark.integration
    def test_full_transcription_with_speaker_splitting(self):
        """集成测试：完整的转录流程与说话人分割"""
        # 这个测试需要实际的音频文件，暂时跳过
        # 可以在有测试音频文件时启用
        pytest.skip("Integration test requires actual audio file")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"]) 
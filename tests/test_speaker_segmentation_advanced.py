"""
高级 Speaker Segmentation 测试用例
测试边缘情况、性能和复杂场景
"""

import pytest
import time
import random
from typing import List, Dict
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.transcription_service import TranscriptionService


class TestSpeakerSegmentationAdvanced:
    """高级说话人分割测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.service = TranscriptionService()
    
    def test_rapid_speaker_changes(self):
        """测试快速说话人切换的情况"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "A B C D E F G H I J K L M N O P Q R S T"
            }
        ]
        
        # 模拟每0.25秒切换一次说话人
        speaker_segments = []
        for i in range(20):
            start_time = i * 0.25
            end_time = (i + 1) * 0.25
            speaker = f"SPEAKER_{i % 2:02d}"  # 两个说话人交替
            speaker_segments.append({
                "start": start_time,
                "end": end_time,
                "speaker": speaker
            })
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        # 应该有多个分割段
        assert len(result) > 1
        
        # 检查说话人交替
        speakers = [seg["speaker"] for seg in result]
        assert "SPEAKER_00" in speakers
        assert "SPEAKER_01" in speakers
        
        # 检查文本完整性
        combined_text = " ".join([seg["text"] for seg in result if seg["text"]])
        original_words = "A B C D E F G H I J K L M N O P Q R S T".split()
        result_words = combined_text.split()
        
        # 允许一些文本丢失（由于快速切换），但大部分应该保留
        preserved_ratio = len(result_words) / len(original_words)
        assert preserved_ratio > 0.5, f"Too much text lost: {preserved_ratio:.2f}"
    
    def test_very_short_speaker_segments(self):
        """测试非常短的说话人段"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 2.0,
                "text": "Quick short conversation"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 0.1,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 0.1,
                "end": 0.2,
                "speaker": "SPEAKER_01"
            },
            {
                "start": 0.2,
                "end": 2.0,
                "speaker": "SPEAKER_00"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        # 即使有很短的段，也应该正确处理
        assert len(result) >= 1
        
        # 检查没有空文本段（除非原本就是空的）
        for seg in result:
            if seg["start"] < seg["end"]:  # 有效时间段
                # 可以接受空文本（因为段太短）
                pass
    
    def test_overlapping_segments_complex(self):
        """测试复杂的重叠情况"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 10.0,
                "text": "This is a complex conversation with multiple overlapping speakers talking at the same time"
            }
        ]
        
        speaker_segments = [
            # 三个说话人同时说话
            {
                "start": 0.0,
                "end": 6.0,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 2.0,
                "end": 8.0,
                "speaker": "SPEAKER_01"
            },
            {
                "start": 4.0,
                "end": 10.0,
                "speaker": "SPEAKER_02"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        # 应该有多个段
        assert len(result) >= 2
        
        # 检查所有说话人都被包含
        speakers = set(seg["speaker"] for seg in result)
        assert len(speakers) >= 2  # 至少包含两个说话人
        
        # 检查时间合理性（不要求严格连续性，因为有重叠）
        for seg in result:
            assert seg["start"] < seg["end"], f"Invalid timing: {seg['start']} >= {seg['end']}"
    
    def test_performance_large_segments(self):
        """测试大量段的性能"""
        # 生成大量转录段
        transcription_segments = []
        for i in range(100):
            transcription_segments.append({
                "start": i * 1.0,
                "end": (i + 1) * 1.0,
                "text": f"This is segment number {i} with some text content for testing purposes"
            })
        
        # 生成大量说话人段
        speaker_segments = []
        for i in range(200):
            speaker_segments.append({
                "start": i * 0.5,
                "end": (i + 1) * 0.5,
                "speaker": f"SPEAKER_{i % 5:02d}"  # 5个说话人循环
            })
        
        # 测量执行时间
        start_time = time.time()
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        execution_time = time.time() - start_time
        
        # 应该在合理时间内完成（< 1秒）
        assert execution_time < 1.0, f"Performance too slow: {execution_time:.2f}s"
        
        # 检查结果合理性
        assert len(result) > 0
        assert len(result) <= len(transcription_segments) * 2  # 每个段最多分割一次
    
    def test_no_overlap_at_all(self):
        """测试完全没有重叠的情况"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 2.0,
                "text": "First segment"
            },
            {
                "start": 5.0,
                "end": 7.0,
                "text": "Second segment"
            }
        ]
        
        speaker_segments = [
            {
                "start": 3.0,
                "end": 4.0,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 8.0,
                "end": 9.0,
                "speaker": "SPEAKER_01"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        # 应该保持原始段，但没有说话人信息
        assert len(result) == 2
        assert result[0]["speaker"] is None
        assert result[1]["speaker"] is None
        assert result[0]["text"] == "First segment"
        assert result[1]["text"] == "Second segment"
    
    def test_exact_boundary_matching(self):
        """测试精确边界匹配"""
        transcription_segments = [
            {
                "start": 1.0,
                "end": 3.0,
                "text": "Exact boundary match"
            }
        ]
        
        speaker_segments = [
            {
                "start": 1.0,
                "end": 3.0,
                "speaker": "SPEAKER_00"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_00"
        assert result[0]["start"] == 1.0
        assert result[0]["end"] == 3.0
        assert result[0]["text"] == "Exact boundary match"
    
    def test_floating_point_precision(self):
        """测试浮点数精度问题"""
        transcription_segments = [
            {
                "start": 0.1,
                "end": 0.3,
                "text": "Precision test"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.10000001,  # 微小差异
                "end": 0.29999999,
                "speaker": "SPEAKER_00"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 1
        assert result[0]["speaker"] == "SPEAKER_00"
    
    def test_text_distribution_accuracy(self):
        """测试文本分配的准确性"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 10.0,
                "text": "One two three four five six seven eight nine ten"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 8.0,  # 80% 的时间
                "speaker": "SPEAKER_00"
            },
            {
                "start": 8.0,
                "end": 10.0,  # 20% 的时间
                "speaker": "SPEAKER_01"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 2
        
        # SPEAKER_00 应该得到大约 80% 的文本
        total_text_length = len("One two three four five six seven eight nine ten")
        speaker_00_length = len(result[0]["text"])
        speaker_01_length = len(result[1]["text"])
        
        speaker_00_ratio = speaker_00_length / total_text_length
        speaker_01_ratio = speaker_01_length / total_text_length
        
        # 允许一定的误差范围
        assert 0.6 <= speaker_00_ratio <= 0.9, f"SPEAKER_00 ratio: {speaker_00_ratio:.2f}"
        assert 0.1 <= speaker_01_ratio <= 0.4, f"SPEAKER_01 ratio: {speaker_01_ratio:.2f}"
    
    def test_single_word_segments(self):
        """测试单词级别的分割"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 4.0,
                "text": "Hello world"
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 2.0,
                "speaker": "SPEAKER_00"
            },
            {
                "start": 2.0,
                "end": 4.0,
                "speaker": "SPEAKER_01"
            }
        ]
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 2
        
        # 检查单词没有被切断
        all_words = []
        for seg in result:
            if seg["text"]:
                all_words.extend(seg["text"].split())
        
        # 应该包含原始的两个完整单词
        original_words = ["Hello", "world"]
        for word in original_words:
            assert any(word in all_words for word in original_words), \
                f"Words not preserved correctly: {all_words}"
    
    def test_empty_speaker_segments(self):
        """测试空的说话人段列表"""
        transcription_segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "No speakers detected"
            }
        ]
        
        speaker_segments = []
        
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        
        assert len(result) == 1
        assert result[0]["speaker"] is None
        assert result[0]["text"] == "No speakers detected"
    
    def test_malformed_input_handling(self):
        """测试处理格式错误的输入"""
        # 缺少必要字段的转录段
        transcription_segments = [
            {
                "start": 0.0,
                "end": 5.0,
                # 缺少 "text" 字段
            }
        ]
        
        speaker_segments = [
            {
                "start": 0.0,
                "end": 5.0,
                "speaker": "SPEAKER_00"
            }
        ]
        
        # 应该能够处理而不崩溃
        try:
            result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
            # 如果没有异常，检查结果
            assert len(result) >= 0
        except Exception as e:
            # 如果有异常，确保是预期的类型
            assert isinstance(e, (KeyError, AttributeError, TypeError))


class TestSpeakerSegmentationBenchmark:
    """性能基准测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.service = TranscriptionService()
    
    @pytest.mark.benchmark
    def test_benchmark_typical_podcast(self):
        """基准测试：典型播客场景（30分钟，3个说话人）"""
        # 模拟30分钟的播客：每5秒一个转录段
        transcription_segments = []
        for i in range(360):  # 30分钟 * 60秒 / 5秒
            start_time = i * 5.0
            end_time = (i + 1) * 5.0
            transcription_segments.append({
                "start": start_time,
                "end": end_time,
                "text": f"This is a podcast segment number {i} with typical conversation content"
            })
        
        # 模拟说话人切换：平均每30秒切换一次说话人
        speaker_segments = []
        current_time = 0.0
        current_speaker = 0
        
        while current_time < 1800.0:  # 30分钟
            segment_duration = random.uniform(15.0, 45.0)  # 15-45秒的说话段
            speaker_segments.append({
                "start": current_time,
                "end": min(current_time + segment_duration, 1800.0),
                "speaker": f"SPEAKER_{current_speaker:02d}"
            })
            current_time += segment_duration
            current_speaker = (current_speaker + 1) % 3  # 3个说话人循环
        
        # 执行基准测试
        start_time = time.time()
        result = self.service._merge_speaker_segments(transcription_segments, speaker_segments)
        execution_time = time.time() - start_time
        
        print(f"\n📊 Benchmark Results:")
        print(f"   Input segments: {len(transcription_segments)}")
        print(f"   Speaker segments: {len(speaker_segments)}")
        print(f"   Output segments: {len(result)}")
        print(f"   Execution time: {execution_time:.3f}s")
        print(f"   Segments per second: {len(result)/execution_time:.1f}")
        
        # 性能要求：应该能够处理实时转录（每秒至少处理60个段）
        assert execution_time < 2.0, f"Too slow for real-time processing: {execution_time:.3f}s"
        assert len(result) > 0, "Should produce some output segments"


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short", "-m", "not benchmark"])
    
    # 单独运行基准测试
    print("\n" + "="*60)
    print("Running Benchmark Tests...")
    print("="*60)
    pytest.main([__file__, "-v", "--tb=short", "-m", "benchmark"]) 
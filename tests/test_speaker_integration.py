"""
Speaker Segmentation 集成测试
验证完整的转录和说话人分割流程
"""

import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.transcription_service import TranscriptionService


def test_speaker_segmentation_integration():
    """测试完整的说话人分割集成流程"""
    service = TranscriptionService()
    
    # 模拟 Whisper 转录的结果
    transcription_segments = [
        {
            "start": 0.0,
            "end": 3.0,
            "text": "Hello, this is Alice speaking."
        },
        {
            "start": 3.0,
            "end": 8.0,
            "text": "Hi Alice, this is Bob responding to your message."
        },
        {
            "start": 8.0,
            "end": 12.0,
            "text": "Great to hear from you Bob, how are you today?"
        },
        {
            "start": 12.0,
            "end": 15.0,
            "text": "I'm doing well, thank you for asking Alice."
        }
    ]
    
    # 模拟说话人分离的结果
    speaker_segments = [
        {"start": 0.0, "end": 3.0, "speaker": "SPEAKER_00"},  # Alice
        {"start": 3.0, "end": 8.0, "speaker": "SPEAKER_01"},  # Bob
        {"start": 8.0, "end": 12.0, "speaker": "SPEAKER_00"}, # Alice
        {"start": 12.0, "end": 15.0, "speaker": "SPEAKER_01"} # Bob
    ]
    
    # 执行说话人分割
    result = service._merge_speaker_segments(transcription_segments, speaker_segments)
    
    # 验证结果
    assert len(result) == 4, f"Expected 4 segments, got {len(result)}"
    
    # 验证说话人分配
    expected_speakers = ["SPEAKER_00", "SPEAKER_01", "SPEAKER_00", "SPEAKER_01"]
    actual_speakers = [seg["speaker"] for seg in result]
    assert actual_speakers == expected_speakers, f"Speaker assignment mismatch: {actual_speakers} != {expected_speakers}"
    
    # 验证文本保持完整
    expected_texts = [
        "Hello, this is Alice speaking.",
        "Hi Alice, this is Bob responding to your message.",
        "Great to hear from you Bob, how are you today?",
        "I'm doing well, thank you for asking Alice."
    ]
    actual_texts = [seg["text"] for seg in result]
    assert actual_texts == expected_texts, f"Text mismatch: {actual_texts} != {expected_texts}"
    
    # 验证时间戳
    for i, seg in enumerate(result):
        assert seg["start"] == transcription_segments[i]["start"]
        assert seg["end"] == transcription_segments[i]["end"]
    
    print("✅ Speaker segmentation integration test passed!")
    print(f"   - Processed {len(transcription_segments)} transcription segments")
    print(f"   - Applied {len(speaker_segments)} speaker assignments")
    print(f"   - Generated {len(result)} final segments")
    
    # 打印结果示例
    print("\n📝 Sample Results:")
    for i, seg in enumerate(result):
        speaker_name = "Alice" if seg["speaker"] == "SPEAKER_00" else "Bob"
        print(f"   {i+1}. [{seg['start']:.1f}s-{seg['end']:.1f}s] {speaker_name}: \"{seg['text']}\"")


def test_complex_conversation_splitting():
    """测试复杂对话中的分割情况"""
    service = TranscriptionService()
    
    # 模拟一个长段对话，其中包含多个说话人
    transcription_segments = [
        {
            "start": 0.0,
            "end": 10.0,
            "text": "Welcome to our podcast today we have a special guest joining us to discuss the latest developments in AI technology and its impact on society"
        }
    ]
    
    # 三个说话人在这个段中依次说话
    speaker_segments = [
        {"start": 0.0, "end": 3.0, "speaker": "HOST"},      # 主持人开场
        {"start": 3.0, "end": 7.0, "speaker": "GUEST"},     # 嘉宾介绍
        {"start": 7.0, "end": 10.0, "speaker": "CO_HOST"}   # 联合主持人
    ]
    
    result = service._merge_speaker_segments(transcription_segments, speaker_segments)
    
    # 验证分割结果
    assert len(result) == 3, f"Expected 3 segments after splitting, got {len(result)}"
    
    # 验证说话人分配
    speakers = [seg["speaker"] for seg in result]
    assert speakers == ["HOST", "GUEST", "CO_HOST"]
    
    # 验证所有文本都被保留
    combined_text = " ".join([seg["text"] for seg in result if seg["text"]])
    original_text = transcription_segments[0]["text"]
    
    # 允许一些小的差异（由于单词边界调整）
    combined_words = set(combined_text.lower().split())
    original_words = set(original_text.lower().split())
    
    # 大部分单词应该被保留
    preserved_ratio = len(combined_words.intersection(original_words)) / len(original_words)
    assert preserved_ratio > 0.8, f"Too many words lost: {preserved_ratio:.2f}"
    
    print("✅ Complex conversation splitting test passed!")
    print(f"   - Split 1 long segment into {len(result)} speaker-specific segments")
    print(f"   - Word preservation ratio: {preserved_ratio:.2%}")
    
    # 打印分割结果
    print("\n📝 Splitting Results:")
    for seg in result:
        print(f"   [{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['speaker']}: \"{seg['text'][:50]}{'...' if len(seg['text']) > 50 else ''}\"")


if __name__ == "__main__":
    test_speaker_segmentation_integration()
    print()
    test_complex_conversation_splitting()
    print("\n🎉 All integration tests passed!") 
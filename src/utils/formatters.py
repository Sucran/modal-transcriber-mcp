"""
Formatting utilities for audio processing outputs
"""

from typing import List, Dict, Any
from ..interfaces.transcriber import TranscriptionSegment


class TimestampFormatter:
    """Utility for formatting timestamps"""
    
    @staticmethod
    def format_srt_timestamp(seconds: float) -> str:
        """Format timestamp for SRT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def format_readable_timestamp(seconds: float) -> str:
        """Format timestamp for human reading"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


class SRTFormatter:
    """Utility for SRT subtitle formatting"""
    
    @staticmethod
    def format_segments(
        segments: List[TranscriptionSegment],
        include_speakers: bool = False
    ) -> str:
        """Format transcription segments as SRT"""
        srt_content = ""
        srt_index = 1
        
        for segment in segments:
            if not segment.text.strip():
                continue
                
            start_time = TimestampFormatter.format_srt_timestamp(segment.start)
            end_time = TimestampFormatter.format_srt_timestamp(segment.end)
            
            # Format text with optional speaker information
            if include_speakers and segment.speaker:
                formatted_text = f"{segment.speaker}: {segment.text.strip()}"
            else:
                formatted_text = segment.text.strip()
            
            srt_content += f"{srt_index}\n{start_time} --> {end_time}\n{formatted_text}\n\n"
            srt_index += 1
        
        return srt_content


class TextFormatter:
    """Utility for plain text formatting"""
    
    @staticmethod
    def format_segments(
        segments: List[TranscriptionSegment],
        include_timestamps: bool = False,
        include_speakers: bool = False
    ) -> str:
        """Format transcription segments as plain text"""
        lines = []
        
        for segment in segments:
            if not segment.text.strip():
                continue
            
            parts = []
            
            if include_timestamps:
                timestamp = TimestampFormatter.format_readable_timestamp(segment.start)
                parts.append(f"[{timestamp}]")
            
            if include_speakers and segment.speaker:
                parts.append(f"{segment.speaker}:")
            
            parts.append(segment.text.strip())
            
            lines.append(" ".join(parts))
        
        return "\n".join(lines)
    
    @staticmethod
    def format_continuous_text(segments: List[TranscriptionSegment]) -> str:
        """Format segments as continuous text without breaks"""
        texts = [segment.text.strip() for segment in segments if segment.text.strip()]
        return " ".join(texts)


# ==================== Legacy compatibility functions ====================

def generate_srt_format(segments: List[Dict[str, Any]], include_speakers: bool = False) -> str:
    """
    Legacy function for generating SRT format from segment dictionaries
    
    Args:
        segments: List of segment dictionaries with 'start', 'end', 'text', and optional 'speaker'
        include_speakers: Whether to include speaker information
        
    Returns:
        SRT formatted string
    """
    srt_content = ""
    srt_index = 1
    
    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue
            
        start_time = format_timestamp(segment.get("start", 0))
        end_time = format_timestamp(segment.get("end", 0))
        
        # Format text with optional speaker information
        if include_speakers and segment.get("speaker"):
            formatted_text = f"{segment['speaker']}: {text}"
        else:
            formatted_text = text
        
        srt_content += f"{srt_index}\n{start_time} --> {end_time}\n{formatted_text}\n\n"
        srt_index += 1
    
    return srt_content


def format_timestamp(seconds: float) -> str:
    """
    Legacy function for formatting timestamps
    
    Args:
        seconds: Time in seconds
        
    Returns:
        SRT formatted timestamp
    """
    return TimestampFormatter.format_srt_timestamp(seconds) 
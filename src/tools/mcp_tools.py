"""
MCP Tools using the new service architecture
"""

from typing import Dict, Any

from .transcription_tools import transcribe_audio_file_tool
from .download_tools import (
    download_apple_podcast_tool,
    download_xyz_podcast_tool,
    get_mp3_files_tool,
    get_file_info_tool,
    read_text_file_segments_tool
)


# ==================== Transcription Tools ====================

async def transcribe_audio_file(
    audio_file_path: str,
    model_size: str = "turbo",
    language: str = None,
    output_format: str = "srt",
    enable_speaker_diarization: bool = False
) -> Dict[str, Any]:
    """
    Transcribe audio files to text using Whisper model with new service architecture
    
    Args:
        audio_file_path: Complete path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large, turbo)
        language: Audio language code (e.g. "zh" for Chinese, "en" for English)
        output_format: Output format (srt, txt, json)
        enable_speaker_diarization: Whether to enable speaker identification
    
    Returns:
        Transcription result dictionary with file paths and metadata
    """
    return await transcribe_audio_file_tool(
        audio_file_path=audio_file_path,
        model_size=model_size,
        language=language,
        output_format=output_format,
        enable_speaker_diarization=enable_speaker_diarization
    )


# ==================== Download Tools ====================

async def download_apple_podcast(url: str) -> Dict[str, Any]:
    """
    Download Apple Podcast audio files using new service architecture
    
    Args:
        url: Complete URL of Apple Podcast page
    
    Returns:
        Download result dictionary with file path and metadata
    """
    return await download_apple_podcast_tool(url)


async def download_xyz_podcast(url: str) -> Dict[str, Any]:
    """
    Download XiaoYuZhou podcast audio files using new service architecture
    
    Args:
        url: Complete URL of XiaoYuZhou podcast page
    
    Returns:
        Download result dictionary with file path and metadata
    """
    return await download_xyz_podcast_tool(url)


# ==================== File Management Tools ====================

async def get_mp3_files(directory: str) -> Dict[str, Any]:
    """
    Scan directory to get detailed information list of all MP3 audio files
    
    Args:
        directory: Absolute or relative path of directory to scan
    
    Returns:
        MP3 file information dictionary with detailed file list
    """
    return await get_mp3_files_tool(directory)


async def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get basic file information including size, modification time, etc.
    
    Args:
        file_path: File path to query
    
    Returns:
        File information dictionary with detailed metadata
    """
    return await get_file_info_tool(file_path)


async def read_text_file_segments(
    file_path: str,
    chunk_size: int = 65536,
    start_position: int = 0
) -> Dict[str, Any]:
    """
    Read text file content in segments with intelligent boundary detection
    
    Args:
        file_path: Path to file to read (supports TXT, SRT and other text files)
        chunk_size: Byte size to read each time (default 64KB)
        start_position: Starting position to read from (byte offset, default 0)
    
    Returns:
        Read result dictionary with content and metadata
    """
    return await read_text_file_segments_tool(
        file_path=file_path,
        chunk_size=chunk_size,
        start_position=start_position
    )
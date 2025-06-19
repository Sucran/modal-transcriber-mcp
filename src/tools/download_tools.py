"""
Download tools using local service architecture
Updated to use PodcastDownloadService for local execution only
"""

import asyncio
import os
import json
import time
from pathlib import Path
from typing import Dict, Any

from ..services import PodcastDownloadService, FileManagementService
from ..models.services import PodcastDownloadRequest


# Global service instances for reuse
_podcast_download_service = None
_file_management_service = None


def get_podcast_download_service() -> PodcastDownloadService:
    """Get or create global PodcastDownloadService instance for local downloads"""
    global _podcast_download_service
    if _podcast_download_service is None:
        # Use storage config for download folder
        _podcast_download_service = PodcastDownloadService()  # Will use storage config defaults
    return _podcast_download_service


def get_file_management_service() -> FileManagementService:
    """Get or create global FileManagementService instance"""
    global _file_management_service
    if _file_management_service is None:
        _file_management_service = FileManagementService()
    return _file_management_service


async def download_apple_podcast_tool(url: str) -> Dict[str, Any]:
    """
    Download Apple Podcast audio files and save to specified directory (LOCAL EXECUTION).
    
    Args:
        url: Complete URL of Apple Podcast page
    
    Returns:
        Download result dictionary containing the following key fields:
            - "status" (str): Download status, "success" or "failed"
            - "original_url" (str): Input original podcast URL
            - "audio_file_path" (str|None): Complete MP3 file path when successful, None when failed
            - "error_message" (str): Only exists when failed, contains specific error description
    """
    try:
        print(f"🏠 Downloading Apple Podcast locally: {url}")
        service = get_podcast_download_service()
        
        # Use local download service
        result = await service.download_podcast(
            url=url,
            output_folder="downloads",
            convert_to_mp3=True,
            keep_original=False
        )
        
        if result.success:
            return {
                "status": "success",
                "original_url": url,
                "audio_file_path": result.file_path,
                "podcast_info": {
                    "title": result.podcast_info.title if result.podcast_info else "Unknown",
                    "platform": "Apple Podcasts"
                }
            }
        else:
            return {
                "status": "failed",
                "original_url": url,
                "audio_file_path": None,
                "error_message": result.error_message
            }
        
    except Exception as e:
        return {
            "status": "failed",
            "original_url": url,
            "audio_file_path": None,
            "error_message": f"Local download tool error: {str(e)}"
        }


async def download_xyz_podcast_tool(url: str) -> Dict[str, Any]:
    """
    Download XiaoYuZhou podcast audio files and save to specified directory (LOCAL EXECUTION).
    
    Args:
        url: Complete URL of XiaoYuZhou podcast page, format: https://www.xiaoyuzhoufm.com/episode/xxxxx
    
    Returns:
        Download result dictionary containing the following key fields:
            - "status" (str): Download status, "success" or "failed"
            - "original_url" (str): Input original podcast URL
            - "audio_file_path" (str|None): Complete MP3 file path when successful, None when failed
            - "error_message" (str): Only exists when failed, contains specific error description
    """
    try:
        print(f"🏠 Downloading XiaoYuZhou Podcast locally: {url}")
        service = get_podcast_download_service()
        
        # Use local download service
        result = await service.download_podcast(
            url=url,
            output_folder="downloads",
            convert_to_mp3=True,
            keep_original=False
        )
        
        if result.success:
            return {
                "status": "success",
                "original_url": url,
                "audio_file_path": result.file_path,
                "podcast_info": {
                    "title": result.podcast_info.title if result.podcast_info else "Unknown",
                    "platform": "XiaoYuZhou"
                }
            }
        else:
            return {
                "status": "failed",
                "original_url": url,
                "audio_file_path": None,
                "error_message": result.error_message
            }
        
    except Exception as e:
        return {
            "status": "failed",
            "original_url": url,
            "audio_file_path": None,
            "error_message": f"Local download tool error: {str(e)}"
        }


async def get_mp3_files_tool(directory: str) -> Dict[str, Any]:
    """
    Scan specified directory to get detailed information list of all MP3 audio files (LOCAL EXECUTION).
    
    Args:
        directory: Absolute or relative path of directory to scan
    
    Returns:
        Dictionary containing MP3 file information
    """
    try:
        service = get_file_management_service()
        return await service.scan_mp3_files(directory)
        
    except Exception as e:
        return {
            "total_files": 0,
            "scanned_directory": directory,
            "file_list": [],
            "error_message": f"Local file scan tool error: {str(e)}"
        }


async def get_file_info_tool(file_path: str) -> Dict[str, Any]:
    """
    Get basic file information including size, modification time, etc (LOCAL EXECUTION).
    
    Args:
        file_path: File path to query
    
    Returns:
        File information dictionary
    """
    try:
        service = get_file_management_service()
        return await service.get_file_info(file_path)
        
    except Exception as e:
        return {
            "status": "failed",
            "file_path": file_path,
            "file_exists": False,
            "error_message": f"Local file info tool error: {str(e)}"
        }


async def read_text_file_segments_tool(
    file_path: str,
    chunk_size: int = 65536,
    start_position: int = 0
) -> Dict[str, Any]:
    """
    Read text file content in segments, intelligently handling text boundaries (LOCAL EXECUTION).
    
    Args:
        file_path: Path to file to read (supports TXT, SRT and other text files)
        chunk_size: Byte size to read each time, default 64KB
        start_position: Starting position to read from (byte offset), default 0
    
    Returns:
        Read result dictionary
    """
    try:
        service = get_file_management_service()
        return await service.read_text_file_segments(
            file_path=file_path,
            chunk_size=chunk_size,
            start_position=start_position
        )
        
    except Exception as e:
        return {
            "status": "failed",
            "file_path": file_path,
            "error_message": f"Local file read tool error: {str(e)}"
        } 
"""
Storage Management Tools
Provides tools for managing download and transcript storage
"""

from typing import Dict, Any, List
from pathlib import Path

from ..utils.storage_config import get_storage_config


async def get_storage_info_tool() -> Dict[str, Any]:
    """
    Get comprehensive storage information including directory sizes and file counts
    
    Returns:
        Storage information dictionary
    """
    try:
        storage_config = get_storage_config()
        storage_info = storage_config.get_storage_info()
        
        print(f"📊 Storage Information:")
        print(f"   Downloads: {storage_info['downloads_dir']}")
        print(f"   Transcripts: {storage_info['transcripts_dir']}")
        print(f"   Cache: {storage_info['cache_dir']}")
        
        return {"status": "success", **storage_info}
        
    except Exception as e:
        return {"status": "failed", "error_message": str(e)}


async def list_audio_files_tool() -> Dict[str, Any]:
    """
    List all audio files in the downloads directory
    
    Returns:
        List of audio files with metadata
    """
    try:
        storage_config = get_storage_config()
        audio_files = storage_config.get_audio_files()
        
        file_list = []
        total_size = 0
        
        for audio_file in audio_files:
            file_size = audio_file.stat().st_size
            total_size += file_size
            
            # Check for corresponding transcript files
            transcript_files = storage_config.get_transcript_files(audio_file.name)
            has_transcripts = {
                'txt': transcript_files['txt'].exists(),
                'srt': transcript_files['srt'].exists(),
                'json': transcript_files['json'].exists()
            }
            
            file_info = {
                "filename": audio_file.name,
                "path": str(audio_file),
                "size_mb": round(file_size / (1024 * 1024), 2),
                "modified": audio_file.stat().st_mtime,
                "has_transcripts": has_transcripts,
                "transcript_count": sum(has_transcripts.values())
            }
            file_list.append(file_info)
        
        print(f"📁 Found {len(audio_files)} audio files ({round(total_size / (1024 * 1024), 2)} MB total)")
        
        return {
            "status": "success",
            "audio_files_count": len(audio_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "downloads_directory": str(storage_config.downloads_dir),
            "audio_files": file_list
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"Audio files listing tool error: {str(e)}"
        }


async def list_transcript_files_tool() -> Dict[str, Any]:
    """
    List all transcript files in the transcripts directory
    
    Returns:
        List of transcript files organized by format
    """
    try:
        storage_config = get_storage_config()
        transcript_files = storage_config.get_transcript_files()
        
        organized_files = {}
        total_files = 0
        total_size = 0
        
        for format_type, files in transcript_files.items():
            format_info = []
            format_size = 0
            
            for transcript_file in files:
                file_size = transcript_file.stat().st_size
                format_size += file_size
                total_size += file_size
                
                # Check if corresponding audio file exists
                base_name = transcript_file.stem
                audio_files = storage_config.get_audio_files()
                has_audio = any(af.stem == base_name for af in audio_files)
                
                file_info = {
                    "filename": transcript_file.name,
                    "path": str(transcript_file),
                    "size_kb": round(file_size / 1024, 2),
                    "modified": transcript_file.stat().st_mtime,
                    "base_name": base_name,
                    "has_audio": has_audio
                }
                format_info.append(file_info)
            
            organized_files[format_type] = {
                "count": len(files),
                "size_kb": round(format_size / 1024, 2),
                "files": format_info
            }
            total_files += len(files)
        
        print(f"📄 Found {total_files} transcript files ({round(total_size / 1024, 2)} KB total)")
        
        return {
            "status": "success",
            "total_files": total_files,
            "total_size_kb": round(total_size / 1024, 2),
            "transcripts_directory": str(storage_config.transcripts_dir),
            "formats": organized_files
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"Transcript files listing tool error: {str(e)}"
        }


async def cleanup_cache_tool(pattern: str = "temp_*") -> Dict[str, Any]:
    """
    Clean up temporary files in cache directory
    
    Args:
        pattern: File pattern to match for cleanup (default: temp_*)
        
    Returns:
        Cleanup result
    """
    try:
        storage_config = get_storage_config()
        
        # Get cache size before cleanup
        cache_info_before = storage_config.get_storage_info()
        cache_size_before = cache_info_before['cache_size_mb']
        
        # Perform cleanup
        storage_config.cleanup_temp_files(pattern)
        
        # Get cache size after cleanup
        cache_info_after = storage_config.get_storage_info()
        cache_size_after = cache_info_after['cache_size_mb']
        
        cleaned_mb = cache_size_before - cache_size_after
        
        print(f"🗑️ Cache cleanup completed")
        print(f"   Pattern: {pattern}")
        print(f"   Cleaned: {cleaned_mb:.2f} MB")
        print(f"   Cache size: {cache_size_before:.2f} MB → {cache_size_after:.2f} MB")
        
        return {
            "status": "success",
            "cleanup_pattern": pattern,
            "cache_directory": str(storage_config.cache_dir),
            "size_before_mb": cache_size_before,
            "size_after_mb": cache_size_after,
            "cleaned_mb": cleaned_mb
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"Cache cleanup tool error: {str(e)}"
        }


async def check_transcript_status_tool(audio_filename: str = None) -> Dict[str, Any]:
    """
    Check transcript status for audio files
    
    Args:
        audio_filename: Specific audio file to check (optional)
        
    Returns:
        Transcript status information
    """
    try:
        storage_config = get_storage_config()
        
        if audio_filename:
            # Check specific file
            audio_path = storage_config.get_download_path(audio_filename)
            if not audio_path.exists():
                return {
                    "status": "failed",
                    "error_message": f"Audio file not found: {audio_filename}"
                }
            
            transcript_files = storage_config.get_transcript_files(audio_filename)
            status = {
                "audio_file": audio_filename,
                "audio_exists": True,
                "transcripts": {
                    format_type: {
                        "exists": file_path.exists(),
                        "path": str(file_path),
                        "size_kb": round(file_path.stat().st_size / 1024, 2) if file_path.exists() else 0
                    }
                    for format_type, file_path in transcript_files.items()
                }
            }
            
            return {
                "status": "success",
                "mode": "single_file",
                **status
            }
        else:
            # Check all audio files
            audio_files = storage_config.get_audio_files()
            statuses = []
            
            summary = {
                "total_audio_files": len(audio_files),
                "files_with_transcripts": 0,
                "files_without_transcripts": 0,
                "transcript_formats": {"txt": 0, "srt": 0, "json": 0}
            }
            
            for audio_file in audio_files:
                transcript_files = storage_config.get_transcript_files(audio_file.name)
                
                has_any_transcript = any(tf.exists() for tf in transcript_files.values())
                if has_any_transcript:
                    summary["files_with_transcripts"] += 1
                else:
                    summary["files_without_transcripts"] += 1
                
                file_status = {
                    "audio_file": audio_file.name,
                    "has_transcripts": has_any_transcript,
                    "transcript_formats": {
                        format_type: file_path.exists()
                        for format_type, file_path in transcript_files.items()
                    }
                }
                
                # Count transcript formats
                for format_type, exists in file_status["transcript_formats"].items():
                    if exists:
                        summary["transcript_formats"][format_type] += 1
                
                statuses.append(file_status)
            
            print(f"📊 Transcript Status Summary:")
            print(f"   Total audio files: {summary['total_audio_files']}")
            print(f"   With transcripts: {summary['files_with_transcripts']}")
            print(f"   Without transcripts: {summary['files_without_transcripts']}")
            print(f"   Format counts: TXT({summary['transcript_formats']['txt']}) SRT({summary['transcript_formats']['srt']}) JSON({summary['transcript_formats']['json']})")
            
            return {
                "status": "success",
                "mode": "all_files",
                "summary": summary,
                "file_statuses": statuses
            }
            
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"Transcript status tool error: {str(e)}"
        } 
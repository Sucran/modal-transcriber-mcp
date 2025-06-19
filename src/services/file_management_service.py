"""
File Management Service - handles audio file and text file operations
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.errors import FileProcessingError


class FileManagementService:
    """Service for managing audio files and text files"""
    
    def __init__(self, base_directory: str = "."):
        self.base_directory = Path(base_directory)
    
    # ==================== MP3/Audio File Management ====================
    
    async def scan_mp3_files(self, directory: str) -> Dict[str, Any]:
        """
        Scan directory for MP3 files and return detailed information
        """
        try:
            scan_path = Path(directory)
            if not scan_path.exists():
                raise FileProcessingError(f"Directory does not exist: {directory}")
            
            if not scan_path.is_dir():
                raise FileProcessingError(f"Path is not a directory: {directory}")
            
            mp3_files = []
            
            # Scan for MP3 files
            for file_path in scan_path.rglob("*.mp3"):
                try:
                    stat = file_path.stat()
                    file_info = {
                        "filename": file_path.name,
                        "full_path": str(file_path.absolute()),
                        "file_size": stat.st_size,
                        "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created_time": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    mp3_files.append(file_info)
                except Exception as e:
                    print(f"⚠️ Error processing file {file_path}: {e}")
                    continue
            
            # Sort by modification time (newest first)
            mp3_files.sort(key=lambda x: x["modified_time"], reverse=True)
            
            return {
                "total_files": len(mp3_files),
                "scanned_directory": str(scan_path.absolute()),
                "file_list": mp3_files
            }
            
        except Exception as e:
            return {
                "total_files": 0,
                "scanned_directory": directory,
                "file_list": [],
                "error_message": str(e)
            }
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific file
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "status": "failed",
                    "file_path": file_path,
                    "file_exists": False,
                    "error_message": "File does not exist"
                }
            
            stat = path.stat()
            
            return {
                "status": "success",
                "file_path": file_path,
                "file_exists": True,
                "filename": path.name,
                "file_size": stat.st_size,
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "is_file": path.is_file(),
                "file_extension": path.suffix
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "file_path": file_path,
                "file_exists": False,
                "error_message": str(e)
            }
    
    async def organize_audio_files(
        self,
        source_directory: str,
        target_directory: str = None,
        organize_by: str = "date"  # "date", "size", "name"
    ) -> Dict[str, Any]:
        """
        Organize audio files in a directory structure
        """
        try:
            source_path = Path(source_directory)
            target_path = Path(target_directory) if target_directory else source_path / "organized"
            
            if not source_path.exists():
                raise FileProcessingError(f"Source directory does not exist: {source_directory}")
            
            # Scan for audio files
            audio_extensions = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
            audio_files = []
            
            for ext in audio_extensions:
                audio_files.extend(source_path.rglob(f"*{ext}"))
            
            organized_count = 0
            
            for audio_file in audio_files:
                try:
                    # Determine target subdirectory based on organization method
                    if organize_by == "date":
                        stat = audio_file.stat()
                        date_folder = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m")
                        target_subdir = target_path / date_folder
                    elif organize_by == "size":
                        stat = audio_file.stat()
                        size_mb = stat.st_size / (1024 * 1024)
                        if size_mb < 10:
                            size_folder = "small"
                        elif size_mb < 100:
                            size_folder = "medium"
                        else:
                            size_folder = "large"
                        target_subdir = target_path / size_folder
                    else:  # organize by name
                        first_letter = audio_file.name[0].upper()
                        target_subdir = target_path / first_letter
                    
                    # Create target directory
                    target_subdir.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    target_file = target_subdir / audio_file.name
                    if not target_file.exists():
                        audio_file.rename(target_file)
                        organized_count += 1
                
                except Exception as e:
                    print(f"⚠️ Error organizing file {audio_file}: {e}")
                    continue
            
            return {
                "status": "success",
                "total_files_found": len(audio_files),
                "files_organized": organized_count,
                "target_directory": str(target_path),
                "organization_method": organize_by
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error_message": str(e)
            }
    
    # ==================== Text File Management ====================
    
    async def read_text_file_segments(
        self,
        file_path: str,
        chunk_size: int = 65536,  # 64KB
        start_position: int = 0
    ) -> Dict[str, Any]:
        """
        Read text file content in segments with intelligent boundary detection
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "status": "failed",
                    "file_path": file_path,
                    "error_message": "File does not exist"
                }
            
            file_size = path.stat().st_size
            
            if start_position >= file_size:
                return {
                    "status": "success",
                    "file_path": file_path,
                    "content": "",
                    "current_position": file_size,
                    "file_size": file_size,
                    "end_of_file_reached": True,
                    "bytes_read": 0,
                    "content_length": 0,
                    "progress_percentage": 100.0,
                    "actual_boundary": "end_of_file"
                }
            
            with open(path, 'r', encoding='utf-8') as f:
                f.seek(start_position)
                
                # Read the chunk
                raw_content = f.read(chunk_size)
                
                if not raw_content:
                    return {
                        "status": "success",
                        "file_path": file_path,
                        "content": "",
                        "current_position": file_size,
                        "file_size": file_size,
                        "end_of_file_reached": True,
                        "bytes_read": 0,
                        "content_length": 0,
                        "progress_percentage": 100.0,
                        "actual_boundary": "end_of_file"
                    }
                
                # Find intelligent boundary
                boundary_type = "chunk_boundary"
                actual_content = raw_content
                bytes_read = len(raw_content.encode('utf-8'))
                
                if len(raw_content) == chunk_size:
                    # Look for newline boundary
                    last_newline = raw_content.rfind('\n')
                    if last_newline > chunk_size * 0.5:  # At least half the chunk
                        actual_content = raw_content[:last_newline + 1]
                        boundary_type = "newline_boundary"
                    else:
                        # Look for space boundary
                        last_space = raw_content.rfind(' ')
                        if last_space > chunk_size * 0.7:  # At least 70% of chunk
                            actual_content = raw_content[:last_space + 1]
                            boundary_type = "space_boundary"
                
                # Calculate actual position
                actual_bytes_read = len(actual_content.encode('utf-8'))
                current_position = start_position + actual_bytes_read
                
                # Check if end of file reached
                end_of_file_reached = current_position >= file_size
                
                return {
                    "status": "success",
                    "file_path": file_path,
                    "content": actual_content,
                    "current_position": current_position,
                    "file_size": file_size,
                    "end_of_file_reached": end_of_file_reached,
                    "bytes_read": actual_bytes_read,
                    "content_length": len(actual_content),
                    "progress_percentage": round((current_position / file_size) * 100, 2),
                    "actual_boundary": boundary_type
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "file_path": file_path,
                "error_message": str(e)
            }
    
    async def read_complete_text_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read complete text file content (use with caution for large files)
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {
                    "status": "failed",
                    "file_path": file_path,
                    "error_message": "File does not exist"
                }
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                return {
                    "status": "failed",
                    "file_path": file_path,
                    "error_message": "File too large (>10MB). Use read_text_file_segments instead."
                }
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "status": "success",
                "file_path": file_path,
                "content": content,
                "file_size": file_size,
                "content_length": len(content)
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "file_path": file_path,
                "error_message": str(e)
            }
    
    async def write_text_file(
        self,
        file_path: str,
        content: str,
        mode: str = "w",  # "w" for write, "a" for append
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Write content to text file
        """
        try:
            path = Path(file_path)
            
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, mode, encoding=encoding) as f:
                f.write(content)
            
            # Get file info after writing
            stat = path.stat()
            
            return {
                "status": "success",
                "file_path": file_path,
                "content_length": len(content),
                "file_size": stat.st_size,
                "mode": mode,
                "encoding": encoding
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "file_path": file_path,
                "error_message": str(e)
            }
    
    async def convert_text_format(
        self,
        input_file: str,
        output_file: str,
        input_format: str = "txt",
        output_format: str = "srt"
    ) -> Dict[str, Any]:
        """
        Convert text files between different formats (e.g., txt to srt)
        """
        try:
            # Read input file
            read_result = await self.read_complete_text_file(input_file)
            if read_result["status"] != "success":
                return read_result
            
            content = read_result["content"]
            
            # Convert based on formats
            if input_format == "txt" and output_format == "srt":
                converted_content = self._convert_txt_to_srt(content)
            elif input_format == "srt" and output_format == "txt":
                converted_content = self._convert_srt_to_txt(content)
            else:
                return {
                    "status": "failed",
                    "error_message": f"Conversion from {input_format} to {output_format} not supported"
                }
            
            # Write output file
            write_result = await self.write_text_file(output_file, converted_content)
            
            if write_result["status"] == "success":
                write_result.update({
                    "input_file": input_file,
                    "input_format": input_format,
                    "output_format": output_format,
                    "conversion": "success"
                })
            
            return write_result
            
        except Exception as e:
            return {
                "status": "failed",
                "error_message": str(e)
            }
    
    def _convert_txt_to_srt(self, content: str) -> str:
        """Convert plain text to SRT format (basic implementation)"""
        lines = content.strip().split('\n')
        srt_content = []
        
        for i, line in enumerate(lines, 1):
            if line.strip():
                # Create basic timestamps (assuming 3 seconds per line)
                start_time = (i - 1) * 3
                end_time = i * 3
                
                start_srt = self._seconds_to_srt_time(start_time)
                end_srt = self._seconds_to_srt_time(end_time)
                
                srt_content.extend([
                    str(i),
                    f"{start_srt} --> {end_srt}",
                    line.strip(),
                    ""
                ])
        
        return '\n'.join(srt_content)
    
    def _convert_srt_to_txt(self, content: str) -> str:
        """Convert SRT to plain text"""
        lines = content.strip().split('\n')
        text_lines = []
        
        for line in lines:
            # Skip sequence numbers and timestamps
            if line.strip() and not line.strip().isdigit() and '-->' not in line:
                text_lines.append(line.strip())
        
        return '\n'.join(text_lines)
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}" 
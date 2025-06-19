"""
File service for handling file operations
"""

import aiofiles
from pathlib import Path
from typing import Optional


class FileService:
    """Service for file operations"""
    
    async def write_text_file(self, file_path: str, content: str, encoding: str = "utf-8"):
        """Write text content to file asynchronously"""
        async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
            await f.write(content)
    
    async def read_text_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """Read text content from file asynchronously"""
        async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
            return await f.read()
    
    def ensure_directory(self, directory_path: str):
        """Ensure directory exists"""
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return Path(file_path).exists()
    
    def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        return Path(file_path).stat().st_size
    
    def get_file_extension(self, file_path: str) -> str:
        """Get file extension"""
        return Path(file_path).suffix.lower()
    
    def is_audio_file(self, file_path: str) -> bool:
        """Check if file is an audio file"""
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
        return self.get_file_extension(file_path) in audio_extensions 
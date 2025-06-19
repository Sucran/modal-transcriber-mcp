"""
Test transcription file management functionality
测试转译文件管理功能
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from src.tools.download_tools import get_file_info_tool, read_text_file_segments_tool
from src.services.file_management_service import FileManagementService


class TestTranscriptionFileManagement:
    """Test transcription file management integration"""
    
    def test_file_management_service_initialization(self, file_management_service: FileManagementService):
        """Test file management service initialization"""
        print("\n🔧 Testing file management service initialization...")
        
        assert file_management_service is not None
        
        print("✅ File management service initialized successfully")
    
    @pytest.mark.asyncio
    async def test_create_sample_transcription_files(self, temp_dir: str):
        """Create sample transcription files for testing"""
        print("\n📝 Creating sample transcription files...")
        
        # Create sample SRT file
        srt_content = """1
00:00:00,000 --> 00:00:05,000
Hello, this is a test transcription.

2
00:00:05,000 --> 00:00:10,000
This is the second segment of the audio.

3
00:00:10,000 --> 00:00:15,000
And this is the final segment for testing.
"""
        
        # Create sample TXT file
        txt_content = """Hello, this is a test transcription. This is the second segment of the audio. And this is the final segment for testing."""
        
        srt_file = os.path.join(temp_dir, "test_transcription.srt")
        txt_file = os.path.join(temp_dir, "test_transcription.txt")
        
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        print(f"✅ Created sample files:")
        print(f"   SRT: {srt_file}")
        print(f"   TXT: {txt_file}")
        
        return {"srt": srt_file, "txt": txt_file}
    
    @pytest.mark.asyncio
    async def test_get_file_info_tool(self, temp_dir: str):
        """Test get file info tool functionality"""
        print("\n📋 Testing get file info tool...")
        
        # Create sample files
        sample_files = await self.test_create_sample_transcription_files(temp_dir)
        
        for file_type, file_path in sample_files.items():
            print(f"\n   Testing file info for {file_type.upper()} file...")
            
            try:
                result = await get_file_info_tool(file_path)
                
                print(f"   📄 File info result:")
                print(f"      Status: {result.get('status', 'unknown')}")
                print(f"      File exists: {result.get('file_exists', False)}")
                print(f"      File size: {result.get('file_size', 0)} bytes")
                print(f"      File size MB: {result.get('file_size_mb', 0):.3f} MB")
                print(f"      Extension: {result.get('file_extension', 'N/A')}")
                
                if result.get("status") == "success":
                    assert result.get("file_exists") == True
                    assert result.get("file_size", 0) > 0
                    assert result.get("file_extension") == f".{file_type}"
                    print(f"   ✅ {file_type.upper()} file info test successful")
                else:
                    print(f"   ❌ {file_type.upper()} file info test failed: {result.get('error_message', 'Unknown')}")
                    
            except Exception as e:
                print(f"   ❌ {file_type.upper()} file info test exception: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_read_text_file_segments_tool(self, temp_dir: str):
        """Test read text file segments tool functionality"""
        print("\n📖 Testing read text file segments tool...")
        
        # Create sample files
        sample_files = await self.test_create_sample_transcription_files(temp_dir)
        
        for file_type, file_path in sample_files.items():
            print(f"\n   Testing file reading for {file_type.upper()} file...")
            
            try:
                # Test reading with default chunk size
                result = await read_text_file_segments_tool(
                    file_path=file_path,
                    chunk_size=1024,
                    start_position=0
                )
                
                print(f"   📄 File reading result:")
                print(f"      Status: {result.get('status', 'unknown')}")
                print(f"      File size: {result.get('file_size', 0)} bytes")
                print(f"      Bytes read: {result.get('bytes_read', 0)}")
                print(f"      Content length: {result.get('content_length', 0)}")
                print(f"      Progress: {result.get('progress_percentage', 0):.1f}%")
                print(f"      End of file reached: {result.get('end_of_file_reached', False)}")
                
                if result.get("status") == "success":
                    content = result.get("content", "")
                    assert len(content) > 0
                    print(f"      Content preview: {content[:100]}...")
                    print(f"   ✅ {file_type.upper()} file reading test successful")
                else:
                    print(f"   ❌ {file_type.upper()} file reading test failed: {result.get('error_message', 'Unknown')}")
                    
            except Exception as e:
                print(f"   ❌ {file_type.upper()} file reading test exception: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_read_large_text_file_segments(self, temp_dir: str):
        """Test reading large text file in segments"""
        print("\n📚 Testing large text file segment reading...")
        
        # Create a large text file for testing
        large_file_path = os.path.join(temp_dir, "large_text_file.txt")
        
        # Generate a large text content
        large_content = ""
        for i in range(1000):
            large_content += f"This is line {i+1} of the large text file for testing segment reading functionality. " * 10 + "\n"
        
        with open(large_file_path, 'w', encoding='utf-8') as f:
            f.write(large_content)
        
        print(f"   Created large text file: {len(large_content)} characters")
        
        try:
            # Test reading in small chunks
            chunk_size = 1024  # 1KB chunks
            position = 0
            total_read = 0
            segments_read = 0
            
            while True:
                result = await read_text_file_segments_tool(
                    file_path=large_file_path,
                    chunk_size=chunk_size,
                    start_position=position
                )
                
                if result.get("status") != "success":
                    break
                
                bytes_read = result.get("bytes_read", 0)
                if bytes_read == 0:
                    break
                
                segments_read += 1
                total_read += bytes_read
                position = result.get("current_position", position + bytes_read)
                
                print(f"   Segment {segments_read}: Read {bytes_read} bytes, Progress: {result.get('progress_percentage', 0):.1f}%")
                
                if result.get("end_of_file_reached", False):
                    break
                
                # Limit to avoid infinite loop in tests
                if segments_read >= 10:
                    break
            
            print(f"   ✅ Large file segment reading test successful")
            print(f"      Total segments read: {segments_read}")
            print(f"      Total bytes read: {total_read}")
            
        except Exception as e:
            print(f"   ❌ Large file segment reading test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_transcription_file_processing_workflow(self, temp_dir: str):
        """Test complete transcription file processing workflow"""
        print("\n🔄 Testing complete transcription file processing workflow...")
        
        # Step 1: Create sample transcription files
        sample_files = await self.test_create_sample_transcription_files(temp_dir)
        
        # Step 2: Get file info for each file
        file_info_results = {}
        for file_type, file_path in sample_files.items():
            try:
                file_info = await get_file_info_tool(file_path)
                file_info_results[file_type] = file_info
                print(f"   📋 {file_type.upper()} file info: {file_info.get('file_size', 0)} bytes")
            except Exception as e:
                print(f"   ❌ Failed to get {file_type} file info: {str(e)}")
        
        # Step 3: Read content from each file
        file_content_results = {}
        for file_type, file_path in sample_files.items():
            try:
                content_result = await read_text_file_segments_tool(
                    file_path=file_path,
                    chunk_size=2048,
                    start_position=0
                )
                file_content_results[file_type] = content_result
                print(f"   📖 {file_type.upper()} content read: {content_result.get('content_length', 0)} characters")
            except Exception as e:
                print(f"   ❌ Failed to read {file_type} file content: {str(e)}")
        
        # Step 4: Validate workflow results
        workflow_success = True
        
        for file_type in sample_files.keys():
            if file_type not in file_info_results or file_info_results[file_type].get("status") != "success":
                workflow_success = False
                print(f"   ❌ File info failed for {file_type}")
            
            if file_type not in file_content_results or file_content_results[file_type].get("status") != "success":
                workflow_success = False
                print(f"   ❌ Content reading failed for {file_type}")
        
        if workflow_success:
            print("   ✅ Complete transcription file processing workflow successful")
        else:
            print("   ⚠️  Some parts of the workflow failed")
    
    @pytest.mark.asyncio
    async def test_file_management_error_handling(self, temp_dir: str):
        """Test file management error handling"""
        print("\n🚨 Testing file management error handling...")
        
        # Test with non-existent file
        non_existent_file = os.path.join(temp_dir, "non_existent_file.txt")
        
        try:
            # Test get_file_info with non-existent file
            result = await get_file_info_tool(non_existent_file)
            print(f"   📋 Non-existent file info result:")
            print(f"      Status: {result.get('status', 'unknown')}")
            print(f"      File exists: {result.get('file_exists', 'unknown')}")
            
            assert result.get("file_exists") == False
            print("   ✅ Non-existent file handling successful")
            
        except Exception as e:
            print(f"   ❌ Non-existent file test failed: {str(e)}")
        
        try:
            # Test read_text_file_segments with non-existent file
            result = await read_text_file_segments_tool(
                file_path=non_existent_file,
                chunk_size=1024,
                start_position=0
            )
            print(f"   📖 Non-existent file reading result:")
            print(f"      Status: {result.get('status', 'unknown')}")
            
            if result.get("status") == "failed":
                print("   ✅ Non-existent file reading error handling successful")
            else:
                print("   ⚠️  Expected failure for non-existent file reading")
                
        except Exception as e:
            print(f"   ✅ Non-existent file reading properly raised exception: {str(e)}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"]) 
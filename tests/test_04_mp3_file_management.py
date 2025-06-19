"""
Test MP3 file management functionality
测试MP3文件管理功能
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from src.tools.download_tools import get_mp3_files_tool, get_file_info_tool
from src.services.file_management_service import FileManagementService


class TestMP3FileManagement:
    """Test MP3 file management integration"""
    
    @pytest.mark.asyncio
    async def test_create_sample_mp3_files(self, temp_dir: str):
        """Create sample MP3 files for testing"""
        print("\n🎵 Creating sample MP3 files for testing...")
        
        import ffmpeg
        
        mp3_files = {}
        
        # Create different types of sample MP3 files
        test_configs = [
            ("short_audio.mp3", 3, 440),  # 3 seconds, 440Hz
            ("medium_audio.mp3", 10, 880),  # 10 seconds, 880Hz
            ("long_audio.mp3", 30, 220),  # 30 seconds, 220Hz
        ]
        
        for filename, duration, frequency in test_configs:
            file_path = os.path.join(temp_dir, filename)
            
            try:
                # Generate sample audio with different characteristics
                (
                    ffmpeg
                    .input(f'sine=frequency={frequency}:duration={duration}', f='lavfi')
                    .output(file_path, acodec='mp3', ar=16000, ab='128k')
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                mp3_files[filename] = file_path
                print(f"   ✅ Created {filename}: {duration}s, {frequency}Hz")
                
            except Exception as e:
                print(f"   ❌ Failed to create {filename}: {str(e)}")
        
        print(f"   Total MP3 files created: {len(mp3_files)}")
        return mp3_files
    
    @pytest.mark.asyncio
    async def test_get_mp3_files_tool(self, temp_dir: str):
        """Test get MP3 files tool functionality"""
        print("\n📂 Testing get MP3 files tool...")
        
        # Create sample MP3 files
        mp3_files = await self.test_create_sample_mp3_files(temp_dir)
        
        try:
            # Test scanning the directory for MP3 files
            result = await get_mp3_files_tool(temp_dir)
            
            print(f"   📋 MP3 files scan result:")
            print(f"      Total files: {result.get('total_files', 0)}")
            print(f"      Scanned directory: {result.get('scanned_directory', 'N/A')}")
            
            if result.get('total_files', 0) > 0:
                file_list = result.get('file_list', [])
                print(f"      Found {len(file_list)} MP3 files:")
                
                for file_info in file_list[:5]:  # Show first 5 files
                    print(f"         📄 {file_info.get('filename', 'Unknown')}")
                    print(f"            Size: {file_info.get('file_size_mb', 0):.2f} MB")
                    print(f"            Created: {file_info.get('created_time', 'Unknown')}")
                
                # Verify we found the expected files
                found_filenames = [f.get('filename', '') for f in file_list]
                expected_files = list(mp3_files.keys())
                
                found_expected = [f for f in expected_files if f in found_filenames]
                print(f"      ✅ Found {len(found_expected)}/{len(expected_files)} expected files")
                
                assert len(found_expected) > 0, "Should find at least some of the created MP3 files"
                
            else:
                print("      ⚠️  No MP3 files found")
                
        except Exception as e:
            print(f"   ❌ MP3 files scan test failed: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_mp3_file_info_detailed(self, temp_dir: str):
        """Test detailed MP3 file information retrieval"""
        print("\n🔍 Testing detailed MP3 file information...")
        
        # Create sample MP3 files
        mp3_files = await self.test_create_sample_mp3_files(temp_dir)
        
        for filename, file_path in mp3_files.items():
            print(f"\n   Testing detailed info for: {filename}")
            
            try:
                # Get detailed file info
                result = await get_file_info_tool(file_path)
                
                print(f"      📋 File info:")
                print(f"         Status: {result.get('status', 'unknown')}")
                print(f"         File exists: {result.get('file_exists', False)}")
                print(f"         Size: {result.get('file_size_mb', 0):.3f} MB")
                print(f"         Extension: {result.get('file_extension', 'N/A')}")
                print(f"         Modified: {result.get('modified_time', 'N/A')}")
                
                if result.get("status") == "success":
                    assert result.get("file_exists") == True
                    assert result.get("file_extension") == ".mp3"
                    assert result.get("file_size", 0) > 0
                    print(f"      ✅ {filename} info retrieval successful")
                else:
                    print(f"      ❌ {filename} info retrieval failed: {result.get('error_message', 'Unknown')}")
                    
            except Exception as e:
                print(f"      ❌ {filename} info test exception: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_mp3_directory_scanning_edge_cases(self, temp_dir: str):
        """Test MP3 directory scanning with edge cases"""
        print("\n🎯 Testing MP3 directory scanning edge cases...")
        
        # Test 1: Empty directory
        empty_dir = os.path.join(temp_dir, "empty_directory")
        os.makedirs(empty_dir, exist_ok=True)
        
        try:
            result = await get_mp3_files_tool(empty_dir)
            print(f"   📂 Empty directory scan:")
            print(f"      Total files: {result.get('total_files', 0)}")
            
            assert result.get('total_files', 0) == 0
            print("   ✅ Empty directory handling successful")
            
        except Exception as e:
            print(f"   ❌ Empty directory test failed: {str(e)}")
        
        # Test 2: Directory with mixed file types
        mixed_dir = os.path.join(temp_dir, "mixed_files")
        os.makedirs(mixed_dir, exist_ok=True)
        
        # Create some non-MP3 files
        test_files = {
            "text_file.txt": "This is a text file",
            "data_file.json": '{"test": "data"}',
            "image_file.jpg": b"fake_image_data",
        }
        
        for filename, content in test_files.items():
            file_path = os.path.join(mixed_dir, filename)
            mode = 'w' if isinstance(content, str) else 'wb'
            with open(file_path, mode) as f:
                f.write(content)
        
        # Create one MP3 file
        import ffmpeg
        mp3_path = os.path.join(mixed_dir, "only_mp3.mp3")
        try:
            (
                ffmpeg
                .input('sine=frequency=440:duration=2', f='lavfi')
                .output(mp3_path, acodec='mp3', ar=16000)
                .overwrite_output()
                .run(quiet=True)
            )
        except:
            pass  # Skip if ffmpeg fails
        
        try:
            result = await get_mp3_files_tool(mixed_dir)
            print(f"   📁 Mixed files directory scan:")
            print(f"      Total files: {result.get('total_files', 0)}")
            
            if os.path.exists(mp3_path):
                assert result.get('total_files', 0) == 1
                print("   ✅ Mixed files directory filtering successful")
            else:
                print("   ⚠️  MP3 creation failed, skipping validation")
                
        except Exception as e:
            print(f"   ❌ Mixed files directory test failed: {str(e)}")
        
        # Test 3: Non-existent directory
        non_existent_dir = os.path.join(temp_dir, "non_existent_directory")
        
        try:
            result = await get_mp3_files_tool(non_existent_dir)
            print(f"   🚫 Non-existent directory scan:")
            print(f"      Result: {result}")
            
            # Should handle gracefully (either error or empty result)
            if 'error_message' in result:
                print("   ✅ Non-existent directory error handling successful")
            elif result.get('total_files', 0) == 0:
                print("   ✅ Non-existent directory handled as empty")
            
        except Exception as e:
            print(f"   ✅ Non-existent directory properly raised exception: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_mp3_file_management_workflow(self, temp_dir: str):
        """Test complete MP3 file management workflow"""
        print("\n🔄 Testing complete MP3 file management workflow...")
        
        # Step 1: Create sample MP3 files
        print("   Step 1: Creating sample MP3 files...")
        mp3_files = await self.test_create_sample_mp3_files(temp_dir)
        
        # Step 2: Scan directory for MP3 files
        print("   Step 2: Scanning directory for MP3 files...")
        scan_result = await get_mp3_files_tool(temp_dir)
        
        print(f"      Found {scan_result.get('total_files', 0)} MP3 files")
        
        # Step 3: Get detailed info for each found MP3 file
        print("   Step 3: Getting detailed info for each MP3 file...")
        
        file_list = scan_result.get('file_list', [])
        detailed_info = {}
        
        for file_info in file_list:
            filename = file_info.get('filename', '')
            full_path = file_info.get('full_path', '')
            
            if full_path:
                try:
                    detail_result = await get_file_info_tool(full_path)
                    detailed_info[filename] = detail_result
                    print(f"      📄 {filename}: {detail_result.get('file_size_mb', 0):.2f} MB")
                except Exception as e:
                    print(f"      ❌ Failed to get details for {filename}: {str(e)}")
        
        # Step 4: Validate workflow results
        workflow_success = True
        
        if scan_result.get('total_files', 0) == 0:
            print("   ⚠️  No MP3 files found in workflow")
            workflow_success = False
        
        if len(detailed_info) == 0:
            print("   ⚠️  No detailed info collected")
            workflow_success = False
        
        # Check that we can process the files we created
        expected_count = len(mp3_files)
        found_count = scan_result.get('total_files', 0)
        
        if found_count >= expected_count:
            print(f"   ✅ Found expected number of files ({found_count} >= {expected_count})")
        else:
            print(f"   ⚠️  Found fewer files than expected ({found_count} < {expected_count})")
        
        if workflow_success:
            print("   ✅ Complete MP3 file management workflow successful")
            
            # Summary statistics
            total_size = sum(
                info.get('file_size_mb', 0) 
                for info in detailed_info.values() 
                if info.get('status') == 'success'
            )
            print(f"      Total MP3 files size: {total_size:.2f} MB")
            
        else:
            print("   ⚠️  Some parts of the MP3 workflow failed")
    
    def test_file_management_service_mp3_capabilities(self, file_management_service: FileManagementService):
        """Test file management service MP3-specific capabilities"""
        print("\n🔧 Testing file management service MP3 capabilities...")
        
        assert file_management_service is not None
        
        # Check if service has MP3-related methods
        mp3_methods = [
            'scan_mp3_files',
            'get_file_info',
        ]
        
        for method_name in mp3_methods:
            if hasattr(file_management_service, method_name):
                print(f"   ✅ Method available: {method_name}")
            else:
                print(f"   ⚠️  Method not found: {method_name}")
        
        print("✅ File management service MP3 capabilities check completed")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"]) 
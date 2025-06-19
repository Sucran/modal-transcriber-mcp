"""
Test for concurrent processing functionality
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.services.distributed_transcription_service import DistributedTranscriptionService


class TestConcurrentProcessing:
    """Test the new concurrent processing logic"""
    
    @pytest.mark.asyncio
    async def test_asyncio_task_creation_and_waiting(self):
        """Test that asyncio tasks are created and waited for correctly"""
        
        service = DistributedTranscriptionService()
        
        # Mock the chunk transcription method
        async def mock_transcribe_chunk(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                "processing_status": "success",
                "text": "Mock transcription",
                "segments": [{"start": 0, "end": 1, "text": "test"}]
            }
        
        # Mock the audio splitting method to return a small number of chunks
        mock_chunks = [
            ("/tmp/chunk1.wav", 0.0, 10.0),
            ("/tmp/chunk2.wav", 10.0, 20.0),
            ("/tmp/chunk3.wav", 20.0, 30.0)
        ]
        
        with patch.object(service, 'split_audio_locally', return_value=mock_chunks):
            with patch.object(service, 'transcribe_chunk_distributed', side_effect=mock_transcribe_chunk):
                with patch.object(service, 'merge_chunk_results') as mock_merge:
                    mock_merge.return_value = {
                        "processing_status": "success",
                        "chunks_processed": 3,
                        "chunks_failed": 0
                    }
                    
                    # Test the distributed transcription
                    result = await service.transcribe_audio_distributed(
                        audio_file_path="test.wav",
                        model_size="turbo",
                        chunk_endpoint_url="http://test.com"
                    )
                    
                    # Verify result
                    assert result["processing_status"] == "success"
                    assert result["chunks_processed"] == 3
                    assert result["chunks_failed"] == 0
                    
                    # Verify merge was called with correct number of results
                    mock_merge.assert_called_once()
                    call_args = mock_merge.call_args[0]
                    chunk_results = call_args[0]
                    assert len(chunk_results) == 3
                    
                    # Verify all chunk results are successful
                    for chunk_result in chunk_results:
                        assert chunk_result["processing_status"] == "success"
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_with_failures(self):
        """Test concurrent processing handles chunk failures correctly"""
        
        service = DistributedTranscriptionService()
        
        # Mock the chunk transcription method with mixed success/failure
        async def mock_transcribe_chunk_mixed(chunk_path, *args, **kwargs):
            await asyncio.sleep(0.1)
            if "chunk1" in chunk_path:
                return {
                    "processing_status": "success",
                    "text": "Success",
                    "segments": [{"start": 0, "end": 1, "text": "test"}]
                }
            else:
                return {
                    "processing_status": "failed",
                    "error_message": "Mock failure"
                }
        
        # Mock chunks
        mock_chunks = [
            ("/tmp/chunk1.wav", 0.0, 10.0),
            ("/tmp/chunk2.wav", 10.0, 20.0),
            ("/tmp/chunk3.wav", 20.0, 30.0)
        ]
        
        with patch.object(service, 'split_audio_locally', return_value=mock_chunks):
            with patch.object(service, 'transcribe_chunk_distributed', side_effect=mock_transcribe_chunk_mixed):
                with patch.object(service, 'merge_chunk_results') as mock_merge:
                    mock_merge.return_value = {
                        "processing_status": "success",
                        "chunks_processed": 1,
                        "chunks_failed": 2
                    }
                    
                    # Test the distributed transcription
                    result = await service.transcribe_audio_distributed(
                        audio_file_path="test.wav",
                        model_size="turbo",
                        chunk_endpoint_url="http://test.com"
                    )
                    
                    # Verify result
                    assert result["processing_status"] == "success"
                    assert result["chunks_processed"] == 1
                    assert result["chunks_failed"] == 2
                    
                    # Verify merge was called with mixed results
                    mock_merge.assert_called_once()
                    call_args = mock_merge.call_args[0]
                    chunk_results = call_args[0]
                    assert len(chunk_results) == 3
                    
                    # Verify result distribution
                    successful_results = [r for r in chunk_results if r["processing_status"] == "success"]
                    failed_results = [r for r in chunk_results if r["processing_status"] == "failed"]
                    assert len(successful_results) == 1
                    assert len(failed_results) == 2
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_exception_handling(self):
        """Test that exceptions in individual chunks are handled correctly"""
        
        service = DistributedTranscriptionService()
        
        # Mock the chunk transcription method that raises exceptions
        async def mock_transcribe_chunk_exception(*args, **kwargs):
            await asyncio.sleep(0.1)
            raise Exception("Mock network error")
        
        # Mock chunks
        mock_chunks = [
            ("/tmp/chunk1.wav", 0.0, 10.0),
            ("/tmp/chunk2.wav", 10.0, 20.0)
        ]
        
        with patch.object(service, 'split_audio_locally', return_value=mock_chunks):
            with patch.object(service, 'transcribe_chunk_distributed', side_effect=mock_transcribe_chunk_exception):
                with patch.object(service, 'merge_chunk_results') as mock_merge:
                    mock_merge.return_value = {
                        "processing_status": "failed",
                        "error_message": "All chunks failed to process",
                        "chunks_processed": 0,
                        "chunks_failed": 2
                    }
                    
                    # Test the distributed transcription
                    result = await service.transcribe_audio_distributed(
                        audio_file_path="test.wav",
                        model_size="turbo",
                        chunk_endpoint_url="http://test.com"
                    )
                    
                    # Verify result
                    assert result["processing_status"] == "failed"
                    assert result["chunks_processed"] == 0
                    assert result["chunks_failed"] == 2
                    
                    # Verify merge was called with failed results
                    mock_merge.assert_called_once()
                    call_args = mock_merge.call_args[0]
                    chunk_results = call_args[0]
                    assert len(chunk_results) == 2
                    
                    # All results should be failures
                    for chunk_result in chunk_results:
                        assert chunk_result["processing_status"] == "failed"
                        assert "Mock network error" in chunk_result["error_message"] 
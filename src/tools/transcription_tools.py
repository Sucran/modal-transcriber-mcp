"""
Transcription tools using the enhanced service architecture
Updated to use ModalTranscriptionService for better separation of concerns
"""

import asyncio
from typing import Dict, Any

from ..services import ModalTranscriptionService


# Global service instance for reuse
_modal_transcription_service = None


def _format_srt_time(seconds: float) -> str:
    """Format seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def get_modal_transcription_service() -> ModalTranscriptionService:
    """Get or create global ModalTranscriptionService instance"""
    global _modal_transcription_service
    if _modal_transcription_service is None:
        _modal_transcription_service = ModalTranscriptionService(use_direct_modal_calls=True)
    return _modal_transcription_service


async def transcribe_audio_file_tool(
    audio_file_path: str,
    model_size: str = "turbo",  # Default to turbo model
    language: str = None,
    output_format: str = "srt",
    enable_speaker_diarization: bool = False,
    use_parallel_processing: bool = True,  # Enable parallel processing by default
    chunk_duration: int = 60,  # 60 seconds chunks for parallel processing
    use_intelligent_segmentation: bool = True  # Enable intelligent segmentation by default
) -> Dict[str, Any]:
    """
    MCP tool function for audio transcription using Modal endpoints with intelligent processing
    Enhanced to save transcription results to local files
    
    Args:
        audio_file_path: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large, turbo)
        language: Language code (e.g., 'en', 'zh', None for auto-detect)
        output_format: Output format (srt, txt, json)
        enable_speaker_diarization: Whether to enable speaker diarization
        use_parallel_processing: Whether to use distributed processing for long audio
        chunk_duration: Duration of each chunk in seconds for parallel processing
        use_intelligent_segmentation: Whether to use intelligent silence-based segmentation
        
    Returns:
        Transcription result dictionary with local file paths
    """
    try:
        import os
        import pathlib
        
        service = get_modal_transcription_service()
        modal_result = await service.transcribe_audio_file(
            audio_file_path=audio_file_path,
            model_size=model_size,
            language=language,
            output_format=output_format,
            enable_speaker_diarization=enable_speaker_diarization,
            use_parallel_processing=use_parallel_processing,
            chunk_duration=chunk_duration,
            use_intelligent_segmentation=use_intelligent_segmentation
        )
        
        # # Check if transcription was successful
        # if modal_result.get("processing_status") != "success":
        #     return modal_result
        
        # Debug: Print modal result structure
        print(f"🔍 Modal result keys: {list(modal_result.keys())}")
        print(f"🔍 Has text: {bool(modal_result.get('text'))}")
        print(f"🔍 Has segments: {bool(modal_result.get('segments'))}")
        if modal_result.get("segments"):
            print(f"🔍 Segments count: {len(modal_result['segments'])}")
        
        # Save transcription results to local files using storage config
        from ..utils.storage_config import get_storage_config
        storage_config = get_storage_config()
        
        base_name = pathlib.Path(audio_file_path).stem
        output_dir = storage_config.transcripts_dir
        
        saved_files = []
        txt_file_path = None
        srt_file_path = None
        json_file_path = None
        
        # Generate SRT content if segments are available
        if modal_result.get("segments"):
            segments = modal_result["segments"]
            srt_content = ""
            for i, segment in enumerate(segments, 1):
                start_time = _format_srt_time(segment.get("start", 0))
                end_time = _format_srt_time(segment.get("end", 0))
                text = segment.get("text", "").strip()
                
                if text:
                    if enable_speaker_diarization and segment.get("speaker"):
                        text = f"[{segment['speaker']}] {text}"
                    
                    srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
            
            if srt_content:
                srt_file_path = output_dir / f"{base_name}.srt"
                with open(srt_file_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                saved_files.append(str(srt_file_path))
                print(f"💾 Saved SRT file: {srt_file_path}")
        
        # Generate TXT content if text is available
        if modal_result.get("text"):
            txt_file_path = output_dir / f"{base_name}.txt"
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write(modal_result["text"])
            saved_files.append(str(txt_file_path))
            print(f"💾 Saved TXT file: {txt_file_path}")
        
        # Save JSON file with full results (always save for debugging)
        import json
        json_file_path = output_dir / f"{base_name}.json"
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(modal_result, f, indent=2, ensure_ascii=False)
        saved_files.append(str(json_file_path))
        print(f"💾 Saved JSON file: {json_file_path}")
        
        # Warn if no text/segments found
        if not modal_result.get("segments") and not modal_result.get("text"):
            print("⚠️ Warning: No text or segments found in transcription result")
        
        # Update result with local file paths
        result = {}
        result["txt_file_path"] = str(txt_file_path) if txt_file_path else None
        result["srt_file_path"] = str(srt_file_path) if srt_file_path else None
        result["json_file_path"] = str(json_file_path) if json_file_path else None
        result["saved_files"] = saved_files
        result["local_files_saved"] = len(saved_files)
        
        print(f"✅ Transcription completed and saved {len(saved_files)} local files")
        
        return result
        
    except Exception as e:
        return {
            "processing_status": "failed",
            "error_message": f"Tool error: {str(e)}"
        }


async def check_modal_endpoints_health() -> Dict[str, Any]:
    """
    Check the health status of Modal endpoints
    
    Returns:
        Health status dictionary for all endpoints
    """
    try:
        service = get_modal_transcription_service()
        return await service.check_endpoints_health()
        
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"Health check tool error: {str(e)}"
        }


async def get_system_status() -> Dict[str, Any]:
    """
    Get comprehensive system status including health checks
    
    Returns:
        System status dictionary
    """
    try:
        service = get_modal_transcription_service()
        return await service.get_system_status()
        
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"System status tool error: {str(e)}"
        }


def get_modal_endpoint_url(endpoint_label: str) -> str:
    """
    Get Modal endpoint URL for given label
    
    Args:
        endpoint_label: Modal endpoint label
        
    Returns:
        Full endpoint URL
    """
    try:
        service = get_modal_transcription_service()
        return service.get_endpoint_url(endpoint_label)
        
    except Exception as e:
        # Fallback to default URL pattern using config
        from ..config.config import build_modal_endpoint_url
        return build_modal_endpoint_url(endpoint_label)


# Note: Download functionality has been moved to download_tools.py
# These functions are now implemented there using PodcastDownloadService for local downloads 
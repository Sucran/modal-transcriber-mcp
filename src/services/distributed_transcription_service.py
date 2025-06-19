"""
Distributed Transcription Service
Handles audio transcription with true distributed processing across multiple Modal containers
Enhanced with intelligent audio segmentation capabilities
"""

import asyncio
import aiohttp
import base64
import os
import tempfile
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import time
import re

import ffmpeg
import torch

from .transcription_service import TranscriptionService


class DistributedTranscriptionService:
    """Service for handling distributed audio transcription across multiple Modal containers"""
    
    def __init__(self, cache_dir: str = "/tmp"):
        self.cache_dir = cache_dir
        self.transcription_service = TranscriptionService(cache_dir)
        
    def split_audio_by_time(self, audio_file_path: str, chunk_duration: int = 60) -> List[Dict[str, Any]]:
        """Split audio into time-based chunks"""
        try:
            # Get audio duration using ffprobe
            duration_cmd = [
                "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                "-of", "csv=p=0", audio_file_path
            ]
            result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
            total_duration = float(result.stdout.strip())
            
            chunks = []
            start_time = 0.0
            chunk_index = 0
            
            while start_time < total_duration:
                end_time = min(start_time + chunk_duration, total_duration)
                actual_duration = end_time - start_time
                
                # Skip very short chunks (less than 5 seconds)
                if actual_duration < 5.0:
                    break
                
                chunk_filename = f"chunk_{chunk_index:03d}.wav"
                chunks.append({
                    "chunk_index": chunk_index,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": actual_duration,
                    "filename": chunk_filename
                })
                
                start_time = end_time
                chunk_index += 1
            
            print(f"📊 Split audio into {len(chunks)} time-based chunks")
            return chunks
            
        except Exception as e:
            print(f"❌ Error splitting audio by time: {e}")
            return []
    
    def split_audio_by_silence(
        self,
        audio_file_path: str,
        min_segment_length: float = 30.0,
        min_silence_length: float = 1.0,
        max_segment_length: float = 120.0
    ) -> List[Dict[str, Any]]:
        """
        Intelligently split audio using FFmpeg's silencedetect filter
        Enhanced from AudioProcessingService
        """
        try:
            silence_end_re = re.compile(
                r" silence_end: (?P<end>[0-9]+(\.?[0-9]*)) \| silence_duration: (?P<dur>[0-9]+(\.?[0-9]*))"
            )
            
            # Get audio duration
            metadata = ffmpeg.probe(audio_file_path)
            total_duration = float(metadata["format"]["duration"])
            
            print(f"🎵 Audio duration: {total_duration:.2f}s")
            print(f"🔍 Detecting silence with min_silence_length={min_silence_length}s...")
            
            # Use silence detection filter
            cmd = [
                "ffmpeg", "-i", audio_file_path,
                "-af", f"silencedetect=noise=-30dB:duration={min_silence_length}",
                "-f", "null", "-"
            ]
            
            process = subprocess.Popen(
                cmd, 
                stderr=subprocess.PIPE, 
                stdout=subprocess.PIPE, 
                text=True
            )
            
            segments = []
            cur_start = 0.0
            chunk_index = 0
            
            # Process silence detection output
            for line in process.stderr:
                match = silence_end_re.search(line)
                if match:
                    silence_end = float(match.group("end"))
                    silence_dur = float(match.group("dur"))
                    split_at = silence_end - (silence_dur / 2)
                    
                    segment_duration = split_at - cur_start
                    
                    # Skip segments that are too short
                    if segment_duration < min_segment_length:
                        continue
                    
                    # Split long segments
                    if segment_duration > max_segment_length:
                        # Split into multiple smaller segments
                        sub_start = cur_start
                        while sub_start < split_at:
                            sub_end = min(sub_start + max_segment_length, split_at)
                            sub_duration = sub_end - sub_start
                            
                            if sub_duration >= min_segment_length:
                                segments.append({
                                    "chunk_index": chunk_index,
                                    "start_time": sub_start,
                                    "end_time": sub_end,
                                    "duration": sub_duration,
                                    "filename": f"silence_chunk_{chunk_index:03d}.wav",
                                    "segmentation_type": "silence_based"
                                })
                                chunk_index += 1
                            
                            sub_start = sub_end
                    else:
                        segments.append({
                            "chunk_index": chunk_index,
                            "start_time": cur_start,
                            "end_time": split_at,
                            "duration": segment_duration,
                            "filename": f"silence_chunk_{chunk_index:03d}.wav",
                            "segmentation_type": "silence_based"
                        })
                        chunk_index += 1
                    
                    cur_start = split_at
            
            process.wait()
            
            # Handle the last segment
            if total_duration > cur_start:
                remaining_duration = total_duration - cur_start
                if remaining_duration >= min_segment_length:
                    segments.append({
                        "chunk_index": chunk_index,
                        "start_time": cur_start,
                        "end_time": total_duration,
                        "duration": remaining_duration,
                        "filename": f"silence_chunk_{chunk_index:03d}.wav",
                        "segmentation_type": "silence_based"
                    })
            
            print(f"🎯 Silence-based segmentation created {len(segments)} segments")
            return segments
            
        except Exception as e:
            print(f"⚠️ Silence-based segmentation failed: {e}")
            # Fallback to time-based segmentation
            print("📋 Falling back to time-based segmentation...")
            return self.split_audio_by_time(audio_file_path, chunk_duration=60)
    
    def choose_segmentation_strategy(
        self,
        audio_file_path: str,
        use_intelligent_segmentation: bool = True,
        chunk_duration: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Choose the best segmentation strategy based on audio characteristics
        """
        try:
            # Get audio metadata
            metadata = ffmpeg.probe(audio_file_path)
            duration = float(metadata["format"]["duration"])
            
            print(f"🎛️ Choosing segmentation strategy for {duration:.2f}s audio...")
            
            # For short audio (< 30s), use single processing
            if duration < 30:
                print("📝 Audio is short, using single chunk")
                return [{
                    "chunk_index": 0,
                    "start_time": 0.0,
                    "end_time": duration,
                    "duration": duration,
                    "filename": "single_chunk.wav",
                    "segmentation_type": "single"
                }]
            
            # For longer audio, choose based on user preference
            if use_intelligent_segmentation:
                print("🧠 Using intelligent silence-based segmentation")
                segments = self.split_audio_by_silence(
                    audio_file_path,
                    min_segment_length=30.0,
                    min_silence_length=1.0,
                    max_segment_length=120.0
                )
                
                # NEW: Check if silence-based segmentation failed for long audio
                if duration > 180 and len(segments) == 1:  # Audio > 3 minutes with only 1 segment
                    print(f"⚠️ Silence-based segmentation created only 1 segment for {duration:.2f}s audio")
                    print("🔄 Falling back to 3-minute time-based segmentation for better processing efficiency")
                    return self.split_audio_by_time(audio_file_path, chunk_duration=180)  # 3-minute chunks
                
                # If silence-based segmentation didn't work well, fallback to time-based
                if len(segments) == 0 or len(segments) > duration / 20:  # Too many tiny segments
                    print("🔄 Silence segmentation not optimal, using time-based")
                    return self.split_audio_by_time(audio_file_path, chunk_duration)
                
                return segments
            else:
                print("⏰ Using time-based segmentation")
                return self.split_audio_by_time(audio_file_path, chunk_duration)
                
        except Exception as e:
            print(f"❌ Error in segmentation strategy: {e}")
            # Ultimate fallback
            return self.split_audio_by_time(audio_file_path, chunk_duration)
    
    def split_audio_locally(
        self, 
        audio_file_path: str, 
        chunk_duration: int = 60,
        use_intelligent_segmentation: bool = True
    ) -> List[Tuple[str, float, float]]:
        """
        Split audio file into chunks locally for distributed processing using intelligent segmentation
        
        Args:
            audio_file_path: Path to audio file
            chunk_duration: Duration of each chunk in seconds
            use_intelligent_segmentation: Whether to use intelligent silence-based segmentation
            
        Returns:
            List of (chunk_file_path, start_time, end_time) tuples
        """
        try:
            # Choose segmentation strategy
            segments = self.choose_segmentation_strategy(
                audio_file_path,
                use_intelligent_segmentation=use_intelligent_segmentation,
                chunk_duration=chunk_duration
            )
            
            if not segments:
                print("❌ No segments generated")
                return []
            
            print(f"🎵 Processing {len(segments)} segments using {segments[0].get('segmentation_type', 'time_based')} segmentation")
            
            # Create temporary directory for chunks
            temp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
            chunks = []
            
            for segment in segments:
                start_time = segment["start_time"]
                end_time = segment["end_time"]
                duration = segment["duration"]
                
                # Create chunk file path
                chunk_filename = f"chunk_{segment['chunk_index']:03d}_{start_time:.1f}s-{end_time:.1f}s.wav"
                chunk_path = os.path.join(temp_dir, chunk_filename)
                
                # Extract chunk using ffmpeg-python (no subprocess)
                try:
                    (
                        ffmpeg
                        .input(audio_file_path, ss=start_time, t=duration)
                        .output(
                            chunk_path,
                            acodec='pcm_s16le',
                            ar=16000,
                            ac=1
                        )
                        .overwrite_output()
                        .run(quiet=True, capture_stdout=True, capture_stderr=True)
                    )
                except ffmpeg.Error as e:
                    print(f"❌ FFmpeg error for chunk {segment['chunk_index']+1}: {e}")
                    print(f"   stderr: {e.stderr.decode() if e.stderr else 'No stderr'}")
                    continue
                
                if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                    chunks.append((chunk_path, start_time, end_time))
                    segmentation_type = segment.get('segmentation_type', 'time_based')
                    print(f"📦 Created {segmentation_type} chunk {segment['chunk_index']+1}: {start_time:.1f}s-{end_time:.1f}s")
                else:
                    print(f"⚠️ Failed to create chunk {segment['chunk_index']+1}")
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error splitting audio: {e}")
            return []
    
    async def transcribe_chunk_distributed(
        self,
        chunk_path: str,
        start_time: float,
        end_time: float,
        model_size: str = "turbo",
        language: str = None,
        enable_speaker_diarization: bool = False,
        chunk_endpoint_url: str = None
    ) -> Dict[str, Any]:
        """
        Transcribe a single chunk using Modal distributed endpoint
        
        Args:
            chunk_path: Path to audio chunk file
            start_time: Start time of chunk in original audio
            end_time: End time of chunk in original audio
            model_size: Whisper model size
            language: Language code
            enable_speaker_diarization: Whether to enable speaker diarization
            chunk_endpoint_url: URL of chunk transcription endpoint
            
        Returns:
            Transcription result for the chunk
        """
        try:
            # Read and encode chunk file
            with open(chunk_path, "rb") as f:
                audio_data = f.read()
            
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Prepare request data
            request_data = {
                "audio_file_data": audio_base64,
                "audio_file_name": os.path.basename(chunk_path),
                "model_size": model_size,
                "language": language,
                "output_format": "json",  # Use JSON for easier merging
                "enable_speaker_diarization": enable_speaker_diarization,
                "chunk_start_time": start_time,
                "chunk_end_time": end_time
            }
            
            # Send request to Modal chunk endpoint with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Adjust timeout based on whether speaker diarization is enabled
                    if enable_speaker_diarization:
                        timeout_config = aiohttp.ClientTimeout(
                            total=720,  # 12 minutes total for speaker diarization
                            connect=45,  # 45 seconds connection timeout
                            sock_read=300  # 5 minutes read timeout for speaker processing
                        )
                    else:
                        timeout_config = aiohttp.ClientTimeout(
                            total=480,  # 8 minutes total for regular transcription
                            connect=30,  # 30 seconds connection timeout
                            sock_read=120  # 2 minutes read timeout for regular processing
                        )
                    
                    async with aiohttp.ClientSession(timeout=timeout_config) as session:
                        async with session.post(
                            chunk_endpoint_url,
                            json=request_data
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                result["chunk_start_time"] = start_time
                                result["chunk_end_time"] = end_time
                                result["chunk_file"] = chunk_path
                                return result
                            else:
                                error_text = await response.text()
                                if attempt < max_retries - 1:
                                    print(f"⚠️ HTTP {response.status} on attempt {attempt + 1}, retrying...")
                                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                    continue
                                else:
                                    return {
                                        "processing_status": "failed",
                                        "error_message": f"HTTP {response.status} after {max_retries} attempts: {error_text}",
                                        "chunk_start_time": start_time,
                                        "chunk_end_time": end_time,
                                        "chunk_file": chunk_path
                                    }
                                    
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Network error on attempt {attempt + 1}: {e}, retrying...")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        return {
                            "processing_status": "failed",
                            "error_message": f"Network error after {max_retries} attempts: {e}",
                            "chunk_start_time": start_time,
                            "chunk_end_time": end_time,
                            "chunk_file": chunk_path
                        }
                        
        except Exception as e:
            return {
                "processing_status": "failed",
                "error_message": str(e),
                "chunk_start_time": start_time,
                "chunk_end_time": end_time,
                "chunk_file": chunk_path
            }
    
    async def merge_chunk_results(
        self,
        chunk_results: List[Dict[str, Any]],
        output_format: str = "srt",
        enable_speaker_diarization: bool = False,
        audio_file_path: str = None
    ) -> Dict[str, Any]:
        """
        Merge transcription results from multiple chunks
        
        Args:
            chunk_results: List of chunk transcription results
            output_format: Output format (srt, txt, json)
            enable_speaker_diarization: Whether speaker diarization was enabled
            audio_file_path: Path to original audio file (needed for speaker embedding)
            
        Returns:
            Merged transcription result
        """
        try:
            print(f"🔗 Starting merge_chunk_results: {len(chunk_results)} chunks to process")
            
            # Filter successful chunks
            successful_chunks = [
                chunk for chunk in chunk_results 
                if chunk.get("processing_status") == "success"
            ]
            
            failed_chunks = [
                chunk for chunk in chunk_results 
                if chunk.get("processing_status") != "success"
            ]
            
            print(f"📊 Chunk processing results: {len(successful_chunks)} successful, {len(failed_chunks)} failed")
            
            if not successful_chunks:
                print("❌ All chunks failed - returning failure result")
                return {
                    "processing_status": "failed",
                    "error_message": "All chunks failed to process",
                    "chunks_processed": 0,
                    "chunks_failed": len(failed_chunks)
                }
            
            # Sort chunks by start time
            successful_chunks.sort(key=lambda x: x.get("chunk_start_time", 0))
            print(f"📈 Sorted {len(successful_chunks)} successful chunks by start time")
            
            # Apply speaker embedding unification if speaker diarization is enabled
            speaker_mapping = {}
            if enable_speaker_diarization and audio_file_path:
                print(f"🎤 Speaker diarization enabled, attempting speaker unification...")
                try:
                    from .speaker_embedding_service import SpeakerIdentificationService, SpeakerEmbeddingService
                    from ..utils.config import AudioProcessingConfig
                    
                    print(f"✅ Successfully imported speaker embedding services")
                    
                    # Initialize speaker services
                    embedding_manager = SpeakerEmbeddingService()
                    speaker_service = SpeakerIdentificationService(embedding_manager)
                    
                    print(f"✅ Speaker services initialized")
                    
                    # Unify speakers across chunks using embedding similarity
                    print("🎤 Unifying speakers across chunks using embedding similarity...")
                    speaker_mapping = await speaker_service.unify_distributed_speakers(
                        successful_chunks, audio_file_path
                    )
                    
                    print(f"✅ Speaker unification returned mapping with {len(speaker_mapping)} entries")
                    
                    if speaker_mapping:
                        print(f"✅ Speaker unification completed: {len(set(speaker_mapping.values()))} unified speakers")
                    else:
                        print("⚠️ Speaker unification returned empty mapping")
                        
                except Exception as e:
                    print(f"⚠️ Speaker unification failed: {e}")
                    print(f"   Exception type: {type(e).__name__}")
                    import traceback
                    print(f"   Traceback: {traceback.format_exc()}")
                    print("📋 Continuing with original speaker labels...")
                    speaker_mapping = {}
            else:
                if enable_speaker_diarization:
                    print("⚠️ Speaker diarization enabled but no audio_file_path provided")
                if audio_file_path:
                    print("ℹ️ Audio file path provided but speaker diarization disabled")
            
            # Merge segments
            all_segments = []
            total_duration = 0
            segment_count = 0
            
            # First pass: collect all segments and mark missing speakers as UNKNOWN
            print("📝 First pass: collecting segments and marking unknown speakers...")
            for chunk_idx, chunk in enumerate(successful_chunks):
                chunk_start = chunk.get("chunk_start_time", 0)
                chunk_segments = chunk.get("segments", [])
                
                for segment in chunk_segments:
                    # Adjust segment timestamps to global timeline
                    adjusted_segment = segment.copy()
                    adjusted_segment["start"] = segment["start"] + chunk_start
                    adjusted_segment["end"] = segment["end"] + chunk_start
                    
                    # Mark segments without speaker as UNKNOWN
                    if "speaker" not in segment or not segment["speaker"]:
                        adjusted_segment["speaker"] = "UNKNOWN"
                        adjusted_segment["chunk_id"] = chunk_idx
                    else:
                        # Preserve original speaker for embedding-based reassignment
                        adjusted_segment["original_speaker"] = segment["speaker"]
                        adjusted_segment["chunk_id"] = chunk_idx
                        # Temporarily use chunk-local speaker ID for embedding processing
                        adjusted_segment["speaker"] = f"chunk_{chunk_idx}_{segment['speaker']}"
                    
                    all_segments.append(adjusted_segment)
                
                segment_count += len(chunk_segments)
                chunk_duration = chunk.get("audio_duration", 0)
                if chunk_duration > 0:
                    total_duration = max(total_duration, chunk_start + chunk_duration)
            
            print(f"📊 Collected {len(all_segments)} segments from {len(successful_chunks)} chunks")
            
            # Second pass: Apply embedding-based speaker unification if enabled
            final_speaker_mapping = {}
            if enable_speaker_diarization and audio_file_path and speaker_mapping:
                print("🎤 Second pass: applying embedding-based speaker unification...")
                
                # Create final speaker mapping based on embedding results
                for mapping_key, unified_speaker_id in speaker_mapping.items():
                    final_speaker_mapping[mapping_key] = unified_speaker_id
                
                # Apply the unified speaker mapping to segments
                for segment in all_segments:
                    if segment["speaker"] != "UNKNOWN":
                        chunk_id = segment["chunk_id"]
                        original_speaker = segment.get("original_speaker", "")
                        mapping_key = f"chunk_{chunk_id}_{original_speaker}"
                        
                        if mapping_key in final_speaker_mapping:
                            segment["speaker"] = final_speaker_mapping[mapping_key]
                            print(f"🎯 Mapped chunk_{chunk_id}_{original_speaker} -> {segment['speaker']}")
                        else:
                            # Fallback: create a new speaker ID if not found in mapping
                            segment["speaker"] = f"SPEAKER_UNMATCHED_{chunk_id}_{original_speaker}"
                            print(f"⚠️ No mapping found for {mapping_key}, using fallback ID")
                
                print(f"✅ Applied speaker unification to segments")
            else:
                print("ℹ️ Speaker diarization disabled or no speaker mapping available")
                # For segments with speakers but no diarization, use chunk-local naming
                for segment in all_segments:
                    if segment["speaker"] != "UNKNOWN" and segment["speaker"].startswith("chunk_"):
                        chunk_id = segment["chunk_id"]
                        original_speaker = segment.get("original_speaker", "")
                        segment["speaker"] = f"SPEAKER_CHUNK_{chunk_id}_{original_speaker}"
            
            # Third pass: Filter and generate output files
            print("📄 Third pass: generating output files...")
            
            # Separate segments by speaker type
            known_speaker_segments = [seg for seg in all_segments if seg["speaker"] != "UNKNOWN"]
            unknown_speaker_segments = [seg for seg in all_segments if seg["speaker"] == "UNKNOWN"]
            
            # Only filter UNKNOWN speakers if:
            # 1. Speaker diarization is enabled, AND
            # 2. There are some known speakers (meaning diarization was successful)
            should_filter_unknown = enable_speaker_diarization and len(known_speaker_segments) > 0
            
            if should_filter_unknown:
                print(f"📊 Segment distribution (diarization enabled, filtering UNKNOWN):")
                print(f"   Known speakers: {len(known_speaker_segments)} segments")
                print(f"   Unknown speakers: {len(unknown_speaker_segments)} segments (will be filtered)")
                
                # Use only known speaker segments
                segments_for_output = known_speaker_segments
            else:
                # When diarization is disabled OR no speakers were successfully identified,
                # use all segments regardless of speaker label
                if enable_speaker_diarization:
                    print(f"📊 Segment distribution (diarization enabled, but no speakers identified):")
                    print(f"   All segments: {len(all_segments)} segments (no speaker filtering - diarization failed)")
                else:
                    print(f"📊 Segment distribution (diarization disabled):")
                    print(f"   All segments: {len(all_segments)} segments (no speaker filtering)")
                
                # Use all segments
                segments_for_output = all_segments
                unknown_speaker_segments = []  # Don't count as filtered if we're not filtering
            
            # Generate output files
            output_files = self._generate_output_files(
                segments_for_output,
                output_format, 
                should_filter_unknown
            )
            
            # Collect speaker information based on filtered segments
            speaker_info = self._collect_speaker_information_from_segments(
                segments_for_output, enable_speaker_diarization
            )
            
            # Determine language (use most common language from chunks)
            languages = [chunk.get("language_detected", "unknown") for chunk in successful_chunks]
            most_common_language = max(set(languages), key=languages.count) if languages else "unknown"
            
            # Combine text from segments used for output
            full_text = " ".join([seg.get("text", "").strip() for seg in segments_for_output if seg.get("text", "").strip()])
            
            print(f"🔗 merge_chunk_results completion summary:")
            print(f"   Total segments collected: {len(all_segments)}")
            print(f"   Output segments: {len(segments_for_output)}")
            print(f"   Unknown speaker segments filtered: {len(unknown_speaker_segments)}")
            print(f"   Final text length: {len(full_text)} characters")
            print(f"   Language detected: {most_common_language}")
            print(f"   Distributed processing flag: True")
            
            return {
                "processing_status": "success",
                "txt_file_path": output_files.get("txt_file_path"),
                "srt_file_path": output_files.get("srt_file_path"),
                "audio_duration": total_duration,
                "segment_count": len(segments_for_output),  # Count segments used for output
                "total_segments_collected": len(all_segments),  # Total including any filtered segments
                "unknown_segments_filtered": len(unknown_speaker_segments),  # UNKNOWN segments count (0 if diarization disabled)
                "language_detected": most_common_language,
                "model_used": successful_chunks[0].get("model_used", "turbo") if successful_chunks else "turbo",
                "distributed_processing": True,
                "chunks_processed": len(successful_chunks),
                "chunks_failed": len(failed_chunks),
                "speaker_diarization_enabled": enable_speaker_diarization,
                "speaker_embedding_unified": len(speaker_mapping) > 0 if speaker_mapping else False,
                "text": full_text,  # Add full text for client-side file saving
                "segments": segments_for_output,  # Add segments for client-side file saving
                **speaker_info
            }
            
        except Exception as e:
            print(f"❌ Error in merge_chunk_results: {e}")
            print(f"   Exception type: {type(e).__name__}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return {
                "processing_status": "failed",
                "error_message": f"Error merging chunk results: {e}",
                "chunks_processed": len(successful_chunks) if 'successful_chunks' in locals() else 0,
                "chunks_failed": len(failed_chunks) if 'failed_chunks' in locals() else len(chunk_results)
            }
    
    def _generate_output_files(
        self, 
        segments: List[Dict], 
        output_format: str,
        should_filter_unknown: bool
    ) -> Dict[str, str]:
        """Generate output files from merged segments (filter UNKNOWN speakers only if should_filter_unknown is True)"""
        try:
            # Create output directory
            output_dir = Path(self.cache_dir) / "transcribe"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamp for unique filenames
            timestamp = int(time.time())
            base_filename = f"distributed_transcription_{timestamp}"
            
            output_files = {}
            
            # Filter segments: only include segments with actual text content
            valid_segments = []
            for segment in segments:
                text = segment.get("text", "").strip()
                speaker = segment.get("speaker", "UNKNOWN")
                
                # Skip segments with no text
                if not text:
                    continue
                
                # Only skip UNKNOWN speakers if filtering is enabled
                if should_filter_unknown and speaker == "UNKNOWN":
                    continue
                
                valid_segments.append(segment)
            
            print(f"📝 Generating output files with {len(valid_segments)} valid segments (filtered from {len(segments)} total)")
            
            # Generate TXT file
            txt_path = output_dir / f"{base_filename}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                for segment in valid_segments:
                    text = segment.get("text", "").strip()
                    if should_filter_unknown and "speaker" in segment and segment["speaker"] != "UNKNOWN":
                        f.write(f"[{segment['speaker']}] {text}\n")
                    else:
                        f.write(f"{text}\n")
            output_files["txt_file_path"] = str(txt_path)
            
            # Generate SRT file if requested
            if output_format in ["srt", "both"]:
                srt_path = output_dir / f"{base_filename}.srt"
                with open(srt_path, "w", encoding="utf-8") as f:
                    srt_index = 1
                    for segment in valid_segments:
                        start_time = self._format_srt_time(segment.get("start", 0))
                        end_time = self._format_srt_time(segment.get("end", 0))
                        text = segment.get("text", "").strip()
                        
                        if should_filter_unknown and "speaker" in segment and segment["speaker"] != "UNKNOWN":
                            text = f"[{segment['speaker']}] {text}"
                        
                        f.write(f"{srt_index}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
                        srt_index += 1
                        
                output_files["srt_file_path"] = str(srt_path)
            
            print(f"✅ Generated output files: {list(output_files.keys())}")
            return output_files
            
        except Exception as e:
            print(f"❌ Error generating output files: {e}")
            return {}
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _collect_speaker_information_from_segments(
        self, 
        segments: List[Dict], 
        enable_speaker_diarization: bool
    ) -> Dict[str, Any]:
        """Collect and merge speaker information from segments"""
        if not enable_speaker_diarization:
            return {}
        
        try:
            # Collect all speakers from segments
            all_speakers = set()
            speaker_summary = {}
            
            for segment in segments:
                speaker = segment.get("speaker", "UNKNOWN")
                if speaker != "UNKNOWN":
                    all_speakers.add(speaker)
                    
                    if speaker not in speaker_summary:
                        speaker_summary[speaker] = {
                            "total_duration": 0,
                            "segment_count": 0
                        }
                    
                    # Calculate segment duration from start and end times
                    segment_duration = segment.get("end", 0) - segment.get("start", 0)
                    speaker_summary[speaker]["total_duration"] += segment_duration
                    speaker_summary[speaker]["segment_count"] += 1
            
            return {
                "global_speaker_count": len(all_speakers),
                "speakers_detected": list(all_speakers),
                "speaker_summary": speaker_summary
            }
            
        except Exception as e:
            print(f"⚠️ Error collecting speaker information: {e}")
            print(f"   Segment data types: {[type(seg.get('duration', 0)) for seg in segments]}")
            return {
                "global_speaker_count": 0,
                "speakers_detected": [],
                "speaker_summary": {}
            }
    
    async def transcribe_audio_distributed(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: str = None,
        output_format: str = "srt",
        enable_speaker_diarization: bool = False,
        chunk_duration: int = 60,
        use_intelligent_segmentation: bool = True,
        chunk_endpoint_url: str = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using distributed processing across multiple Modal containers
        
        Args:
            audio_file_path: Path to audio file
            model_size: Whisper model size
            language: Language code
            output_format: Output format
            enable_speaker_diarization: Whether to enable speaker diarization
            chunk_duration: Duration of each chunk in seconds
            use_intelligent_segmentation: Whether to use intelligent segmentation
            chunk_endpoint_url: URL of chunk transcription endpoint
            
        Returns:
            Transcription result dictionary
        """
        temp_files = []
        
        try:
            print(f"🚀 Starting distributed transcription for: {audio_file_path}")
            print(f"🚀 Using model: {model_size}")
            print(f"⚡ Chunk duration: {chunk_duration}s")
            
            # Step 1: Split audio locally into chunks
            chunks = self.split_audio_locally(
                audio_file_path, 
                chunk_duration, 
                use_intelligent_segmentation
            )
            
            if not chunks:
                return {
                    "processing_status": "failed",
                    "error_message": "Failed to split audio into chunks"
                }
            
            temp_files.extend([chunk[0] for chunk in chunks])
            
            # Step 2: Process all chunks concurrently (no batching)
            print(f"🔄 Processing {len(chunks)} chunks concurrently across multiple containers...")
            
            # Set default chunk endpoint URL if not provided
            if not chunk_endpoint_url:
                from ..config.config import get_modal_transcribe_chunk_endpoint
                chunk_endpoint_url = get_modal_transcribe_chunk_endpoint()
            
            # Create all tasks simultaneously for maximum concurrency
            all_tasks = []
            for chunk_idx, (chunk_path, start_time, end_time) in enumerate(chunks):
                # Create a coroutine first
                coro = self.transcribe_chunk_distributed(
                    chunk_path=chunk_path,
                    start_time=start_time,
                    end_time=end_time,
                    model_size=model_size,
                    language=language,
                    enable_speaker_diarization=enable_speaker_diarization,
                    chunk_endpoint_url=chunk_endpoint_url
                )
                # Convert coroutine to Task explicitly
                task = asyncio.create_task(coro)
                all_tasks.append((chunk_idx, task))
            
            print(f"📤 Launched {len(all_tasks)} concurrent transcription tasks")
            
            # Process results as they complete (optimal resource utilization)
            chunk_results = [None] * len(chunks)  # Pre-allocate results array
            completed_count = 0
            failed_count = 0
            
            # Set timeout based on speaker diarization
            total_timeout = 1800 if enable_speaker_diarization else 1200  # 30min vs 20min total
            print(f"⏰ Total processing timeout: {total_timeout//60} minutes")
            
            try:
                # Use asyncio.wait with return_when=FIRST_COMPLETED for real-time progress
                pending_tasks = {task: chunk_idx for chunk_idx, task in all_tasks}
                
                start_time = asyncio.get_event_loop().time()
                
                while pending_tasks:
                    # Check for timeout
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > total_timeout:
                        print(f"⏰ Total timeout reached ({total_timeout//60} minutes), cancelling remaining tasks...")
                        for task in pending_tasks.keys():
                            task.cancel()
                        break
                    
                    # Wait for at least one task to complete
                    remaining_timeout = total_timeout - elapsed
                    done, pending = await asyncio.wait(
                        pending_tasks.keys(),
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=min(60, remaining_timeout)  # Check every minute
                    )
                    
                    # Process completed tasks
                    for task in done:
                        chunk_idx = pending_tasks.pop(task)
                        try:
                            result = await task
                            chunk_results[chunk_idx] = result
                            
                            if result.get("processing_status") == "success":
                                completed_count += 1
                                print(f"✅ Chunk {chunk_idx + 1}/{len(chunks)} completed successfully")
                            else:
                                failed_count += 1
                                error_msg = result.get("error_message", "Unknown error")
                                print(f"❌ Chunk {chunk_idx + 1}/{len(chunks)} failed: {error_msg}")
                                
                        except Exception as e:
                            failed_count += 1
                            chunk_results[chunk_idx] = {
                                "processing_status": "failed",
                                "error_message": str(e),
                                "chunk_start_time": chunks[chunk_idx][1],
                                "chunk_end_time": chunks[chunk_idx][2],
                                "chunk_file": chunks[chunk_idx][0]
                            }
                            print(f"❌ Chunk {chunk_idx + 1}/{len(chunks)} exception: {e}")
                    
                    # Show progress
                    total_processed = completed_count + failed_count
                    if total_processed > 0:
                        print(f"📊 Progress: {total_processed}/{len(chunks)} chunks processed "
                              f"({completed_count} ✅, {failed_count} ❌)")
                
                # Handle any remaining cancelled tasks
                for task, chunk_idx in pending_tasks.items():
                    if chunk_results[chunk_idx] is None:
                        chunk_results[chunk_idx] = {
                            "processing_status": "failed",
                            "error_message": "Task cancelled due to timeout",
                            "chunk_start_time": chunks[chunk_idx][1],
                            "chunk_end_time": chunks[chunk_idx][2],
                            "chunk_file": chunks[chunk_idx][0]
                        }
                        failed_count += 1
                
            except Exception as e:
                print(f"❌ Error during concurrent processing: {e}")
                # Fill in any missing results
                for i, result in enumerate(chunk_results):
                    if result is None:
                        chunk_results[i] = {
                            "processing_status": "failed",
                            "error_message": f"Processing error: {e}",
                            "chunk_start_time": chunks[i][1],
                            "chunk_end_time": chunks[i][2],
                            "chunk_file": chunks[i][0]
                        }
            
            print(f"🏁 Concurrent processing completed: {completed_count} successful, {failed_count} failed")
            
            # Step 3: Merge results from all chunks
            print("🔗 Merging results from all chunks...")
            final_result = await self.merge_chunk_results(
                chunk_results, 
                output_format, 
                enable_speaker_diarization,
                audio_file_path
            )
            
            print(f"✅ Distributed transcription completed successfully")
            print(f"   Chunks processed: {final_result.get('chunks_processed', 0)}")
            print(f"   Chunks failed: {final_result.get('chunks_failed', 0)}")
            print(f"   Total segments: {final_result.get('segment_count', 0)}")
            print(f"   Duration: {final_result.get('audio_duration', 0):.2f}s")
            
            return final_result
            
        except Exception as e:
            return {
                "processing_status": "failed",
                "error_message": f"Distributed transcription failed: {e}",
                "chunks_processed": 0,
                "chunks_failed": len(chunks) if 'chunks' in locals() else 0
            }
        
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"⚠️ Failed to clean up temp file {temp_file}: {e}")
            
            # Clean up temporary directories
            for chunk_path, _, _ in chunks if 'chunks' in locals() else []:
                try:
                    temp_dir = os.path.dirname(chunk_path)
                    if temp_dir.startswith("/tmp/audio_chunks_"):
                        import shutil
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    print(f"⚠️ Failed to clean up temp directory: {e}") 
"""
Transcription Service
Handles audio transcription logic with support for parallel processing
"""

import whisper
import os
import json
import tempfile
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List


class TranscriptionService:
    """Service for handling audio transcription"""
    
    def __init__(self, cache_dir: str = "/tmp"):
        self.cache_dir = cache_dir
        
    def _load_cached_model(self, model_size: str = "turbo"):
        """Load Whisper model from cache directory if available"""
        try:
            # Try to load from preloaded cache first
            model_cache_dir = "/model"
            if os.path.exists(model_cache_dir):
                print(f"📦 Loading {model_size} model from cache: {model_cache_dir}")
                # Set download root to cache directory
                model = whisper.load_model(model_size, download_root=model_cache_dir)
                print(f"✅ Successfully loaded {model_size} model from cache")
                return model
            else:
                print(f"⚠️ Cache directory not found, downloading {model_size} model...")
                return whisper.load_model(model_size)
        except Exception as e:
            print(f"⚠️ Failed to load cached model, downloading: {e}")
            return whisper.load_model(model_size)
    
    def _load_speaker_diarization_pipeline(self):
        """Load speaker diarization pipeline from cache if available"""
        try:
            speaker_cache_dir = "/model/speaker-diarization"
            config_file = os.path.join(speaker_cache_dir, "download_complete.json")
            
            # Set proper cache directory for pyannote
            os.environ["PYANNOTE_CACHE"] = "/model/speaker-diarization"
            
            # Check if cached speaker diarization models exist
            if os.path.exists(config_file):
                print(f"📦 Loading speaker diarization from cache: {speaker_cache_dir}")
                # Load from cache with proper cache_dir
                from pyannote.audio import Pipeline
                
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=os.environ.get("HF_TOKEN"),
                    cache_dir="/model/speaker-diarization"
                )
                print("✅ Successfully loaded speaker diarization pipeline from cache")
                return pipeline
            else:
                print("⚠️ Speaker diarization cache not found, downloading...")
                # Download fresh if cache not available
                from pyannote.audio import Pipeline
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=os.environ.get("HF_TOKEN"),
                    cache_dir="/model/speaker-diarization"
                )
                
                # Create marker file to indicate successful download
                import json
                config = {
                    "model_name": "pyannote/speaker-diarization-3.1",
                    "cached_at": speaker_cache_dir,
                    "cache_complete": True,
                    "runtime_download": True
                }
                with open(config_file, "w") as f:
                    json.dump(config, f)
                
                return pipeline
        except Exception as e:
            print(f"⚠️ Failed to load speaker diarization pipeline: {e}")
            return None
        
    def transcribe_audio(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: str = None,
        output_format: str = "srt",
        enable_speaker_diarization: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper
        
        Args:
            audio_file_path: Path to audio file
            model_size: Whisper model size
            language: Language code (optional)
            output_format: Output format
            enable_speaker_diarization: Enable speaker identification
            
        Returns:
            Transcription result dictionary
        """
        try:
            print(f"🎤 Starting transcription for: {audio_file_path}")
            print(f"🚀 Using model: {model_size}")
        
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Load Whisper model from cache
            model = self._load_cached_model(model_size)
            
            # Load speaker diarization pipeline if enabled
            speaker_pipeline = None
            if enable_speaker_diarization:
                speaker_pipeline = self._load_speaker_diarization_pipeline()
                if speaker_pipeline is None:
                    print("⚠️ Speaker diarization disabled due to loading failure")
                    enable_speaker_diarization = False
            
            # Transcribe audio
            transcribe_options = {
                "language": language if language and language != "auto" else None,
                "task": "transcribe",
                "verbose": True
            }
            
            print(f"🔄 Transcribing with options: {transcribe_options}")
            result = model.transcribe(audio_file_path, **transcribe_options)
            
            # Extract information
            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            language_detected = result.get("language", "unknown")
            
            # Apply speaker diarization if enabled
            speaker_segments = []
            global_speaker_count = 0
            speaker_summary = {}
            
            if enable_speaker_diarization and speaker_pipeline:
                try:
                    print("👥 Applying speaker diarization...")
                    diarization_result = speaker_pipeline(audio_file_path)
                    
                    # Process diarization results
                    speakers = set()
                    for turn, _, speaker in diarization_result.itertracks(yield_label=True):
                        speakers.add(speaker)
                        speaker_segments.append({
                            "start": turn.start,
                            "end": turn.end,
                            "speaker": speaker
                        })
                    
                    global_speaker_count = len(speakers)
                    speaker_summary = {f"SPEAKER_{i:02d}": speaker for i, speaker in enumerate(sorted(speakers))}
                    
                    # Merge speaker information with transcription segments
                    segments = self._merge_speaker_segments(segments, speaker_segments)
                    
                    print(f"✅ Speaker diarization completed: {global_speaker_count} speakers detected")
                    
                except Exception as e:
                    print(f"⚠️ Speaker diarization failed: {e}")
                    enable_speaker_diarization = False
            
            # Generate output files
            output_files = self._generate_output_files(
                audio_file_path, text, segments, enable_speaker_diarization
            )
            
            # Get audio duration
            audio_duration = 0.0
            if segments:
                audio_duration = max(seg.get("end", 0) for seg in segments)
            
            print(f"✅ Transcription completed successfully")
            print(f"   Text length: {len(text)} characters")
            print(f"   Segments: {len(segments)}")
            print(f"   Duration: {audio_duration:.2f}s")
            print(f"   Language: {language_detected}")
            
            return {
                "txt_file_path": output_files.get("txt_file"),
                "srt_file_path": output_files.get("srt_file"),
                "audio_file": audio_file_path,
                "model_used": model_size,
                "segment_count": len(segments),
                "audio_duration": audio_duration,
                "processing_status": "success",
                "saved_files": [f for f in output_files.values() if f],
                "speaker_diarization_enabled": enable_speaker_diarization,
                "global_speaker_count": global_speaker_count,
                "speaker_summary": speaker_summary,
                "language_detected": language_detected,
                "text": text,
                "segments": [
                    {
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "text": seg.get("text", "").strip(),
                        "speaker": seg.get("speaker", None)
                    }
                    for seg in segments
                ]
            }
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return self._create_error_result(audio_file_path, model_size, str(e))
    
    def _merge_speaker_segments(self, transcription_segments: List[Dict], speaker_segments: List[Dict]) -> List[Dict]:
        """
        Merge speaker information with transcription segments, splitting transcription segments
        when multiple speakers are detected within a single segment
        """
        merged_segments = []
        
        for trans_seg in transcription_segments:
            trans_start = trans_seg.get("start", 0)
            trans_end = trans_seg.get("end", 0)
            trans_text = trans_seg.get("text", "").strip()
            
            # Find all overlapping speaker segments
            overlapping_speakers = []
            for speaker_seg in speaker_segments:
                speaker_start = speaker_seg["start"]
                speaker_end = speaker_seg["end"]
                
                # Check if there's any overlap
                overlap_start = max(trans_start, speaker_start)
                overlap_end = min(trans_end, speaker_end)
                overlap_duration = max(0, overlap_end - overlap_start)
                
                if overlap_duration > 0:
                    overlapping_speakers.append({
                        "speaker": speaker_seg["speaker"],
                        "start": speaker_start,
                        "end": speaker_end,
                        "overlap_start": overlap_start,
                        "overlap_end": overlap_end,
                        "overlap_duration": overlap_duration
                    })
            
            if not overlapping_speakers:
                # No speaker detected, keep original segment
                merged_seg = trans_seg.copy()
                merged_seg["speaker"] = None
                merged_segments.append(merged_seg)
                continue
            
            # Sort overlapping speakers by start time
            overlapping_speakers.sort(key=lambda x: x["overlap_start"])
            
            if len(overlapping_speakers) == 1:
                # Single speaker for this transcription segment
                merged_seg = trans_seg.copy()
                merged_seg["speaker"] = overlapping_speakers[0]["speaker"]
                merged_segments.append(merged_seg)
            else:
                # Multiple speakers detected - split the transcription segment
                print(f"🔄 Splitting segment ({trans_start:.2f}s-{trans_end:.2f}s) with {len(overlapping_speakers)} speakers")
                split_segments = self._split_transcription_segment(
                    trans_seg, overlapping_speakers, trans_text
                )
                merged_segments.extend(split_segments)
        
        return merged_segments
    
    def _split_transcription_segment(self, trans_seg: Dict, overlapping_speakers: List[Dict], trans_text: str) -> List[Dict]:
        """
        Split a transcription segment into multiple segments based on speaker changes
        """
        split_segments = []
        trans_start = trans_seg.get("start", 0)
        trans_end = trans_seg.get("end", 0)
        trans_duration = trans_end - trans_start
        
        # Calculate the proportion of text for each speaker based on overlap duration
        total_overlap_duration = sum(sp["overlap_duration"] for sp in overlapping_speakers)
        
        if total_overlap_duration == 0:
            # Fallback: equal distribution
            text_per_speaker = len(trans_text) // len(overlapping_speakers)
        
        current_text_pos = 0
        for i, speaker_info in enumerate(overlapping_speakers):
            # Calculate text portion for this speaker
            if total_overlap_duration > 0:
                text_proportion = speaker_info["overlap_duration"] / total_overlap_duration
            else:
                text_proportion = 1.0 / len(overlapping_speakers)
            
            # Calculate text length for this speaker
            if i == len(overlapping_speakers) - 1:
                # Last speaker gets remaining text
                speaker_text_length = len(trans_text) - current_text_pos
            else:
                speaker_text_length = int(len(trans_text) * text_proportion)
            
            # Extract text for this speaker
            speaker_text_end = min(current_text_pos + speaker_text_length, len(trans_text))
            speaker_text = trans_text[current_text_pos:speaker_text_end].strip()
            
            # Adjust word boundaries to avoid cutting words in half
            if speaker_text_end < len(trans_text) and i < len(overlapping_speakers) - 1:
                # Find the last complete word
                last_space = speaker_text.rfind(' ')
                if last_space > 0:
                    speaker_text = speaker_text[:last_space]
                    speaker_text_end = current_text_pos + last_space + 1  # +1 to skip the space
                else:
                    # If no space found, keep original text but update position
                    speaker_text_end = current_text_pos + speaker_text_length
            
            # Use actual speaker diarization timing directly
            segment_start = speaker_info["overlap_start"]
            segment_end = speaker_info["overlap_end"]
            
            # Always create segment if we have valid timing, even with empty text
            if segment_start < segment_end:
                split_segment = {
                    "start": segment_start,
                    "end": segment_end,
                    "text": speaker_text,
                    "speaker": speaker_info["speaker"]
                }
                split_segments.append(split_segment)
                print(f"   → {speaker_info['speaker']}: {segment_start:.2f}s-{segment_end:.2f}s: \"{speaker_text[:50]}{'...' if len(speaker_text) > 50 else ''}\"")
            
            current_text_pos = speaker_text_end
        
        return split_segments
    
    def transcribe_audio_parallel(
        self,
        audio_file_path: str,
        model_size: str = "turbo",
        language: str = None,
        output_format: str = "srt",
        enable_speaker_diarization: bool = False,
        chunk_duration: int = 300
    ) -> Dict[str, Any]:
        """
        Transcribe audio with parallel processing for long files
        
        Args:
            audio_file_path: Path to audio file
            model_size: Whisper model size
            language: Language code (optional)
            output_format: Output format
            enable_speaker_diarization: Enable speaker identification
            chunk_duration: Duration of chunks in seconds
            
        Returns:
            Transcription result dictionary
        """
        try:
            print(f"🎤 Starting parallel transcription for: {audio_file_path}")
            print(f"🚀 Using model: {model_size}")
            print(f"⚡ Chunk duration: {chunk_duration}s")
            
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Get audio duration
            total_duration = self._get_audio_duration(audio_file_path)
            print(f"📊 Total audio duration: {total_duration:.2f}s")
            
            # If audio is shorter than chunk duration, use single processing
            if total_duration <= chunk_duration:
                print("📝 Audio is short, using single processing")
                return self.transcribe_audio(
                    audio_file_path, model_size, language, output_format, enable_speaker_diarization
                )
            
            # Split audio into chunks
            chunks = self._split_audio_into_chunks(audio_file_path, chunk_duration, total_duration)
            print(f"🔀 Created {len(chunks)} chunks for parallel processing")
            
            # Load Whisper model once from cache
            model = self._load_cached_model(model_size)
            
            # Process chunks in parallel
            chunk_results = self._process_chunks_parallel(chunks, model, language)
            
            # Combine results
            combined_result = self._combine_chunk_results(
                chunk_results, audio_file_path, model_size, 
                enable_speaker_diarization, total_duration
            )
            
            # Cleanup chunk files
            self._cleanup_chunks(chunks)
            
            return combined_result
            
        except Exception as e:
            print(f"❌ Parallel transcription failed: {e}")
            result = self._create_error_result(audio_file_path, model_size, str(e))
            result["parallel_processing"] = True
            return result
    
    def normalize_audio_file(self, input_file: str, output_file: str = None) -> str:
        """
        Normalize audio file for better Whisper compatibility
        
        Args:
            input_file: Input audio file path
            output_file: Output file path (optional)
            
        Returns:
            Path to normalized audio file
        """
        if output_file is None:
            temp_dir = tempfile.mkdtemp()
            output_file = os.path.join(temp_dir, "normalized_audio.wav")
        
        # Convert to standardized format: 16kHz, mono, PCM
        cmd = [
            "ffmpeg", "-i", input_file,
            "-ar", "16000",  # 16kHz sample rate (Whisper's native)
            "-ac", "1",      # Mono channel
            "-c:a", "pcm_s16le",  # PCM 16-bit encoding
            "-y",  # Overwrite output file
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️ FFmpeg normalization failed: {result.stderr}")
            return input_file  # Return original file if normalization fails
        else:
            print("✅ Audio normalized for Whisper")
            return output_file
    
    def _get_audio_duration(self, audio_file_path: str) -> float:
        """Get audio duration using ffprobe"""
        cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", audio_file_path]
        duration_output = subprocess.run(cmd, capture_output=True, text=True)
        return float(duration_output.stdout.strip())
    
    def _split_audio_into_chunks(self, audio_file_path: str, chunk_duration: int, total_duration: float) -> List[Dict]:
        """Split audio file into chunks for parallel processing"""
        chunks = []
        temp_dir = tempfile.mkdtemp()
        
        for i in range(0, int(total_duration), chunk_duration):
            chunk_start = i
            chunk_end = min(i + chunk_duration, total_duration)
            chunk_file = os.path.join(temp_dir, f"chunk_{i//chunk_duration:03d}.wav")
            
            # Extract chunk using ffmpeg
            cmd = [
                "ffmpeg", "-i", audio_file_path,
                "-ss", str(chunk_start),
                "-t", str(chunk_end - chunk_start),
                "-c:a", "pcm_s16le",  # Use PCM encoding for better quality
                "-ar", "16000",  # 16kHz sample rate for Whisper
                chunk_file
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if os.path.exists(chunk_file):
                chunks.append({
                    "file": chunk_file,
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                    "index": len(chunks),
                    "temp_dir": temp_dir
                })
                print(f"📦 Created chunk {len(chunks)}: {chunk_start:.1f}s-{chunk_end:.1f}s")
        
        return chunks
    
    def _process_chunks_parallel(self, chunks: List[Dict], model, language: str) -> List[Dict]:
        """Process audio chunks in parallel"""
        def process_chunk(chunk_info):
            try:
                print(f"🔄 Processing chunk {chunk_info['index']}: {chunk_info['start_time']:.1f}s-{chunk_info['end_time']:.1f}s")
                
                transcribe_options = {
                    "language": language if language and language != "auto" else None,
                    "task": "transcribe",
                    "verbose": False  # Reduce verbosity for parallel processing
                }
                
                result = model.transcribe(chunk_info["file"], **transcribe_options)
                
                # Adjust segment timing to global timeline
                segments = []
                for seg in result.get("segments", []):
                    adjusted_seg = {
                        "start": seg["start"] + chunk_info["start_time"],
                        "end": seg["end"] + chunk_info["start_time"],
                        "text": seg["text"].strip(),
                        "speaker": None
                    }
                    segments.append(adjusted_seg)
                
                print(f"✅ Chunk {chunk_info['index']} completed: {len(segments)} segments")
                
                return {
                    "text": result.get("text", "").strip(),
                    "segments": segments,
                    "language": result.get("language", "unknown"),
                    "chunk_index": chunk_info["index"]
                }
                
            except Exception as e:
                print(f"❌ Chunk {chunk_info['index']} failed: {e}")
                return {
                    "text": "",
                    "segments": [],
                    "language": "unknown",
                    "chunk_index": chunk_info["index"],
                    "error": str(e)
                }
        
        # Process chunks in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(chunks), 8)) as executor:
            chunk_results = list(executor.map(process_chunk, chunks))
        
        # Sort results by chunk index
        chunk_results.sort(key=lambda x: x["chunk_index"])
        return chunk_results
    
    def _combine_chunk_results(
        self, 
        chunk_results: List[Dict], 
        audio_file_path: str, 
        model_size: str, 
        enable_speaker_diarization: bool,
        total_duration: float
    ) -> Dict[str, Any]:
        """Combine results from multiple chunks"""
        # Combine results
        full_text = " ".join([chunk["text"] for chunk in chunk_results if chunk["text"]])
        all_segments = []
        for chunk in chunk_results:
            all_segments.extend(chunk["segments"])
        
        # Sort segments by start time
        all_segments.sort(key=lambda x: x["start"])
        
        # Get detected language (use most common one)
        languages = [chunk["language"] for chunk in chunk_results if chunk["language"] != "unknown"]
        language_detected = max(set(languages), key=languages.count) if languages else "unknown"
        
        # Generate output files
        output_files = self._generate_output_files(
            audio_file_path, full_text, all_segments, enable_speaker_diarization
        )
        
        print(f"✅ Parallel transcription completed successfully")
        print(f"   Text length: {len(full_text)} characters")
        print(f"   Total segments: {len(all_segments)}")
        print(f"   Duration: {total_duration:.2f}s")
        print(f"   Language: {language_detected}")
        print(f"   Chunks processed: {len(chunk_results)}")
        
        return {
            "txt_file_path": output_files.get("txt_file"),
            "srt_file_path": output_files.get("srt_file"),
            "audio_file": audio_file_path,
            "model_used": model_size,
            "segment_count": len(all_segments),
            "audio_duration": total_duration,
            "processing_status": "success",
            "saved_files": [f for f in output_files.values() if f],
            "speaker_diarization_enabled": enable_speaker_diarization,
            "global_speaker_count": 0,
            "speaker_summary": {},
            "language_detected": language_detected,
            "text": full_text,
            "segments": all_segments,
            "chunks_processed": len(chunk_results),
            "parallel_processing": True
        }
    
    def _cleanup_chunks(self, chunks: List[Dict]):
        """Clean up temporary chunk files"""
        temp_dirs = set()
        for chunk in chunks:
            try:
                if os.path.exists(chunk["file"]):
                    os.remove(chunk["file"])
                temp_dirs.add(chunk["temp_dir"])
            except Exception as e:
                print(f"⚠️ Failed to cleanup chunk file: {e}")
        
        # Remove temp directories
        for temp_dir in temp_dirs:
            try:
                os.rmdir(temp_dir)
            except Exception as e:
                print(f"⚠️ Failed to cleanup temp directory: {e}")
    
    def _generate_output_files(
        self, 
        audio_file_path: str, 
        text: str, 
        segments: List[Dict], 
        enable_speaker_diarization: bool
    ) -> Dict[str, str]:
        """Generate output files (TXT and SRT)"""
        base_path = Path(audio_file_path).with_suffix("")
        output_files = {}
        
        # Generate TXT file
        if text:
            txt_file = f"{base_path}.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(text)
            output_files["txt_file"] = txt_file
        
        # Generate SRT file
        if segments:
            srt_file = f"{base_path}.srt"
            srt_content = self._generate_srt_content(segments, enable_speaker_diarization)
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            output_files["srt_file"] = srt_file
        
        return output_files
    
    def _generate_srt_content(self, segments: List[Dict], include_speakers: bool = False) -> str:
        """Generate SRT format content from segments"""
        srt_lines = []
        
        for i, segment in enumerate(segments, 1):
            start_time = self._format_timestamp(segment.get('start', 0))
            end_time = self._format_timestamp(segment.get('end', 0))
            text = segment.get('text', '').strip()
            
            if include_speakers and segment.get('speaker'):
                text = f"[{segment['speaker']}] {text}"
            
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")  # Empty line between segments
        
        return "\n".join(srt_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def _create_error_result(self, audio_file_path: str, model_size: str, error_message: str) -> Dict[str, Any]:
        """Create error result dictionary"""
        return {
            "txt_file_path": None,
            "srt_file_path": None,
            "audio_file": audio_file_path,
            "model_used": model_size,
            "segment_count": 0,
            "audio_duration": 0,
            "processing_status": "failed",
            "saved_files": [],
            "speaker_diarization_enabled": False,
            "global_speaker_count": 0,
            "speaker_summary": {},
            "error_message": error_message
        } 
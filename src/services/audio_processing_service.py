"""
Audio Processing Service - integrates audio segmentation and transcription
"""

import re
import asyncio
import pathlib
import tempfile
from typing import Dict, Any, List, Optional

import ffmpeg

from ..interfaces.audio_processor import IAudioProcessor, AudioSegment
from ..interfaces.transcriber import ITranscriber
from ..interfaces.speaker_manager import ISpeakerIdentificationService
from ..utils.config import AudioProcessingConfig
from ..utils.errors import AudioProcessingError
from ..models.transcription import TranscriptionResponse, TranscriptionSegment


class AudioProcessingService(IAudioProcessor):
    """High-level audio processing service that coordinates transcription and speaker identification"""
    
    def __init__(
        self,
        transcriber: ITranscriber,
        speaker_service: Optional[ISpeakerIdentificationService] = None,
        config: Optional[AudioProcessingConfig] = None
    ):
        self.transcriber = transcriber
        self.speaker_service = speaker_service
        self.config = config or AudioProcessingConfig()
    
    async def split_audio_by_silence(
        self,
        audio_path: str,
        min_segment_length: float = 30.0,
        min_silence_length: float = 1.0
    ) -> List[AudioSegment]:
        """
        Intelligently split audio using FFmpeg's silencedetect filter
        """
        try:
            silence_end_re = re.compile(
                r" silence_end: (?P<end>[0-9]+(\.?[0-9]*)) \| silence_duration: (?P<dur>[0-9]+(\.?[0-9]*))"
            )
            
            # Get audio duration
            metadata = ffmpeg.probe(audio_path)
            duration = float(metadata["format"]["duration"])
            
            # Use silence detection filter
            reader = (
                ffmpeg.input(str(audio_path))
                .filter("silencedetect", n="-10dB", d=min_silence_length)
                .output("pipe:", format="null")
                .run_async(pipe_stderr=True)
            )
            
            segments = []
            cur_start = 0.0
            
            while True:
                line = reader.stderr.readline().decode("utf-8")
                if not line:
                    break
                    
                match = silence_end_re.search(line)
                if match:
                    silence_end, silence_dur = match.group("end"), match.group("dur")
                    split_at = float(silence_end) - (float(silence_dur) / 2)
                    
                    if (split_at - cur_start) < min_segment_length:
                        continue
                        
                    segments.append(AudioSegment(
                        start=cur_start,
                        end=split_at,
                        file_path=audio_path,
                        duration=split_at - cur_start
                    ))
                    cur_start = split_at
            
            # Handle the last segment
            if duration > cur_start:
                segments.append(AudioSegment(
                    start=cur_start,
                    end=duration,
                    file_path=audio_path,
                    duration=duration - cur_start
                ))
            
            print(f"Audio split into {len(segments)} segments")
            return segments
            
        except Exception as e:
            raise AudioProcessingError(f"Audio segmentation failed: {str(e)}")
    
    async def process_audio_segment(
        self,
        segment: AudioSegment,
        model_name: str = "turbo",
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False
    ) -> Dict[str, Any]:
        """
        Process a single audio segment
        """
        try:
            # Create temporary segment file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Extract segment using ffmpeg
            (
                ffmpeg.input(segment.file_path, ss=segment.start, t=segment.duration)
                .output(temp_path)
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Transcribe segment
            result = await self.transcriber.transcribe(
                audio_file_path=temp_path,
                model_size=model_name,
                language=language,
                enable_speaker_diarization=enable_speaker_diarization
            )
            
            # Adjust timestamps to match original audio
            adjusted_segments = []
            for seg in result.segments:
                adjusted_segments.append(TranscriptionSegment(
                    start=seg.start + segment.start,
                    end=seg.end + segment.start,
                    text=seg.text,
                    speaker=seg.speaker,
                    confidence=seg.confidence
                ))
            
            # Clean up temp file
            pathlib.Path(temp_path).unlink(missing_ok=True)
            
            return {
                "segment_start": segment.start,
                "segment_end": segment.end,
                "text": result.text,
                "segments": [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text,
                        "speaker": seg.speaker,
                        "confidence": seg.confidence
                    } for seg in adjusted_segments
                ],
                "language_detected": result.language,
                "model_used": result.model_used
            }
            
        except Exception as e:
            raise AudioProcessingError(f"Segment processing failed: {str(e)}")
    
    async def process_complete_audio(
        self,
        audio_path: str,
        model_name: str = "turbo",
        language: Optional[str] = None,
        enable_speaker_diarization: bool = False,
        min_segment_length: float = 30.0
    ) -> Dict[str, Any]:
        """
        Process complete audio file with intelligent segmentation
        """
        try:
            print(f"🚀 Starting complete audio processing: {audio_path}")
            
            # Get audio metadata
            metadata = ffmpeg.probe(audio_path)
            total_duration = float(metadata["format"]["duration"])
            
            # Split audio into segments
            segments = await self.split_audio_by_silence(
                audio_path=audio_path,
                min_segment_length=min_segment_length,
                min_silence_length=1.0
            )
            
            # Process segments in parallel (with limited concurrency)
            semaphore = asyncio.Semaphore(3)  # Limit concurrent processing
            
            async def process_segment_with_semaphore(segment):
                async with semaphore:
                    return await self.process_audio_segment(
                        segment=segment,
                        model_name=model_name,
                        language=language,
                        enable_speaker_diarization=enable_speaker_diarization
                    )
            
            # Process all segments
            segment_results = await asyncio.gather(*[
                process_segment_with_semaphore(segment) for segment in segments
            ])
            
            # Combine results
            all_segments = []
            combined_text = []
            
            for result in segment_results:
                all_segments.extend(result["segments"])
                if result["text"].strip():
                    combined_text.append(result["text"].strip())
            
            # Apply speaker identification if enabled
            if enable_speaker_diarization and self.speaker_service:
                try:
                    speaker_segments = await self.speaker_service.identify_speakers_in_audio(
                        audio_path=audio_path,
                        transcription_segments=all_segments
                    )
                    
                    # Map transcription to speakers
                    all_segments = await self.speaker_service.map_transcription_to_speakers(
                        transcription_segments=all_segments,
                        speaker_segments=speaker_segments
                    )
                except Exception as e:
                    print(f"⚠️ Speaker identification failed: {e}")
            
            return {
                "text": " ".join(combined_text),
                "segments": all_segments,
                "audio_duration": total_duration,
                "segment_count": len(all_segments),
                "processing_segments": len(segments),
                "language_detected": segment_results[0]["language_detected"] if segment_results else "unknown",
                "model_used": model_name,
                "speaker_diarization_enabled": enable_speaker_diarization,
                "processing_status": "success"
            }
            
        except Exception as e:
            raise AudioProcessingError(f"Complete audio processing failed: {str(e)}")
    
    def get_supported_models(self) -> List[str]:
        """Get supported transcription models"""
        return self.transcriber.get_supported_models()
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        return self.transcriber.get_supported_languages() 
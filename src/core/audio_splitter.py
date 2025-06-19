"""
Audio splitter implementation using FFmpeg
"""

import re
from typing import Iterator
import ffmpeg

from ..interfaces.audio_splitter import IAudioSplitter, AudioSegment
from ..utils.errors import AudioSplittingError


class FFmpegAudioSplitter(IAudioSplitter):
    """Audio splitter using FFmpeg's silence detection"""
    
    def split_audio(
        self,
        audio_path: str,
        min_segment_length: float = 30.0,
        min_silence_length: float = 1.0
    ) -> Iterator[AudioSegment]:
        """Split audio by silence detection"""
        
        try:
            silence_end_re = re.compile(
                r" silence_end: (?P<end>[0-9]+(\.?[0-9]*)) \| silence_duration: (?P<dur>[0-9]+(\.?[0-9]*))"
            )
            
            # Get audio duration
            duration = self.get_audio_duration(audio_path)
            
            # Use silence detection filter
            reader = (
                ffmpeg.input(str(audio_path))
                .filter("silencedetect", n="-10dB", d=min_silence_length)
                .output("pipe:", format="null")
                .run_async(pipe_stderr=True)
            )
            
            cur_start = 0.0
            segment_count = 0
            
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
                        
                    yield AudioSegment(
                        start=cur_start,
                        end=split_at,
                        duration=split_at - cur_start
                    )
                    cur_start = split_at
                    segment_count += 1
            
            # Handle the last segment
            if duration > cur_start:
                yield AudioSegment(
                    start=cur_start,
                    end=duration,
                    duration=duration - cur_start
                )
                segment_count += 1
            
            print(f"Audio split into {segment_count} segments")
            
        except Exception as e:
            raise AudioSplittingError(
                f"Failed to split audio: {str(e)}",
                audio_file=audio_path
            )
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get total duration of audio file"""
        try:
            metadata = ffmpeg.probe(audio_path)
            return float(metadata["format"]["duration"])
        except Exception as e:
            raise AudioSplittingError(
                f"Failed to get audio duration: {str(e)}",
                audio_file=audio_path
            ) 
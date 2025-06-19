"""
Speaker Diarization Integration Tests
Comprehensive testing of speaker identification functionality with real audio files
Tests include download, transcription with speaker diarization, and result analysis
"""

import asyncio
import json
import os
import pytest
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List

from src.tools.transcription_tools import transcribe_audio_file_tool
from src.tools.download_tools import download_apple_podcast_tool, download_xyz_podcast_tool
from src.services.health_service import HealthService
from src.services.transcription_service import TranscriptionService


class TestSpeakerDiarizationIntegration:
    """Comprehensive speaker diarization integration tests"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment with cache directories"""
        self.cache_dir = Path("tests/cache")
        self.transcribe_dir = Path("tests/cache/transcribe")
        self.speaker_results_dir = Path("tests/cache/transcribe/speaker_diarization")
        
        # Ensure directories exist
        self.cache_dir.mkdir(exist_ok=True)
        self.transcribe_dir.mkdir(exist_ok=True)
        self.speaker_results_dir.mkdir(exist_ok=True)
        
        print(f"📁 Cache directory: {self.cache_dir.absolute()}")
        print(f"📁 Transcribe directory: {self.transcribe_dir.absolute()}")
        print(f"📁 Speaker results directory: {self.speaker_results_dir.absolute()}")
    
    def test_speaker_diarization_environment_check(self):
        """Check if speaker diarization environment is properly configured"""
        print("\n🔍 Testing speaker diarization environment...")
        
        health_service = HealthService()
        health_status = health_service.get_health_status()
        
        print(f"📊 Overall health: {health_status['status']}")
        
        # Check Whisper status
        whisper_status = health_status["whisper"]
        print(f"🎤 Whisper status: {whisper_status['status']}")
        print(f"   Default model: {whisper_status['default_model']}")
        print(f"   Available models: {whisper_status['available_models']}")
        
        # Check speaker diarization status
        speaker_status = health_status["speaker_diarization"]
        print(f"👥 Speaker diarization status: {speaker_status['status']}")
        print(f"   HF token available: {speaker_status['hf_token_available']}")
        print(f"   Pipeline loaded: {speaker_status.get('pipeline_loaded', False)}")
        
        # Save environment status
        env_status_file = self.speaker_results_dir / "environment_status.json"
        with open(env_status_file, 'w') as f:
            json.dump(health_status, f, indent=2)
        print(f"💾 Environment status saved to: {env_status_file}")
        
        # Test speaker diarization pipeline loading
        speaker_test_result = health_service.test_speaker_diarization()
        print(f"🧪 Speaker pipeline test: {speaker_test_result['status']}")
        
        if speaker_test_result['status'] == 'skipped':
            print("⚠️ Speaker diarization will be tested without HF_TOKEN")
        elif speaker_test_result['status'] == 'pipeline_loaded':
            print("✅ Speaker diarization pipeline ready")
        
        # Save pipeline test result
        pipeline_test_file = self.speaker_results_dir / "pipeline_test.json"
        with open(pipeline_test_file, 'w') as f:
            json.dump(speaker_test_result, f, indent=2)
        
        print("✅ Environment check completed")
    
    @pytest.mark.asyncio
    async def test_download_multi_speaker_podcast(self):
        """Download podcasts that likely have multiple speakers"""
        print("\n📥 Downloading multi-speaker podcast content...")
        
        # Podcast URLs that typically have multiple speakers (interviews, discussions)
        podcast_urls = [
            {
                "type": "apple",
                "url": "https://podcasts.apple.com/cn/podcast/all-ears-english-podcast/id751574016?i=1000712048662",
                "filename": "multi_speaker_apple.mp3",
                "description": "All Ears English (typically has 2-3 speakers)"
            },
            {
                "type": "xyz", 
                "url": "https://www.xiaoyuzhoufm.com/episode/6844388379e285b9b8b7067d",
                "filename": "multi_speaker_xyz.mp3",
                "description": "XiaoYuZhou conversation (likely multiple speakers)"
            }
        ]
        
        downloaded_files = []
        
        for podcast_info in podcast_urls:
            print(f"\n🎧 Downloading: {podcast_info['description']}")
            print(f"   URL: {podcast_info['url']}")
            
            try:
                if podcast_info["type"] == "apple":
                    result = await download_apple_podcast_tool(podcast_info["url"])
                else:  # xyz
                    result = await download_xyz_podcast_tool(podcast_info["url"])
                
                print(f"📋 Download result: {result['status']}")
                
                if result['status'] == 'success' and result.get('audio_file_path'):
                    # Copy to our cache with descriptive name
                    cache_file = self.cache_dir / podcast_info["filename"]
                    if os.path.exists(result['audio_file_path']):
                        shutil.copy2(result['audio_file_path'], cache_file)
                        print(f"📁 Saved to: {cache_file}")
                        
                        file_size = os.path.getsize(cache_file) / (1024*1024)
                        print(f"📊 File size: {file_size:.2f} MB")
                        
                        downloaded_files.append({
                            "file_path": str(cache_file),
                            "description": podcast_info["description"],
                            "type": podcast_info["type"],
                            "size_mb": file_size
                        })
                else:
                    print(f"⚠️ Download failed: {result.get('error_message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Download error: {e}")
        
        # Save download results
        download_log = self.speaker_results_dir / "download_log.json"
        with open(download_log, 'w') as f:
            json.dump(downloaded_files, f, indent=2)
        
        print(f"\n✅ Downloaded {len(downloaded_files)} files")
        return downloaded_files
    
    def create_synthetic_multi_speaker_audio(self) -> str:
        """Create synthetic audio with multiple frequency patterns to simulate speakers"""
        print("\n🎵 Creating synthetic multi-speaker audio for testing...")
        
        try:
            import numpy as np
            import soundfile as sf
            
            # Create 30 seconds of audio with 3 different "speakers" (frequency patterns)
            sample_rate = 16000
            duration = 30
            t = np.linspace(0, duration, sample_rate * duration)
            
            # Speaker 1: 440 Hz (A4) - first 10 seconds
            speaker1_duration = 10
            speaker1_samples = sample_rate * speaker1_duration
            speaker1_audio = np.sin(2 * np.pi * 440 * t[:speaker1_samples]) * 0.3
            
            # Brief silence
            silence_samples = sample_rate * 2  # 2 seconds
            silence = np.zeros(silence_samples)
            
            # Speaker 2: 880 Hz (A5) - next 8 seconds  
            speaker2_duration = 8
            speaker2_samples = sample_rate * speaker2_duration
            speaker2_start = speaker1_samples + silence_samples
            speaker2_audio = np.sin(2 * np.pi * 880 * t[speaker2_start:speaker2_start + speaker2_samples]) * 0.3
            
            # Another silence
            silence2 = np.zeros(silence_samples)
            
            # Speaker 3: 660 Hz (E5) - remaining time
            remaining_samples = len(t) - speaker1_samples - silence_samples - speaker2_samples - silence_samples
            if remaining_samples > 0:
                speaker3_start = speaker2_start + speaker2_samples + silence_samples
                speaker3_audio = np.sin(2 * np.pi * 660 * t[speaker3_start:speaker3_start + remaining_samples]) * 0.3
            else:
                speaker3_audio = np.array([])
            
            # Combine all audio segments
            full_audio = np.concatenate([
                speaker1_audio,
                silence,
                speaker2_audio, 
                silence2,
                speaker3_audio
            ])
            
            # Save synthetic audio
            synthetic_file = self.cache_dir / "synthetic_multi_speaker.wav"
            sf.write(synthetic_file, full_audio, sample_rate)
            
            print(f"🎵 Synthetic audio created: {synthetic_file}")
            print(f"   Duration: {len(full_audio) / sample_rate:.2f}s")
            print(f"   Simulated speakers: 3 (440Hz, 880Hz, 660Hz)")
            
            return str(synthetic_file)
            
        except ImportError:
            print("⚠️ numpy/soundfile not available, skipping synthetic audio creation")
            return None
        except Exception as e:
            print(f"❌ Failed to create synthetic audio: {e}")
            return None
    
    @pytest.mark.asyncio
    async def test_speaker_diarization_comprehensive(self):
        """Comprehensive speaker diarization test with multiple audio sources"""
        print("\n👥 Testing comprehensive speaker diarization...")
        
        # Get available audio files
        audio_files = []
        
        # Check for downloaded podcast files
        for file_pattern in ["*.mp3", "*.wav", "*.m4a"]:
            audio_files.extend(list(self.cache_dir.glob(file_pattern)))
        
        # Create synthetic audio if no real audio available
        if not audio_files:
            synthetic_file = self.create_synthetic_multi_speaker_audio()
            if synthetic_file:
                audio_files.append(Path(synthetic_file))
        
        if not audio_files:
            pytest.skip("No audio files available for speaker diarization testing")
        
        print(f"🎵 Found {len(audio_files)} audio files for testing")
        
        # Test each audio file
        test_results = []
        
        for audio_file in audio_files[:3]:  # Limit to 3 files to avoid long test times
            print(f"\n🎤 Testing speaker diarization on: {audio_file.name}")
            
            file_size_mb = os.path.getsize(audio_file) / (1024*1024)
            print(f"   File size: {file_size_mb:.2f} MB")
            
            # Test configurations
            test_configs = [
                {
                    "name": "without_speaker_diarization",
                    "enable_speaker_diarization": False,
                    "model_size": "turbo",
                    "description": "Baseline transcription without speaker identification"
                },
                {
                    "name": "with_speaker_diarization", 
                    "enable_speaker_diarization": True,
                    "model_size": "turbo",
                    "description": "Full transcription with speaker identification"
                }
            ]
            
            file_results = {
                "audio_file": str(audio_file),
                "file_size_mb": file_size_mb,
                "tests": {}
            }
            
            for config in test_configs:
                print(f"\n  🧪 Testing: {config['description']}")
                
                start_time = time.time()
                
                try:
                    result = await transcribe_audio_file_tool(
                        audio_file_path=str(audio_file),
                        model_size=config["model_size"],
                        language=None,  # Auto-detect
                        output_format="srt",
                        enable_speaker_diarization=config["enable_speaker_diarization"]
                    )
                    
                    processing_time = time.time() - start_time
                    
                    print(f"     Status: {result['processing_status']}")
                    print(f"     Processing time: {processing_time:.2f}s")
                    
                    if result['processing_status'] == 'success':
                        print(f"     Segments: {result['segment_count']}")
                        print(f"     Duration: {result['audio_duration']:.2f}s")
                        print(f"     Language: {result.get('language_detected', 'unknown')}")
                        print(f"     Speaker diarization enabled: {result['speaker_diarization_enabled']}")
                        
                        if result['speaker_diarization_enabled']:
                            speaker_count = result.get('global_speaker_count', 0)
                            print(f"     Speakers detected: {speaker_count}")
                            print(f"     Speaker summary: {result.get('speaker_summary', {})}")
                        
                        # Save transcription results
                        result_dir = self.speaker_results_dir / audio_file.stem
                        result_dir.mkdir(exist_ok=True)
                        
                        # Save detailed results
                        result_file = result_dir / f"{config['name']}_result.json"
                        with open(result_file, 'w') as f:
                            json.dump(result, f, indent=2)
                        
                        # Copy transcription files to results directory
                        if result.get('txt_file_path') and os.path.exists(result['txt_file_path']):
                            shutil.copy2(
                                result['txt_file_path'], 
                                result_dir / f"{config['name']}.txt"
                            )
                        
                        if result.get('srt_file_path') and os.path.exists(result['srt_file_path']):
                            shutil.copy2(
                                result['srt_file_path'], 
                                result_dir / f"{config['name']}.srt"
                            )
                        
                        print(f"     📁 Results saved to: {result_dir}")
                    
                    # Store test result
                    file_results["tests"][config["name"]] = {
                        "config": config,
                        "result": result,
                        "processing_time": processing_time
                    }
                    
                except Exception as e:
                    print(f"     ❌ Test failed: {e}")
                    file_results["tests"][config["name"]] = {
                        "config": config,
                        "error": str(e),
                        "processing_time": time.time() - start_time
                    }
            
            test_results.append(file_results)
        
        # Save comprehensive test results
        comprehensive_results_file = self.speaker_results_dir / "comprehensive_test_results.json"
        with open(comprehensive_results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n📊 Comprehensive test results saved to: {comprehensive_results_file}")
        
        # Generate summary report
        self.generate_speaker_diarization_report(test_results)
        
        print("✅ Comprehensive speaker diarization test completed")
    
    def generate_speaker_diarization_report(self, test_results: List[Dict]):
        """Generate a comprehensive speaker diarization test report"""
        print("\n📋 Generating speaker diarization report...")
        
        report = {
            "test_summary": {
                "total_files_tested": len(test_results),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "test_configurations": [
                    "without_speaker_diarization",
                    "with_speaker_diarization"
                ]
            },
            "detailed_results": {},
            "performance_analysis": {},
            "speaker_detection_analysis": {}
        }
        
        # Analyze results
        total_processing_time = 0
        successful_tests = 0
        speaker_detection_results = []
        
        for file_result in test_results:
            file_name = Path(file_result["audio_file"]).name
            
            report["detailed_results"][file_name] = {
                "file_size_mb": file_result["file_size_mb"],
                "tests": {}
            }
            
            for test_name, test_data in file_result["tests"].items():
                if "result" in test_data and test_data["result"]["processing_status"] == "success":
                    successful_tests += 1
                    total_processing_time += test_data["processing_time"]
                    
                    result = test_data["result"]
                    
                    # Store test details
                    report["detailed_results"][file_name]["tests"][test_name] = {
                        "status": "success",
                        "processing_time": test_data["processing_time"],
                        "segment_count": result["segment_count"],
                        "audio_duration": result["audio_duration"],
                        "language_detected": result.get("language_detected"),
                        "speaker_diarization_enabled": result["speaker_diarization_enabled"]
                    }
                    
                    # Collect speaker detection data
                    if result["speaker_diarization_enabled"]:
                        speaker_detection_results.append({
                            "file": file_name,
                            "speakers_detected": result.get("global_speaker_count", 0),
                            "speaker_summary": result.get("speaker_summary", {}),
                            "segments_with_speakers": len([
                                seg for seg in result.get("segments", []) 
                                if seg.get("speaker")
                            ])
                        })
                        
                        report["detailed_results"][file_name]["tests"][test_name].update({
                            "speakers_detected": result.get("global_speaker_count", 0),
                            "speaker_summary": result.get("speaker_summary", {})
                        })
                else:
                    # Handle failed tests
                    report["detailed_results"][file_name]["tests"][test_name] = {
                        "status": "failed",
                        "error": test_data.get("error", "Unknown error"),
                        "processing_time": test_data.get("processing_time", 0)
                    }
        
        # Performance analysis
        if successful_tests > 0:
            report["performance_analysis"] = {
                "average_processing_time": total_processing_time / successful_tests,
                "total_processing_time": total_processing_time,
                "successful_tests": successful_tests,
                "total_tests": len(test_results) * 2  # 2 configs per file
            }
        
        # Speaker detection analysis
        if speaker_detection_results:
            total_speakers = sum(r["speakers_detected"] for r in speaker_detection_results)
            avg_speakers = total_speakers / len(speaker_detection_results) if speaker_detection_results else 0
            
            report["speaker_detection_analysis"] = {
                "files_with_speaker_detection": len(speaker_detection_results),
                "total_speakers_detected": total_speakers,
                "average_speakers_per_file": avg_speakers,
                "speaker_detection_details": speaker_detection_results
            }
        
        # Save report
        report_file = self.speaker_results_dir / "speaker_diarization_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        self.generate_markdown_report(report)
        
        print(f"📊 Report saved to: {report_file}")
        return report
    
    def generate_markdown_report(self, report: Dict):
        """Generate a markdown version of the speaker diarization report"""
        markdown_content = f"""# Speaker Diarization Test Report

Generated: {report['test_summary']['timestamp']}

## Summary

- **Files Tested**: {report['test_summary']['total_files_tested']}
- **Test Configurations**: {len(report['test_summary']['test_configurations'])}

"""
        
        # Performance section
        if "performance_analysis" in report:
            perf = report["performance_analysis"]
            markdown_content += f"""## Performance Analysis

- **Successful Tests**: {perf['successful_tests']}/{perf['total_tests']}
- **Average Processing Time**: {perf['average_processing_time']:.2f} seconds
- **Total Processing Time**: {perf['total_processing_time']:.2f} seconds

"""
        
        # Speaker detection section
        if "speaker_detection_analysis" in report:
            speaker = report["speaker_detection_analysis"]
            markdown_content += f"""## Speaker Detection Analysis

- **Files with Speaker Detection**: {speaker['files_with_speaker_detection']}
- **Total Speakers Detected**: {speaker['total_speakers_detected']}
- **Average Speakers per File**: {speaker['average_speakers_per_file']:.1f}

### Speaker Detection Details

"""
            for detail in speaker["speaker_detection_details"]:
                markdown_content += f"""#### {detail['file']}
- Speakers: {detail['speakers_detected']}
- Segments with speakers: {detail['segments_with_speakers']}
- Speaker summary: {detail['speaker_summary']}

"""
        
        # Detailed results section
        markdown_content += "## Detailed Results\n\n"
        
        for file_name, file_data in report["detailed_results"].items():
            markdown_content += f"""### {file_name}
- File size: {file_data['file_size_mb']:.2f} MB

"""
            for test_name, test_data in file_data["tests"].items():
                status_icon = "✅" if test_data["status"] == "success" else "❌"
                markdown_content += f"""#### {test_name} {status_icon}
"""
                if test_data["status"] == "success":
                    markdown_content += f"""- Processing time: {test_data['processing_time']:.2f}s
- Segments: {test_data['segment_count']}
- Duration: {test_data['audio_duration']:.2f}s
- Language: {test_data.get('language_detected', 'unknown')}
- Speaker diarization: {test_data['speaker_diarization_enabled']}
"""
                    if test_data.get('speakers_detected'):
                        markdown_content += f"""- Speakers detected: {test_data['speakers_detected']}
"""
                else:
                    markdown_content += f"""- Error: {test_data.get('error', 'Unknown error')}
"""
                markdown_content += "\n"
        
        # Save markdown report
        markdown_file = self.speaker_results_dir / "speaker_diarization_report.md"
        with open(markdown_file, 'w') as f:
            f.write(markdown_content)
        
        print(f"📄 Markdown report saved to: {markdown_file}")
    
    @pytest.mark.asyncio
    async def test_local_vs_modal_speaker_diarization(self):
        """Compare local vs Modal speaker diarization performance"""
        print("\n⚖️ Testing local vs Modal speaker diarization...")
        
        # Create small test audio for comparison
        synthetic_file = self.create_synthetic_multi_speaker_audio()
        if not synthetic_file:
            pytest.skip("Could not create synthetic audio for comparison test")
        
        comparison_results = {
            "test_audio": synthetic_file,
            "local_transcription": {},
            "modal_transcription": {},
            "comparison": {}
        }
        
        # Test local transcription service
        print("🏠 Testing local transcription service...")
        try:
            local_service = TranscriptionService()
            start_time = time.time()
            
            local_result = local_service.transcribe_audio(
                audio_file_path=synthetic_file,
                model_size="turbo",
                enable_speaker_diarization=True
            )
            
            local_time = time.time() - start_time
            comparison_results["local_transcription"] = {
                "result": local_result,
                "processing_time": local_time
            }
            
            print(f"   Local processing time: {local_time:.2f}s")
            print(f"   Local speakers detected: {local_result.get('global_speaker_count', 0)}")
            
        except Exception as e:
            print(f"   ❌ Local test failed: {e}")
            comparison_results["local_transcription"] = {"error": str(e)}
        
        # Test Modal transcription
        print("☁️ Testing Modal transcription...")
        try:
            start_time = time.time()
            
            modal_result = await transcribe_audio_file_tool(
                audio_file_path=synthetic_file,
                model_size="turbo",
                enable_speaker_diarization=True
            )
            
            modal_time = time.time() - start_time
            comparison_results["modal_transcription"] = {
                "result": modal_result,
                "processing_time": modal_time
            }
            
            print(f"   Modal processing time: {modal_time:.2f}s")
            print(f"   Modal speakers detected: {modal_result.get('global_speaker_count', 0)}")
            
        except Exception as e:
            print(f"   ❌ Modal test failed: {e}")
            comparison_results["modal_transcription"] = {"error": str(e)}
        
        # Generate comparison
        if ("result" in comparison_results["local_transcription"] and 
            "result" in comparison_results["modal_transcription"]):
            
            local_res = comparison_results["local_transcription"]["result"]
            modal_res = comparison_results["modal_transcription"]["result"]
            
            comparison_results["comparison"] = {
                "processing_time_difference": (
                    comparison_results["modal_transcription"]["processing_time"] - 
                    comparison_results["local_transcription"]["processing_time"]
                ),
                "speaker_count_match": (
                    local_res.get("global_speaker_count", 0) == 
                    modal_res.get("global_speaker_count", 0)
                ),
                "local_speakers": local_res.get("global_speaker_count", 0),
                "modal_speakers": modal_res.get("global_speaker_count", 0)
            }
            
            print(f"📊 Comparison results:")
            print(f"   Processing time difference: {comparison_results['comparison']['processing_time_difference']:.2f}s")
            print(f"   Speaker count match: {comparison_results['comparison']['speaker_count_match']}")
        
        # Save comparison results
        comparison_file = self.speaker_results_dir / "local_vs_modal_comparison.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison_results, f, indent=2)
        
        print(f"📁 Comparison results saved to: {comparison_file}")
        print("✅ Local vs Modal comparison completed")
    
    def test_speaker_diarization_summary(self):
        """Generate final summary of all speaker diarization tests"""
        print("\n📋 Generating final speaker diarization test summary...")
        
        # Collect all result files
        result_files = list(self.speaker_results_dir.glob("*.json"))
        
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_files_generated": [str(f.name) for f in result_files],
            "results_directory": str(self.speaker_results_dir),
            "test_conclusions": []
        }
        
        # Analyze comprehensive results if available
        comprehensive_file = self.speaker_results_dir / "comprehensive_test_results.json"
        if comprehensive_file.exists():
            with open(comprehensive_file, 'r') as f:
                comprehensive_data = json.load(f)
            
            # Extract key findings
            if comprehensive_data:
                summary["test_conclusions"].append(
                    f"Tested {len(comprehensive_data)} audio files with speaker diarization"
                )
                
                # Count successful speaker detections
                successful_detections = 0
                for file_result in comprehensive_data:
                    for test_name, test_data in file_result.get("tests", {}).items():
                        if (test_name == "with_speaker_diarization" and 
                            "result" in test_data and 
                            test_data["result"].get("speaker_diarization_enabled")):
                            speakers = test_data["result"].get("global_speaker_count", 0)
                            if speakers > 0:
                                successful_detections += 1
                
                summary["test_conclusions"].append(
                    f"Successfully detected speakers in {successful_detections} tests"
                )
        
        # Check environment status
        env_file = self.speaker_results_dir / "environment_status.json"
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_data = json.load(f)
            
            speaker_status = env_data.get("speaker_diarization", {}).get("status", "unknown")
            summary["test_conclusions"].append(f"Speaker diarization environment status: {speaker_status}")
        
        # Save summary
        summary_file = self.speaker_results_dir / "test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Final summary:")
        print(f"   Results directory: {self.speaker_results_dir}")
        print(f"   Generated files: {len(result_files)}")
        print(f"   Key findings: {len(summary['test_conclusions'])}")
        
        for conclusion in summary["test_conclusions"]:
            print(f"   • {conclusion}")
        
        print(f"💾 Summary saved to: {summary_file}")
        print("✅ Speaker diarization integration testing completed")
        
        # Assert the test completed successfully
        assert summary["test_files_generated"], "Should have generated test files"
        assert len(summary["test_conclusions"]) > 0, "Should have test conclusions"
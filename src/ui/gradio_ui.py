"""
Gradio interface module
Contains all UI components and interface logic
"""

import gradio as gr
import asyncio
import os
from ..tools import mcp_tools
from ..tools.download_tools import get_file_info_tool, get_mp3_files_tool, read_text_file_segments_tool
from ..tools.transcription_tools import transcribe_audio_file_tool

def write_text_file_content(file_path: str, content: str, mode: str = "w", position: int = None):
    """Simple text file writing function"""
    try:
        if mode == "r+" and position is not None:
            with open(file_path, mode, encoding='utf-8') as f:
                f.seek(position)
                characters_written = f.write(content)
        else:
            with open(file_path, mode, encoding='utf-8') as f:
                characters_written = f.write(content)
        
        return {
            "status": "success",
            "characters_written": characters_written,
            "operation_type": mode,
            "size_change": len(content)
        }
    except Exception as e:
        return {
            "status": "failed",
            "error_message": str(e)
        }

def temporarily_set_hf_token(hf_token: str):
    """Temporarily set HF_TOKEN in environment"""
    original_token = os.environ.get("HF_TOKEN")
    if hf_token and hf_token.strip():
        os.environ["HF_TOKEN"] = hf_token.strip()
        print(f"🔑 Using user-provided HF_TOKEN: {hf_token[:10]}...")
    return original_token

def restore_hf_token(original_token: str):
    """Restore original HF_TOKEN in environment"""
    if original_token is not None:
        os.environ["HF_TOKEN"] = original_token
    elif "HF_TOKEN" in os.environ:
        del os.environ["HF_TOKEN"]

def get_default_directories():
    """Get default directories based on current environment"""
    import pathlib
    
    # Detect environment
    is_modal = os.environ.get("MODAL_ENVIRONMENT") == "1" or os.path.exists("/modal")
    is_docker = os.path.exists("/.dockerenv")
    current_dir = pathlib.Path.cwd()
    
    # Base directories
    base_dirs = []
    
    if is_modal:
        # Modal environment - use cache directories
        base_dirs.extend([
            "/root/cache/apple_podcasts",
            "/root/cache/xyz_podcasts",
            "/tmp/downloads"
        ])
    elif is_docker:
        # Docker environment
        base_dirs.extend([
            "/app/downloads",
            "/data/downloads",
            "/tmp/downloads"
        ])
    else:
        # Local environment - use current directory and common locations
        base_dirs.extend([
            str(current_dir / "downloads"),
            str(current_dir / "cache" / "apple_podcasts"), 
            str(current_dir / "cache" / "xyz_podcasts"),
            "~/Downloads",
            "~/Music"
        ])
    
    # Add common directories
    base_dirs.extend(["/tmp", "."])
    
    # Filter out duplicates while preserving order
    seen = set()
    unique_dirs = []
    for d in base_dirs:
        if d not in seen:
            seen.add(d)
            unique_dirs.append(d)
    
    # Determine default directory
    default_dir = unique_dirs[0] if unique_dirs else str(current_dir / "downloads")
    
    return unique_dirs, default_dir

def create_gradio_interface():
    """Create Gradio interface
    
    Returns:
        gr.Blocks: Configured Gradio interface
    """
    
    with gr.Blocks(title="ModalTranscriberMCP") as demo:
        gr.Markdown("# 🎙️ ModalTranscriberMCP")
        gr.Markdown("**Advanced Audio Transcription with Modal Cloud Computing & MCP Integration**")

        # Performance Highlight
        gr.Markdown("""
        ### ⚡ **Supercharged by Modal Serverless GPU**
        🚀 **10-20x Faster Processing**: 1-hour audio transcribed in just 3-6 minutes  
        🎯 **Parallel GPU Processing**: Up to 10 concurrent GPU containers  
        ☁️ **Zero Infrastructure Management**: Fully serverless, pay-per-use
        """, elem_classes=["performance-highlight"])
        
        # MCP Usage Instructions
        gr.Markdown("""
        ### 📚 How to Use This MCP Server
        
        This application provides both a **Web UI** and **MCP (Model Context Protocol) Tools** for AI assistants
        
        A youtube video demo is below:            
        
        [![YouTube Video](https://img.youtube.com/vi/Ut5jw7Epb0o/0.jpg)](https://youtu.be/Ut5jw7Epb0o)
        

        
        #### 🌐 Web Interface
        - Use the tabs above to download podcasts and transcribe audio files
        - Support for multi-platform downloads (Apple Podcasts, XiaoYuZhou)
        - Advanced features: speaker diarization (requires Hugging Face Token), multiple output formats
        - **High-speed processing**: Powered by Modal's distributed GPU infrastructure
        
        #### 🤖 MCP Integration
        **For AI Assistants (Claude, etc.):**
        ```
        MCP Server URL: /api/mcp
        Available Tools:
        • transcribe_audio_file_tool - High-quality audio transcription
        • download_apple_podcast_tool - Apple Podcasts audio download
        • download_xyz_podcast_tool - XiaoYuZhou podcast download
        • get_mp3_files_tool - Scan directories for audio files
        • get_file_info_tool - Get file information
        • read_text_file_segments_tool - Read large text files in chunks
        ```
        
        **Connect via MCP Client:**

        we deploy mcp server on modal, and we can use the url to connect to the gradio ui.
        The URL is configured via environment variables (see config.env.example).
        
        Current configuration:
        ```json
        {
            "mcpServers": {
                "podcast-mcp": {
                    "url": "MODAL_GRADIO_UI_ENDPOINT/api/mcp"
                }
            }
        }
        ```
        """, elem_classes=["mcp-instructions"])
        
        # ==================== Podcast Download Tab ====================
        with gr.Tab("Podcast Download"):
            gr.Markdown("### 🎙️ Download Podcast Audio")
            
            url_input = gr.Textbox(
                label="Podcast Link",
                placeholder="Enter podcast page URL",
                lines=1
            )
            
            platform_choice = gr.Radio(
                choices=["Apple Podcast", "XiaoYuZhou"],
                label="Select Podcast Platform",
                value="Apple Podcast"
            )
            
            # Transcription options
            with gr.Row():
                auto_transcribe = gr.Checkbox(
                    label="Auto-transcribe after download",
                    value=True,
                    info="Start transcription immediately after download"
                )
                enable_speaker_diarization = gr.Checkbox(
                    label="Enable speaker diarization",
                    value=False,
                    info="Identify different speakers (requires Hugging Face Token)"
                )
            
                # HF Token input for speaker diarization
                hf_token_input_download = gr.Textbox(
                    label="Hugging Face Token (Optional)",
                    placeholder="Enter your HF token here to override environment variable",
                    type="password",
                    info="Required for speaker diarization. If provided, will override HF_TOKEN environment variable."
                )
            
            download_btn = gr.Button("📥 Start Download", variant="primary")
            result_output = gr.JSON(label="Download Results")
            
            async def download_podcast_and_transcribe(url, platform, auto_transcribe, enable_speaker, hf_token):
                """Call corresponding download tool based on selected platform"""
                # Temporarily set HF_TOKEN if provided
                original_token = temporarily_set_hf_token(hf_token)
                
                try:
                    if platform == "Apple Podcast":
                        download_result = await mcp_tools.download_apple_podcast(url)
                    else:
                        download_result = await mcp_tools.download_xyz_podcast(url)
                    
                    # 2. Check if download was successful
                    if download_result["status"] != "success":
                        return {
                            "download_status": "failed",
                            "error_message": download_result.get("error_message", "Download failed"),
                            "transcription_status": "not_started"
                        }
                    
                    # 3. If not auto-transcribing, return only download results
                    if not auto_transcribe:
                        return {
                            "download_status": "success",
                            "audio_file": download_result["audio_file_path"],
                            "transcription_status": "skipped (user chose not to auto-transcribe)"
                        }
                    
                    # 4. Start transcription
                    try:
                        audio_path = download_result["audio_file_path"]
                        print(f"Transcribing audio file: {audio_path}")
                        transcribe_result = await mcp_tools.transcribe_audio_file(
                            audio_path,
                            model_size="turbo",
                            language=None,
                            output_format="srt",
                            enable_speaker_diarization=enable_speaker
                        )
                        
                        # 5. Merge results
                        result = {
                            "download_status": "success",
                            "audio_file": audio_path,
                            "transcription_status": "success",
                            "txt_file_path": transcribe_result.get("txt_file_path"),
                            "srt_file_path": transcribe_result.get("srt_file_path"),
                            "transcription_details": {
                                "model_used": transcribe_result.get("model_used"),
                                "segment_count": transcribe_result.get("segment_count"),
                                "audio_duration": transcribe_result.get("audio_duration"),
                                "saved_files": transcribe_result.get("saved_files", []),
                                "speaker_diarization_enabled": transcribe_result.get("speaker_diarization_enabled", False)
                            }
                        }
                        
                        # 6. Add speaker diarization info if enabled
                        if enable_speaker and transcribe_result.get("speaker_diarization_enabled", False):
                            result["speaker_diarization"] = {
                                "global_speaker_count": transcribe_result.get("global_speaker_count", 0),
                                "speaker_summary": transcribe_result.get("speaker_summary", {})
                            }
                        
                        return result
                        
                    except Exception as e:
                        return {
                            "download_status": "success",
                            "audio_file": download_result["audio_file_path"],
                            "transcription_status": "failed",
                            "error_message": str(e)
                        }
                
                finally:
                    # Restore original HF_TOKEN
                    restore_hf_token(original_token)
            
            # Bind callback function
            download_btn.click(
                download_podcast_and_transcribe,
                inputs=[url_input, platform_choice, auto_transcribe, enable_speaker_diarization, hf_token_input_download],
                outputs=result_output
            )
        
        # ==================== Audio Transcription Tab ====================
        with gr.Tab("Audio Transcription"):
            gr.Markdown("### 🎤 Audio Transcription and Speaker Diarization")
            gr.Markdown("Upload audio files for high-quality transcription with speaker diarization support")
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Audio file input
                    audio_file_input = gr.Textbox(
                        label="Audio File Path",
                        placeholder="Enter complete path to audio file (supports mp3, wav, m4a, etc.)",
                        lines=1
                    )
                    
                    # Transcription parameter settings
                    with gr.Row():
                        model_size_choice = gr.Dropdown(
                            choices=["tiny", "base", "small", "medium", "large", "turbo"],
                            value="turbo",
                            label="Model Size",
                            info="Affects transcription accuracy and speed"
                        )
                        language_choice = gr.Dropdown(
                            choices=["auto", "zh", "en", "ja", "ko", "fr", "de", "es"],
                            value="auto",
                            label="Language",
                            info="auto=auto-detect"
                        )
                    
                    with gr.Row():
                        with gr.Column():
                            output_format_choice = gr.Radio(
                                choices=["srt", "txt", "json"],
                                value="srt",
                                label="Output Format"
                            )
                        with gr.Column():
                            enable_speaker_separation = gr.Checkbox(
                                label="Enable speaker diarization",
                                value=False,
                                info="Requires Hugging Face Token"
                            )
                            # HF Token input for speaker diarization
                            hf_token_input_transcribe = gr.Textbox(
                                label="Hugging Face Token (Optional)",
                                placeholder="Enter your HF token here to override environment variable",
                                type="password",
                                info="Required for speaker diarization. If provided, will override HF_TOKEN environment variable."
                            )
                    
                    transcribe_btn = gr.Button("🎤 Start Transcription", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    # Audio file information
                    audio_info_output = gr.JSON(label="Audio File Information", visible=False)
                    
                    # Transcription progress and status
                    transcribe_status = gr.Textbox(
                        label="Transcription Status",
                        value="Waiting to start transcription...",
                        interactive=False,
                        lines=3
                    )
            
            # Transcription results display
            transcribe_result_output = gr.JSON(
                label="Transcription Results",
                visible=True
            )
            
            # Speaker diarization results (if enabled)
            speaker_info_output = gr.JSON(
                label="Speaker Diarization Information",
                visible=False
            )
            
            def perform_transcription(audio_path, model_size, language, output_format, enable_speaker, hf_token):
                """Execute audio transcription"""
                if not audio_path.strip():
                    return {
                        "error": "Please enter audio file path"
                    }, "Transcription failed: No audio file selected", gr.update(visible=False)
                
                # Temporarily set HF_TOKEN if provided
                original_token = temporarily_set_hf_token(hf_token)
                
                try:
                    # Check if file exists
                    import asyncio
                    file_info = asyncio.run(get_file_info_tool(audio_path))
                    if file_info["status"] != "success":
                        return {
                            "error": f"File does not exist or cannot be accessed: {file_info.get('error_message', 'Unknown error')}"
                        }, "Transcription failed: File inaccessible", gr.update(visible=False)
                    
                    try:
                        # Process language parameter
                        lang = None if language == "auto" else language
                        
                        # Call transcription tool
                        result = asyncio.run(transcribe_audio_file_tool(
                            audio_file_path=audio_path,
                            model_size=model_size,
                            language=lang,
                            output_format=output_format,
                            enable_speaker_diarization=enable_speaker
                        ))
                        
                        # Prepare status information
                        if result.get("processing_status") == "success":
                            status_text = f"""✅ Transcription completed!
📁 Generated files: {len(result.get('saved_files', []))} files
🎵 Audio duration: {result.get('audio_duration', 0):.2f} seconds
📝 Transcription segments: {result.get('segment_count', 0)} segments
🎯 Model used: {result.get('model_used', 'N/A')}
🎭 Speaker diarization: {'Enabled' if result.get('speaker_diarization_enabled', False) else 'Disabled'}"""
                            
                            # Show speaker information
                            speaker_visible = result.get('speaker_diarization_enabled', False) and result.get('global_speaker_count', 0) > 0
                            speaker_info = result.get('speaker_summary', {}) if speaker_visible else {}
                            
                            return result, status_text, gr.update(visible=speaker_visible, value=speaker_info)
                        else:
                            error_msg = result.get('error_message', 'Unknown error')
                            return result, f"❌ Transcription failed: {error_msg}", gr.update(visible=False)
                            
                    except Exception as e:
                        return {
                            "error": f"Exception occurred during transcription: {str(e)}"
                        }, f"❌ Transcription exception: {str(e)}", gr.update(visible=False)
                
                finally:
                    # Restore original HF_TOKEN
                    restore_hf_token(original_token)
            
            # Bind transcription button
            transcribe_btn.click(
                perform_transcription,
                inputs=[
                    audio_file_input, 
                    model_size_choice, 
                    language_choice, 
                    output_format_choice, 
                    enable_speaker_separation,
                    hf_token_input_transcribe
                ],
                outputs=[
                    transcribe_result_output, 
                    transcribe_status,
                    speaker_info_output
                ]
            )
        
        # ==================== MP3 File Management Tab ====================
        with gr.Tab("MP3 File Management"):
            gr.Markdown("### 🎵 MP3 File Management")
            
            # Get environment-specific directories
            available_dirs, default_dir = get_default_directories()
            
            # Display environment info
            import pathlib
            is_modal = os.environ.get("MODAL_ENVIRONMENT") == "1" or os.path.exists("/modal")
            is_docker = os.path.exists("/.dockerenv")
            current_dir = pathlib.Path.cwd()
            
            if is_modal:
                env_info = "🚀 **Modal Environment Detected** - Using Modal cache directories"
            elif is_docker:
                env_info = "🐳 **Docker Environment Detected** - Using container directories"
            else:
                env_info = f"💻 **Local Environment Detected** - Using current directory: `{current_dir}`"
            
            gr.Markdown(env_info)
            
            with gr.Row():
                with gr.Column(scale=3):
                    # Flexible directory path input
                    custom_dir_input = gr.Textbox(
                        label="Custom Directory Path",
                        placeholder="Enter custom directory path (e.g., /path/to/your/audio/files)",
                        lines=1,
                        value=default_dir
                    )
                with gr.Column(scale=2):
                    # Quick select for environment-specific directories
                    quick_select = gr.Dropdown(
                        label="Quick Select",
                        choices=available_dirs,
                        value=default_dir,
                        info="Select directories based on current environment"
                    )
                with gr.Column(scale=1):
                    scan_btn = gr.Button("🔍 Scan Directory", variant="primary")
            
            file_list = gr.Textbox(
                label="MP3 File List", 
                interactive=False,
                lines=10,
                max_lines=20,
                show_copy_button=True,
                autoscroll=True
            )
            
            def list_mp3_files(directory):
                """List MP3 files in directory"""
                if not directory or not directory.strip():
                    return "Please enter a directory path"
                
                try:
                    result = asyncio.run(get_mp3_files_tool(directory.strip()))
                    
                    # Check if there's an error
                    if "error_message" in result:
                        return f"❌ Error scanning directory: {result['error_message']}"
                    
                    # Get file list
                    total_files = result.get('total_files', 0)
                    file_list = result.get('file_list', [])
                    scanned_directory = result.get('scanned_directory', directory)
                    
                    if total_files == 0:
                        return f"📂 No MP3 files found in: {scanned_directory}"
                    
                    # Format file list for display
                    display_lines = [
                        f"📂 Found {total_files} MP3 file{'s' if total_files != 1 else ''} in: {scanned_directory}",
                        "=" * 60
                    ]
                    
                    for i, file_info in enumerate(file_list, 1):
                        filename = file_info.get('filename', 'Unknown')
                        size_mb = file_info.get('file_size_mb', 0)
                        created_time = file_info.get('created_time', 'Unknown')
                        full_path = file_info.get('full_path', 'Unknown')
                        
                        display_lines.append(
                            f"{i:2d}. 📄 {filename}\n"
                            f"     💾 Size: {size_mb:.2f} MB\n"
                            f"     📅 Created: {created_time}\n"
                            f"     📁 Path: {full_path}"
                        )
                    
                    return "\n".join(display_lines)
                    
                except Exception as e:
                    return f"❌ Exception occurred while scanning directory: {str(e)}"
            
            def use_quick_select(selected_path):
                """Use quick select path and auto-scan"""
                if selected_path:
                    return selected_path, list_mp3_files(selected_path)
                return "", ""
            
            def scan_directory(custom_path, quick_path):
                """Scan the directory based on custom input or quick select"""
                directory = custom_path.strip() if custom_path.strip() else quick_path
                return list_mp3_files(directory)
            
            # Bind callback functions
            quick_select.change(
                use_quick_select,
                inputs=[quick_select],
                outputs=[custom_dir_input, file_list]
            )
            
            scan_btn.click(
                scan_directory,
                inputs=[custom_dir_input, quick_select],
                outputs=[file_list]
            )
            
            # Auto-scan when custom directory is entered
            custom_dir_input.change(
                lambda x: list_mp3_files(x) if x.strip() else "",
                inputs=[custom_dir_input],
                outputs=[file_list]
            )
        
        # ==================== Transcription Text Management Tab ====================
        with gr.Tab("Transcription Text Management"):
            gr.Markdown("### 📝 Transcription Text File Management")
            gr.Markdown("View TXT and SRT files generated from audio transcription")
            
            # File path input
            file_path_input = gr.Textbox(
                label="File Path",
                placeholder="Enter path to TXT or SRT file to read",
                lines=1
            )
            
            # Load button
            load_file_btn = gr.Button("📂 Load File", variant="primary")
            
            # Text content viewer
            content_editor = gr.Textbox(
                label="File Content",
                placeholder="File content will be displayed here after loading...",
                lines=25,
                max_lines=40,
                show_copy_button=True,
                interactive=False
            )
            
            # Status information
            status_output = gr.Textbox(
                label="Status",
                interactive=False,
                lines=2
            )
            
            def load_and_display_file(file_path):
                """Load and display complete file content"""
                if not file_path.strip():
                    return "Please enter a file path", "❌ No file path provided"
                
                try:
                    # Get file info first
                    info = asyncio.run(get_file_info_tool(file_path))
                    
                    if info["status"] != "success":
                        return "", f"❌ Error: {info.get('error_message', 'Unknown error')}"
                    
                    # Check file size (warn for very large files)
                    file_size_mb = info.get('file_size_mb', 0)
                    if file_size_mb > 10:  # Warn for files larger than 10MB
                        return "", f"⚠️ File is too large ({file_size_mb:.2f} MB). Please use a smaller file for viewing."
                    
                    # Read entire file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Status message
                    status = f"✅ File loaded successfully: {info.get('filename', 'Unknown')}\n📁 Size: {file_size_mb:.2f} MB"
                    
                    return content, status
                    
                except UnicodeDecodeError:
                    return "", "❌ Error: File contains non-text content or encoding is not UTF-8"
                except FileNotFoundError:
                    return "", "❌ Error: File not found"
                except PermissionError:
                    return "", "❌ Error: Permission denied to read file"
                except Exception as e:
                    return "", f"❌ Error: {str(e)}"
            
            # Bind event handler
            load_file_btn.click(
                load_and_display_file,
                inputs=[file_path_input],
                outputs=[content_editor, status_output]
            )
    
    return demo 
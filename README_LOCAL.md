# Modal AudioTranscriber MCP

AudioTranscriber MCP is a serverless service based on the 👑 Modal platform, integrating Gradio, FastMCP, and Modal for podcast transcription MCP server.

Supports both Apple Podcasts and Xiaoyuzhou podcast platforms, enabling URL-to-text transcription for podcasts.

One hour of podcast content can be transcribed in just 3-4 minutes, achieving 15x-20x acceleration.

Thanks to Modal platform for providing credits, enabling simultaneous processing with 10 GPU parallel containers during transcription.

## Features

- 🎵 High-quality audio transcription (using OpenAI Whisper turbo)
- 🎭 Optional speaker diarization (using pyannote.audio)
- 🚀 GPU-accelerated processing (Modal deployment)
- 🌐 Web interface (Gradio)
- 🔧 MCP StreamableHttp tool integration (FastMCP)

## Quick Start

1. Deploy to Modal:
```bash
modal deploy main.py
```

2. Access web interface or use MCP client

Direct access to Gradio interface: https://richardsucran--gradio-mcp-server-gradio-mcp-app.modal.run

Cursor configuration:
```json
{
  "mcpServers": {
    "audiotranscriber-mcp": {
      "url": "https://richardsucran--gradio-mcp-server-gradio-mcp-app.modal.run/api/mcp"
    }
  }
}
```

## 🎭 Speaker Diarization (Optional)

Speaker diarization can identify different speakers in audio, but requires Hugging Face authentication.

### Setup Steps:

1. **Get Hugging Face Token**:
   - Visit [https://hf.co/settings/tokens](https://hf.co/settings/tokens)
   - Create a new access token

2. **Accept Model License**:
   - Visit [https://hf.co/pyannote/embedding](https://hf.co/pyannote/embedding)
   - Visit [https://hf.co/pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1)
   - Accept user conditions

3. **Configure Modal Secret**:
```bash
modal secret create huggingface-secret HUGGING_FACE_TOKEN=your_token
```

### Features:

- ✅ **With Token**: Complete speaker diarization functionality
- ⚠️ **Without Token**: Transcription only, speaker diarization will be automatically disabled
- 📝 **Error Handling**: Shows friendly error messages when token is missing

## Storage Configuration

MCP tools will store downloaded audio and transcribed text to Modal platform storage.

Users need to specify in the client and guide the client to read text and write transcription text to local storage.

### Modal Secrets (Optional)
```bash
# Required for speaker diarization
modal secret create huggingface-secret HUGGING_FACE_TOKEN=your_token
```

## MCP Tools

- `download_apple_podcast_tool`: Download Apple Podcast audio files and save to specified directory in Modal storage volume
- `download_xyz_podcast_tool`: Download Xiaoyuzhou podcast audio files and save to specified directory in Modal storage volume
- `get_mp3_files_tool`: Scan specified directory in Modal storage volume to get detailed information list of all MP3 audio files
- `transcribe_audio_file_tool`: Transcribe audio files to text using Whisper model, supporting multiple output formats and speaker diarization
- `read_text_file_segments_tool`: Read text file content in segments from Modal storage volume, intelligently handling text boundaries
- `get_file_info_tool`: Get basic file information from Modal storage volume, including size, modification time, etc.

## Development

```bash
# Development mode
modal serve main.py

# Production deployment
modal deploy main.py
```


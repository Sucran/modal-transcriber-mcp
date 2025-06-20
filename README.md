# 🎙️ Modal Transcriber MCP

[中文版本](./README_zh.md)

A powerful audio transcription streamhttp mcp server integrating Gradio UI, FastMCP Tools, and Modal cloud computing with intelligent speaker identification.

## ✨ Core Features

- **🎵 Multi-platform Audio Download**: Support for Apple Podcasts, XiaoYuZhou, and other podcast platforms
- **🚀 High-performance Transcription**: Based on OpenAI Whisper with multiple model support (turbo, large-v3, etc.)
- **🎤 Intelligent Speaker Identification**: Using pyannote.audio for speaker separation and embedding clustering
- **⚡ Distributed Processing**: Support for large file concurrent chunk processing, significantly improving processing speed
- **🔧 FastMCP Tools**: Complete MCP (Model Context Protocol) tool integration
- **☁️ Modal Deployment**: Support for both local and cloud deployment modes

## 🎯 Core Advantages

### 🧠 Intelligent Audio Segmentation
- **Silence Detection Segmentation**: Automatically identify silent segments in audio for intelligent chunking
- **Fallback Mechanism**: Long audio automatically degrades to time-based segmentation, ensuring processing efficiency
- **Concurrent Processing**: Multiple chunks processed simultaneously, dramatically improving transcription speed

### 🎤 Advanced Speaker Identification
- **Embedding Clustering**: Using deep learning embeddings for speaker consistency identification
- **Cross-chunk Unification**: Solving speaker label inconsistency issues in distributed processing
- **Quality Filtering**: Automatically filter low-quality segments to improve output accuracy

### 🔧 Developer Friendly
- **MCP Protocol Support**: Complete tool invocation interface
- **REST API**: Standardized API interface
- **Gradio UI**: Intuitive web interface
- **Test Coverage**: 29 unit tests and integration tests

## 🚀 Quick Start

### Environment Setup

1. **Clone Repository**
```bash
git clone https://github.com/Sucran/modal-transcriber-mcp.git
cd modal-transcriber-mcp
```

2. **Install Dependencies [Strongly Recommend Using uv]**
```bash
uv init --bare --python 3.10
uv sync --python 3.12
source .venv/bin/activate
```

3. **Configure Hugging Face Token** (Optional, for speaker identification)
```bash
# Copy configuration template
cp config.env.example config.env
# YOUR_ACTUAL_TOKEN_HERE is your real Huggingface platform token
# This token needs permission to access the following three model repositories:
# pyannote/embedding: https://huggingface.co/pyannote/embedding 
# pyannote/segmentation-3.0: https://huggingface.co/pyannote/segmentation-3.0
# pyannote/speaker-diarization-3.1: https://huggingface.co/pyannote/speaker-diarization-3.1
sed -i 's/your-huggingface-token-here/YOUR_ACTUAL_TOKEN_HERE/' config.env
```

4. **Modal Platform Authentication**

```bash
# Need to login to Modal platform via web browser, then token will be saved locally
modal token new
```

5. **Deploy Modal GPU Function Endpoints**
```bash
python start_modal.py
```
Then modify your config.env:
```text
MODAL_TRANSCRIBE_CHUNK_ENDPOINT=https://your-username--transcribe-audio-chunk-endpoint.modal.run
MODAL_HEALTH_CHECK_ENDPOINT=https://your-username--health-check-endpoint.modal.run
MODAL_GRADIO_UI_ENDPOINT=https://your-username--gradio-mcp-ui-app-entry.modal.run
```
Replace `your-username` with your actual Modal username

6. **Local Deployment of Gradio and FastMCP** (Optional, for local debugging/development)

```bash
python start_local.py
```

7. **Modal Cloud Deployment of Gradio and FastMCP**

```bash
modal deploy src.app::gradio_mcp_app
```

### 📚 How to Use This MCP Server

This application provides both **Web Interface** and **MCP (Model Context Protocol) Tools** for AI assistants to use.

Here's a demo video:

[![YouTube Video](https://img.youtube.com/vi/Ut5jw7Epb0o/0.jpg)](https://youtu.be/Ut5jw7Epb0o)

For local deployment, MCP configuration is:
```json
{
    "mcpServers": {
        "podcast-mcp": {
            "url": "http://127.0.0.1:7860/api/mcp"
        }
    }
}
```

For Modal deployment, MCP configuration is:
```json
{
    "mcpServers": {
        "podcast-mcp": {
            "url": "https://{your-username}--gradio-mcp-ui-app-entry.modal.run/api/mcp"
        }
    }
}
```

Both will use the GPU functions deployed on Modal:
MODAL_TRANSCRIBE_CHUNK_ENDPOINT=https://{your-username}--transcribe-audio-chunk-endpoint.modal.run

## 🛠️ Technical Architecture

- **Frontend**: Gradio 5.31
- **Backend**: FastAPI + FastMCP
- **Transcription Engine**: OpenAI Whisper
- **Speaker Identification**: pyannote.audio
- **Cloud Computing**: Modal.com
- **Audio Processing**: FFmpeg

## Future Plans

- [] Improve speaker identification accuracy
- [] Increase concurrent processing capacity of single GPU functions
- [] Optimize speaker clustering algorithms
- [] Support computing platforms in mainland China
- [] Test cost-effectiveness of other GPU types

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📜 License

MIT License

## 🔗 Related Links

- **Test Coverage**: 29 test cases ensuring functional stability
- **Modal Deployment**: Support for cloud high-performance processing

---
*Last updated: 2025-06-11* 
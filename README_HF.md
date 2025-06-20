---
title: Modal Transcriber MCP
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
tag: mcp-server-track
---

# 🎙️ Modal Transcriber MCP

A powerful audio transcription system integrating Gradio UI, FastMCP Tools, and Modal cloud computing with intelligent speaker identification.

## ✨ Key Features

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

### Local Setup

1. **Clone Repository**
```bash
git clone https://huggingface.co/spaces/Agents-MCP-Hackathon/ModalTranscriberMCP
cd ModalTranscriberMCP
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Hugging Face Token** (Optional, for speaker identification)
```bash
# Create .env file
echo "HF_TOKEN=your_huggingface_token_here" > .env
```

4. **Start Application**
```bash
python app.py
```

### Usage Instructions

1. **Upload audio file** or **Input podcast URL**
2. **Select transcription options**:
   - Model size: turbo (recommended) / large-v3
   - Output format: SRT / TXT
   - Enable speaker identification
3. **Start transcription**, the system will automatically process and generate results

## 🛠️ Technical Architecture

- **Frontend**: Gradio 4.44.0
- **Backend**: FastAPI + FastMCP
- **Transcription Engine**: OpenAI Whisper
- **Speaker Identification**: pyannote.audio
- **Cloud Computing**: Modal.com
- **Audio Processing**: FFmpeg

## 📊 Performance Metrics

- **Processing Speed**: Support for 30x real-time transcription speed
- **Concurrency**: Up to 10 chunks processed simultaneously
- **Accuracy**: Chinese accuracy >95%
- **Supported Formats**: MP3, WAV, M4A, FLAC, etc.

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📜 License

MIT License

## 🔗 Related Links

- **Project Documentation**: See `docs/` directory in the repository
- **Test Coverage**: 29 test cases ensuring functional stability
- **Modal Deployment**: Support for cloud high-performance processing
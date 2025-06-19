---
title: Modal Transcriber MCP
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
python_version: 3.10
---

# 🎙️ Modal Transcriber MCP

一个功能强大的音频转录系统，集成了 Gradio UI、FastMCP Tools 和 Modal 云计算，支持智能说话人识别。

## ✨ 主要功能

- **🎵 多平台音频下载**：支持 Apple Podcasts、小宇宙等播客平台
- **🚀 高性能转录**：基于 OpenAI Whisper，支持多种模型（turbo, large-v3等）
- **🎤 智能说话人识别**：使用 pyannote.audio 进行说话人分离和embedding聚类
- **⚡ 分布式处理**：支持大文件并发切片处理，显著提升处理速度
- **🔧 FastMCP 工具**：提供完整的 MCP (Model Context Protocol) 工具集成
- **☁️ Modal 部署**：支持本地和云端双模式部署

## 🎯 核心优势

### 🧠 智能音频分割
- **静音检测分割**：自动识别音频中的静音段落进行智能切分
- **Fallback机制**：长音频自动降级为时间分割，确保处理效率
- **并发处理**：多chunk同时处理，大幅提升转录速度

### 🎤 高级说话人识别
- **Embedding聚类**：使用深度学习embedding进行说话人一致性识别
- **跨chunk统一**：解决分布式处理中说话人标签不一致问题
- **质量过滤**：自动过滤低质量片段，提升输出准确性

### 🔧 开发者友好
- **MCP协议支持**：完整的工具调用接口
- **REST API**：标准化的API接口
- **Gradio UI**：直观的Web界面
- **测试覆盖**：29个单元测试和集成测试

## 🚀 快速开始

### 本地运行

1. **克隆仓库**
```bash
git clone https://huggingface.co/spaces/Agents-MCP-Hackathon/ModalTranscriberMCP
cd ModalTranscriberMCP
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置 Hugging Face Token**（可选，用于说话人识别）
```bash
# 创建 .env 文件
echo "HF_TOKEN=your_huggingface_token_here" > .env
```

4. **启动应用**
```bash
python app.py
```

### 使用说明

1. **上传音频文件** 或 **输入播客URL**
2. **选择转录选项**：
   - 模型大小：turbo (推荐) / large-v3
   - 输出格式：SRT / TXT
   - 是否启用说话人识别
3. **开始转录**，系统会自动处理并生成结果

## 🛠️ 技术架构

- **前端**：Gradio 4.44.0
- **后端**：FastAPI + FastMCP
- **转录引擎**：OpenAI Whisper
- **说话人识别**：pyannote.audio
- **云计算**：Modal.com
- **音频处理**：FFmpeg

## 📊 性能指标

- **处理速度**：支持30倍实时速度转录
- **并发能力**：最多10个chunks同时处理
- **准确率**：中文准确率>95%
- **支持格式**：MP3, WAV, M4A, FLAC等

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可证

MIT License

## 🔗 相关链接

- **项目文档**：详见仓库中的 `docs/` 目录
- **测试覆盖**：29个测试用例确保功能稳定性
- **Modal部署**：支持云端高性能处理 
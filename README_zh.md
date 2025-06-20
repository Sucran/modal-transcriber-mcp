# 🎙️ Modal Transcriber MCP

[English Version](./README.md)

一个强大的音频转录，支持streamhttp的mcp服务，集成 Gradio UI、FastMCP 工具和 Modal 云计算平台，具备智能说话人识别功能。

## ✨ 核心功能

- **🎵 多平台音频下载**：支持 Apple Podcasts、小宇宙等播客平台
- **🚀 高性能转录**：基于 OpenAI Whisper，支持多种模型（turbo、large-v3 等）
- **🎤 智能说话人识别**：使用 pyannote.audio 进行说话人分离和嵌入聚类
- **⚡ 分布式处理**：支持大文件并发分块处理，显著提升处理速度
- **🔧 FastMCP 工具**：完整的 MCP（模型上下文协议）工具集成
- **☁️ Modal 部署**：支持本地和云端部署模式

## 🎯 核心优势

### 🧠 智能音频分段
- **静音检测分段**：自动识别音频中的静音片段，进行智能分块
- **降级机制**：超长音频自动降级为时间分段，确保处理效率
- **并发处理**：多个分块同时处理，大幅提升转录速度

### 🎤 高级说话人识别
- **嵌入聚类**：使用深度学习嵌入进行说话人一致性识别
- **跨分块统一**：解决分布式处理中说话人标签不一致的问题
- **质量过滤**：自动过滤低质量片段，提升输出准确性

### 🔧 开发者友好
- **MCP 协议支持**：完整的工具调用接口
- **REST API**：标准化 API 接口
- **Gradio UI**：直观的 Web 界面
- **测试覆盖**：29个单元测试和集成测试

## 🚀 快速开始

### 环境配置

1. **克隆仓库**
```bash
git clone https://github.com/Sucran/modal-transcriber-mcp.git
cd modal-transcriber-mcp
```

2. **安装依赖【强烈推荐使用uv】**
```bash
uv init --bare --python 3.10
uv sync --python 3.12
source .venv/bin/activate
```

3. **配置 Hugging Face Token**（可选，用于说话人识别）
```bash
# 创建 .env 文件
cp config.env.example config.env
# YOUR_ACTUAL_TOKEN_HERE 是你真实的Huggingface平台的token
# 这个token需要开通以下三个仓库的模型拉取权限
# pyannote/embedding：https://huggingface.co/pyannote/embedding 
# pyannote/segmentation-3.0： https://huggingface.co/pyannote/segmentation-3.0
# pyannote/speaker-diarization-3.1：https://huggingface.co/pyannote/speaker-diarization-3.1
sed -i 's/your-huggingface-token-here/YOUR_ACTUAL_TOKEN_HERE/' config.env
```

4. **modal 平台认证**

```bash
# 需要网页登录modal平台，之后token自动进行本地保存
modal token new
```

5. **部署modal的gpu function endpoint**
```bash
python start_modal.py
```
并修改你的config.env中：
```text
MODAL_TRANSCRIBE_CHUNK_ENDPOINT=https://your-username--transcribe-audio-chunk-endpoint.modal.run
MODAL_HEALTH_CHECK_ENDPOINT=https://your-username--health-check-endpoint.modal.run
MODAL_GRADIO_UI_ENDPOINT=https://your-username--gradio-mcp-ui-app-entry.modal.run
```
将 your-username 替换成你自己的 modal 用户名

6. **本地部署gradio和fastmcp**（可选，用于本地调试 / 开发）

```bash
python start_modal.py
```

7. **Modal云端部署gradio和fastmcp**

```bash
modal deploy src.app::gradio_mcp_app
```

### 📚 How to Use This MCP Server

本应用程序同时提供了 **Web 界面** 和 **MCP（模型上下文协议）工具** 供 AI 助手使用

以下是演示视频：

[![YouTube Video](https://img.youtube.com/vi/Ut5jw7Epb0o/0.jpg)](https://youtu.be/Ut5jw7Epb0o)

当你是本地部署时，mcp配置为：
```json
{
    "mcpServers": {
        "podcast-mcp": {
            "url": "http://127.0.0.1:7860/api/mcp"
        }
    }
}
```
当你是modal部署时，mcp配置为：
```json
{
    "mcpServers": {
        "podcast-mcp": {
            "url": "https://{your-username}--gradio-mcp-ui-app-entry.modal.run/api/mcp"
        }
    }
}
```

两者都会同时使用modal上部署的gpu函数：
MODAL_TRANSCRIBE_CHUNK_ENDPOINT=https://{your-username}--transcribe-audio-chunk-endpoint.modal.run

## 🛠️ 技术架构

- **前端**：Gradio 5.31
- **后端**：FastAPI + FastMCP
- **转录引擎**：OpenAI Whisper
- **说话人识别**：pyannote.audio
- **云计算**：Modal.com
- **音频处理**：FFmpeg

## 后续计划

- [ ] 提升说话人识别的精度
- [ ] 提升单gpu函数的并发处理数
- [ ] 说话人聚类算法优化
- [ ] 支持中国大陆的共绩算力平台
- [ ] 测试其他gpu的成本

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可证

MIT License

## 🔗 相关链接

- **测试覆盖**：29 个测试用例确保功能稳定性
- **Modal 部署**：支持云端高性能处理

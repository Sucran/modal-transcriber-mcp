# Modal AudioTranscriber MCP

AudioTranscriber MCP 是一个 基于 👑 Modal 平台 的Serverless服务. ，是集成 Gradio 、FastMCP 和 Modal 的播客转录 MCP 服务器

支持Apple和小宇宙两个播客平台，支持播客的url转录为文本

一小时的播客内容只需要转录3-4分钟，加速15x-20x

感谢 Modal 平台提供的额度，在转录过程中同时启用10个gpu并行容器进行处理

## 功能特性

- 🎵 高质量音频转录（使用 OpenAI Whisper turbo）
- 🎭 可选的说话人分离（使用 pyannote.audio）
- 🚀 GPU 加速处理（Modal 部署）
- 🌐 Web 界面（Gradio）
- 🔧 MCP StreambleHttp 工具集成（FastMCP）

## 快速开始

1. 部署到 Modal：
```bash
modal deploy main.py
```

2. 访问 Web 界面或使用 MCP 客户端

直接访问Gradio界面： https://richardsucran--gradio-mcp-server-gradio-mcp-app.modal.run

Cusor配置：
```json
{
  "mcpServers": {
    "audiotranscriber-mcp": {
      "url": "https://richardsucran--gradio-mcp-server-gradio-mcp-app.modal.run/api/mcp"
    }
  }
```

## 🎭 说话人分离（可选）

说话人分离可以识别音频中的不同说话人，但需要 Hugging Face 身份验证。

### 设置步骤：

1. **获取 Hugging Face Token**：
   - 访问 [https://hf.co/settings/tokens](https://hf.co/settings/tokens)
   - 创建新的访问令牌

2. **接受模型许可证**：
   - 访问 [https://hf.co/pyannote/embedding](https://hf.co/pyannote/embedding)
   - 访问 [https://hf.co/pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1)
   - 接受用户条款

3. **配置 Modal 密钥**：
```bash
modal secret create huggingface-secret HUGGING_FACE_TOKEN=你的令牌
```

### 功能说明：

- ✅ **有 Token**：完整的说话人分离功能
- ⚠️ **无 Token**：仅转录功能，说话人分离将自动禁用
- 📝 **错误处理**：缺少令牌时显示友好的错误消息

## 存储配置

mcp工具会将下载的音频和转录的文本存储到 Modal平台上

用户需要在客户端说明并引导客户端进行读取文本，并将转录文本写入本地

### Modal 密钥（可选）
```bash
# 说话人分离功能必需
modal secret create huggingface-secret HUGGING_FACE_TOKEN=你的令牌
```

## MCP 工具

- `download_apple_podcast_tool`: 下载 Apple Podcast 音频文件并保存到Modal存储卷中指定目录
- `download_xyz_podcast_tool`: 下载小宇宙播客音频文件并保存到Modal存储卷中指定目录
- `get_mp3_files_tool`: 扫描Modal存储卷中指定目录获取所有 MP3 音频文件的详细信息列表
- `transcribe_audio_file_tool`: 使用 Whisper 模型将音频文件转录为文本，支持多种输出格式和说话人分离
- `read_text_file_segments_tool`: 分段读取Modal存储卷中文本文件内容，智能处理文本边界
- `get_file_info_tool`: 获取Modal存储卷中文件的基本信息，包括大小、修改时间等

## 开发

```bash
# 开发模式
modal serve main.py

# 生产部署
modal deploy main.py
``` 
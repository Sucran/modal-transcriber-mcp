# Modal URL 环境变量配置说明

这个文档说明如何将项目中硬编码的Modal URL提取到环境变量中，以便更好地管理不同部署环境的配置。

## 🔍 已识别的硬编码URL

我们找到并修复了以下位置的硬编码Modal URL：

1. **`src/services/modal_transcription_service.py`** - Modal转录服务端点
2. **`src/services/distributed_transcription_service.py`** - 分布式转录服务端点
3. **`src/tools/transcription_tools.py`** - 转录工具端点
4. **`src/ui/gradio_ui.py`** - Gradio UI中的端点引用
5. **`tests/test_05_real_world_integration.py`** - 测试文件中的端点

## 📋 环境变量配置

### 1. 复制配置文件

```bash
cp config.env.example config.env
```

### 2. 配置Modal相关环境变量

编辑 `config.env` 文件，设置以下变量：

```bash
# Modal 用户名配置
MODAL_USERNAME=your-modal-username

# Modal 基础URL (通常不需要修改)
MODAL_BASE_URL=modal.run

# 具体的端点URL (会从用户名和基础URL自动构建)
MODAL_TRANSCRIBE_AUDIO_ENDPOINT=https://your-modal-username--transcribe-audio-endpoint.modal.run
MODAL_TRANSCRIBE_CHUNK_ENDPOINT=https://your-modal-username--transcribe-audio-chunk-endpoint.modal.run
MODAL_HEALTH_CHECK_ENDPOINT=https://your-modal-username--health-check-endpoint.modal.run
MODAL_GRADIO_UI_ENDPOINT=https://your-modal-username--gradio-mcp-ui-app-entry.modal.run
```

### 3. 环境变量优先级

系统按以下优先级读取URL配置：

1. **直接环境变量** - 如 `MODAL_TRANSCRIBE_AUDIO_ENDPOINT`
2. **用户名构建** - 如果没有直接URL，则从 `MODAL_USERNAME` + `MODAL_BASE_URL` 构建
3. **默认值** - 如果以上都没有，使用 `richardsucran` 作为默认用户名

## 🚀 使用方式

### 方式一：设置完整URL（推荐）

```bash
# 在 config.env 中
MODAL_TRANSCRIBE_AUDIO_ENDPOINT=https://yourname--transcribe-audio-endpoint.modal.run
MODAL_TRANSCRIBE_CHUNK_ENDPOINT=https://yourname--transcribe-audio-chunk-endpoint.modal.run
MODAL_HEALTH_CHECK_ENDPOINT=https://yourname--health-check-endpoint.modal.run
MODAL_GRADIO_UI_ENDPOINT=https://yourname--gradio-mcp-ui-app-entry.modal.run
```

### 方式二：设置用户名自动构建

```bash
# 在 config.env 中
MODAL_USERNAME=yourname
MODAL_BASE_URL=modal.run
```

### 方式三：运行时环境变量

```bash
export MODAL_USERNAME=yourname
export MODAL_TRANSCRIBE_AUDIO_ENDPOINT=https://yourname--transcribe-audio-endpoint.modal.run
python start_local.py
```

## 🛠️ 代码变更说明

### 新增配置函数

在 `src/config/config.py` 中新增：

- `get_modal_username()` - 获取Modal用户名
- `get_modal_base_url()` - 获取Modal基础URL
- `build_modal_endpoint_url()` - 构建端点URL
- `get_modal_*_endpoint()` - 获取各种端点URL

### 代码修改位置

所有原本硬编码的URL现在都会：

1. 首先尝试从环境变量读取
2. 如果没有环境变量，使用用户名构建URL
3. 最后回退到默认值

## 🧪 测试配置

运行测试验证配置：

```bash
# 测试配置是否正确加载
python -c "from src.config.config import get_modal_transcribe_audio_endpoint; print(get_modal_transcribe_audio_endpoint())"

# 验证Modal资源配置
python verify_modal_config.py

# 运行集成测试
python -m pytest tests/test_05_real_world_integration.py::TestRealWorldIntegration::test_modal_endpoints_accessibility -v
```

## ⚙️ Modal资源配置

现在项目也支持通过环境变量配置Modal部署的资源分配：

### 资源配置变量

```bash
# Modal应用名称
MODAL_APP_NAME=podcast-transcription

# GPU类型 (T4, A10G, A100等)
MODAL_GPU_TYPE=A10G

# 内存大小 (MB)
MODAL_MEMORY=10240

# CPU核心数
MODAL_CPU=4
```

### 资源使用说明

- **转录服务端点**: 使用完整的配置资源（CPU、内存、GPU）
- **健康检查端点**: 自动使用一半CPU和四分之一内存（最小值保证）

### 配置生效位置

Modal资源配置在 `src/config/modal_config.py` 中生效：

```python
@app.function(
    cpu=MODAL_CPU,  # 从环境变量加载
    memory=MODAL_MEMORY,  # 从环境变量加载
    gpu=MODAL_GPU_TYPE,  # 从环境变量加载
    # ...
)
```

## 📝 MCP客户端配置

如果你使用MCP客户端连接，请更新你的配置：

```json
{
    "mcpServers": {
        "podcast-mcp": {
            "url": "https://your-modal-username--gradio-mcp-ui-app-entry.modal.run/api/mcp"
        }
    }
}
```

## 🔧 开发提示

### 检查当前配置

```python
from src.config.config import (
    get_modal_transcribe_audio_endpoint,
    get_modal_transcribe_chunk_endpoint,
    get_modal_health_check_endpoint,
    get_modal_gradio_ui_endpoint
)

print("当前Modal端点配置:")
print(f"转录音频: {get_modal_transcribe_audio_endpoint()}")
print(f"转录块: {get_modal_transcribe_chunk_endpoint()}")
print(f"健康检查: {get_modal_health_check_endpoint()}")
print(f"Gradio UI: {get_modal_gradio_ui_endpoint()}")
```

### 添加新端点

如果需要添加新的Modal端点：

1. 在 `config.env.example` 中添加环境变量
2. 在 `src/config/config.py` 中添加对应的getter函数
3. 在需要使用的地方调用getter函数

## ⚠️ 注意事项

1. **不要提交包含真实URL的 `config.env` 文件到版本控制**
2. **确保在生产环境中正确设置环境变量**
3. **测试时使用 `config.env.example` 作为模板**
4. **Modal用户名和端点名称必须与你实际部署的匹配**

## 🔄 迁移步骤

如果你已经在使用这个项目：

1. 备份现有配置
2. 复制 `config.env.example` 到 `config.env`
3. 设置 `MODAL_USERNAME` 为你的Modal用户名
4. 如果有自定义端点，设置完整的URL环境变量
5. 重新启动应用并验证功能

现在你的Modal URL已经完全通过环境变量管理，便于在不同环境间切换和部署！ 
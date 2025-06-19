# Playwright MCP Testing Guide for Gradio UI

本文档详细说明如何使用Playwright MCP工具测试`src/ui/gradio_ui.py`中的所有功能。

## 📋 目录

1. [测试环境设置](#测试环境设置)
2. [基本MCP工具使用](#基本mcp工具使用)
3. [Tab 1: Podcast Download 测试](#tab-1-podcast-download-测试)
4. [Tab 2: Audio Transcription 测试](#tab-2-audio-transcription-测试)
5. [Tab 3: MP3 File Management 测试](#tab-3-mp3-file-management-测试)
6. [Tab 4: Transcription Text Management 测试](#tab-4-transcription-text-management-测试)
7. [完整测试流程示例](#完整测试流程示例)
8. [故障排除](#故障排除)

## 测试环境设置

### 1. 启动应用
```bash
# 确保应用在localhost:8000运行
python app.py
```

### 2. 初始化浏览器
```python
# 导航到应用
mcp_playwright_browser_navigate("http://localhost:8000")

# 等待页面加载
mcp_playwright_browser_wait_for(time=3)

# 获取页面快照以查看当前状态
mcp_playwright_browser_snapshot()
```

## 基本MCP工具使用

### 核心工具列表
- `mcp_playwright_browser_navigate(url)` - 导航到URL
- `mcp_playwright_browser_snapshot()` - 获取页面快照
- `mcp_playwright_browser_click(element, ref)` - 点击元素
- `mcp_playwright_browser_type(element, ref, text)` - 输入文本
- `mcp_playwright_browser_select_option(element, ref, values)` - 选择下拉选项
- `mcp_playwright_browser_wait_for(time=seconds)` - 等待指定时间
- `mcp_playwright_browser_wait_for(text="显示文本")` - 等待文本出现

### 基本测试模式
1. 获取快照 → 找到元素ref → 执行操作 → 验证结果

## Tab 1: Podcast Download 测试

### 界面元素映射
- **播客链接输入框**: `role='textbox', name='Podcast Link'`
- **平台选择**: `role='radio', name='Apple Podcast'` / `role='radio', name='XiaoYuZhou'`
- **自动转录复选框**: `role='checkbox', name='Auto-transcribe after download'`
- **说话人识别复选框**: `role='checkbox', name='Enable speaker diarization'`
- **下载按钮**: `role='button', name='📥 Start Download'`

### 测试用例 1: Apple Podcast 下载 + 转录 + 说话人识别

```python
# 1. 导航到Podcast Download tab (默认已选中)
mcp_playwright_browser_snapshot()

# 2. 输入Apple Podcast URL
mcp_playwright_browser_type(
    element="播客链接输入框",
    ref="[从snapshot获取的ref]", 
    text="https://podcasts.apple.com/cn/podcast/all-ears-english-podcast/id751574016?i=1000712048662"
)

# 3. 确保Apple Podcast已选中（默认）
# 如果需要选择：
# mcp_playwright_browser_click(element="Apple Podcast选项", ref="[ref]")

# 4. 确保自动转录已启用（默认启用）
# 如果需要切换：
# mcp_playwright_browser_click(element="自动转录复选框", ref="[ref]")

# 5. 启用说话人识别
mcp_playwright_browser_click(element="说话人识别复选框", ref="[ref]")

# 6. 开始下载
mcp_playwright_browser_click(element="开始下载按钮", ref="[ref]")

# 7. 等待处理完成（可能需要2-5分钟）
mcp_playwright_browser_wait_for(time=180)  # 等待3分钟

# 8. 检查结果
mcp_playwright_browser_snapshot()
# 查看result_output区域是否显示成功结果
```

### 测试用例 2: XiaoYuZhou 下载 + 仅下载

```python
# 1. 切换到XiaoYuZhou平台
mcp_playwright_browser_click(element="XiaoYuZhou选项", ref="[ref]")

# 2. 输入XiaoYuZhou URL
mcp_playwright_browser_type(
    element="播客链接输入框", 
    ref="[ref]",
    text="https://www.xiaoyuzhoufm.com/episode/your-episode-id"
)

# 3. 禁用自动转录
mcp_playwright_browser_click(element="自动转录复选框", ref="[ref]")

# 4. 开始下载
mcp_playwright_browser_click(element="开始下载按钮", ref="[ref]")

# 5. 等待下载完成
mcp_playwright_browser_wait_for(time=60)

# 6. 验证结果
mcp_playwright_browser_snapshot()
```

## Tab 2: Audio Transcription 测试

### 界面元素映射
- **Tab切换**: `role='tab', name='Audio Transcription'`
- **文件路径输入**: `role='textbox', name='Audio File Path'`
- **模型选择**: `role='combobox', name='Model Size'`
- **语言选择**: `role='combobox', name='Language'`
- **输出格式**: `role='radio', name='srt'/'txt'/'json'`
- **说话人识别**: `role='checkbox', name='Enable speaker diarization'`
- **转录按钮**: `role='button', name='🎤 Start Transcription'`

### 测试用例 1: 转录下载的音频文件

```python
# 1. 切换到Audio Transcription tab
mcp_playwright_browser_click(element="Audio Transcription tab", ref="[ref]")

# 2. 输入音频文件路径（使用之前下载的文件）
mcp_playwright_browser_type(
    element="音频文件路径输入框",
    ref="[ref]",
    text="downloads/1000712048662_episode_audio.mp3"
)

# 3. 选择模型大小
mcp_playwright_browser_select_option(
    element="模型大小下拉框",
    ref="[ref]",
    values=["turbo"]
)

# 4. 选择语言
mcp_playwright_browser_select_option(
    element="语言下拉框", 
    ref="[ref]",
    values=["auto"]
)

# 5. 选择输出格式为SRT
mcp_playwright_browser_click(element="SRT格式选项", ref="[ref]")

# 6. 启用说话人识别
mcp_playwright_browser_click(element="说话人识别复选框", ref="[ref]")

# 7. 开始转录
mcp_playwright_browser_click(element="开始转录按钮", ref="[ref]")

# 8. 等待转录完成
mcp_playwright_browser_wait_for(time=120)

# 9. 检查结果
mcp_playwright_browser_snapshot()
```

### 测试用例 2: 不同参数组合测试

```python
# 测试不同模型大小
for model in ["small", "medium", "large"]:
    mcp_playwright_browser_select_option(
        element="模型大小下拉框",
        ref="[ref]", 
        values=[model]
    )
    # 执行转录并验证结果

# 测试不同输出格式
for format in ["txt", "json"]:
    mcp_playwright_browser_click(element=f"{format}格式选项", ref="[ref]")
    # 执行转录并验证结果
```

## Tab 3: MP3 File Management 测试

### 界面元素映射
- **Tab切换**: `role='tab', name='MP3 File Management'`
- **目录选择**: `role='combobox', name='Directory Path'`
- **文件列表**: `role='textbox', name='MP3 File List'`

### 测试用例: 浏览MP3文件

```python
# 1. 切换到MP3 File Management tab
mcp_playwright_browser_click(element="MP3 File Management tab", ref="[ref]")

# 2. 选择目录
mcp_playwright_browser_select_option(
    element="目录路径下拉框",
    ref="[ref]",
    values=["/root/cache/apple_podcasts"]
)

# 3. 等待文件列表更新
mcp_playwright_browser_wait_for(time=2)

# 4. 检查文件列表
mcp_playwright_browser_snapshot()

# 5. 切换到另一个目录
mcp_playwright_browser_select_option(
    element="目录路径下拉框",
    ref="[ref]", 
    values=["/root/cache/xyz_podcasts"]
)

# 6. 验证文件列表更新
mcp_playwright_browser_wait_for(time=2)
mcp_playwright_browser_snapshot()
```

## Tab 4: Transcription Text Management 测试

### 界面元素映射
- **Tab切换**: `role='tab', name='Transcription Text Management'`
- **文件路径输入**: `role='textbox', name='File Path'`
- **加载文件按钮**: `role='button', name='📂 Load File'`
- **保存文件按钮**: `role='button', name='💾 Save File'`
- **刷新按钮**: `role='button', name='🔄 Refresh'`
- **内容编辑器**: `role='textbox', name='File Content'`
- **上一个按钮**: `role='button', name='⬅️ Previous'`
- **下一个按钮**: `role='button', name='➡️ Next'`

### 测试用例 1: 加载和编辑转录文件

```python
# 1. 切换到Text Management tab
mcp_playwright_browser_click(element="Transcription Text Management tab", ref="[ref]")

# 2. 输入转录文件路径
mcp_playwright_browser_type(
    element="文件路径输入框",
    ref="[ref]",
    text="downloads/1000712048662_episode_audio.srt"
)

# 3. 加载文件
mcp_playwright_browser_click(element="加载文件按钮", ref="[ref]")

# 4. 等待文件加载
mcp_playwright_browser_wait_for(time=3)

# 5. 检查文件内容
mcp_playwright_browser_snapshot()

# 6. 编辑内容
mcp_playwright_browser_type(
    element="内容编辑器",
    ref="[ref]",
    text="编辑后的内容..."
)

# 7. 保存文件
mcp_playwright_browser_click(element="保存文件按钮", ref="[ref]")

# 8. 验证保存状态
mcp_playwright_browser_wait_for(time=2)
mcp_playwright_browser_snapshot()
```

### 测试用例 2: 分段阅读大文件

```python
# 1. 使用下一个按钮浏览文件
mcp_playwright_browser_click(element="下一个按钮", ref="[ref]")
mcp_playwright_browser_wait_for(time=2)
mcp_playwright_browser_snapshot()

# 2. 使用上一个按钮返回
mcp_playwright_browser_click(element="上一个按钮", ref="[ref]")
mcp_playwright_browser_wait_for(time=2)
mcp_playwright_browser_snapshot()

# 3. 刷新文件内容
mcp_playwright_browser_click(element="刷新按钮", ref="[ref]")
mcp_playwright_browser_wait_for(time=2)
mcp_playwright_browser_snapshot()
```

## 完整测试流程示例

### 端到端测试流程

```python
# 完整的端到端测试流程
def complete_e2e_test():
    # Phase 1: 下载播客
    print("=== Phase 1: Podcast Download ===")
    mcp_playwright_browser_navigate("http://localhost:8000")
    mcp_playwright_browser_snapshot()
    
    # 输入URL并配置选项
    mcp_playwright_browser_type(
        element="播客链接输入框",
        ref="[ref]",
        text="https://podcasts.apple.com/cn/podcast/all-ears-english-podcast/id751574016?i=1000712048662"
    )
    
    # 启用说话人识别
    mcp_playwright_browser_click(element="说话人识别复选框", ref="[ref]")
    
    # 开始下载
    mcp_playwright_browser_click(element="开始下载按钮", ref="[ref]")
    
    # 等待完成
    mcp_playwright_browser_wait_for(time=180)
    
    # Phase 2: 验证下载结果并管理文件
    print("=== Phase 2: File Management ===")
    mcp_playwright_browser_click(element="MP3 File Management tab", ref="[ref]")
    mcp_playwright_browser_snapshot()
    
    # Phase 3: 手动转录测试
    print("=== Phase 3: Manual Transcription ===")
    mcp_playwright_browser_click(element="Audio Transcription tab", ref="[ref]")
    
    # 使用不同参数进行转录
    mcp_playwright_browser_type(
        element="音频文件路径输入框",
        ref="[ref]",
        text="downloads/1000712048662_episode_audio.mp3"
    )
    
    # 测试不同模型
    mcp_playwright_browser_select_option(
        element="模型大小下拉框",
        ref="[ref]",
        values=["medium"]
    )
    
    mcp_playwright_browser_click(element="开始转录按钮", ref="[ref]")
    mcp_playwright_browser_wait_for(time=120)
    
    # Phase 4: 文本管理和编辑
    print("=== Phase 4: Text Management ===")
    mcp_playwright_browser_click(element="Transcription Text Management tab", ref="[ref]")
    
    # 加载和编辑转录文件
    mcp_playwright_browser_type(
        element="文件路径输入框",
        ref="[ref]",
        text="downloads/1000712048662_episode_audio.srt"
    )
    
    mcp_playwright_browser_click(element="加载文件按钮", ref="[ref]")
    mcp_playwright_browser_wait_for(time=3)
    mcp_playwright_browser_snapshot()
    
    print("=== 测试完成 ===")

# 执行完整测试
complete_e2e_test()
```

## 故障排除

### 常见问题和解决方案

1. **元素未找到**
   - 先使用`mcp_playwright_browser_snapshot()`获取当前页面状态
   - 确认元素的正确ref和描述
   - 检查页面是否完全加载

2. **操作超时**
   - 增加等待时间：`mcp_playwright_browser_wait_for(time=更长时间)`
   - 检查网络连接和服务状态
   - 验证Modal endpoints是否正常工作

3. **文件路径错误**
   - 确认文件实际存在于指定路径
   - 使用绝对路径而非相对路径
   - 检查文件权限

4. **表单提交失败**
   - 确认所有必填字段已填写
   - 检查输入格式是否正确
   - 验证服务器端错误日志

### 调试技巧

1. **逐步执行**
   ```python
   # 在每个关键步骤后添加快照
   mcp_playwright_browser_snapshot()
   ```

2. **等待策略**
   ```python
   # 等待特定文本出现
   mcp_playwright_browser_wait_for(text="Processing completed")
   
   # 等待特定文本消失
   mcp_playwright_browser_wait_for(textGone="Loading...")
   ```

3. **错误恢复**
   ```python
   # 如果操作失败，刷新页面重试
   mcp_playwright_browser_navigate("http://localhost:8000")
   ```

## 测试数据

### 推荐的测试URL

**Apple Podcast URLs:**
- 短音频: `https://podcasts.apple.com/cn/podcast/short-episode-id`
- 中等音频: `https://podcasts.apple.com/cn/podcast/all-ears-english-podcast/id751574016?i=1000712048662`
- 长音频: `https://podcasts.apple.com/cn/podcast/long-episode-id`

**XiaoYuZhou URLs:**
- 测试URL: `https://www.xiaoyuzhoufm.com/episode/test-episode-id`

### 测试文件路径
- 音频文件: `downloads/*.mp3`
- 转录文件: `downloads/*.srt`, `downloads/*.txt`
- JSON文件: `downloads/*.json`

---

**注意**: 在使用此指南时，需要根据实际的页面快照结果替换`[ref]`占位符为真实的元素引用。每次测试前建议先获取快照以确认当前页面状态。 
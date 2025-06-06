# FastAPI + Gradio + FastMCP MCP 服务器实现

import asyncio
import modal
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, List
import os
from fastapi import FastAPI, Request, Response
from gradio.routes import mount_gradio_app
import gradio as gr

# FastMCP 相关导入
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route

# 创建 FastMCP 服务器实例
mcp = FastMCP("Gradio文本分析服务器")
sessions: dict[str, asyncio.Future] = {}

# 创建 Modal 应用
app = modal.App(name="gradio-mcp-server")

# 创建镜像环境 - 添加 FastMCP 依赖
image = modal.Image.debian_slim(python_version="3.10").pip_install(
    "gradio>=5.31.0",
    "fastapi",
    "pydantic", 
    "python-dotenv",
    "mcp[cli]",
    "fastmcp>=2.7.0",
    "starlette",
)

# ==================== MCP 工具定义 ====================

def letter_counter(word: str, letter: str) -> int:
    """Count the occurrence of a specific letter in a word or text
    
    Args:
        word (str): The text to analyze
        letter (str): The letter to count
    
    Returns:
        int: Number of occurrences of the letter
    """
    word = word.lower()
    letter = letter.lower()
    count = word.count(letter)
    return count

@mcp.tool()
def count_letter_in_text(text: str, letter: str) -> Dict[str, Any]:
    """统计文本中指定字母的出现次数
    
    Args:
        text (str): 要分析的文本
        letter (str): 要统计的字母
    
    Returns:
        Dict[str, Any]: 统计结果
    """
    count = letter_counter(text, letter)
    return {
        "原文本": text,
        "目标字母": letter,
        "出现次数": count,
        "文本长度": len(text),
        "字母占比": f"{(count/len(text)*100):.2f}%" if len(text) > 0 else "0%"
    }

@mcp.tool()
def analyze_text_stats(text: str) -> Dict[str, Any]:
    """分析文本的基本统计信息
    
    Args:
        text (str): 要分析的文本
    
    Returns:
        Dict[str, Any]: 文本分析结果
    """
    lines = text.strip().split('\n')
    words = text.split()
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 字符频率统计（前5个）
    char_freq = {}
    for char in text.lower():
        if char.isalpha():
            char_freq[char] = char_freq.get(char, 0) + 1
    
    return {
        "字符数": len(text),
        "单词数": len(words),
        "行数": len(lines),
        "句子数": len(sentences),
        "唯一字符数": len(set(text.lower())),
        "最频繁字符": dict(sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:5])
    }

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """获取个性化问候语"""
    return f"你好, {name}! 欢迎使用 Gradio MCP 服务器!"

# ==================== FastAPI 应用创建（SSE支持）====================

def create_mcp_app(mcp_server: Server, *, debug: bool = False) -> FastAPI:
    """创建支持 SSE 的 MCP FastAPI 应用"""
    
    sse = SseServerTransport("/messages/")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        for fut in sessions.values():
            fut.set_result(None)

    async def handle_sse(request: Request) -> Response:
        try:
            session_id = request.query_params.get("session_id")
            if session_id not in sessions:
                sessions[session_id] = asyncio.Future()

            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
            ) as (read_stream, write_stream):
                task = asyncio.create_task(
                    mcp_server.run(
                        read_stream,
                        write_stream,
                        mcp_server.create_initialization_options(),
                    )
                )

                try:
                    await asyncio.wait(
                        [sessions[session_id], task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    if sessions[session_id].done() and not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                finally:
                    if session_id in sessions:
                        del sessions[session_id]

            return Response(status_code=200)
        except Exception as e:
            return Response(status_code=500, content=str(e))

    async def disconnect(request: Request) -> Response:
        try:
            session_id = request.query_params.get("session_id")
            if session_id in sessions:
                fut = sessions[session_id]
                fut.set_result(None)
                return Response(status_code=200)
            else:
                return Response(status_code=404, content="Session not found")
        except Exception as e:
            return Response(status_code=500, content=str(e))

    mcp_app = FastAPI(
        debug=debug,
        routes=[
            # MCP SSE 端点
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Route("/disconnect", endpoint=disconnect, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )

    return mcp_app

@app.function(
    image=image,
    max_containers=5,
    min_containers=0,
    scaledown_window=600,
    timeout=1800,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def gradio_mcp_app():
    print("🚀 启动 Gradio + FastMCP 服务器")
    
    # 创建主 FastAPI 应用
    web_app = FastAPI(
        title="Gradio MCP Server",
        description="Gradio UI + FastMCP Tool Integration"
    )
    
    # 创建 MCP 子应用
    mcp_server = mcp._mcp_server
    mcp_app = create_mcp_app(mcp_server, debug=False)
    
    # 挂载 MCP 应用到 /mcp 路径
    web_app.mount("/mcp", mcp_app)
    
    # 创建 Gradio 界面
    with gr.Blocks(title="MCP Tool Server") as demo:
        gr.Markdown("# 🤖 Gradio + FastMCP 服务器")
        gr.Markdown("这个服务器同时提供 Gradio UI 和 FastMCP 工具！")
        
        with gr.Tab("字母统计器"):
            gr.Markdown("### 📝 统计文本中指定字母的出现次数")
            with gr.Row():
                word_input = gr.Textbox(
                    label="输入文本", 
                    placeholder="输入要分析的文本",
                    lines=3
                )
                letter_input = gr.Textbox(
                    label="目标字母", 
                    placeholder="要统计的字母",
                    max_lines=1
                )
            
            count_btn = gr.Button("📊 开始统计", variant="primary")
            result_output = gr.Number(label="出现次数")
            
            count_btn.click(
                letter_counter,
                inputs=[word_input, letter_input],
                outputs=result_output
            )
        
        with gr.Tab("文本分析"):
            gr.Markdown("### 📊 完整文本统计分析")
            text_input = gr.Textbox(
                label="输入文本",
                placeholder="输入要分析的文本",
                lines=5
            )
            analyze_btn = gr.Button("🔍 分析文本", variant="primary")
            
            with gr.Row():
                chars_output = gr.Number(label="字符数")
                words_output = gr.Number(label="单词数")
                lines_output = gr.Number(label="行数")
            
            def analyze_text_ui(text):
                result = analyze_text_stats(text)
                return result["字符数"], result["单词数"], result["行数"]
            
            analyze_btn.click(
                analyze_text_ui,
                inputs=text_input,
                outputs=[chars_output, words_output, lines_output]
            )
        
        with gr.Tab("MCP 信息"):
            gr.Markdown("### 🔧 MCP 服务器信息")
            gr.Markdown(f"""
            **服务器名称**: {mcp.name}
            
            **MCP 端点**: 
            - SSE: `/mcp/sse`
            - 断开: `/mcp/disconnect`
            - 消息: `/mcp/messages/`
            
            **可用工具**:
            - `count_letter_in_text`: 统计字母出现次数
            - `analyze_text_stats`: 文本统计分析
            
            **可用资源**:
            - `greeting://{{name}}`: 获取问候语
            """)
    
    # 挂载 Gradio 应用
    gradio_app = mount_gradio_app(
        app=web_app,
        blocks=demo,
        path="/",
        app_kwargs={
            "docs_url": "/docs",
            "redoc_url": "/redoc",
        }
    )
    
    print("✅ 服务器启动完成")
    print("🎨 Gradio UI: /")
    print("🔧 MCP SSE: /mcp/sse")
    print("📋 API 文档: /docs")
    
    return gradio_app

# 本地开发入口点
@app.local_entrypoint()
def main():
    print("🚀 Gradio + FastMCP 服务器启动!")
    print("=" * 50)
    print()
    print("📋 端点信息:")
    print("  🎨 Gradio UI: https://your-app.modal.run/")
    print("  🔧 MCP SSE: https://your-app.modal.run/mcp/sse")
    print("  🔌 MCP 断开: https://your-app.modal.run/mcp/disconnect")
    print("  📨 MCP 消息: https://your-app.modal.run/mcp/messages/")
    print("  ❤️ 健康检查: https://your-app.modal.run/health")
    print("  📋 API 文档: https://your-app.modal.run/docs")
    print()
    print("🛠️ MCP 客户端配置:")
    print('  {')
    print('    "mcpServers": {')
    print('      "gradio-mcp": {')
    print('        "url": "https://your-app.modal.run/mcp/sse"')
    print('      }')
    print('    }')
    print('  }')
    print()
    print("🎯 可用 MCP 工具:")
    print("  📝 count_letter_in_text: 统计字母出现次数")
    print("  📊 analyze_text_stats: 文本统计分析")
    print()
    print("🚀 启动命令:")
    print("  modal serve main.py")
    print("  modal deploy main.py")
#!/usr/bin/env python3
"""
FastMCP MCP 服务器 - 基于 SSE 传输和 Modal 部署
提供文本分析工具，模仿 GitHub Gist 的实现模式
"""

import asyncio
import modal
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, Response
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route

# 创建 FastMCP 服务器实例
mcp = FastMCP("文本分析服务器")
sessions: dict[str, asyncio.Future] = {}

# ==================== 工具定义 ====================

@mcp.tool()
def analyze_text(text: str) -> Dict[str, Any]:
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
        "最频繁字符": dict(sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:5]),
        "分析时间": datetime.now().isoformat(),
    }

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """获取个性化问候语"""
    return f"你好, {name}!"

# ==================== FastAPI 应用创建 ====================

def create_app(mcp_server: Server, *, debug: bool = False) -> FastAPI:
    """创建可以为提供的 MCP 服务器提供 SSE 服务的 FastAPI 应用"""
    
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

                    # 如果是 future 完成了，正确地取消任务
                    if sessions[session_id].done() and not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                finally:
                    # 清理会话（如果仍在字典中）
                    if session_id in sessions:
                        del sessions[session_id]

            return Response(status_code=200)
        except Exception as e:
            return Response(status_code=500)

    async def disconnect(request: Request) -> Response:
        try:
            session_id = request.query_params.get("session_id")
            if session_id in sessions:
                fut = sessions[session_id]
                # 设置结果以向 handle_sse 中的等待代码发出信号
                fut.set_result(None)
                return Response(status_code=200)
            else:
                return Response(status_code=404, content="Session not found")
        except Exception as e:
            return Response(status_code=500)

    app = FastAPI(
        debug=debug,
        routes=[
            # 长时间运行的 sse 连接，由超时控制
            Route("/sse", endpoint=handle_sse),
            # 断开会话连接
            Route("/disconnect", endpoint=disconnect),
            # 发布消息
            Mount("/messages/", app=sse.handle_post_message),
        ],
        lifespan=lifespan,
    )

    return app

# ==================== Modal 部署配置 ====================

# 创建 Modal 镜像
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ssh")
    .pip_install("uv")
    .run_commands("uv pip install --system mcp[cli] fastmcp>=2.7.0 uvicorn fastapi starlette")
)

# 创建 Modal 应用
app = modal.App(name="fastmcp-sse-server", image=image)

@app.function(
    include_source=True,
    max_containers=10,
    min_containers=1,
    timeout=60 * 3,
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def mcp_server():
    """Modal ASGI 应用函数"""
    app_instance = create_app(mcp._mcp_server, debug=False)
    return app_instance

# ==================== 本地开发和测试 ====================

if __name__ == "__main__":
    mcp_server = mcp._mcp_server  # noqa: WPS437

    import argparse

    parser = argparse.ArgumentParser(description="运行基于 SSE 的 MCP 服务器")
    parser.add_argument("--host", default="0.0.0.0", help="绑定主机")
    parser.add_argument("--port", type=int, default=8080, help="监听端口")
    args = parser.parse_args()

    app_instance = create_app(mcp_server, debug=True)
    print("🚀 启动 FastMCP SSE 服务器")
    print(f"📡 SSE 端点: http://{args.host}:{args.port}/sse")
    print(f"🔌 断开端点: http://{args.host}:{args.port}/disconnect")
    print(f"📨 消息端点: http://{args.host}:{args.port}/messages/")
    uvicorn.run(app_instance, host=args.host, port=args.port) 
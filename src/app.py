# FastAPI + Gradio + FastMCP MCP server main entry point

import modal
from contextlib import asynccontextmanager
from fastapi import FastAPI
from gradio.routes import mount_gradio_app
import os
from dotenv import load_dotenv
import uvicorn
from mcp.server.fastmcp import FastMCP

# Import modules
from .tools import mcp_tools  # Import the module, not get_mcp_server function
from .ui.gradio_ui import create_gradio_interface
from .config.config import is_modal_mode, is_local_mode

# Always import modal config since this module might be imported in modal context
try:
    from .config.modal_config import app, image, volume, cache_dir, secrets
    _modal_available = True
except ImportError:
    _modal_available = False

# ==================== Application Creation Function ====================

def create_app():
    """Create and return complete Gradio + MCP application"""
    
    print("🚀 Starting Gradio + FastMCP server")
    
    # Create FastMCP server with new tools
    mcp = FastMCP("Podcast MCP")
    
    # Register tools using the new service architecture
    @mcp.tool(description="Transcribe audio files to text using Whisper model with speaker diarization support")
    async def transcribe_audio_file_tool(
        audio_file_path: str,
        model_size: str = "turbo",
        language: str = None,
        output_format: str = "srt",
        enable_speaker_diarization: bool = False
    ):
        return await mcp_tools.transcribe_audio_file(
            audio_file_path, model_size, language, output_format, enable_speaker_diarization
        )
    
    @mcp.tool(description="Download Apple Podcast audio files")
    async def download_apple_podcast_tool(url: str):
        return await mcp_tools.download_apple_podcast(url)
    
    @mcp.tool(description="Download XiaoYuZhou podcast audio files")
    async def download_xyz_podcast_tool(url: str):
        return await mcp_tools.download_xyz_podcast(url)
    
    @mcp.tool(description="Scan directory for MP3 audio files")
    async def get_mp3_files_tool(directory: str):
        return await mcp_tools.get_mp3_files(directory)
    
    @mcp.tool(description="Get basic file information")
    async def get_file_info_tool(file_path: str):
        return await mcp_tools.get_file_info(file_path)
    
    @mcp.tool(description="Read text file content in segments")
    async def read_text_file_segments_tool(
        file_path: str,
        chunk_size: int = 65536,
        start_position: int = 0
    ):
        return await mcp_tools.read_text_file_segments(file_path, chunk_size, start_position)
    
    # Create FastAPI wrapper
    fastapi_wrapper = FastAPI(
        title="Modal AudioTranscriber MCP",
        description="Gradio UI + FastMCP Tool + Modal Integration AudioTranscriber MCP",
        version="1.0.0",
        lifespan=lambda app: mcp.session_manager.run()
    )
    
    # Get FastMCP's streamable HTTP app
    mcp_app = mcp.streamable_http_app()
    
    # Mount FastMCP application to /api path  
    fastapi_wrapper.mount("/api", mcp_app)
    
    # Create Gradio interface
    ui_app = create_gradio_interface()
    
    # Use Gradio's standard mounting approach
    final_app = mount_gradio_app(
        app=fastapi_wrapper,
        blocks=ui_app,
        path="",
        app_kwargs={
            "docs_url": "/docs",
            "redoc_url": "/redoc",
        }
    )
    
    print("✅ Server startup completed")
    print("🎨 Gradio UI: /")
    print("🔧 MCP Streamable HTTP: /api/mcp")
    print(f"📝 Server name: {mcp.name}")
    
    return final_app

# ==================== Modal Deployment Configuration ====================

# Create a separate Modal app for the Gradio interface
if _modal_available:
    gradio_mcp_app = modal.App(name="gradio-mcp-ui")
    
    @gradio_mcp_app.function(
        image=image,
        cpu=2,  # Adequate CPU for UI operations
        memory=4096,  # 4GB memory for stable UI performance
        max_containers=5,  # Reduced to control resource usage
        min_containers=1,  # Keep minimum containers for faster response
        scaledown_window=600,  # 20 minutes before scaling down
        timeout=1800,  # 30 minutes timeout to prevent preemption
        volumes={cache_dir: volume},
        secrets=secrets,
    )
    @modal.concurrent(max_inputs=100)
    @modal.asgi_app()
    def app_entry():
        """Modal deployment function - create and return complete Gradio + MCP application"""
        return create_app()

# ==================== Main Entry Point ====================

def main():
    """Main entry point for all deployment modes"""
    
    if is_modal_mode():
        print("☁️ Modal mode: Use 'modal deploy src.app::gradio_mcp_app'")
        return None
    else:
        print("🏠 Starting in local mode")
        print("💡 GPU functions will be routed to Modal endpoints")
        
        app = create_app()
        return app

def run_local():
    """Run local server with uvicorn (for direct execution)"""
    app = main()
    if app:
        # Use port 7860 for HF Spaces compatibility, 7860 for local
        port = int(os.environ.get("PORT", 7860))  # HF Spaces uses port 7860
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False
        )

# ==================== Hugging Face Spaces Support ====================

# For Hugging Face Spaces, directly create the app
def get_app():
    """Get app instance for HF Spaces"""
    if "DEPLOYMENT_MODE" not in os.environ:
        os.environ["DEPLOYMENT_MODE"] = "local"
    return main()

# Create app for HF Spaces when imported
app = get_app()  # Always create app for HF Spaces

if __name__ == "__main__":
    run_local()
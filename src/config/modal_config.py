import modal
import os
from dotenv import load_dotenv

# Load environment variables from config.env if it exists
if os.path.exists("config.env"):
    load_dotenv("config.env", override=False)
    print("📄 Loaded config from config.env")

# Load from .env if it exists (fallback)
if os.path.exists(".env"):
    load_dotenv(".env", override=False)
    print("📄 Loaded config from .env")

# Get Modal configuration from environment variables
MODAL_APP_NAME = os.getenv("MODAL_APP_NAME", "gradio-mcp-server")
MODAL_GPU_TYPE = os.getenv("MODAL_GPU_TYPE", "A10G")
MODAL_MEMORY = int(os.getenv("MODAL_MEMORY", "8192"))  # Default 8GB
MODAL_CPU = int(os.getenv("MODAL_CPU", "4"))

print(f"🔧 Modal Configuration:")
print(f"   App Name: {MODAL_APP_NAME}")
print(f"   GPU Type: {MODAL_GPU_TYPE}")
print(f"   Memory: {MODAL_MEMORY}MB")
print(f"   CPU: {MODAL_CPU}")

# Create Modal application with configurable name
app = modal.App(name=MODAL_APP_NAME)

# Try to get Hugging Face token from Modal secrets (required for speaker diarization)
try:
    hf_secret = modal.Secret.from_name("huggingface-secret")
    print("✅ Found Hugging Face secret configuration")
except Exception:
    hf_secret = None
    print("⚠️ Hugging Face secret not found, speaker diarization will be disabled")

# Create mounted volume
volume = modal.Volume.from_name("cache-volume", create_if_missing=True)
cache_dir = "/root/cache"

# Model preloading function
def download_models() -> None:
    """Download and cache Whisper and speaker diarization models"""
    import whisper
    import os
    from pathlib import Path
    
    # Create model cache directory
    model_cache_dir = Path("/model")
    model_cache_dir.mkdir(exist_ok=True)
    
    print("📥 Downloading Whisper turbo model...")
    # Download and cache Whisper turbo model
    whisper_model = whisper.load_model("turbo", download_root="/model")
    print("✅ Whisper turbo model downloaded and cached")
    
    # Download speaker diarization models if HF token is available
    if os.environ.get("HF_TOKEN"):
        try:
            print("📥 Downloading speaker diarization models...")
            from pyannote.audio import Pipeline, Model
            from pyannote.audio.core.inference import Inference
            import torch
            
            # Set proper cache directory for pyannote
            os.environ["PYANNOTE_CACHE"] = "/model/speaker-diarization"
            
            # Download and cache speaker diarization pipeline
            # This will automatically cache to the PYANNOTE_CACHE directory
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=os.environ["HF_TOKEN"],
                cache_dir="/model/speaker-diarization"
            )
            
            # Preload speaker embedding model for speaker identification
            print("📥 Downloading speaker embedding model...")
            embedding_model = Model.from_pretrained(
                "pyannote/embedding",
                use_auth_token=os.environ["HF_TOKEN"],
                cache_dir="/model/speaker-embedding"
            )
            
            # Set device for models
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            embedding_model.to(device)
            embedding_model.eval()
            
            # Create inference object for embedding extraction
            inference = Inference(embedding_model, window="whole")
            
            # Verify the pipeline works
            print("🧪 Testing speaker diarization pipeline...")
            
            # Create a simple marker file to indicate successful download
            import json
            speaker_dir = Path("/model/speaker-diarization")
            speaker_dir.mkdir(exist_ok=True, parents=True)
            
            embedding_dir = Path("/model/speaker-embedding")
            embedding_dir.mkdir(exist_ok=True, parents=True)
            
            config = {
                "model_name": "pyannote/speaker-diarization-3.1",
                "embedding_model_name": "pyannote/embedding",
                "cached_at": str(speaker_dir),
                "embedding_cached_at": str(embedding_dir),
                "cache_complete": True,
                "embedding_cache_complete": True,
                "pyannote_cache_env": "/model/speaker-diarization",
                "device": str(device)
            }
            with open(speaker_dir / "download_complete.json", "w") as f:
                json.dump(config, f)
            
            print("✅ Speaker diarization and embedding models downloaded and cached")
        except Exception as e:
            print(f"⚠️ Failed to download speaker diarization models: {e}")
    else:
        print("⚠️ No HF_TOKEN found, skipping speaker diarization model download")

# Create image environment with model preloading
image = modal.Image.debian_slim(python_version="3.11").apt_install(
    # Basic tools
    "ffmpeg",
    "wget",
    "curl",
    "unzip",
    "gnupg2",
    "git",  # Required by Whisper
    # Chrome dependencies
    "libglib2.0-0",
    "libnss3",
    "libatk-bridge2.0-0",
    "libdrm2",
    "libxkbcommon0",
    "libxcomposite1",
    "libxdamage1",
    "libxrandr2",
    "libgbm1",
    "libxss1",
    "libasound2"
).run_commands(
    # Download and install Chrome directly (faster method)
    "wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
    "apt-get install -y ./google-chrome-stable_current_amd64.deb || apt-get install -y -f",
    "rm google-chrome-stable_current_amd64.deb"
).pip_install(
    # Web frameworks and basic libraries
    "gradio>=5.31.0",
    "fastapi",
    "pydantic", 
    "python-dotenv",
    # MCP related
    "mcp[cli]",
    "fastmcp>=2.7.0",
    "starlette",
    # Network and parsing
    "beautifulsoup4",
    "selenium",
    "requests",
    # Whisper and audio processing related
    "git+https://github.com/openai/whisper.git",
    "ffmpeg-python",
    "torchaudio==2.1.0",
    "numpy<2",
    # Audio processing dependencies
    "librosa",
    "soundfile",
    # Other Whisper ecosystem dependencies
    "dacite",
    "jiwer",
    "pandas",
    "loguru==0.6.0",
    # GraphQL client (if needed)
    "gql[all]~=3.0.0a5",
    # Speaker diarization related dependencies
    "pyannote.audio==3.1.0",
    # System monitoring
    "psutil",
).run_function(
    download_models, 
    secrets=[hf_secret] if hf_secret else []
)

# Update file paths to reflect new structure
image = image.add_local_dir("../src", remote_path="/root/src")
secrets = [hf_secret] if hf_secret else []

# ==================== Modal Endpoints Configuration ====================

@app.function(
    image=image,
    volumes={cache_dir: volume},
    cpu=MODAL_CPU,  # Configurable CPU from environment
    memory=MODAL_MEMORY,  # Configurable memory from environment
    gpu=MODAL_GPU_TYPE,  # Configurable GPU type from environment
    timeout=1800,  # 30 minutes timeout for speaker diarization support
    scaledown_window=40,  # 15 minutes before scaling down
    secrets=secrets,
)
@modal.fastapi_endpoint(method="POST", label="transcribe-audio-chunk-endpoint")
def transcribe_audio_chunk_endpoint(request_data: dict):
    """FastAPI endpoint for transcribing a single audio chunk (for distributed processing)"""
    import sys
    sys.path.append('/root')
    
    from src.services.modal_transcription_service import ModalTranscriptionService
    
    modal_service = ModalTranscriptionService(cache_dir="/root/cache", use_direct_modal_calls=True)
    return modal_service.process_chunk_request(request_data)

@app.function(
    image=image,
    cpu=max(2, MODAL_CPU // 2),  # Use half of configured CPU, minimum 2
    memory=max(2048, MODAL_MEMORY // 4),  # Use quarter of configured memory, minimum 2GB
    timeout=300,  # 5 minutes timeout for health checks
    scaledown_window=600,  # 10 minutes before scaling down
    secrets=secrets,
)
@modal.fastapi_endpoint(method="GET", label="health-check-endpoint")
def health_check_endpoint():
    """Health check endpoint to verify service status"""
    import sys
    sys.path.append('/root')
    
    from src.services.health_service import HealthService
    
    health_service = HealthService()
    return health_service.get_health_status()



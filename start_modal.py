#!/usr/bin/env python3
"""
Modal deployment script
"""

import os
import sys
import subprocess

def main():
    """Deploy application to Modal"""
    
    print("☁️ Deploying PodcastMcpGradio to MODAL")
    print("🚀 GPU functions will run locally on Modal")
    
    # Set deployment mode to modal
    os.environ["DEPLOYMENT_MODE"] = "modal"
    
    try:
        # First deploy the endpoints
        print("🚀 Deploying Modal endpoints...")
        result = subprocess.run([
            "modal", "deploy", "-m", "src.config.modal_config"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Successfully deployed Modal endpoints!")
        print("Endpoints output:", result.stdout)
        
        # Then deploy the Gradio UI (if needed)
        print("🚀 Deploying Gradio UI to Modal...")
        print("Note: For now, use local mode with Modal endpoints.")
        print("To run locally with Modal endpoints: python start_local.py")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Modal deployment failed: {e}")
        print("Error output:", e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Modal CLI not found. Please install it with: pip install modal")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Modal mode deployment script
Sets environment variables and deploys the application to Modal
"""

import os
import sys
import subprocess

def main():
    """Deploy application to Modal"""
    
    print("☁️ Deploying Gradio MCP Server to MODAL")
    print("🚀 GPU functions will run locally on Modal")
    
    # Set deployment mode to modal
    os.environ["DEPLOYMENT_MODE"] = "modal"
    
    try:
        # Deploy to Modal using modal deploy command
        print("🚀 Deploying to Modal...")
        result = subprocess.run([
            "modal", "deploy", "src.app::gradio_mcp_app"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Successfully deployed to Modal!")
        print("Output:", result.stdout)
        
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
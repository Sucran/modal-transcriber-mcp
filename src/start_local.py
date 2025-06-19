#!/usr/bin/env python3
"""
Local mode startup script
Sets environment variables and starts the application in local mode
"""

import os
import sys

def main():
    """Start application in local mode"""
    
    print("🏠 Starting Gradio MCP Server in LOCAL mode")
    print("💡 GPU functions will be routed to Modal endpoints")
    
    # Set deployment mode to local
    os.environ["DEPLOYMENT_MODE"] = "local"
    
    # Add parent directory to path for src imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    # Import and run the app
    from src.app import run_local
    
    try:
        run_local()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
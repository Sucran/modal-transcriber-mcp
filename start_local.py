#!/usr/bin/env python3
"""
Local development startup script
"""

import os
import sys

def main():
    """Start application in local mode"""
    
    print("🏠 Starting PodcastMcpGradio in LOCAL mode")
    print("💡 GPU functions will be routed to Modal endpoints")
    
    # Set deployment mode to local
    os.environ["DEPLOYMENT_MODE"] = "local"
    
    # Add current directory to path for src imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
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
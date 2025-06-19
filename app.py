#!/usr/bin/env python3
"""
PodcastMcpGradio - Main Entry Point

This is the main entry point for the PodcastMcpGradio application.
It supports both local and Modal deployment modes.
"""

import os
import sys

# Add current directory to path for src imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the actual app from src
from src.app import create_app, main, get_app

# Re-export for compatibility
__all__ = ["create_app", "main", "get_app"]

# For direct execution
if __name__ == "__main__":
    from src.app import run_local
    run_local() 
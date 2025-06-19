#!/usr/bin/env python3
"""
Deployment Manager - Root Entry Point

This is the main entry point for deployment management.
"""

import os
import sys

# Add current directory to path for src imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import and run the deployment manager from src
from src.deployment.deployment_manager import main

if __name__ == "__main__":
    main() 
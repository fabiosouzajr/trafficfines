#!/usr/bin/env python
"""
Entry point script for Traffic Fine Manager.

This script allows running the application from the project root
without needing to install the package.
"""
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import and run main
from src.trafficfines.main import main

if __name__ == "__main__":
    main()


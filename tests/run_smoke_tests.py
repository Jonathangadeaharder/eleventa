#!/usr/bin/env python
"""
Smoke Tests Runner

This script runs the UI smoke tests, which are designed to be more stable
than comprehensive UI tests. Use this to quickly verify that critical UI
functionality still works after making changes.

Usage:
    python tests/run_smoke_tests.py
"""

import os
import sys
import subprocess

if __name__ == "__main__":
    # Determine project root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    
    # Ensure the tests directory is in the Python path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Ensure the project directory is in the Python path
    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    
    # Run the smoke tests
    print("Running UI smoke tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/ui/smoke_tests.py", "-v"],
        cwd=project_dir
    )
    
    # Exit with the same status code as the pytest run
    sys.exit(result.returncode) 
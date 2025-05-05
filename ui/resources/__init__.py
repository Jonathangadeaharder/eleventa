"""
UI resources package.
This package contains Qt resources files and compiled resources.
"""
# This file ensures the resources directory is a proper Python package 

try:
    # Try to import the resources module directly
    from . import resources
except ImportError:
    # If it fails, log a message but don't crash
    import sys
    print(f"Warning: Failed to import resources module in ui/resources/__init__.py", file=sys.stderr) 
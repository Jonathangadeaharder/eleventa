"""
Patch resources module for UI tests.

This module provides mock implementations for resources that may not be available during tests.
"""
import os
import sys

# Add the project root to sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to import the resources, but provide a mock if it fails
try:
    from ui.resources import resources
    print("Successfully imported ui.resources.resources")
except ImportError:
    print("Creating mock resources module")
    
    # Create a mock resources module
    class MockResources:
        """Mock resources module."""
        
        @staticmethod
        def get_icon(name):
            """Return a mock icon."""
            from PySide6.QtGui import QIcon
            return QIcon()
        
        @staticmethod
        def get_pixmap(name):
            """Return a mock pixmap."""
            from PySide6.QtGui import QPixmap
            return QPixmap()
    
    # Register the mock as the resources module
    sys.modules['ui.resources.resources'] = MockResources() 
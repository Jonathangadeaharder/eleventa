"""
This module patches PySide6 resource loading to prevent issues in tests
related to missing icons or other resources.
"""

from PySide6.QtGui import QIcon
from unittest.mock import MagicMock
import sys

# Store original implementations
_orig_icon_init = QIcon.__init__

def _patched_icon_init(self, *args, **kwargs):
    """
    Patched QIcon.__init__ that doesn't fail on missing icons in test environments
    """
    try:
        _orig_icon_init(self, *args, **kwargs)
    except Exception as e:
        # If resource loading fails, explicitly create a default QIcon
        print(f"[PATCH] Resource loading failed, creating default icon: {e}", file=sys.stderr)
        QIcon.__init__(self) # Explicitly call the (potentially patched) __init__

def patch_resources():
    """
    Apply patches to prevent resource loading issues in tests
    """
    print("[PATCH] Patching resource loading for tests", file=sys.stderr)
    QIcon.__init__ = _patched_icon_init

def restore_resources():
    """
    Restore original resource loading behavior
    """
    print("[PATCH] Restoring original resource loading", file=sys.stderr)
    QIcon.__init__ = _orig_icon_init

# Apply patches automatically when imported
# patch_resources() # Commented out to see if tests pass without it 
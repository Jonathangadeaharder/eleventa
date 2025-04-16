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
        # Just create an empty icon if resource loading fails
        _orig_icon_init(self)
        print(f"[PATCH] Resource loading failed, using empty icon: {e}", file=sys.stderr)

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
patch_resources() 
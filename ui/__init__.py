# Simple relative import that works with PyInstaller
try:
    from . import widgets
except ImportError:
    # Fallback for development environment
    import widgets

__all__ = ["widgets"]

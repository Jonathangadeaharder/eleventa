import importlib.util
import os

# Dynamically import the widgets package to resolve import issues
spec = importlib.util.spec_from_file_location(
    "widgets", os.path.abspath("ui/widgets/__init__.py")
)
widgets_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(widgets_module)

__all__ = ["widgets"]

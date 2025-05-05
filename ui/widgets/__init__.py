import importlib.util
import os

# Dynamically import widget modules to ensure proper loading
def _import_widget(module_name):
    spec = importlib.util.spec_from_file_location(
        module_name, os.path.abspath(f"ui/widgets/{module_name}.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Example for importing a specific widget (adjust as needed)
# ButtonWidget = _import_widget("button_widget")
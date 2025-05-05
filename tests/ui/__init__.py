"""
UI tests initialization module.
This ensures Qt environment is properly set before any tests are run.
"""
import os
import sys

# Set Qt environment variables
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["PYTEST_QT_API"] = "pyside6"
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"
os.environ["QT_FORCE_STDERR_LOGGING"] = "1" 
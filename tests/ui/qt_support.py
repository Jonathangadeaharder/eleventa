"""
Provides Qt support utilities for UI testing.
"""
import os
import sys
from PySide6.QtCore import Qt, QSize, QTimer, QEventLoop, QObject, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QWidget, QPushButton, 
    QTableView, QLineEdit, QMessageBox, QVBoxLayout, QFrame, QLabel,
    QAbstractItemView
)

# Ensure singleton QApplication instance
def get_app():
    """Get or create a QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

# Qt event processing
def process_events():
    """Process Qt events."""
    app = get_app()
    app.processEvents()

# Wait utilities
def wait(ms):
    """Wait for the specified milliseconds."""
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec_()

# Widget finding utilities
def find_widget(parent, widget_type, name=None, text=None):
    """Find a widget by type, name, or text."""
    for widget in parent.findChildren(widget_type):
        if name and widget.objectName() == name:
            return widget
        if text and hasattr(widget, 'text') and widget.text() == text:
            return widget
    return None

# Test window base class for reuse
class TestWindow(QMainWindow):
    """Base test window for UI tests."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Window")
        self.resize(800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

# Set up Qt environment before any imports of PySide6
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PySide6', 'plugins', 'platforms')
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
os.environ['QT_FORCE_STDERR_LOGGING'] = '1'
os.environ['QT_QPA_ENABLE_HIGHDPI_SCALING'] = '0'
os.environ['QT_SCALE_FACTOR'] = '1'
os.environ["PYTEST_QT_API"] = "pyside6"

# Safe imports - these will be used by test files
try:
    from PySide6.QtCore import Qt, QModelIndex, QAbstractTableModel, QTimer, Signal
    from PySide6.QtWidgets import QApplication, QMessageBox, QTableView, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QAbstractItemView
    from PySide6.QtGui import QIcon, QAction
    
    # Flag to show whether imports succeeded
    QT_IMPORTS_AVAILABLE = True
    
except ImportError as e:
    # Fallback - create dummy attributes
    print(f"WARNING: Unable to import PySide6 modules: {e}")
    QT_IMPORTS_AVAILABLE = False
    
    # Create dummy classes to prevent import errors
    class DummyClass:
        """Dummy class to substitute for unavailable Qt classes"""
        def __init__(self, *args, **kwargs):
            # Assign a default name based on the class it's replacing
            # This requires knowing which class name is being assigned to DummyClass
            # We'll handle this during assignment below.
            pass
            
        def __call__(self, *args, **kwargs):
            return self
    
    # Create dummy Qt module
    class QtDummy:
        """Dummy Qt namespace"""
        LeftButton = DummyClass()
        DisplayRole = DummyClass()
        UserRole = DummyClass()
        Horizontal = DummyClass()
        Vertical = DummyClass()
        # Add other Qt constants as needed
    
    # Assign dummy objects to the expected names, adding __name__
    Qt = QtDummy()
    QModelIndex = type('QModelIndex', (DummyClass,), {'__name__': 'QModelIndex'})
    QAbstractTableModel = type('QAbstractTableModel', (DummyClass,), {'__name__': 'QAbstractTableModel'})
    QTimer = type('QTimer', (DummyClass,), {'__name__': 'QTimer'})
    Signal = type('Signal', (DummyClass,), {'__name__': 'Signal'})
    QApplication = type('QApplication', (DummyClass,), {'__name__': 'QApplication'})
    QMessageBox = type('QMessageBox', (DummyClass,), {'__name__': 'QMessageBox'})
    QTableView = type('QTableView', (DummyClass,), {'__name__': 'QTableView'})
    QWidget = type('QWidget', (DummyClass,), {'__name__': 'QWidget'})
    QVBoxLayout = type('QVBoxLayout', (DummyClass,), {'__name__': 'QVBoxLayout'})
    QHBoxLayout = type('QHBoxLayout', (DummyClass,), {'__name__': 'QHBoxLayout'})
    QIcon = type('QIcon', (DummyClass,), {'__name__': 'QIcon'})
    QAction = type('QAction', (DummyClass,), {'__name__': 'QAction'})
    QLabel = type('QLabel', (DummyClass,), {'__name__': 'QLabel'})
    QAbstractItemView = type('QAbstractItemView', (DummyClass,), {'__name__': 'QAbstractItemView'})

# Import UI resources
try:
    import ui.resources.resources
except ImportError:
    print("Warning: Could not import Qt resources (ui.resources.resources). Icons might be missing.")
import pytest
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from tests.ui.qt_test_base import BaseQtTest

class ButtonTestWidget(QWidget):
    """A simple widget with a button and label for demonstration purposes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ButtonTestWidget")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create button
        self.button = QPushButton("Click Me", self)
        self.button.setObjectName("testButton")
        self.button.clicked.connect(self.on_button_clicked)
        
        # Create label to display click count
        self.label = QLabel("Button not clicked yet", self)
        self.label.setObjectName("clickCountLabel")
        
        # Add widgets to layout
        layout.addWidget(self.button)
        layout.addWidget(self.label)
        
        # Initialize click count
        self.click_count = 0

    def on_button_clicked(self):
        """Handle button click event."""
        self.click_count += 1
        self.label.setText(f"Button clicked {self.click_count} time(s)")


class TestButtonWidget:
    """Test case for the ButtonTestWidget."""
    
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        """Set up the test fixture."""
        # Create the widget
        self.widget = ButtonTestWidget()
        # Add widget to qtbot
        qtbot.addWidget(self.widget)
        # Show the widget
        self.widget.show()
        # Store qtbot reference
        self.qtbot = qtbot
        
    def test_initial_state(self):
        """Test the initial state of the widget."""
        # Verify the button text
        button = self.widget.button
        assert button.text() == "Click Me"
        
        # Verify the label's initial text
        label = self.widget.label
        assert label.text() == "Button not clicked yet"
        
        # Verify the click count is zero
        assert self.widget.click_count == 0
    
    def test_button_click(self):
        """Test that clicking the button updates the label."""
        # Get the button
        button = self.widget.button
        
        # Click the button
        self.qtbot.mouseClick(button, Qt.LeftButton)
        
        # Verify the click count was incremented
        assert self.widget.click_count == 1
        
        # Verify the label text was updated
        label = self.widget.label
        assert label.text() == "Button clicked 1 time(s)"
        
        # Click the button again
        self.qtbot.mouseClick(button, Qt.LeftButton)
        
        # Verify the click count and label were updated again
        assert self.widget.click_count == 2
        assert label.text() == "Button clicked 2 time(s)"
    
    def test_widget_resize(self):
        """Test that the widget can be resized."""
        # Get original size
        original_size = self.widget.size()
        
        # Resize the widget
        new_width = original_size.width() + 50
        new_height = original_size.height() + 50
        self.widget.resize(new_width, new_height)
        
        # Process events
        QApplication.processEvents()
        
        # Verify the new size
        assert self.widget.width() == new_width
        assert self.widget.height() == new_height


if __name__ == "__main__":
    # Allow this file to be run directly for debugging
    pytest.main(["-v", __file__]) 
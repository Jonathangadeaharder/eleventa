from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableView, QHeaderView, QAbstractItemView,
    QLineEdit, QLabel, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon

from ui.utils import show_error_message, show_info_message, ask_confirmation
from ui.resources import resources  # Import the compiled resources

class ViewBase(QWidget):
    """Base class for views to standardize layout and common functionalities."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName(self.__class__.__name__.lower())
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)
        
        # Header area for view title and top controls
        self.header_frame = QFrame()
        self.header_frame.setObjectName("header_frame")
        self.header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.header_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.header_frame.setStyleSheet("""
            #header_frame {
                background-color: #f5f5f5;
                border-radius: 6px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Create default components (can be hidden or replaced by subclasses)
        self.view_title = QLabel("View Title")
        self.view_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.header_layout.addWidget(self.view_title)
        
        # Spacer in the middle
        self.header_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Search field (commonly used in list views)
        self.search_container = QFrame()
        self.search_layout = QHBoxLayout(self.search_container)
        self.search_layout.setContentsMargins(0, 0, 0, 0)
        self.search_layout.setSpacing(5)
        
        self.search_label = QLabel("Buscar:")
        self.search_layout.addWidget(self.search_label)
        
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Ingrese término de búsqueda...")
        self.search_entry.setMinimumWidth(200)
        self.search_layout.addWidget(self.search_entry)
        
        self.header_layout.addWidget(self.search_container)
        self.main_layout.addWidget(self.header_frame)
        
        # Content area - to be filled by subclasses
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.content_frame)
        
        # Footer area for common buttons
        self.footer_frame = QFrame()
        self.footer_layout = QHBoxLayout(self.footer_frame)
        self.footer_layout.setContentsMargins(0, 0, 0, 0)
        
        # Right-aligned buttons
        self.footer_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.main_layout.addWidget(self.footer_frame)
        
        # Initialize common connections
        self.search_entry.returnPressed.connect(self._on_search)
        
    def set_view_title(self, title):
        """Set the title of the view."""
        self.view_title.setText(title)
        
    def setup_table_view(self, table_view, model, enable_selection=True, enable_editing=False):
        """Configure a QTableView with standard settings."""
        table_view.setModel(model)
        table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        if enable_selection:
            table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        else:
            table_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            
        if enable_editing:
            table_view.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        else:
            table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            
        table_view.horizontalHeader().setStretchLastSection(True)
        table_view.setAlternatingRowColors(True)
        table_view.setStyleSheet("""
            QTableView {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 2px;
                gridline-color: #e0e0e0;
            }
            QTableView::item:selected {
                background-color: #2980b9;
                color: white;
            }
        """)
        
        # Auto-resize columns to content
        table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
    def add_action_button(self, text, icon=None, connected_slot=None, is_primary=False):
        """Add a button to the footer area and optionally connect its clicked signal."""
        button = QPushButton(text)
        
        if icon:
            button.setIcon(QIcon(icon))
            
        if is_primary:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2980b9;
                    color: white;
                    border: 1px solid #2573a7;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3498db;
                }
                QPushButton:pressed {
                    background-color: #1c638f;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
                QPushButton:pressed {
                    background-color: #e0e0e0;
                }
            """)
        
        if connected_slot:
            button.clicked.connect(connected_slot)
            
        self.footer_layout.addWidget(button)
        return button
    
    def get_selected_row_data(self, table_view, role=Qt.ItemDataRole.UserRole):
        """Get the data from the selected row in a table view."""
        selected_indexes = table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
            
        # Get the data using the UserRole (usually contains the full object)
        model_index = selected_indexes[0]
        return model_index.data(role)
    
    def show_error(self, title, message):
        """Show an error message dialog."""
        show_error_message(self, title, message)
        
    def show_info(self, title, message):
        """Show an information message dialog."""
        show_info_message(self, title, message)
        
    def ask_confirmation(self, title, message):
        """Ask for user confirmation."""
        return ask_confirmation(self, title, message)
    
    @Slot()
    def _on_search(self):
        """Default search handler - to be overridden by subclasses."""
        pass
    
    def hide_search(self):
        """Hide the search field."""
        self.search_container.setVisible(False)
        
    def show_search(self):
        """Show the search field."""
        self.search_container.setVisible(True) 
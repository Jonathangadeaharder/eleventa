from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, 
    QDateEdit, QPushButton, QFrame, QVBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, Signal, Slot, Property
from PySide6.QtGui import QIcon
from datetime import datetime, timedelta

from ui.utils import style_dropdown, style_secondary_button, style_primary_button

# Ensure style functions have __name__ for shiboken support
for func, name in [(style_dropdown, 'style_dropdown'),
                   (style_secondary_button, 'style_secondary_button'),
                   (style_primary_button, 'style_primary_button')]:
    if not hasattr(func, '__name__'):
        setattr(func, '__name__', name)


class PeriodFilterWidget(QWidget):
    """
    A reusable widget for filtering by time period that includes:
    - A dropdown for common period options (Today, Yesterday, This Week, etc.)
    - Optional date pickers for custom period selection
    
    Emits a periodChanged signal with start and end datetime objects when selection changes.
    """
    
    periodChanged = Signal(datetime, datetime)
    
    def __init__(self, label_text="Mostrar:", parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self._init_ui()
        
        # Set default period (Today)
        self._on_period_changed(0)
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label
        self.label = QLabel(self.label_text)
        self.label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.label)
        
        # Period dropdown
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Hoy", 
            "Ayer", 
            "Esta semana", 
            "Semana pasada",
            "Este mes", 
            "Mes pasado", 
            "Este año", 
            "Período personalizado"
        ])
        self.period_combo.setMinimumWidth(150)
        style_dropdown(self.period_combo)
        layout.addWidget(self.period_combo)
        
        # Custom date controls (initially hidden)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setMinimumHeight(28)
        self.start_date_edit.setStyleSheet("""
            QDateEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QDateEdit:focus {
                border: 1px solid #2c6ba5;
            }
        """)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setMinimumHeight(28)
        self.end_date_edit.setStyleSheet("""
            QDateEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: white;
            }
            QDateEdit:focus {
                border: 1px solid #2c6ba5;
            }
        """)
        
        self.date_from_label = QLabel("Desde:")
        self.date_to_label = QLabel("Hasta:")
        self.apply_btn = QPushButton("Aplicar")
        style_secondary_button(self.apply_btn)
        self.apply_btn.setIcon(QIcon(":/icons/icons/save.png"))
        
        layout.addWidget(self.date_from_label)
        layout.addWidget(self.start_date_edit)
        layout.addWidget(self.date_to_label)
        layout.addWidget(self.end_date_edit)
        layout.addWidget(self.apply_btn)
        
        # Hide custom date controls initially
        self._toggle_custom_date_controls(False)
        
        # Add stretch to prevent widget from expanding too much
        layout.addStretch()
        
        # Connect signals
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        self.apply_btn.clicked.connect(self._on_custom_dates_applied)
    
    def _toggle_custom_date_controls(self, show):
        """Show or hide the custom date selection controls."""
        self.date_from_label.setVisible(show)
        self.start_date_edit.setVisible(show)
        self.date_to_label.setVisible(show)
        self.end_date_edit.setVisible(show)
        self.apply_btn.setVisible(show)
    
    @Slot(int)
    def _on_period_changed(self, index):
        """Handle selection of a different period in the combobox."""
        today = QDate.currentDate()
        show_custom = (index == 7)  # "Período personalizado" is the last option
        
        self._toggle_custom_date_controls(show_custom)
        
        if not show_custom:
            # Set date range based on selection and emit signal
            if index == 0:  # Hoy
                start_date = today
                end_date = today
            elif index == 1:  # Ayer
                yesterday = today.addDays(-1)
                start_date = yesterday
                end_date = yesterday
            elif index == 2:  # Esta semana
                days_to_monday = today.dayOfWeek() - 1
                monday = today.addDays(-days_to_monday)
                start_date = monday
                end_date = today
            elif index == 3:  # Semana pasada
                days_to_monday = today.dayOfWeek() - 1
                last_monday = today.addDays(-days_to_monday - 7)
                last_sunday = today.addDays(-days_to_monday - 1)
                start_date = last_monday
                end_date = last_sunday
            elif index == 4:  # Este mes
                first_day = QDate(today.year(), today.month(), 1)
                start_date = first_day
                end_date = today
            elif index == 5:  # Mes pasado
                first_day_last_month = QDate(today.year(), today.month(), 1).addMonths(-1)
                last_day_last_month = QDate(today.year(), today.month(), 1).addDays(-1)
                start_date = first_day_last_month
                end_date = last_day_last_month
            elif index == 6:  # Este año
                first_day = QDate(today.year(), 1, 1)
                start_date = first_day
                end_date = today
            
            # Update the date edit controls (even if hidden)
            self.start_date_edit.setDate(start_date)
            self.end_date_edit.setDate(end_date)
            
            # Emit the period change with start/end datetime objects
            self._emit_period_change(start_date, end_date)
    
    @Slot()
    def _on_custom_dates_applied(self):
        """Handle when the user clicks Apply after setting custom dates."""
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        if start_date > end_date:
            # Handle invalid date range (could show error message)
            temp = start_date
            start_date = end_date
            end_date = temp
            
            # Update the controls
            self.start_date_edit.setDate(start_date)
            self.end_date_edit.setDate(end_date)
        
        self._emit_period_change(start_date, end_date)
    
    def _emit_period_change(self, start_date, end_date):
        """Convert QDates to datetime objects and emit the signal."""
        # Convert QDate to Python date, then to datetime with time = 00:00:00 for start_date
        start_datetime = datetime.combine(start_date.toPython(), datetime.min.time())
        
        # Convert QDate to Python date, then to datetime with time = 23:59:59 for end_date
        end_datetime = datetime.combine(end_date.toPython(), datetime.max.time())
        
        # Emit the signal with the datetime objects
        self.periodChanged.emit(start_datetime, end_datetime)
    
    def get_period_range(self):
        """Return the current selected period range as a tuple of datetimes."""
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        
        start_datetime = datetime.combine(start_date.toPython(), datetime.min.time())
        end_datetime = datetime.combine(end_date.toPython(), datetime.max.time())
        
        return start_datetime, end_datetime


class FilterBoxWidget(QFrame):
    """
    A styled frame containing multiple filter widgets, typically used at the top of report views.
    Organizes filter controls in a horizontal layout with proper spacing and visual separation.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            FilterBoxWidget {
                background-color: #f8f8f8; 
                border: 1px solid #ddd; 
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(15)
    
    def add_widget(self, widget):
        """Add a widget to the filter box layout."""
        self.layout.addWidget(widget)
    
    def add_separator(self):
        """Add a vertical separator line between filter controls."""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("""
            background-color: #dddddd;
            min-width: 1px;
            max-width: 1px;
        """)
        self.layout.addWidget(separator)
    
    def add_stretch(self):
        """Add stretch to push filters to the left."""
        self.layout.addStretch()


class FilterDropdown(QWidget):
    """
    A simple filter widget combining a label and dropdown.
    Used for department, customer, register selections, etc.
    """
    
    selectionChanged = Signal(object)  # Emits the selected value/id
    
    def __init__(self, label_text, items=None, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        self.label = QLabel(label_text)
        self.label.setStyleSheet("font-weight: bold;")
        
        self.combo = QComboBox()
        self.combo.setMinimumWidth(150)
        style_dropdown(self.combo)
        
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        
        # Add items if provided
        if items:
            self.set_items(items)
        
        # Connect signals
        self.combo.currentIndexChanged.connect(self._on_selection_changed)
    
    def set_items(self, items):
        """
        Set the dropdown items.
        Items can be:
        - A list of strings
        - A list of (display_text, value) tuples
        - A list of objects with a 'name' and 'id' attribute (like Department, Customer)
        """
        self.combo.clear()
        
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:
                # Tuple of (display_text, value)
                self.combo.addItem(str(item[0]), item[1])
            elif hasattr(item, 'name') and hasattr(item, 'id'):
                # Object with name and id attributes
                self.combo.addItem(item.name, item.id)
            else:
                # Simple string or other object
                self.combo.addItem(str(item))
    
    @Slot(int)
    def _on_selection_changed(self, index):
        """Emit the selected value when changed."""
        value = self.combo.itemData(index)
        self.selectionChanged.emit(value)
    
    def get_selected_value(self):
        """Return the currently selected value."""
        return self.combo.currentData()
    
    def get_selected_text(self):
        """Return the currently selected text."""
        return self.combo.currentText() 
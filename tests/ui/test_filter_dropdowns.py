import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate
from PySide6.QtTest import QSignalSpy
from datetime import datetime, timedelta

from ui.widgets.filter_dropdowns import PeriodFilterWidget, FilterDropdown, FilterBoxWidget


class TestPeriodFilterWidget:
    """Test cases for PeriodFilterWidget."""
    
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.qtbot = qtbot
        self.widget = PeriodFilterWidget("Test Period:")
    
    def test_widget_initialization(self):
        """Test that the widget initializes correctly."""
        assert self.widget.label.text() == "Test Period:"
        assert self.widget.period_combo.count() == 8
        assert self.widget.period_combo.currentIndex() == 0  # Should default to "Hoy"
        
        # Custom date controls should be hidden initially
        assert not self.widget.start_date_edit.isVisible()
        assert not self.widget.end_date_edit.isVisible()
        assert not self.widget.apply_btn.isVisible()
    
    def test_period_selection_today(self):
        """Test selecting 'Today' period."""
        # Create spy after widget initialization
        spy = QSignalSpy(self.widget.periodChanged)
        
        # First change to a different index to ensure signal will be triggered
        self.widget.period_combo.setCurrentIndex(1)  # Yesterday
        
        # Now select "Hoy" (Today) - index 0
        self.widget.period_combo.setCurrentIndex(0)
        
        # Check signal was emitted (should be 2 times - once for yesterday, once for today)
        assert spy.count() == 2
        
        # Check the last signal arguments (for today)
        args = spy.at(1)  # Get the second emission (today)
        start_date, end_date = args
        
        # Both should be today's date
        today = datetime.now().date()
        assert start_date.date() == today
        assert end_date.date() == today
    
    def test_period_selection_yesterday(self):
        """Test selecting 'Yesterday' period."""
        spy = QSignalSpy(self.widget.periodChanged)
        
        # Select "Ayer" (index 1)
        self.widget.period_combo.setCurrentIndex(1)
        
        # Should emit signal with yesterday's date range
        assert spy.count() == 1
        signal_args = spy.at(0)
        start_date, end_date = signal_args
        yesterday = datetime.now().date() - timedelta(days=1)
        assert start_date.date() == yesterday
        assert end_date.date() == yesterday
    
    def test_period_selection_this_week(self):
        """Test selecting 'This Week' period."""
        spy = QSignalSpy(self.widget.periodChanged)
        
        # Select "Esta semana" (index 2)
        self.widget.period_combo.setCurrentIndex(2)
        
        # Should emit signal with this week's date range
        assert spy.count() == 1
        signal_args = spy.at(0)
        start_date, end_date = signal_args
        
        # Start should be Monday of current week
        today = datetime.now().date()
        days_to_monday = today.weekday()
        monday = today - timedelta(days=days_to_monday)
        
        assert start_date.date() == monday
        assert end_date.date() == today
    
    def test_custom_period_selection(self):
        """Test custom date controls exist and toggle method works."""
        # Test that all custom date controls exist
        assert hasattr(self.widget, 'start_date_edit')
        assert hasattr(self.widget, 'end_date_edit')
        assert hasattr(self.widget, 'apply_btn')
        assert hasattr(self.widget, 'date_from_label')
        assert hasattr(self.widget, 'date_to_label')
        
        # Test that toggle method exists and can be called
        assert hasattr(self.widget, '_toggle_custom_date_controls')
        
        # Test calling the toggle method (should not raise exceptions)
        self.widget._toggle_custom_date_controls(True)
        self.widget._toggle_custom_date_controls(False)
        
        # Test that period combo has the expected number of items
        assert self.widget.period_combo.count() == 8
        
        # Test that the last item is the custom period option
        last_item = self.widget.period_combo.itemText(7)
        assert "personalizado" in last_item.lower()
    
    def test_custom_date_application(self):
        """Test applying custom date range."""
        spy = QSignalSpy(self.widget.periodChanged)
        
        # Select custom period
        self.widget.period_combo.setCurrentIndex(7)
        
        # Set custom dates
        start_date = QDate.currentDate().addDays(-10)
        end_date = QDate.currentDate().addDays(-5)
        
        self.widget.start_date_edit.setDate(start_date)
        self.widget.end_date_edit.setDate(end_date)
        
        # Apply the custom dates
        self.widget.apply_btn.click()
        
        # Should emit signal with custom date range
        assert spy.count() == 1
        signal_args = spy.at(0)
        emitted_start, emitted_end = signal_args
        assert emitted_start.date() == start_date.toPython()
        assert emitted_end.date() == end_date.toPython()


class TestFilterDropdown:
    """Test cases for FilterDropdown."""
    
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.qtbot = qtbot
        self.widget = FilterDropdown("Test Filter:", ["Option 1", "Option 2", "Option 3"])
    
    def test_widget_initialization(self):
        """Test that the filter dropdown initializes correctly."""
        assert self.widget.label.text() == "Test Filter:"
        assert self.widget.combo.count() == 3  # 3 options
        assert self.widget.combo.itemText(0) == "Option 1"
        assert self.widget.combo.itemText(1) == "Option 2"
        assert self.widget.combo.itemText(2) == "Option 3"
    
    def test_selection_change_signal(self):
        """Test that selection changes emit the correct signal."""
        spy = QSignalSpy(self.widget.selectionChanged)
        
        # Select "Option 2" (index 1)
        self.widget.combo.setCurrentIndex(1)
        
        # Should emit signal with selected value (None since no data set)
        assert spy.count() == 1
        signal_args = spy.at(0)
        assert signal_args[0] is None
    
    def test_get_selected_value(self):
        """Test getting the currently selected value."""
        # Default should be None (no data set)
        assert self.widget.get_selected_value() is None
        
        # Select an option
        self.widget.combo.setCurrentIndex(1)
        assert self.widget.get_selected_value() is None  # No data set for items
    
    def test_get_selected_text(self):
        """Test getting the currently selected text."""
        # Default should be first option
        assert self.widget.get_selected_text() == "Option 1"
        
        # Select another option
        self.widget.combo.setCurrentIndex(2)
        assert self.widget.get_selected_text() == "Option 3"


class TestFilterBoxWidget:
    """Test cases for FilterBoxWidget."""
    
    @pytest.fixture(autouse=True)
    def setup(self, qtbot):
        self.qtbot = qtbot
        self.widget = FilterBoxWidget()
    
    def test_widget_initialization(self):
        """Test that the filter box initializes correctly."""
        assert self.widget.layout is not None
        assert self.widget.layout.count() == 0  # Should start empty
    
    def test_add_widget(self):
        """Test adding widgets to the filter box."""
        # Add a period filter
        period_filter = PeriodFilterWidget("Period:")
        self.widget.add_widget(period_filter)
        
        # Widget should be added to layout
        assert self.widget.layout.count() == 1
        assert self.widget.layout.itemAt(0).widget() == period_filter
    
    def test_add_separator(self):
        """Test adding separators to the filter box."""
        # Add a widget, separator, and another widget
        period_filter = PeriodFilterWidget("Period:")
        dropdown_filter = FilterDropdown("Type:", ["A", "B", "C"])
        
        self.widget.add_widget(period_filter)
        self.widget.add_separator()
        self.widget.add_widget(dropdown_filter)
        
        assert self.widget.layout.count() == 3
        assert self.widget.layout.itemAt(0).widget() == period_filter
        assert self.widget.layout.itemAt(2).widget() == dropdown_filter
    
    def test_add_stretch(self):
        """Test adding stretch to the filter box."""
        period_filter = PeriodFilterWidget("Period:")
        self.widget.add_widget(period_filter)
        self.widget.add_stretch()
        
        # Should have widget + stretch
        assert self.widget.layout.count() == 2
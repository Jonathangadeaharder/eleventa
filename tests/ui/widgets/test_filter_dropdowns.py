import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate
from ui.widgets.filter_dropdowns import PeriodFilterWidget


class TestPeriodFilterWidget:
    """Test cases for PeriodFilterWidget."""
    
    @pytest.fixture
    def widget(self, qtbot):
        """Create a PeriodFilterWidget for testing."""
        widget = PeriodFilterWidget()
        qtbot.addWidget(widget)
        return widget
    
    def test_widget_initialization(self, widget):
        """Test that the widget initializes correctly."""
        # Check that combo box has expected items
        expected_periods = ['Hoy', 'Ayer', 'Esta semana', 'Semana pasada', 
                           'Este mes', 'Mes pasado', 'Este año', 'Año pasado', 'Personalizado']
        
        actual_periods = [widget.period_combo.itemText(i) for i in range(widget.period_combo.count())]
        assert actual_periods == expected_periods
        
        # Check initial state
        assert widget.period_combo.currentText() == 'Hoy'
        assert not widget.start_date.isEnabled()
        assert not widget.end_date.isEnabled()
    
    def test_custom_period_enables_dates(self, widget):
        """Test that selecting 'Personalizado' enables date fields."""
        custom_index = widget.period_combo.findText('Personalizado')
        widget.period_combo.setCurrentIndex(custom_index)
        widget._on_period_changed(widget.period_combo.currentIndex())
        
        assert widget.start_date.isEnabled()
        assert widget.end_date.isEnabled()
    
    def test_predefined_period_disables_dates(self, widget):
        """Test that selecting predefined periods disables date fields."""
        # First set to custom to enable dates
        custom_index = widget.period_combo.findText('Personalizado')
        widget.period_combo.setCurrentIndex(custom_index)
        widget._on_period_changed(widget.period_combo.currentIndex())
        
        # Then set to predefined period
        today_index = widget.period_combo.findText('Hoy')
        widget.period_combo.setCurrentIndex(today_index)
        widget._on_period_changed(widget.period_combo.currentIndex())
        
        assert not widget.start_date.isEnabled()
        assert not widget.end_date.isEnabled()
    
    @pytest.mark.parametrize("period_text,expected_days", [
        ('Hoy', 0),
        ('Ayer', 1),
        ('Esta semana', None),  # Variable based on current date
        ('Semana pasada', None),  # Variable based on current date
        ('Este mes', None),  # Variable based on current date
        ('Mes pasado', None),  # Variable based on current date
        ('Este año', None),  # Variable based on current date
        ('Año pasado', None),  # Variable based on current date
    ])
    def test_get_date_range_predefined(self, widget, period_text, expected_days):
        """Test getting date range for predefined periods."""
        period_index = widget.period_combo.findText(period_text)
        widget.period_combo.setCurrentIndex(period_index)
        
        start_date, end_date = widget.get_date_range()
        
        # Basic validation that we get dates
        assert isinstance(start_date, date)
        assert isinstance(end_date, date)
        assert start_date <= end_date
        
        # For simple cases, check exact values
        if expected_days is not None:
            today = date.today()
            if period_text == 'Hoy':
                assert start_date == today
                assert end_date == today
            elif period_text == 'Ayer':
                yesterday = today - timedelta(days=1)
                assert start_date == yesterday
                assert end_date == yesterday
    
    def test_get_date_range_this_week(self, widget):
        """Test getting date range for 'Esta semana'."""
        period_index = widget.period_combo.findText('Esta semana')
        widget.period_combo.setCurrentIndex(period_index)
        
        start_date, end_date = widget.get_date_range()
        
        # Should be from Monday to Sunday of current week
        today = date.today()
        days_since_monday = today.weekday()
        expected_start = today - timedelta(days=days_since_monday)
        expected_end = expected_start + timedelta(days=6)
        
        assert start_date == expected_start
        assert end_date == expected_end
    
    def test_get_date_range_last_week(self, widget):
        """Test getting date range for 'Semana pasada'."""
        period_index = widget.period_combo.findText('Semana pasada')
        widget.period_combo.setCurrentIndex(period_index)
        
        start_date, end_date = widget.get_date_range()
        
        # Should be from Monday to Sunday of last week
        today = date.today()
        days_since_monday = today.weekday()
        this_monday = today - timedelta(days=days_since_monday)
        last_monday = this_monday - timedelta(days=7)
        last_sunday = last_monday + timedelta(days=6)
        
        assert start_date == last_monday
        assert end_date == last_sunday
    
    def test_get_date_range_this_month(self, widget):
        """Test getting date range for 'Este mes'."""
        period_index = widget.period_combo.findText('Este mes')
        widget.period_combo.setCurrentIndex(period_index)
        
        start_date, end_date = widget.get_date_range()
        
        today = date.today()
        expected_start = date(today.year, today.month, 1)
        
        # Last day of current month
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        expected_end = next_month - timedelta(days=1)
        
        assert start_date == expected_start
        assert end_date == expected_end
    
    def test_get_date_range_custom(self, widget):
        """Test getting date range for 'Personalizado' (Custom)."""
        custom_index = widget.period_combo.findText('Personalizado')
        widget.period_combo.setCurrentIndex(custom_index)
        widget._on_period_changed(widget.period_combo.currentIndex())
        
        # Set custom dates
        test_start = date(2024, 1, 15)
        test_end = date(2024, 1, 31)
        
        widget.start_date.setDate(QDate(test_start))
        widget.end_date.setDate(QDate(test_end))
        
        start_date, end_date = widget.get_date_range()
        
        assert start_date == test_start
        assert end_date == test_end
    
    def test_get_date_range_custom_invalid_order(self, widget):
        """Test custom date range with end date before start date."""
        custom_index = widget.period_combo.findText('Personalizado')
        widget.period_combo.setCurrentIndex(custom_index)
        widget._on_period_changed(widget.period_combo.currentIndex())
        
        # Set end date before start date
        test_start = date(2024, 1, 31)
        test_end = date(2024, 1, 15)
        
        widget.start_date.setDate(QDate(test_start))
        widget.end_date.setDate(QDate(test_end))
        
        start_date, end_date = widget.get_date_range()
        
        # Should swap the dates to maintain logical order
        assert start_date == test_end  # Earlier date becomes start
        assert end_date == test_start  # Later date becomes end
    
    def test_period_change_signal(self, widget):
        """Test that period change emits signal."""
        with patch.object(widget, 'filter_applied') as mock_signal:
            # Change period
            today_index = widget.period_combo.findText('Hoy')
            widget.period_combo.setCurrentIndex(today_index)
            
            # Manually trigger the change (since we're not using real UI events)
            widget._on_period_changed(widget.period_combo.currentIndex())
            
            # Signal should be emitted
            mock_signal.emit.assert_called_once()
    
    def test_date_change_signal(self, widget):
        """Test that date change emits signal for custom period."""
        # Set to custom period first
        custom_index = widget.period_combo.findText('Personalizado')
        widget.period_combo.setCurrentIndex(custom_index)
        widget._on_period_changed(widget.period_combo.currentIndex())
        
        with patch.object(widget, 'filter_applied') as mock_signal:
            # Change start date (this should automatically trigger the signal)
            widget.start_date.setDate(QDate(2024, 1, 15))
            
            # Signal should be emitted once automatically
            mock_signal.emit.assert_called_once()
    
    def test_widget_has_filter_applied_signal(self, widget):
        """Test that widget has filter_applied signal."""
        assert hasattr(widget, 'filter_applied')
        assert hasattr(widget.filter_applied, 'emit')
    
    def test_date_widgets_exist(self, widget):
        """Test that date widgets are properly created."""
        assert hasattr(widget, 'start_date')
        assert hasattr(widget, 'end_date')
        assert hasattr(widget, 'period_combo')
    
    def test_signal_connections(self, widget):
        """Test that signals are properly connected."""
        # Test that period combo signal connection works by checking if method exists
        assert hasattr(widget, '_on_period_changed')
        
        # Test that date change signal connection works by checking if method exists
        assert hasattr(widget, 'on_date_changed')
        
        # Test that the signals exist
        assert hasattr(widget.period_combo, 'currentIndexChanged')
        assert hasattr(widget.start_date, 'dateChanged')
        assert hasattr(widget.end_date, 'dateChanged')
    
    @pytest.mark.parametrize("period_text,expected_enabled", [
        ('Hoy', False),
        ('Ayer', False),
        ('Esta semana', False),
        ('Semana pasada', False),
        ('Este mes', False),
        ('Mes pasado', False),
        ('Este año', False),
        ('Año pasado', False),
        ('Personalizado', True),
    ])
    def test_date_fields_enabled_state(self, widget, period_text, expected_enabled):
        """Test that date fields are enabled/disabled correctly for each period."""
        period_index = widget.period_combo.findText(period_text)
        widget.period_combo.setCurrentIndex(period_index)
        widget._on_period_changed(widget.period_combo.currentIndex())
        
        assert widget.start_date.isEnabled() == expected_enabled
        assert widget.end_date.isEnabled() == expected_enabled
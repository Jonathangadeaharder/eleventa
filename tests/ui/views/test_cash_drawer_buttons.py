"""
Test for CashDrawerView button actions.
"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# Very short timeout
pytestmark = pytest.mark.timeout(5)

def create_drawer_summary(is_open=True):
    """Create a mock drawer summary."""
    return {
        'is_open': is_open,
        'current_balance': Decimal('100.00'),
        'initial_amount': Decimal('100.00'),
        'total_in': Decimal('0.00'),
        'total_out': Decimal('0.00'),
        'entries_today': [],
        'opened_at': None,
        'opened_by': 1
    }

def test_open_drawer_button(qtbot):
    """Test opening the cash drawer with the button."""
    with patch('ui.views.cash_drawer_view.OpenDrawerDialog') as mock_open_dialog, \
         patch('ui.views.cash_drawer_view.QMessageBox') as mock_message_box, \
         patch('ui.models.table_models.CashDrawerTableModel.update_entries', MagicMock()):

        # Import view *after* patches are applied
        from ui.views.cash_drawer_view import CashDrawerView
        from core.services.cash_drawer_service import CashDrawerService
        from core.models.cash_drawer import CashDrawerEntry

        # Create mock service
        mock_service = MagicMock(spec=CashDrawerService)
        # State management using side effect for get_drawer_summary
        drawer_state = {'is_open': False}
        def get_summary_side_effect(*args, **kwargs):
            return create_drawer_summary(is_open=drawer_state['is_open'])
        mock_service.get_drawer_summary.side_effect = get_summary_side_effect

        # Mock the dialog instance returned by the patched OpenDrawerDialog
        mock_dialog_instance = MagicMock()
        mock_dialog_instance.exec.return_value = True # Simulate clicking OK
        # Simulate the dialog creating an entry upon success
        mock_dialog_instance.entry = MagicMock(spec=CashDrawerEntry)
        mock_open_dialog.return_value = mock_dialog_instance

        # Create view and add to qtbot
        view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
        qtbot.addWidget(view)
        
        # Disconnect signals before cleanup
        def cleanup():
            view.open_button.clicked.disconnect()
            view.add_cash_button.clicked.disconnect()
            view.remove_cash_button.clicked.disconnect()
            view.deleteLater()
        
        try:
            # Patch the view's refresh method AFTER instance creation
            with patch.object(view, '_refresh_data', wraps=view._refresh_data) as mock_refresh:
                # Verify initial state (drawer closed)
                assert view.open_button.text() == "Abrir Caja"
                assert view.open_button.isEnabled()
                assert not view.add_cash_button.isEnabled()
                assert not view.remove_cash_button.isEnabled()
                mock_service.get_drawer_summary.assert_called() # Called during init
                initial_refresh_call_count = mock_refresh.call_count

                # Wait until the button is enabled before clicking
                qtbot.waitUntil(lambda: view.open_button.isEnabled(), timeout=1000)

                # --- Action: Click open button --- 
                # Simulate the state change that happens AFTER the dialog is accepted
                # The view's handler will call _refresh_data if dialog.exec is True and dialog.entry exists
                def exec_side_effect(*args, **kwargs):
                    # Simulate the dialog succeeding and updating the state *conceptually*
                    # The real dialog would call service.open_drawer, but the view only cares about the result
                    drawer_state['is_open'] = True
                    return True # Return True for exec()
                mock_dialog_instance.exec.side_effect = exec_side_effect

                qtbot.mouseClick(view.open_button, Qt.LeftButton)

                # --- Verification --- 
                # Verify the dialog was instantiated and executed
                mock_open_dialog.assert_called_once_with(mock_service, 1, view)
                mock_dialog_instance.exec.assert_called_once()

                # Wait for the refresh call triggered by the successful dialog
                qtbot.waitUntil(lambda: mock_refresh.call_count > initial_refresh_call_count, timeout=1000)
                
                # Verify button state changed (drawer open) due to the refresh
                qtbot.waitUntil(lambda: view.open_button.text() == "Cerrar Caja", timeout=2000)
                assert view.open_button.isEnabled()
                assert view.add_cash_button.isEnabled()
                assert view.remove_cash_button.isEnabled()

        except Exception as e:
            pytest.fail(f"Test 'test_open_drawer_button' failed with exception: {e}")
        finally:
            cleanup()
            view = None

def test_add_remove_cash_buttons(qtbot):
    """Test add and remove cash buttons."""
    try:
        # Patch dependencies
        with patch('ui.views.cash_drawer_view.CashMovementDialog') as mock_cash_movement_dialog_class, \
             patch('ui.views.cash_drawer_view.QMessageBox') as mock_message_box, \
             patch('ui.models.table_models.CashDrawerTableModel.update_entries', MagicMock()):

            # Import view *after* patches are applied
            from ui.views.cash_drawer_view import CashDrawerView
            from core.services.cash_drawer_service import CashDrawerService
            from core.models.cash_drawer import CashDrawerEntry

            # Create mock service
            mock_service = MagicMock(spec=CashDrawerService)
            # Simulate drawer is open
            drawer_state = {'is_open': True}
            def get_summary_side_effect(*args, **kwargs):
                return create_drawer_summary(is_open=drawer_state['is_open'])
            mock_service.get_drawer_summary.side_effect = get_summary_side_effect

            # --- Prepare Mock Dialog Instances ---
            mock_add_dialog_instance = MagicMock(name="AddDialogInstance")
            mock_add_dialog_instance.exec.return_value = True
            mock_add_dialog_instance.entry = MagicMock(spec=CashDrawerEntry)

            mock_remove_dialog_instance = MagicMock(name="RemoveDialogInstance")
            mock_remove_dialog_instance.exec.return_value = True
            mock_remove_dialog_instance.entry = MagicMock(spec=CashDrawerEntry)
            
            # Configure the class mock to return instances sequentially using side_effect
            mock_cash_movement_dialog_class.side_effect = [mock_add_dialog_instance, mock_remove_dialog_instance]

            # Create view and add to qtbot
            view = CashDrawerView(cash_drawer_service=mock_service, user_id=1)
            qtbot.addWidget(view)
            
            # Disconnect signals before cleanup
            def cleanup():
                view.open_button.clicked.disconnect()
                view.add_cash_button.clicked.disconnect()
                view.remove_cash_button.clicked.disconnect()
                view.deleteLater()
            
            try:
                # Patch the view's refresh method AFTER instance creation
                with patch.object(view, '_refresh_data', wraps=view._refresh_data) as mock_refresh:
                    # Verify initial state (drawer open)
                    assert view.add_cash_button.isEnabled()
                    assert view.remove_cash_button.isEnabled()
                    initial_refresh_call_count = mock_refresh.call_count
                    
                    # --- Add Cash Action ---
                    qtbot.mouseClick(view.add_cash_button, Qt.LeftButton)
                    
                    # Verify the add cash dialog was instantiated correctly
                    mock_cash_movement_dialog_class.assert_any_call(mock_service, 1, is_adding=True, parent=view)
                    mock_add_dialog_instance.exec.assert_called_once()
                    # Wait for refresh triggered by successful add dialog
                    qtbot.waitUntil(lambda: mock_refresh.call_count > initial_refresh_call_count, timeout=1000)
                    add_refresh_call_count = mock_refresh.call_count
                    
                    # --- Remove Cash Action ---
                    qtbot.mouseClick(view.remove_cash_button, Qt.LeftButton)
                    
                    # Verify the remove cash dialog was instantiated correctly
                    mock_cash_movement_dialog_class.assert_called_with(mock_service, 1, is_adding=False, parent=view)
                    mock_remove_dialog_instance.exec.assert_called_once()
                    # Wait for refresh triggered by successful remove dialog
                    qtbot.waitUntil(lambda: mock_refresh.call_count > add_refresh_call_count, timeout=1000)

                    # Final Check: Ensure exec was called exactly once on EACH instance
                    mock_add_dialog_instance.exec.assert_called_once()
                    mock_remove_dialog_instance.exec.assert_called_once()
                    # Ensure the class mock was called exactly twice
                    assert mock_cash_movement_dialog_class.call_count == 2

            except Exception as e:
                pytest.fail(f"Test failed with exception: {e}")
            finally:
                cleanup()
                view = None

    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")


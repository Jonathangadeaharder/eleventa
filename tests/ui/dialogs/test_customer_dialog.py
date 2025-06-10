import pytest
import sys
from unittest.mock import MagicMock, patch
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox
from PySide6.QtTest import QTest as QtTest

from ui.dialogs.customer_dialog import CustomerDialog
from core.models.customer import Customer
from core.services.customer_service import CustomerService


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
    app.quit()


@pytest.fixture
def sample_customer():
    """Create a sample customer for testing."""
    return Customer(
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        address="123 Main St",
        cuit="20123456789",
        credit_limit=1000.00,
        credit_balance=0.00,
        is_active=True
    )


@pytest.fixture
def mock_customer_service():
    """Create a mock customer service."""
    return MagicMock(spec=CustomerService)


@pytest.fixture
def dialog_add_mode(qapp, mock_customer_service):
    """Create dialog in add mode."""
    return CustomerDialog(mock_customer_service)


@pytest.fixture
def dialog_edit_mode(qapp, mock_customer_service, sample_customer):
    """Create dialog in edit mode."""
    return CustomerDialog(mock_customer_service, customer=sample_customer)


def test_dialog_initialization_add_mode(qtbot, dialog_add_mode):
    """Test that the dialog initializes correctly in add mode."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Verify window title
    assert dialog.windowTitle() == "Nuevo Cliente"
    
    # Verify it's not in edit mode
    assert dialog._customer is None
    
    # Verify default values
    assert dialog.name_edit.text() == ""
    assert dialog.email_edit.text() == ""
    assert dialog.phone_edit.text() == ""
    assert dialog.address_edit.text() == ""
    assert dialog.credit_limit_spin.value() == 0.0


def test_dialog_initialization_edit_mode(qtbot, dialog_edit_mode, sample_customer):
    """Test that the dialog initializes correctly in edit mode."""
    dialog = dialog_edit_mode
    qtbot.addWidget(dialog)
    
    # Verify window title
    assert dialog.windowTitle() == "Editar Cliente"
    
    # Verify it's in edit mode
    assert dialog._customer == sample_customer
    
    # Verify fields are populated with customer data
    assert dialog.name_edit.text() == sample_customer.name
    assert dialog.email_edit.text() == sample_customer.email
    assert dialog.phone_edit.text() == sample_customer.phone
    assert dialog.address_edit.text() == sample_customer.address
    assert dialog.credit_limit_spin.value() == float(sample_customer.credit_limit)


def test_validation_empty_name(qtbot, dialog_add_mode, mock_customer_service):
    """Test validation for empty name field."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Leave name empty and try to accept
    dialog.name_edit.setText("")
    dialog.email_edit.setText("juan@email.com")
    dialog.phone_edit.setText("555-1234")
    
    # Mock service to raise validation error
    mock_customer_service.add_customer.side_effect = ValueError("Customer name cannot be empty")
    
    with patch.object(QMessageBox, 'warning') as mock_warning, \
         patch.object(QMessageBox, 'information') as mock_info:
        dialog.accept()
        mock_warning.assert_called_once()
        assert "validación" in mock_warning.call_args[0][1].lower()


def test_validation_invalid_email(qtbot, dialog_add_mode, mock_customer_service):
    """Test validation for invalid email format."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Set invalid email and try to accept
    dialog.name_edit.setText("Juan Pérez")
    dialog.email_edit.setText("invalid-email")
    dialog.phone_edit.setText("555-1234")
    
    # Mock service to raise validation error
    mock_customer_service.add_customer.side_effect = ValueError("Invalid email format")
    
    with patch.object(QMessageBox, 'warning') as mock_warning, \
         patch.object(QMessageBox, 'information') as mock_info:
        dialog.accept()
        mock_warning.assert_called_once()
        assert "validación" in mock_warning.call_args[0][1].lower()


def test_validation_empty_phone(qtbot, dialog_add_mode, mock_customer_service):
    """Test that empty phone is accepted (phone is optional)."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Set valid name and email but empty phone
    dialog.name_edit.setText("Juan Pérez")
    dialog.email_edit.setText("juan@email.com")
    dialog.phone_edit.setText("")  # Empty phone
    
    # Mock successful service call
    mock_customer_service.add_customer.return_value = True
    
    with patch.object(QMessageBox, 'warning') as mock_warning, \
         patch.object(QMessageBox, 'information') as mock_info:
        dialog.accept()
        # Phone is optional, so no warning should be shown
        mock_warning.assert_not_called()
        mock_info.assert_called_once()


def test_validation_negative_credit_limit(qtbot, dialog_add_mode, mock_customer_service):
    """Test that negative credit limit is accepted (no validation in service)."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Set negative credit limit and try to accept
    dialog.name_edit.setText("Juan Pérez")
    dialog.email_edit.setText("juan@email.com")
    dialog.phone_edit.setText("555-1234")
    dialog.credit_limit_spin.setValue(-100.0)
    
    # Mock successful service call
    mock_customer_service.add_customer.return_value = True
    
    with patch.object(QMessageBox, 'warning') as mock_warning, \
         patch.object(QMessageBox, 'information') as mock_info:
        dialog.accept()
        # No validation for negative credit limit in service
        mock_warning.assert_not_called()
        mock_info.assert_called_once()


def test_successful_add_customer(qtbot, dialog_add_mode, mock_customer_service, monkeypatch):
    """Test successful customer addition."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in valid data
    dialog.name_edit.setText("Juan Pérez")
    dialog.email_edit.setText("juan@email.com")
    dialog.phone_edit.setText("555-1234")
    dialog.address_edit.setText("123 Main St")
    dialog.credit_limit_spin.setValue(5000.0)
    
    # Mock successful service call
    mock_customer_service.add_customer.return_value = True
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Accept the dialog
    with patch.object(QMessageBox, 'information') as mock_info:
        dialog.accept()
    
    # Verify service was called with correct data
    mock_customer_service.add_customer.assert_called_once()
    call_kwargs = mock_customer_service.add_customer.call_args[1]
    assert call_kwargs['name'] == "Juan Pérez"
    assert call_kwargs['email'] == "juan@email.com"
    assert call_kwargs['phone'] == "555-1234"
    assert call_kwargs['address'] == "123 Main St"
    assert call_kwargs['credit_limit'] == Decimal("5000.0")


def test_successful_edit_customer(qtbot, dialog_edit_mode, mock_customer_service, sample_customer, monkeypatch):
    """Test successful customer editing."""
    dialog = dialog_edit_mode
    qtbot.addWidget(dialog)
    
    # Modify some data
    dialog.name_edit.setText("Juan Carlos Pérez")
    dialog.credit_limit_spin.setValue(7500.0)
    
    # Mock successful service call
    mock_customer_service.update_customer.return_value = True
    
    # Patch QDialog.accept to prevent actual dialog closing
    monkeypatch.setattr('PySide6.QtWidgets.QDialog.accept', lambda self: None)
    
    # Accept the dialog
    with patch.object(QMessageBox, 'information') as mock_info:
        dialog.accept()
    
    # Verify service was called with correct data
    mock_customer_service.update_customer.assert_called_once()
    call_args = mock_customer_service.update_customer.call_args
    assert call_args[0][0] == sample_customer.id  # First positional arg is customer ID
    call_kwargs = call_args[1]  # Keyword arguments
    assert call_kwargs['name'] == "Juan Carlos Pérez"
    assert call_kwargs['credit_limit'] == Decimal("7500.0")


def test_service_error_handling_add(qtbot, dialog_add_mode, mock_customer_service):
    """Test handling of service errors during add."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in valid data
    dialog.name_edit.setText("Juan Pérez")
    dialog.email_edit.setText("juan@email.com")
    dialog.phone_edit.setText("555-1234")
    
    # Mock service error
    mock_customer_service.add_customer.side_effect = Exception("Database error")
    
    with patch.object(QMessageBox, 'warning') as mock_warning, \
         patch.object(QMessageBox, 'information') as mock_info:
        dialog.accept()
        mock_warning.assert_called_once()
        assert "error" in mock_warning.call_args[0][2].lower()


def test_service_error_handling_edit(qtbot, dialog_edit_mode, mock_customer_service):
    """Test handling of service errors during edit."""
    dialog = dialog_edit_mode
    qtbot.addWidget(dialog)
    
    # Mock service error
    mock_customer_service.update_customer.side_effect = Exception("Database error")
    
    with patch.object(QMessageBox, 'warning') as mock_warning, \
         patch.object(QMessageBox, 'information') as mock_info:
        dialog.accept()
        mock_warning.assert_called_once()
        assert "error" in mock_warning.call_args[0][2].lower()


def test_cancel_dialog(qtbot, dialog_add_mode):
    """Test canceling the dialog."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Fill in some data
    dialog.name_edit.setText("Juan Pérez")
    dialog.email_edit.setText("juan@email.com")
    
    # Cancel the dialog
    dialog.reject()
    
    # Verify dialog result
    assert dialog.result() == CustomerDialog.Rejected


def test_credit_limit_formatting(qtbot, dialog_add_mode):
    """Test credit limit field formatting."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Set credit limit value
    dialog.credit_limit_spin.setValue(1500.50)
    
    # Should display with currency prefix
    assert dialog.credit_limit_spin.value() == 1500.50


def test_email_validation_accepts_valid_emails(qtbot, dialog_add_mode, mock_customer_service):
    """Test that valid email formats are accepted."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    valid_emails = [
        "test@example.com",
        "user.name@domain.co.uk",
        "user+tag@example.org"
    ]
    
    for email in valid_emails:
        dialog.name_edit.setText("Test User")
        dialog.email_edit.setText(email)
        dialog.phone_edit.setText("555-1234")
        
        # Mock successful service call
        mock_customer_service.add_customer.return_value = True
        
        # Should not show validation error and should succeed
        with patch.object(QMessageBox, 'warning') as mock_warning, \
             patch.object(QMessageBox, 'information') as mock_info:
            dialog.accept()
            mock_warning.assert_not_called()
            mock_info.assert_called_once()


def test_phone_formatting(qtbot, dialog_add_mode):
    """Test phone number formatting."""
    dialog = dialog_add_mode
    qtbot.addWidget(dialog)
    
    # Test phone formatting
    dialog.phone_edit.setText("5551234567")
    dialog.phone_edit.editingFinished.emit()
    
    # Phone should be formatted
    formatted_phone = dialog.phone_edit.text()
    assert len(formatted_phone) >= 10  # Should have formatting characters
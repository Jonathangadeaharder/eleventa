import pytest
from unittest.mock import MagicMock, patch
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from core.services.cash_drawer_service import CashDrawerService
from datetime import datetime
from decimal import Decimal


@pytest.fixture
def cash_drawer_repo_mock():
    mock = MagicMock()
    return mock


@pytest.fixture
def cash_drawer_service(cash_drawer_repo_mock):
    return CashDrawerService(cash_drawer_repo_mock)


def test_open_drawer(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    initial_amount = Decimal('1000.0')
    user_id = 1
    description = "Opening drawer"
    
    # Setup mock
    cash_drawer_repo_mock.is_drawer_open.return_value = False
    
    # Act
    cash_drawer_service.open_drawer(initial_amount, description, user_id)
    
    # Assert
    cash_drawer_repo_mock.add_entry.assert_called_once()
    args = cash_drawer_repo_mock.add_entry.call_args[0][0]
    assert args.entry_type == CashDrawerEntryType.START
    assert args.amount == initial_amount
    assert args.user_id == user_id
    assert args.description == description


def test_open_drawer_already_open(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    initial_amount = Decimal('1000.0')
    user_id = 1
    description = "Opening drawer"
    
    # Setup mock to return drawer is already open
    cash_drawer_repo_mock.is_drawer_open.return_value = True
    
    # Act & Assert
    with pytest.raises(ValueError, match="Cash drawer is already open"):
        cash_drawer_service.open_drawer(initial_amount, description, user_id)


def test_open_drawer_negative_amount(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    initial_amount = Decimal('-100.0')
    user_id = 1
    description = "Opening drawer"
    
    # Setup mock
    cash_drawer_repo_mock.is_drawer_open.return_value = False
    
    # Act & Assert
    with pytest.raises(ValueError, match="Initial amount cannot be negative"):
        cash_drawer_service.open_drawer(initial_amount, description, user_id)


def test_add_cash(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    amount = Decimal('200.0')
    user_id = 1
    description = "Adding cash"
    
    # Setup mock for drawer open check
    cash_drawer_repo_mock.is_drawer_open.return_value = True
    
    # Act
    cash_drawer_service.add_cash(amount, description, user_id)
    
    # Assert
    cash_drawer_repo_mock.add_entry.assert_called_once()
    args = cash_drawer_repo_mock.add_entry.call_args[0][0]
    assert args.entry_type == CashDrawerEntryType.IN
    assert args.amount == amount
    assert args.user_id == user_id
    assert args.description == description


def test_add_cash_drawer_not_open(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    amount = Decimal('200.0')
    user_id = 1
    description = "Adding cash"
    
    # Setup mock for drawer closed
    cash_drawer_repo_mock.is_drawer_open.return_value = False
    
    # Act & Assert
    with pytest.raises(ValueError, match="Cash drawer is not open"):
        cash_drawer_service.add_cash(amount, description, user_id)


def test_add_cash_negative_amount(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    amount = Decimal('-50.0')
    user_id = 1
    description = "Adding cash"
    
    # Setup mock for drawer open check
    cash_drawer_repo_mock.is_drawer_open.return_value = True
    
    # Act & Assert
    with pytest.raises(ValueError, match="Amount must be positive"):
        cash_drawer_service.add_cash(amount, description, user_id)


def test_remove_cash(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    amount = Decimal('150.0')
    user_id = 1
    description = "Removing cash"
    
    # Setup mocks
    cash_drawer_repo_mock.is_drawer_open.return_value = True
    cash_drawer_repo_mock.get_current_balance.return_value = Decimal('500.0')
    
    # Act
    cash_drawer_service.remove_cash(amount, description, user_id)
    
    # Assert
    cash_drawer_repo_mock.add_entry.assert_called_once()
    args = cash_drawer_repo_mock.add_entry.call_args[0][0]
    assert args.entry_type == CashDrawerEntryType.OUT
    assert args.amount == -amount  # Should be negative for removals
    assert args.user_id == user_id
    assert args.description == description


def test_remove_cash_drawer_not_open(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    amount = Decimal('150.0')
    user_id = 1
    description = "Removing cash"
    
    # Setup mock for drawer closed
    cash_drawer_repo_mock.is_drawer_open.return_value = False
    
    # Act & Assert
    with pytest.raises(ValueError, match="Cash drawer is not open"):
        cash_drawer_service.remove_cash(amount, description, user_id)


def test_remove_cash_negative_amount(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    amount = Decimal('-50.0')
    user_id = 1
    description = "Removing cash"
    
    # Setup mocks
    cash_drawer_repo_mock.is_drawer_open.return_value = True
    
    # Act & Assert
    with pytest.raises(ValueError, match="Amount must be positive"):
        cash_drawer_service.remove_cash(amount, description, user_id)


def test_remove_cash_insufficient_funds(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    amount = Decimal('600.0')
    user_id = 1
    description = "Removing cash"
    
    # Setup mocks
    cash_drawer_repo_mock.is_drawer_open.return_value = True
    cash_drawer_repo_mock.get_current_balance.return_value = Decimal('500.0')
    
    # Act & Assert
    with pytest.raises(ValueError, match="Insufficient cash in drawer"):
        cash_drawer_service.remove_cash(amount, description, user_id)


def test_get_drawer_summary(cash_drawer_service, cash_drawer_repo_mock):
    # Arrange
    # Setup mocks for the repository methods
    cash_drawer_repo_mock.is_drawer_open.return_value = True
    
    today_entries = [
        CashDrawerEntry(
            id=1, 
            entry_type=CashDrawerEntryType.START, 
            amount=Decimal('1000.0'), 
            user_id=1, 
            timestamp=datetime.now(),
            description="Opening",
            drawer_id=1
        ),
        CashDrawerEntry(
            id=2, 
            entry_type=CashDrawerEntryType.IN, 
            amount=Decimal('200.0'), 
            user_id=1, 
            timestamp=datetime.now(),
            description="Adding cash",
            drawer_id=1
        ),
        CashDrawerEntry(
            id=3, 
            entry_type=CashDrawerEntryType.OUT, 
            amount=Decimal('-100.0'), 
            user_id=1, 
            timestamp=datetime.now(),
            description="Removing cash",
            drawer_id=1
        )
    ]
    
    cash_drawer_repo_mock.get_today_entries.return_value = today_entries
    cash_drawer_repo_mock.get_current_balance.return_value = Decimal('1100.0')
    
    # Act
    summary = cash_drawer_service.get_drawer_summary()
    
    # Assert
    assert summary['is_open'] is True
    assert summary['current_balance'] == Decimal('1100.0')
    assert summary['initial_amount'] == Decimal('1000.0')
    assert summary['total_in'] == Decimal('200.0')
    assert summary['total_out'] == Decimal('100.0')  # Absolute value
    assert summary['entries_today'] == today_entries
    assert summary['opened_at'] == today_entries[0].timestamp
    assert summary['opened_by'] == today_entries[0].user_id 
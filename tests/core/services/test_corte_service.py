import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal

from core.services.corte_service import CorteService
from core.models.sale import Sale, SaleItem
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType


class TestCorteService(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.sale_repository = Mock()
        self.cash_drawer_repository = Mock()
        self.corte_service = CorteService(
            sale_repository=self.sale_repository,
            cash_drawer_repository=self.cash_drawer_repository
        )
        
        # Set up test periods
        self.start_time = datetime(2025, 4, 13, 8, 0)  # April 13, 2025, 8:00 AM
        self.end_time = datetime(2025, 4, 13, 20, 0)   # April 13, 2025, 8:00 PM

    def test_calculate_corte_data(self):
        """Test the calculate_corte_data method with mock sales and cash drawer entries."""
        # Mock starting balance entry (created before start_time)
        starting_entry = CashDrawerEntry(
            timestamp=datetime(2025, 4, 13, 7, 45),  # Before start_time
            entry_type=CashDrawerEntryType.START,
            amount=Decimal("1000.00"),
            description="Opening balance",
            user_id=1,
            drawer_id=1
        )
        
        # Mock sales data
        mock_sales = [
            # Cash sale
            Mock(
                id=1, 
                timestamp=datetime(2025, 4, 13, 10, 15),
                payment_type="Efectivo",
                total=Decimal("150.00")
            ),
            # Card sale
            Mock(
                id=2, 
                timestamp=datetime(2025, 4, 13, 11, 30),
                payment_type="Tarjeta",
                total=Decimal("250.00")
            ),
            # Another cash sale
            Mock(
                id=3, 
                timestamp=datetime(2025, 4, 13, 14, 45),
                payment_type="Efectivo",
                total=Decimal("75.50")
            ),
            # Credit sale
            Mock(
                id=4, 
                timestamp=datetime(2025, 4, 13, 16, 20),
                payment_type="Crédito",
                total=Decimal("430.00")
            )
        ]
        
        # Mock cash drawer entries
        mock_cash_entries = [
            # Cash in entry
            CashDrawerEntry(
                timestamp=datetime(2025, 4, 13, 12, 0),
                entry_type=CashDrawerEntryType.IN,
                amount=Decimal("500.00"),
                description="Deposit",
                user_id=1,
                drawer_id=1
            ),
            # Cash out entry
            CashDrawerEntry(
                timestamp=datetime(2025, 4, 13, 15, 30),
                entry_type=CashDrawerEntryType.OUT,
                amount=Decimal("200.00"),
                description="Withdrawal for supplies",
                user_id=1,
                drawer_id=1
            )
        ]
        
        # Set up repository mocks
        self.sale_repository.get_sales_by_period.return_value = mock_sales
        self.cash_drawer_repository.get_last_start_entry.return_value = starting_entry
        self.cash_drawer_repository.get_entries_by_date_range.return_value = mock_cash_entries
        
        # Call the method being tested
        result = self.corte_service.calculate_corte_data(self.start_time, self.end_time)
        
        # Verify repository methods were called with correct parameters
        self.sale_repository.get_sales_by_period.assert_called_once_with(self.start_time, self.end_time)
        self.cash_drawer_repository.get_last_start_entry.assert_called_once()
        self.cash_drawer_repository.get_entries_by_date_range.assert_called_once_with(self.start_time, self.end_time)
        
        # Assert results
        self.assertEqual(result["starting_balance"], Decimal("1000.00"))
        self.assertEqual(result["total_sales"], Decimal("905.50"))  # Sum of all sales
        self.assertEqual(result["sales_by_payment_type"]["Efectivo"], Decimal("225.50"))  # Sum of cash sales
        self.assertEqual(result["sales_by_payment_type"]["Tarjeta"], Decimal("250.00"))
        self.assertEqual(result["sales_by_payment_type"]["Crédito"], Decimal("430.00"))
        self.assertEqual(result["cash_in_total"], Decimal("500.00"))
        self.assertEqual(result["cash_out_total"], Decimal("200.00"))
        
        # Expected cash: starting balance + cash sales + cash in - cash out
        expected_cash = Decimal("1000.00") + Decimal("225.50") + Decimal("500.00") - Decimal("200.00")
        self.assertEqual(result["expected_cash_in_drawer"], expected_cash)
        self.assertEqual(result["sale_count"], 4)

    def test_calculate_starting_balance(self):
        """Test the _calculate_starting_balance private method."""
        # Mock a start entry before our period
        start_entry = CashDrawerEntry(
            timestamp=datetime(2025, 4, 13, 7, 45),
            entry_type=CashDrawerEntryType.START,
            amount=Decimal("1000.00"),
            description="Morning opening balance",
            user_id=1,
            drawer_id=1
        )
        
        # Set up the mock
        self.cash_drawer_repository.get_last_start_entry.return_value = start_entry
        
        # Call the method
        result = self.corte_service._calculate_starting_balance(self.start_time)
        
        # Verify result
        self.assertEqual(result, Decimal("1000.00"))
        
        # Test when no start entry exists
        self.cash_drawer_repository.get_last_start_entry.return_value = None
        result = self.corte_service._calculate_starting_balance(self.start_time)
        self.assertEqual(result, Decimal("0.00"))

    def test_calculate_sales_by_payment_type(self):
        """Test the _calculate_sales_by_payment_type method."""
        # Create mock sales
        mock_sales = [
            Mock(payment_type="Efectivo", total=Decimal("100.00")),
            Mock(payment_type="Tarjeta", total=Decimal("200.00")),
            Mock(payment_type="Efectivo", total=Decimal("50.00")),
            Mock(payment_type="Crédito", total=Decimal("300.00")),
            Mock(payment_type=None, total=Decimal("75.00"))  # Test handling of None payment type
        ]
        
        # Call the method
        result = self.corte_service._calculate_sales_by_payment_type(mock_sales)
        
        # Verify results
        self.assertEqual(len(result), 4)  # Efectivo, Tarjeta, Crédito, Sin especificar
        self.assertEqual(result["Efectivo"], Decimal("150.00"))
        self.assertEqual(result["Tarjeta"], Decimal("200.00"))
        self.assertEqual(result["Crédito"], Decimal("300.00"))
        self.assertEqual(result["Sin especificar"], Decimal("75.00"))

    def test_register_closing_balance(self):
        """Test registering a closing balance entry."""
        # Set up test data
        drawer_id = 1
        actual_amount = Decimal("1525.50")
        description = "End of day closing"
        user_id = 1
        
        # Mock the repository response
        mock_entry = CashDrawerEntry(
            timestamp=datetime.now(),
            entry_type=CashDrawerEntryType.CLOSE,
            amount=actual_amount,
            description=description,
            user_id=user_id,
            drawer_id=drawer_id
        )
        self.cash_drawer_repository.add_entry.return_value = mock_entry
        
        # Call the method
        result = self.corte_service.register_closing_balance(
            drawer_id=drawer_id,
            actual_amount=actual_amount,
            description=description,
            user_id=user_id
        )
        
        # Verify repository was called
        self.cash_drawer_repository.add_entry.assert_called_once()
        
        # Verify the entry type is correct
        self.assertEqual(result.entry_type, CashDrawerEntryType.CLOSE)
        self.assertEqual(result.amount, actual_amount)
        self.assertEqual(result.description, description)

    # --- Added error handling tests below ---

    def test_calculate_corte_data_invalid_period(self):
        """Test calculate_corte_data with invalid period (end_time before start_time)."""
        with self.assertRaises(ValueError):
            self.corte_service.calculate_corte_data(self.end_time, self.start_time)

    def test_calculate_corte_data_repository_failure(self):
        """Test calculate_corte_data handles repository exceptions gracefully."""
        self.sale_repository.get_sales_by_period.side_effect = Exception("Repository failure")
        with self.assertRaises(Exception):
            self.corte_service.calculate_corte_data(self.start_time, self.end_time)

        # Test cash drawer repository failure
        self.sale_repository.get_sales_by_period.side_effect = None
        self.cash_drawer_repository.get_last_start_entry.side_effect = Exception("Repository failure")
        with self.assertRaises(Exception):
            self.corte_service.calculate_corte_data(self.start_time, self.end_time)

        self.cash_drawer_repository.get_last_start_entry.side_effect = None
        self.cash_drawer_repository.get_entries_by_date_range.side_effect = Exception("Repository failure")
        with self.assertRaises(Exception):
            self.corte_service.calculate_corte_data(self.start_time, self.end_time)


if __name__ == "__main__":
    unittest.main()
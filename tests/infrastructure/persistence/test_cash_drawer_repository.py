import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from infrastructure.persistence.sqlite.cash_drawer_repository import SQLiteCashDrawerRepository
from infrastructure.persistence.sqlite.models_mapping import CashDrawerEntryOrm

@pytest.mark.usefixtures("clean_db")
class TestSQLiteCashDrawerRepository:
    def create_entry(self, entry_type, amount, user_id=1, drawer_id=1, description="Test entry", ts=None):
        return CashDrawerEntry(
            timestamp=ts or datetime.now(),
            entry_type=entry_type,
            amount=Decimal(amount),
            description=description,
            user_id=user_id,
            drawer_id=drawer_id
        )

    def test_add_and_get_entry_by_id(self, test_db_session):
        repo = SQLiteCashDrawerRepository(test_db_session)
        entry = self.create_entry(CashDrawerEntryType.START, "100.00")
        added = repo.add_entry(entry)
        assert added.id is not None

        fetched = repo.get_entry_by_id(added.id)
        assert fetched is not None
        assert fetched.amount == Decimal("100.00")
        assert fetched.entry_type == CashDrawerEntryType.START

    def test_get_entry_by_id_not_found(self, test_db_session):
        repo = SQLiteCashDrawerRepository(test_db_session)
        assert repo.get_entry_by_id(99999) is None

    def test_get_entries_by_date_range(self, test_db_session):
        repo = SQLiteCashDrawerRepository(test_db_session)
        today = date.today()
        yesterday = today - timedelta(days=1)
        entry1 = self.create_entry(CashDrawerEntryType.IN, "50.00", ts=datetime.combine(today, datetime.min.time()))
        entry2 = self.create_entry(CashDrawerEntryType.OUT, "20.00", ts=datetime.combine(yesterday, datetime.min.time()))
        repo.add_entry(entry1)
        repo.add_entry(entry2)

        results = repo.get_entries_by_date_range(yesterday, today)
        assert len(results) >= 2
        types = {e.entry_type for e in results}
        assert CashDrawerEntryType.IN in types
        assert CashDrawerEntryType.OUT in types

    def test_get_entries_by_drawer_id(self, test_db_session):
        repo = SQLiteCashDrawerRepository(test_db_session)
        entry1 = self.create_entry(CashDrawerEntryType.SALE, "30.00", drawer_id=1)
        entry2 = self.create_entry(CashDrawerEntryType.RETURN, "10.00", drawer_id=2)
        repo.add_entry(entry1)
        repo.add_entry(entry2)

        results = repo.get_entries_by_drawer_id(1)
        assert all(e.drawer_id == 1 for e in results)
        assert any(e.entry_type == CashDrawerEntryType.SALE for e in results)

    def test_get_current_balance(self, test_db_session):
        # Ensure the table is empty
        test_db_session.query(CashDrawerEntryOrm).delete()
        test_db_session.commit()
        
        repo = SQLiteCashDrawerRepository(test_db_session)
        
        # Add entries with specific amounts
        entries = [
            (CashDrawerEntryType.START, "100.00"),
            (CashDrawerEntryType.IN, "50.00"),
            (CashDrawerEntryType.OUT, "20.00"),
            (CashDrawerEntryType.SALE, "30.00"),
            (CashDrawerEntryType.RETURN, "10.00"),
            (CashDrawerEntryType.IN, "40.00")
        ]
        
        expected_balance = Decimal("0")
        for entry_type, amount in entries:
            repo.add_entry(self.create_entry(entry_type, amount))
            # Add to expected balance based on entry type
            expected_balance += Decimal(amount)
            
        # Get actual balance from repository
        balance = repo.get_current_balance()
        assert balance == expected_balance, f"Expected {expected_balance}, got {balance}"

    def test_get_current_balance_no_entries(self, test_db_session):
        # Ensure the table is empty
        test_db_session.query(CashDrawerEntryOrm).delete()
        test_db_session.commit()
        
        repo = SQLiteCashDrawerRepository(test_db_session)
        balance = repo.get_current_balance()
        assert balance == Decimal("0.00")

    def test_is_drawer_open(self, test_db_session):
        repo = SQLiteCashDrawerRepository(test_db_session)
        assert not repo.is_drawer_open()
        repo.add_entry(self.create_entry(CashDrawerEntryType.START, "100.00"))
        assert repo.is_drawer_open()
        repo.add_entry(self.create_entry(CashDrawerEntryType.CLOSE, "0.00"))
        assert not repo.is_drawer_open()

    def test_get_today_entries(self, test_db_session):
        repo = SQLiteCashDrawerRepository(test_db_session)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        repo.add_entry(self.create_entry(CashDrawerEntryType.IN, "10.00", ts=today))
        repo.add_entry(self.create_entry(CashDrawerEntryType.OUT, "5.00", ts=yesterday))
        today_entries = repo.get_today_entries()
        assert any(e.entry_type == CashDrawerEntryType.IN for e in today_entries)
        assert all(e.timestamp.date() == today.date() for e in today_entries)
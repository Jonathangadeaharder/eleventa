import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal
from core.models.cash_drawer import CashDrawerEntry, CashDrawerEntryType
from infrastructure.persistence.sqlite.cash_drawer_repository import SQLiteCashDrawerRepository
from infrastructure.persistence.sqlite.models_mapping import CashDrawerEntryOrm

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

    def setup_for_test(self, test_db_session):
        # Individual setup here
        # Replace with actual per-test setup logic
        pass

    def test_add_and_get_entry_by_id(self, test_db_session):
        self.setup_for_test(test_db_session)
        repo = SQLiteCashDrawerRepository(test_db_session)
        entry = self.create_entry(CashDrawerEntryType.START, "100.00")
        added = repo.add_entry(entry)
        assert added.id is not None

        fetched = repo.get_entry_by_id(added.id)
        assert fetched is not None
        assert fetched.amount == Decimal("100.00")
        assert fetched.entry_type == CashDrawerEntryType.START

    def test_get_entry_by_id_not_found(self, test_db_session):
        self.setup_for_test(test_db_session)
        repo = SQLiteCashDrawerRepository(test_db_session)
        assert repo.get_entry_by_id(99999) is None

    def test_get_entries_by_date_range(self, test_db_session):
        self.setup_for_test(test_db_session)
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
        self.setup_for_test(test_db_session)
        repo = SQLiteCashDrawerRepository(test_db_session)
        entry1 = self.create_entry(CashDrawerEntryType.SALE, "30.00", drawer_id=1)
        entry2 = self.create_entry(CashDrawerEntryType.RETURN, "10.00", drawer_id=2)
        repo.add_entry(entry1)
        repo.add_entry(entry2)

        results = repo.get_entries_by_drawer_id(1)
        assert all(e.drawer_id == 1 for e in results)
        assert any(e.entry_type == CashDrawerEntryType.SALE for e in results)

    def test_get_current_balance(self, test_db_session):
        self.setup_for_test(test_db_session)
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
        self.setup_for_test(test_db_session)
        # Ensure the table is empty
        test_db_session.query(CashDrawerEntryOrm).delete()
        test_db_session.commit()
        
        repo = SQLiteCashDrawerRepository(test_db_session)
        balance = repo.get_current_balance()
        assert balance == Decimal("0.00")

    def test_is_drawer_open(self, test_db_session):
        self.setup_for_test(test_db_session)
        repo = SQLiteCashDrawerRepository(test_db_session)
        assert not repo.is_drawer_open()
        repo.add_entry(self.create_entry(CashDrawerEntryType.START, "100.00"))
        assert repo.is_drawer_open()
        repo.add_entry(self.create_entry(CashDrawerEntryType.CLOSE, "0.00"))
        assert not repo.is_drawer_open()

    def test_get_today_entries(self, test_db_session):
        self.setup_for_test(test_db_session)
        repo = SQLiteCashDrawerRepository(test_db_session)
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        repo.add_entry(self.create_entry(CashDrawerEntryType.IN, "10.00", ts=today))
        repo.add_entry(self.create_entry(CashDrawerEntryType.OUT, "5.00", ts=yesterday))
        today_entries = repo.get_today_entries()
        assert any(e.entry_type == CashDrawerEntryType.IN for e in today_entries)
        assert all(e.timestamp.date() == today.date() for e in today_entries)

    def test_get_entries_by_type(self, test_db_session):
        self.setup_for_test(test_db_session)
        repo = SQLiteCashDrawerRepository(test_db_session)
        # Add various entry types
        repo.add_entry(self.create_entry(CashDrawerEntryType.START, "100"))
        repo.add_entry(self.create_entry(CashDrawerEntryType.SALE, "50"))
        repo.add_entry(self.create_entry(CashDrawerEntryType.SALE, "25"))
        repo.add_entry(self.create_entry(CashDrawerEntryType.OUT, "10"))

        # Test retrieving by SALE type
        sale_entries = repo.get_entries_by_type(CashDrawerEntryType.SALE.value)
        assert len(sale_entries) == 2
        assert all(e.entry_type == CashDrawerEntryType.SALE for e in sale_entries)

        # Test retrieving by OUT type
        out_entries = repo.get_entries_by_type(CashDrawerEntryType.OUT.value)
        assert len(out_entries) == 1
        assert out_entries[0].entry_type == CashDrawerEntryType.OUT
        assert out_entries[0].amount == Decimal("10.00")

        # Test retrieving a type with no entries
        close_entries = repo.get_entries_by_type(CashDrawerEntryType.CLOSE.value)
        assert len(close_entries) == 0

    def test_get_last_start_entry(self, test_db_session):
        self.setup_for_test(test_db_session)
        repo = SQLiteCashDrawerRepository(test_db_session)
        now = datetime.now()
        start1 = self.create_entry(CashDrawerEntryType.START, "100", ts=now - timedelta(hours=1))
        start2 = self.create_entry(CashDrawerEntryType.START, "150", ts=now) # Most recent
        other = self.create_entry(CashDrawerEntryType.SALE, "50", ts=now + timedelta(hours=1))
        repo.add_entry(start1)
        repo.add_entry(start2)
        repo.add_entry(other)

        # Get last start entry
        last_start = repo.get_last_start_entry()
        assert last_start is not None
        assert last_start.id == start2.id
        assert last_start.entry_type == CashDrawerEntryType.START
        assert last_start.amount == Decimal("150.00")

    def test_get_last_start_entry_none(self, test_db_session):
        self.setup_for_test(test_db_session)
        repo = SQLiteCashDrawerRepository(test_db_session)
        # Add only non-start entries
        repo.add_entry(self.create_entry(CashDrawerEntryType.SALE, "50"))
        repo.add_entry(self.create_entry(CashDrawerEntryType.OUT, "10"))

        last_start = repo.get_last_start_entry()
        assert last_start is None
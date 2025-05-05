import pytest
import datetime
from decimal import Decimal
import time
import sys
import os

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.models.customer import Customer
from core.models.credit import CreditPayment
from infrastructure.persistence.sqlite.repositories import (
    SqliteCustomerRepository,
    SqliteCreditPaymentRepository
)
from infrastructure.persistence.sqlite.database import engine, Base
from sqlalchemy import delete
from infrastructure.persistence.sqlite.models_mapping import CustomerOrm, CreditPaymentOrm
from core.models.user import User

@pytest.fixture
def customer_repo(test_db_session):
    return SqliteCustomerRepository(test_db_session)

@pytest.fixture
def credit_payment_repo(test_db_session):
    """Fixture to provide a repository instance with the test session."""
    return SqliteCreditPaymentRepository(test_db_session)

def create_sample_customer(customer_repo):
    suffix = str(int(time.time()))
    customer = Customer(
        name="Test Customer",
        address="123 Test St",
        phone="555-1234",
        email=f"test{suffix}@example.com",
        cuit=f"20{suffix}",
        iva_condition="Responsable Inscripto"
    )
    return customer_repo.add(customer)

def create_sample_payment(credit_repo, customer_id, user_id=None):
    payment = CreditPayment(
        customer_id=customer_id,
        amount=Decimal("100.00"),
        user_id=user_id
    )
    return credit_repo.add(payment)

def test_add_and_get_credit_payment(customer_repo, credit_payment_repo):
    cust = create_sample_customer(customer_repo)
    pay = create_sample_payment(credit_payment_repo, cust.id)
    assert pay.id is not None
    assert pay.customer_id == cust.id
    fetched = credit_payment_repo.get_by_id(pay.id)
    assert fetched is not None
    assert fetched.id == pay.id
    assert fetched.amount == pay.amount

def test_get_credit_payments_for_customer(customer_repo, credit_payment_repo):
    cust = create_sample_customer(customer_repo)
    p1 = create_sample_payment(credit_payment_repo, cust.id)
    p2 = create_sample_payment(credit_payment_repo, cust.id)
    lst = credit_payment_repo.get_for_customer(cust.id)
    assert isinstance(lst, list)
    assert {p.id for p in lst} == {p1.id, p2.id}

def test_get_for_customer_empty(customer_repo, credit_payment_repo):
    cust = create_sample_customer(customer_repo)
    assert credit_payment_repo.get_for_customer(cust.id) == []

def test_negative_payment_amount_raises_error():
    with pytest.raises(ValueError):
        CreditPayment(customer_id=1, amount=Decimal("-10.00"))

@pytest.fixture
def sample_user(test_db_session):
    user = User(username="testuser", password_hash="hash", is_active=True)
    test_db_session.add(user)
    test_db_session.commit()
    return user

@pytest.fixture
def sample_customer(test_db_session, customer_repo):
    return create_sample_customer(customer_repo)

# --- Test Class ---
class TestSqliteCreditPaymentRepository:
    def test_add_credit_payment(self, credit_payment_repo, sample_customer, sample_user, test_db_session):
        payment = CreditPayment(
            customer_id=sample_customer.id,
            amount=Decimal("150.00"),
            user_id=sample_user.id,
            timestamp=datetime.datetime.now()
        )
        
        added = credit_payment_repo.add(payment)
        assert added.id is not None
        assert added.customer_id == sample_customer.id
        assert added.amount == Decimal("150.00")
        assert added.user_id == sample_user.id

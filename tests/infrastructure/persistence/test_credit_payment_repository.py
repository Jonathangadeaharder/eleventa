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

@pytest.fixture(scope="function", autouse=True)
def setup_database(test_db_session):
    # Create tables and clear data
    Base.metadata.create_all(bind=engine)
    test_db_session.execute(delete(CreditPaymentOrm))
    test_db_session.execute(delete(CustomerOrm))
    test_db_session.flush()
    yield
    # Cleanup
    test_db_session.execute(delete(CreditPaymentOrm))
    test_db_session.execute(delete(CustomerOrm))
    test_db_session.flush()

@pytest.fixture
def customer_repo(test_db_session):
    return SqliteCustomerRepository(test_db_session)

@pytest.fixture
def credit_repo(test_db_session):
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

def test_add_and_get_credit_payment(customer_repo, credit_repo):
    cust = create_sample_customer(customer_repo)
    pay = create_sample_payment(credit_repo, cust.id)
    assert pay.id is not None
    assert pay.customer_id == cust.id
    fetched = credit_repo.get_by_id(pay.id)
    assert fetched is not None
    assert fetched.id == pay.id
    assert fetched.amount == pay.amount

def test_get_credit_payments_for_customer(customer_repo, credit_repo):
    cust = create_sample_customer(customer_repo)
    p1 = create_sample_payment(credit_repo, cust.id)
    p2 = create_sample_payment(credit_repo, cust.id)
    lst = credit_repo.get_for_customer(cust.id)
    assert isinstance(lst, list)
    assert {p.id for p in lst} == {p1.id, p2.id}

def test_get_for_customer_empty(customer_repo, credit_repo):
    cust = create_sample_customer(customer_repo)
    assert credit_repo.get_for_customer(cust.id) == []

def test_negative_payment_amount_raises_error():
    with pytest.raises(ValueError):
        CreditPayment(customer_id=1, amount=Decimal("-10.00"))

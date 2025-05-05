import pytest
import uuid

from infrastructure.persistence.sqlite.models_mapping import CustomerOrm
from infrastructure.persistence.sqlite.repositories import SqliteCustomerRepository
from core.models.customer import Customer

@pytest.fixture
def repository(test_db_session):
    """Get a repository instance with a test session."""
    return SqliteCustomerRepository(test_db_session)

def _add_sample_customer(session, name="Test Customer", cuit="12345678", **kwargs) -> Customer:
    """Helper function to add a sample customer."""
    email = kwargs.pop("email", f"{name.lower().replace(' ', '.')}@test.com")
    customer_repo = SqliteCustomerRepository(session)
    customer = Customer(name=name, cuit=cuit, email=email, **kwargs)
    return customer_repo.add(customer)

# Define the test functions
def test_add_customer(repository, test_db_session):
    """Test adding a new customer."""
    customer_data = Customer(name="New Customer", cuit="11223344", phone="555-1234")
    added_customer = repository.add(customer_data)

    assert added_customer is not None
    assert added_customer.id is not None
    assert added_customer.name == "New Customer"
    assert added_customer.cuit == "11223344"
    assert added_customer.phone == "555-1234"

    # Verify it's in the database directly
    db_customer = test_db_session.query(CustomerOrm).filter_by(id=added_customer.id).first()
    assert db_customer is not None
    assert db_customer.name == "New Customer"

def test_add_customer_duplicate_cuit(repository, test_db_session):
    """Test adding a customer with a duplicate CUIT raises ValueError."""
    # First add a customer with a specific CUIT
    _add_sample_customer(test_db_session, cuit="99887766")
    test_db_session.commit()
    
    # Create another customer with the same CUIT
    duplicate_customer = Customer(name="Another Customer", cuit="99887766")
    
    # Try to add the duplicate customer - this should raise an exception
    with pytest.raises(ValueError):
        repository.add(duplicate_customer)

def test_add_customer_duplicate_email(repository, test_db_session):
    """Test adding a customer with a duplicate email raises ValueError."""
    # Add a customer with a specific email
    email_to_test = "unique.email@example.com"
    customer1 = Customer(name="First User", cuit="10101010", email=email_to_test)
    repository.add(customer1)
    test_db_session.commit()
    
    # Create another customer with a different CUIT but the same email
    duplicate_customer = Customer(name="Second User", cuit="20202020", email=email_to_test)
    
    # Expect a ValueError (or potentially IntegrityError wrapped as ValueError)
    with pytest.raises(ValueError):
        repository.add(duplicate_customer)

def test_get_customer_by_id(repository, test_db_session):
    """Test retrieving a customer by ID."""
    added_customer = _add_sample_customer(test_db_session)
    test_db_session.commit()
    
    retrieved_customer = repository.get_by_id(added_customer.id)

    assert retrieved_customer is not None
    assert retrieved_customer.id == added_customer.id
    assert retrieved_customer.name == added_customer.name

def test_get_customer_by_id_not_found(repository):
    """Test retrieving a non-existent customer ID returns None."""
    non_existent_id = uuid.uuid4()
    retrieved_customer = repository.get_by_id(non_existent_id)
    assert retrieved_customer is None

def test_get_customer_by_cuit(repository, test_db_session):
    """Test retrieving a customer by CUIT."""
    cuit = "55667788"
    added_customer = _add_sample_customer(test_db_session, cuit=cuit)
    test_db_session.commit()
    
    retrieved_customer = repository.get_by_cuit(cuit)

    assert retrieved_customer is not None
    assert retrieved_customer.id == added_customer.id
    assert retrieved_customer.cuit == cuit

def test_get_customer_by_cuit_not_found(repository):
    """Test retrieving a non-existent CUIT returns None."""
    retrieved_customer = repository.get_by_cuit("00000000")
    assert retrieved_customer is None

def test_get_all_customers(repository, test_db_session):
    """Test retrieving all customers."""
    _add_sample_customer(test_db_session, name="Customer Alpha", cuit="1")
    _add_sample_customer(test_db_session, name="Customer Beta", cuit="2")
    _add_sample_customer(test_db_session, name="Customer Gamma", cuit="3")
    test_db_session.commit()

    all_customers = repository.get_all()
    assert len(all_customers) == 3
    
    # Check if names are present (order might vary)
    names = {c.name for c in all_customers}
    assert "Customer Alpha" in names
    assert "Customer Beta" in names
    assert "Customer Gamma" in names

def test_update_customer(repository, test_db_session):
    """Test updating an existing customer."""
    added_customer = _add_sample_customer(test_db_session)
    test_db_session.commit()
    
    updated_data = Customer(
        id=added_customer.id,
        name="Updated Name",
        phone="555-9999",
        email="updated@example.com",
        address="456 Updated Ave",
        cuit=added_customer.cuit, # CUIT might not be updatable easily due to unique constraint
        iva_condition="Monotributista",
        credit_limit=5000.0,
        credit_balance=100.0,
        is_active=False
    )
    updated_customer = repository.update(updated_data)

    assert updated_customer is not None
    assert updated_customer.name == "Updated Name"
    assert updated_customer.phone == "555-9999"
    assert updated_customer.email == "updated@example.com"
    assert updated_customer.address == "456 Updated Ave"
    assert updated_customer.iva_condition == "Monotributista"
    assert updated_customer.credit_limit == 5000.0
    assert updated_customer.credit_balance == 100.0
    assert not updated_customer.is_active

    # Verify changes in DB
    db_customer = test_db_session.query(CustomerOrm).filter_by(id=added_customer.id).first()
    assert db_customer.name == "Updated Name"
    assert not db_customer.is_active

def test_update_customer_not_found(repository):
    """Test updating a non-existent customer returns None."""
    non_existent_customer = Customer(id=uuid.uuid4(), name="Ghost")
    updated_customer = repository.update(non_existent_customer)
    assert updated_customer is None

def test_delete_customer(repository, test_db_session):
    """Test deleting a customer."""
    added_customer = _add_sample_customer(test_db_session)
    test_db_session.commit()
    
    success = repository.delete(added_customer.id)
    assert success is True
    
    # Verify it's gone from DB
    db_customer = test_db_session.query(CustomerOrm).filter_by(id=added_customer.id).first()
    assert db_customer is None

def test_delete_customer_not_found(repository):
    """Test deleting a non-existent customer returns False."""
    non_existent_id = uuid.uuid4()
    success = repository.delete(non_existent_id)
    assert success is False

def test_search_customer_by_name(repository, test_db_session):
    """Test searching customers by name."""
    _add_sample_customer(test_db_session, name="John Smith", cuit="101")
    _add_sample_customer(test_db_session, name="John Doe", cuit="102")
    _add_sample_customer(test_db_session, name="Jane Smith", cuit="103")
    _add_sample_customer(test_db_session, name="Bob Johnson", cuit="104")
    test_db_session.commit()

    # Search for "John" - notes: "Johnson" also contains "John" (partial match)
    results = repository.search(search_term="John")
    # Check that at least the two "John X" results are included
    john_matches = [c for c in results if c.name.startswith("John")]
    assert len(john_matches) == 2
    john_names = sorted([c.name for c in john_matches])
    assert john_names == ["John Doe", "John Smith"]
    
    # Ensure Bob Johnson is also found (because "John" is a substring)
    bob_matches = [c for c in results if c.name == "Bob Johnson"]
    assert len(bob_matches) == 1
    
    # Search for "Smith"
    results = repository.search(search_term="Smith")
    # Validate that both "Smith" results are found
    smith_customers = [c for c in results if "Smith" in c.name]
    assert len(smith_customers) == 2
    smith_names = sorted([c.name for c in smith_customers])
    assert smith_names == ["Jane Smith", "John Smith"]

def test_get_all_customers_pagination(repository, test_db_session):
    """Test retrieving customers with pagination."""
    # Add 25 customers
    for i in range(25):
        _add_sample_customer(test_db_session, name=f"Customer {i}", cuit=str(i+1000))
    test_db_session.commit()
    
    # Test first page (10 results by default)
    page1 = repository.get_all(page=1)
    assert len(page1) == 10
    
    # Test second page (10 more)
    page2 = repository.get_all(page=2)
    assert len(page2) == 10
    
    # Test third page (5 remaining)
    page3 = repository.get_all(page=3)
    assert len(page3) == 5
    
    # Test custom page size
    custom_page = repository.get_all(page=1, page_size=15)
    assert len(custom_page) == 15
    
    # Test page beyond data range
    empty_page = repository.get_all(page=4)
    assert len(empty_page) == 0

def test_search_customers_filtering_and_sorting(repository, test_db_session):
    """Test advanced filtering and sorting of customers."""
    # Add test customers with varied attributes
    _add_sample_customer(
        test_db_session,
        name="Gold Customer",
        cuit="1001",
        credit_limit=10000.0,
        iva_condition="Responsable Inscripto"
    )
    _add_sample_customer(
        test_db_session,
        name="Silver Customer",
        cuit="1002",
        credit_limit=5000.0,
        iva_condition="Monotributista"
    )
    _add_sample_customer(
        test_db_session,
        name="Bronze Customer",
        cuit="1003",
        credit_limit=1000.0,
        iva_condition="Consumidor Final"
    )
    _add_sample_customer(
        test_db_session,
        name="Inactive Customer",
        cuit="1004",
        is_active=False
    )
    test_db_session.commit()

    # Test filtering by IVA condition
    resp_inscriptos = repository.search(iva_condition="Responsable Inscripto")
    assert len(resp_inscriptos) == 1
    assert resp_inscriptos[0].name == "Gold Customer"

    # Test filtering by active status with filters parameter
    active_customers = repository.search(filters={"is_active": True})
    assert len(active_customers) == 3
    active_names = sorted([c.name for c in active_customers])
    assert "Inactive Customer" not in active_names
    
    # Test searching with name pattern
    cust_with_customer = repository.search(search_term="Customer")
    assert len(cust_with_customer) >= 3
    
    # Test sorting
    credit_sorted = repository.search(
        filters={"is_active": True}, 
        sort_by="credit_limit_desc"
    )
    # Should be sorted by credit limit (highest first)
    sorted_names = [c.name for c in credit_sorted]
    assert "Gold Customer" == sorted_names[0]
    assert "Silver Customer" == sorted_names[1]
    assert "Bronze Customer" == sorted_names[2]

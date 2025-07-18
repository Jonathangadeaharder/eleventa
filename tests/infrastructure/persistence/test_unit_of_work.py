"""Tests for the Unit of Work pattern implementation."""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import sessionmaker

from infrastructure.persistence.unit_of_work import UnitOfWork, unit_of_work
from infrastructure.persistence.utils import session_scope_provider
from core.models.product import Product, Department
from core.models.inventory import InventoryMovement
from core.models.customer import Customer
from core.models.enums import InventoryMovementType


class TestUnitOfWork:
    """Test cases for Unit of Work pattern."""
    
    def test_unit_of_work_initialization(self, clean_db):
        """Test that Unit of Work initializes correctly."""
        session, domain_user = clean_db
            
        with UnitOfWork() as uow:
            # Check that all repositories are initialized
            assert uow.departments is not None
            assert uow.products is not None
            assert uow.inventory is not None
            assert uow.sales is not None
            assert uow.customers is not None
            assert uow.invoices is not None
            assert uow.credit_payments is not None
            assert uow.users is not None
            assert uow.cash_drawer is not None
            
            # Check that session is active
            assert uow.session is not None
    
    def test_unit_of_work_context_manager(self, clean_db):
        """Test Unit of Work as context manager."""
        session, domain_user = clean_db
            
        uow_instance = None
        with UnitOfWork() as uow:
            uow_instance = uow
            assert uow.session is not None
        
        # After exiting context, session should be None
        assert uow_instance.session is None
        assert uow_instance.departments is None
        assert uow_instance.products is None
    
    def test_unit_of_work_convenience_function(self, clean_db):
        """Test the convenience unit_of_work() function."""
        session, domain_user = clean_db
            
        with unit_of_work() as uow:
            assert isinstance(uow, UnitOfWork)
            assert uow.session is not None
            assert uow.products is not None
    
    def test_unit_of_work_shared_session(self, clean_db):
        """Test that all repositories share the same session."""
        session, domain_user = clean_db
            
        with UnitOfWork() as uow:
            # All repositories should share the same session
            assert uow.departments.session is uow.session
            assert uow.products.session is uow.session
            assert uow.inventory.session is uow.session
            assert uow.sales.session is uow.session
            assert uow.customers.session is uow.session
            assert uow.invoices.session is uow.session
            assert uow.credit_payments.session is uow.session
            assert uow.users.session is uow.session
            # Note: SQLiteCashDrawerRepository uses _session internally, not session
            assert uow.cash_drawer._session is uow.session
    
    def test_unit_of_work_transaction_commit(self, clean_db):
        """Test that successful operations are committed."""
        session, domain_user = clean_db
            
        # Create a department and product in the same transaction
        with UnitOfWork() as uow:
            # Add department
            department = Department(name="Test Department UoW")
            created_dept = uow.departments.add(department)
            
            # Add product with the department
            product = Product(
                code="UOW001",
                description="Unit of Work Test Product",
                sell_price=Decimal('25.00'),
                department_id=created_dept.id
            )
            created_product = uow.products.add(product)
            
            # Verify they exist within the transaction
            assert uow.departments.get_by_id(created_dept.id) is not None
            assert uow.products.get_by_id(created_product.id) is not None
        
        # Verify they still exist after transaction commit
        with UnitOfWork() as uow:
            dept = uow.departments.get_by_name("Test Department UoW")
            assert dept is not None
            
            product = uow.products.get_by_code("UOW001")
            assert product is not None
            assert product.department_id == dept.id
    
    def test_unit_of_work_transaction_rollback(self, clean_db):
        """Test that failed operations are rolled back."""
        session, domain_user = clean_db
            
        # First, create a department that will be used for conflict
        with UnitOfWork() as uow:
            department = Department(name="Conflict Department")
            uow.departments.add(department)
        
        # Now try to create another department with the same name (should fail)
        with pytest.raises(ValueError, match="already exists"):
            with UnitOfWork() as uow:
                # This should succeed
                product = Product(
                    code="ROLLBACK001",
                    description="Should be rolled back",
                    sell_price=Decimal('10.00')
                )
                created_product = uow.products.add(product)
                
                # This should fail and cause rollback
                duplicate_dept = Department(name="Conflict Department")
                uow.departments.add(duplicate_dept)  # This will raise ValueError
        
        # Verify that the product was not saved due to rollback
        with UnitOfWork() as uow:
            product = uow.products.get_by_code("ROLLBACK001")
            assert product is None
    
    def test_unit_of_work_manual_commit(self, clean_db):
        """Test manual commit functionality."""
        session, domain_user = clean_db
            
        # Test that manual commit works
        with UnitOfWork() as uow:
            # Add a department
            department = Department(name="Manual Commit Dept")
            created_dept = uow.departments.add(department)
            
            # Manual commit
            uow.commit()
            
            # Verify department exists after manual commit
            dept_check = uow.departments.get_by_name("Manual Commit Dept")
            assert dept_check is not None
        
        # Verify department still exists after context exit
        with UnitOfWork() as uow:
            dept = uow.departments.get_by_name("Manual Commit Dept")
            assert dept is not None
    
    def test_unit_of_work_manual_rollback(self, clean_db):
        """Test manual rollback functionality."""
        session, domain_user = clean_db
            
        with UnitOfWork() as uow:
            # Add a department
            department = Department(name="Manual Rollback Dept")
            uow.departments.add(department)
            
            # Manual rollback
            uow.rollback()
            
            # Add another department after rollback
            department2 = Department(name="After Rollback Dept")
            uow.departments.add(department2)
        
        # Verify only the second department exists
        with UnitOfWork() as uow:
            dept1 = uow.departments.get_by_name("Manual Rollback Dept")
            assert dept1 is None
            
            dept2 = uow.departments.get_by_name("After Rollback Dept")
            assert dept2 is not None
    

    
    def test_unit_of_work_complex_operation(self, clean_db):
        """Test a complex operation involving multiple repositories."""
        session, domain_user = clean_db
            
        with UnitOfWork() as uow:
            # Create customer
            customer = Customer(
                name="UoW Test Customer",
                email="uow@test.com",
                phone="123-456-7890",
                cuit="12345678"
            )
            created_customer = uow.customers.add(customer)
            
            # Create department
            department = Department(name="UoW Complex Dept")
            created_dept = uow.departments.add(department)
            
            # Create product
            product = Product(
                code="COMPLEX001",
                description="Complex operation product",
                sell_price=Decimal('30.00'),
                cost_price=Decimal('20.00'),
                department_id=created_dept.id,
                uses_inventory=True,
                quantity_in_stock=Decimal('100')
            )
            created_product = uow.products.add(product)
            
            # Create inventory movement
            movement = InventoryMovement(
                product_id=created_product.id,
                user_id=domain_user.id,  # Use the test user from clean_db fixture
                timestamp=datetime.now(),
                movement_type=InventoryMovementType.INITIAL,
                quantity=Decimal('100'),
                description="Initial stock for complex operation test"
            )
            uow.inventory.add_movement(movement)
        
        # Verify all entities were created successfully
        with UnitOfWork() as uow:
            customer = uow.customers.get_by_cuit("12345678")
            assert customer is not None
            assert customer.name == "UoW Test Customer"
            
            department = uow.departments.get_by_name("UoW Complex Dept")
            assert department is not None
            
            product = uow.products.get_by_code("COMPLEX001")
            assert product is not None
            assert product.department_id == department.id
            assert product.quantity_in_stock == Decimal('100')
            
            movements = uow.inventory.get_movements_for_product(product.id)
            assert len(movements) == 1
            assert movements[0].movement_type == InventoryMovementType.INITIAL
            assert movements[0].quantity == Decimal('100')


def test_unit_of_work_no_session_factory_error():
    """Test error when no session factory is set.
    
    This test is outside the TestUnitOfWork class to avoid using the clean_db fixture,
    allowing it to properly test the error condition where no session factory is set.
    """
    # Clear both default and current session factories to ensure clean state
    session_scope_provider.set_default_session_factory(None)
    session_scope_provider.set_session_factory(None)
    
    with pytest.raises(ValueError, match="No session factory has been set"):
        with UnitOfWork() as uow:
            pass
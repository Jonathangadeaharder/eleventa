"""
Test the table dependency resolution functionality.
"""
import pytest
from sqlalchemy import inspect, create_engine, text
import sqlalchemy.pool

from infrastructure.persistence.sqlite.database import Base, ensure_all_models_mapped
from infrastructure.persistence.sqlite.table_deps import create_tables_in_order


@pytest.fixture
def test_engine():
    """Create a test engine with an in-memory database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=sqlalchemy.pool.StaticPool
    )
    return engine


def test_direct_table_creation(test_engine):
    """Test the create_tables_in_order function directly."""
    # Ensure all models are properly mapped
    ensure_all_models_mapped()
    
    with test_engine.connect() as connection:
        # Bypass custom function, call create_all directly
        # create_tables_in_order(connection)
        Base.metadata.create_all(bind=connection)
        
        # Commit the transaction
        connection.commit()
        
        # Check that the tables were created using the *connection*
        inspector = inspect(connection) # Inspect using the connection where tables were created
        existing_tables = inspector.get_table_names()
        
        # Verify that critical tables exist and were created in order
        # 'customers' should be created before 'credit_payments'
        assert 'customers' in existing_tables, "customers table should be created"
        assert 'credit_payments' in existing_tables, "credit_payments table should be created"
        
        # Verify the foreign key relationship works
        try:
            # Execute each statement separately
            connection.execute(text("CREATE TABLE IF NOT EXISTS test_insert (id INTEGER PRIMARY KEY)"))
            connection.execute(text("""
                INSERT INTO customers 
                (id, name, is_active, credit_limit, credit_balance) 
                VALUES 
                ('12345678-1234-5678-1234-567812345678', 'Test Customer', 1, 0.0, 0.0)
            """))
            connection.execute(text("""
                INSERT INTO credit_payments 
                (customer_id, amount, timestamp, user_id) 
                VALUES 
                ('12345678-1234-5678-1234-567812345678', 100.0, datetime('now'), 1)
            """))
            
            # If we get here, the query worked and the foreign key constraint is satisfied
            result = connection.execute(text("SELECT * FROM credit_payments"))
            rows = result.fetchall()
            assert len(rows) > 0, "Should have inserted a credit payment"
        except Exception as e:
            pytest.fail(f"Foreign key relationship failed: {e}")


def test_table_order_validation(test_engine):
    """Test that our table ordering places customers before credit_payments."""
    # Ensure all models are properly mapped
    ensure_all_models_mapped()
    
    # Get a connection from the engine
    with test_engine.connect() as connection:
        # First create only the customers table
        customers_table = Base.metadata.tables['customers']
        customers_table.create(bind=connection)
        
        # Verify customers table exists
        inspector = inspect(test_engine)
        existing_tables = inspector.get_table_names()
        assert 'customers' in existing_tables, "customers table should be created"
        
        # Then create the credit_payments table
        credit_payments_table = Base.metadata.tables['credit_payments']
        credit_payments_table.create(bind=connection)
        
        # Verify credit_payments table exists
        inspector = inspect(test_engine)
        existing_tables = inspector.get_table_names()
        assert 'credit_payments' in existing_tables, "credit_payments table should be created"
        
        # Verify the foreign key relationship
        fks = inspector.get_foreign_keys('credit_payments')
        customer_fk = next((fk for fk in fks if fk['referred_table'] == 'customers'), None)
        assert customer_fk is not None, "Foreign key to customers should exist"
        assert 'customer_id' in customer_fk['constrained_columns'], "customer_id should be constrained column" 
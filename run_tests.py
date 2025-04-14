import os
import sys
import pytest

def initialize_sqlalchemy():
    """Initialize SQLAlchemy ORM models before testing."""
    print("Initializing SQLAlchemy models...")
    # Import models to ensure they are properly registered
    from infrastructure.persistence.sqlite.database import Base
    from infrastructure.persistence.sqlite.models_mapping import (
        UserOrm, DepartmentOrm, ProductOrm, InventoryMovementOrm, 
        SaleOrm, SaleItemOrm, CustomerOrm, CreditPaymentOrm,
        SupplierOrm, PurchaseOrderOrm, PurchaseOrderItemOrm,
        InvoiceOrm, CashDrawerEntryOrm, ensure_all_models_mapped
    )
    # Make sure all models are properly mapped
    ensure_all_models_mapped()
    print("SQLAlchemy initialization complete.")

if __name__ == "__main__":
    # Add the current directory to the Python path
    sys.path.insert(0, os.path.abspath('.'))
    
    # Initialize SQLAlchemy before running tests
    initialize_sqlalchemy()
    
    # Run the tests
    pytest.main()
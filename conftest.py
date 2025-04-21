import os
import pytest
import platform # Import platform module
from PySide6.QtWidgets import QApplication # Needed for type hinting if desired, but not strictly required for the fixture

# Import compiled resources early
try:
    import ui.resources.resources
except ImportError:
    print("Warning: Could not import Qt resources (ui.resources.resources). Icons might be missing.")

# Set platform plugin based on OS
# if platform.system() == "Windows":
#     os.environ.setdefault('QT_QPA_PLATFORM', 'minimal')
# else:
#     os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
# Force 'offscreen' for all platforms during testing to avoid GUI issues
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

# Define the session-scoped qapp fixture provided by pytest-qt
# This ensures a single QApplication instance for the entire test session.
# @pytest.fixture(scope='session')
# def qapp(qapp_args):
#     """Session-scoped QApplication instance."""
#     # The actual implementation is handled by pytest-qt
#     # We just need to define it to make it available session-wide.
#     # You might customize qapp_args if needed, but defaults are usually fine.
#     app = QApplication.instance()
#     if app is None:
#         app = QApplication(qapp_args or [])
#     return app


@pytest.fixture(scope="session", autouse=True)
def initialize_sqlalchemy_session():
    """Initialize SQLAlchemy ORM models once per test session."""
    print("Initializing SQLAlchemy models for test session...")
    try:
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
    except ImportError as e:
        print(f"Error during SQLAlchemy initialization: {e}")
        pytest.fail(f"Failed to initialize SQLAlchemy: {e}", pytrace=False)
    except Exception as e:
        print(f"Unexpected error during SQLAlchemy initialization: {e}")
        pytest.fail(f"Unexpected error during SQLAlchemy initialization: {e}", pytrace=False)

def pytest_configure(config):
    """
    Configure pytest session.

    Force offscreen Qt platform to avoid GUI-related crashes on headless environments.
    """

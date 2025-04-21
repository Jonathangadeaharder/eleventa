"""
Repository mocking utilities for tests.

This module provides standardized patterns for mocking repositories
to ensure consistency across tests.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional, Any, Type, Callable

# Import repository interfaces
from core.interfaces.repository_interfaces import (
    IProductRepository, IDepartmentRepository,
    ICustomerRepository, ISaleRepository, 
    IInventoryRepository, ICreditPaymentRepository,
    ISupplierRepository, IPurchaseOrderRepository,
    IUserRepository, IInvoiceRepository,
    ICashDrawerRepository
)

# Helper functions for creating mock repositories
def mock_repository(repo_interface: Type, custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """
    Create a mock repository with standard method behavior.
    
    Args:
        repo_interface: The repository interface to mock
        custom_methods: Dict of method names and their custom implementations
        
    Returns:
        A configured MagicMock object that follows repository patterns
    """
    mock_repo = MagicMock(spec=repo_interface)
    
    # Default behavior for common repository methods
    entities_dict = {}
    next_id = 1
    
    def mock_add(entity):
        nonlocal next_id
        # Set ID if not already set
        if not hasattr(entity, 'id') or entity.id is None:
            entity.id = next_id
            next_id += 1
        # Store entity
        entities_dict[entity.id] = entity
        return entity
    
    def mock_get_by_id(id):
        return entities_dict.get(id)
    
    def mock_get_all():
        return list(entities_dict.values())
    
    def mock_update(entity):
        if entity.id in entities_dict:
            entities_dict[entity.id] = entity
            return entity
        return None
    
    def mock_delete(id):
        if id in entities_dict:
            del entities_dict[id]
            return True
        return False
    
    # Set up standard methods
    mock_repo.add.side_effect = mock_add
    mock_repo.get_by_id.side_effect = mock_get_by_id
    mock_repo.get_all.side_effect = mock_get_all
    mock_repo.update.side_effect = mock_update
    mock_repo.delete.side_effect = mock_delete
    
    # Add any custom method implementations
    if custom_methods:
        for method_name, method_impl in custom_methods.items():
            setattr(mock_repo, method_name, MagicMock(side_effect=method_impl))
    
    return mock_repo

# Factory functions for specific repository types
def mock_product_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock product repository with standard behavior."""
    return mock_repository(IProductRepository, custom_methods)

def mock_department_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock department repository with standard behavior."""
    return mock_repository(IDepartmentRepository, custom_methods)

def mock_customer_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock customer repository with standard behavior."""
    return mock_repository(ICustomerRepository, custom_methods)

def mock_sale_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock sale repository with standard behavior."""
    return mock_repository(ISaleRepository, custom_methods)

def mock_inventory_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock inventory repository with standard behavior."""
    return mock_repository(IInventoryRepository, custom_methods)

def mock_invoice_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock invoice repository with standard behavior."""
    return mock_repository(IInvoiceRepository, custom_methods)

def mock_user_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock user repository with standard behavior."""
    return mock_repository(IUserRepository, custom_methods)

def mock_supplier_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock supplier repository with standard behavior."""
    return mock_repository(ISupplierRepository, custom_methods)

def mock_purchase_order_repository(custom_methods: Dict[str, Callable] = None) -> MagicMock:
    """Create a mock purchase order repository with standard behavior."""
    return mock_repository(IPurchaseOrderRepository, custom_methods)

# Pytest fixtures for commonly used mock repositories
@pytest.fixture
def mock_product_repo():
    """Fixture that provides a mock product repository."""
    return mock_product_repository()

@pytest.fixture
def mock_department_repo():
    """Fixture that provides a mock department repository."""
    return mock_department_repository()

@pytest.fixture
def mock_customer_repo():
    """Fixture that provides a mock customer repository."""
    return mock_customer_repository()

@pytest.fixture
def mock_sale_repo():
    """Fixture that provides a mock sale repository."""
    return mock_sale_repository()

@pytest.fixture
def mock_inventory_repo():
    """Fixture that provides a mock inventory repository."""
    return mock_inventory_repository()

@pytest.fixture
def mock_invoice_repo():
    """Fixture that provides a mock invoice repository."""
    return mock_invoice_repository()

@pytest.fixture
def mock_user_repo():
    """Fixture that provides a mock user repository."""
    return mock_user_repository()

@pytest.fixture
def mock_supplier_repo():
    """Fixture that provides a mock supplier repository."""
    return mock_supplier_repository()

@pytest.fixture
def mock_purchase_order_repo():
    """Fixture that provides a mock purchase order repository."""
    return mock_purchase_order_repository()

# Helper patch functions to use with pytest.fixture
def patch_repository(target_path: str, repo_interface: Type, custom_methods: Dict[str, Callable] = None):
    """
    Create a patch for a repository.
    
    Args:
        target_path: The import path to patch
        repo_interface: The repository interface to mock
        custom_methods: Dict of method names and their implementations
        
    Returns:
        A patch context manager
    """
    mock_repo = mock_repository(repo_interface, custom_methods)
    return patch(target_path, return_value=mock_repo)

# Examples of patching specific repositories
def patch_product_repository(target_path: str, custom_methods: Dict[str, Callable] = None):
    """Patch a product repository at the specified path."""
    return patch_repository(target_path, IProductRepository, custom_methods)

def patch_sale_repository(target_path: str, custom_methods: Dict[str, Callable] = None):
    """Patch a sale repository at the specified path."""
    return patch_repository(target_path, ISaleRepository, custom_methods) 
import pytest
from unittest.mock import MagicMock
from contextlib import contextmanager

from core.services.product_service import ProductService
from core.models.product import Department
from core.interfaces.repository_interfaces import IDepartmentRepository, IProductRepository

# Patch session_scope to return a mock session
@pytest.fixture(autouse=True)
def patch_session_scope(monkeypatch):
    mock_session = MagicMock()
    
    @contextmanager
    def mock_session_scope():
        yield mock_session
        
    monkeypatch.setattr('core.services.product_service.session_scope', mock_session_scope)
    return mock_session

@pytest.fixture
def prod_repo():
    return MagicMock(spec=IProductRepository)

@pytest.fixture
def dept_repo():
    return MagicMock(spec=IDepartmentRepository)

@pytest.fixture
def svc(prod_repo, dept_repo):
    # Create factory functions that return the mock repositories
    def product_repo_factory(session):
        return prod_repo
        
    def department_repo_factory(session):
        return dept_repo
        
    # Pass the factory functions to the service
    return ProductService(
        product_repo_factory=product_repo_factory,
        department_repo_factory=department_repo_factory
    )

# Tests for department operations

def test_add_department_success(svc, dept_repo):
    dept = Department(name="Dept1")
    dept_repo.get_by_name.return_value = None
    dept_repo.add.return_value = Department(id=1, name="Dept1")

    result = svc.add_department(dept)

    dept_repo.get_by_name.assert_called_once_with("Dept1")
    dept_repo.add.assert_called_once_with(dept)
    assert result.id == 1


def test_add_department_duplicate_name(svc, dept_repo):
    dept = Department(name="Exist")
    existing = Department(id=2, name="Exist")
    dept_repo.get_by_name.return_value = existing

    with pytest.raises(ValueError, match="Departamento 'Exist' ya existe"):
        svc.add_department(dept)
    dept_repo.add.assert_not_called()


def test_get_all_departments(svc, dept_repo):
    dept1 = Department(id=1, name="A")
    dept2 = Department(id=2, name="B")
    dept_repo.get_all.return_value = [dept1, dept2]

    result = svc.get_all_departments()

    dept_repo.get_all.assert_called_once()
    assert result == [dept1, dept2]


def test_delete_department_nonexistent(svc, dept_repo):
    dept_repo.get_by_id.return_value = None
    # Should not raise
    svc.delete_department(99)
    dept_repo.get_by_id.assert_called_once_with(99)


def test_delete_department_in_use_fails(svc, prod_repo, dept_repo):
    dept = Department(id=3, name="C")
    dept_repo.get_by_id.return_value = dept
    prod_repo.get_by_department_id.return_value = [MagicMock()]

    with pytest.raises(ValueError, match=r"no puede ser eliminado.*producto"):
        svc.delete_department(3)
    dept_repo.delete.assert_not_called()


def test_delete_department_success(svc, prod_repo, dept_repo):
    dept = Department(id=4, name="D")
    dept_repo.get_by_id.return_value = dept
    prod_repo.get_by_department_id.return_value = []

    svc.delete_department(4)
    dept_repo.delete.assert_called_once_with(4)


def test_update_department_missing_id(svc):
    dept = Department(name="X")
    with pytest.raises(ValueError, match="Department ID must be provided for update."):
        svc.update_department(dept)


def test_update_department_not_found(svc, dept_repo):
    dept = Department(id=5, name="Y")
    dept_repo.get_by_id.return_value = None
    with pytest.raises(ValueError, match="Departamento con ID 5 no encontrado"):
        svc.update_department(dept)


def test_update_department_validation_fails(svc, dept_repo):
    # name conflict with different ID
    dept = Department(id=6, name="Z")
    existing = Department(id=7, name="Z")
    dept_repo.get_by_id.return_value = existing
    dept_repo.get_by_name.return_value = existing

    with pytest.raises(ValueError, match="Departamento 'Z' ya existe"):
        svc.update_department(dept)


def test_update_department_success(svc, dept_repo):
    orig = Department(id=8, name="Old")
    updated = Department(id=8, name="New")
    dept_repo.get_by_id.return_value = orig
    dept_repo.get_by_name.return_value = None
    dept_repo.update.return_value = updated

    result = svc.update_department(updated)

    dept_repo.get_by_id.assert_called_once_with(8)
    dept_repo.get_by_name.assert_called_once_with("New")
    dept_repo.update.assert_called_once_with(updated)
    assert result.name == "New"

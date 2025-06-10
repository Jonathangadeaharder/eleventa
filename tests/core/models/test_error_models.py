# tests/core/models/test_error_models.py
"""
Tests for error models (RFC 7807 Problem Details).
"""
import pytest
from typing import Optional

from core.models.error_models import ProblemDetail


class TestProblemDetail:
    """Tests for ProblemDetail model."""
    
    def test_default_values(self):
        """Test ProblemDetail with default values."""
        problem = ProblemDetail()
        
        assert problem.type == "about:blank"
        assert problem.title is None
        assert problem.status is None
        assert problem.detail is None
        assert problem.instance is None
    
    def test_basic_problem_detail(self):
        """Test ProblemDetail with basic fields."""
        problem = ProblemDetail(
            type="https://example.com/probs/validation-error",
            title="Validation Error",
            status=400,
            detail="The request body contains invalid data",
            instance="/api/products/123"
        )
        
        assert problem.type == "https://example.com/probs/validation-error"
        assert problem.title == "Validation Error"
        assert problem.status == 400
        assert problem.detail == "The request body contains invalid data"
        assert problem.instance == "/api/products/123"
    
    def test_validation_error_problem(self):
        """Test ProblemDetail for validation errors."""
        problem = ProblemDetail(
            type="https://eleventa.com/problems/validation-error",
            title="Validation Failed",
            status=422,
            detail="One or more fields contain invalid values",
            instance="/api/customers"
        )
        
        assert problem.type == "https://eleventa.com/problems/validation-error"
        assert problem.title == "Validation Failed"
        assert problem.status == 422
        assert problem.detail == "One or more fields contain invalid values"
        assert problem.instance == "/api/customers"
    
    def test_not_found_problem(self):
        """Test ProblemDetail for resource not found errors."""
        problem = ProblemDetail(
            type="https://eleventa.com/problems/not-found",
            title="Resource Not Found",
            status=404,
            detail="The requested product does not exist",
            instance="/api/products/999"
        )
        
        assert problem.type == "https://eleventa.com/problems/not-found"
        assert problem.title == "Resource Not Found"
        assert problem.status == 404
        assert problem.detail == "The requested product does not exist"
        assert problem.instance == "/api/products/999"
    
    def test_business_logic_problem(self):
        """Test ProblemDetail for business logic errors."""
        problem = ProblemDetail(
            type="https://eleventa.com/problems/insufficient-stock",
            title="Insufficient Stock",
            status=409,
            detail="Cannot complete sale: insufficient stock for product P001",
            instance="/api/sales"
        )
        
        assert problem.type == "https://eleventa.com/problems/insufficient-stock"
        assert problem.title == "Insufficient Stock"
        assert problem.status == 409
        assert problem.detail == "Cannot complete sale: insufficient stock for product P001"
        assert problem.instance == "/api/sales"
    
    def test_server_error_problem(self):
        """Test ProblemDetail for server errors."""
        problem = ProblemDetail(
            type="https://eleventa.com/problems/database-error",
            title="Database Connection Failed",
            status=500,
            detail="Unable to connect to the database server",
            instance="/api/products"
        )
        
        assert problem.type == "https://eleventa.com/problems/database-error"
        assert problem.title == "Database Connection Failed"
        assert problem.status == 500
        assert problem.detail == "Unable to connect to the database server"
        assert problem.instance == "/api/products"
    
    def test_partial_problem_detail(self):
        """Test ProblemDetail with only some fields set."""
        problem = ProblemDetail(
            title="Bad Request",
            status=400
        )
        
        assert problem.type == "about:blank"  # Default value
        assert problem.title == "Bad Request"
        assert problem.status == 400
        assert problem.detail is None
        assert problem.instance is None
    
    def test_model_serialization(self):
        """Test ProblemDetail model serialization."""
        problem = ProblemDetail(
            type="https://example.com/problems/test",
            title="Test Problem",
            status=400,
            detail="This is a test problem",
            instance="/test"
        )
        
        # Test model_dump (Pydantic v2)
        data = problem.model_dump()
        expected = {
            "type": "https://example.com/problems/test",
            "title": "Test Problem",
            "status": 400,
            "detail": "This is a test problem",
            "instance": "/test"
        }
        assert data == expected
    
    def test_model_serialization_exclude_none(self):
        """Test ProblemDetail serialization excluding None values."""
        problem = ProblemDetail(
            title="Test Problem",
            status=400
        )
        
        # Test model_dump excluding None values
        data = problem.model_dump(exclude_none=True)
        expected = {
            "type": "about:blank",
            "title": "Test Problem",
            "status": 400
        }
        assert data == expected
    
    def test_model_creation_from_dict(self):
        """Test creating ProblemDetail from dictionary."""
        data = {
            "type": "https://example.com/problems/test",
            "title": "Test Problem",
            "status": 422,
            "detail": "Validation failed",
            "instance": "/api/test"
        }
        
        problem = ProblemDetail(**data)
        
        assert problem.type == data["type"]
        assert problem.title == data["title"]
        assert problem.status == data["status"]
        assert problem.detail == data["detail"]
        assert problem.instance == data["instance"]
    
    def test_model_validation(self):
        """Test ProblemDetail field validation."""
        # Test with valid status code
        problem = ProblemDetail(status=200)
        assert problem.status == 200
        
        # Test with valid URI
        problem = ProblemDetail(type="https://example.com/problems/test")
        assert problem.type == "https://example.com/problems/test"
        
        # Test with relative URI
        problem = ProblemDetail(instance="/api/test")
        assert problem.instance == "/api/test"
    
    def test_model_equality(self):
        """Test ProblemDetail equality comparison."""
        problem1 = ProblemDetail(
            type="https://example.com/problems/test",
            title="Test Problem",
            status=400
        )
        
        problem2 = ProblemDetail(
            type="https://example.com/problems/test",
            title="Test Problem",
            status=400
        )
        
        problem3 = ProblemDetail(
            type="https://example.com/problems/different",
            title="Different Problem",
            status=500
        )
        
        assert problem1 == problem2
        assert problem1 != problem3
    
    def test_model_repr(self):
        """Test ProblemDetail string representation."""
        problem = ProblemDetail(
            type="https://example.com/problems/test",
            title="Test Problem",
            status=400
        )
        
        repr_str = repr(problem)
        assert "ProblemDetail" in repr_str
        assert "type='https://example.com/problems/test'" in repr_str
        assert "title='Test Problem'" in repr_str
        assert "status=400" in repr_str
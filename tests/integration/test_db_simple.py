"""
Simple database integration tests.

These tests verify that our database setup for tests is working correctly.
"""
import pytest
from sqlalchemy import text


@pytest.mark.integration
def test_db_import():
    """Test that the database modules can be imported."""
    from infrastructure.persistence.sqlite.database import SessionLocal, engine, Base
    assert SessionLocal is not None
    assert engine is not None
    assert Base is not None


@pytest.mark.integration
def test_simple_db_session(clean_db):
    """Test that we can get a clean database session."""
    assert clean_db is not None, "Clean database session should be available"
    
    # Try a simple operation using proper SQLAlchemy text() function
    result = clean_db.execute(text("SELECT 1")).scalar()
    assert result == 1, "Basic SQL query should work" 
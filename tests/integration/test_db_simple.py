"""
Simple database integration tests.

These tests verify that our database setup for tests is working correctly.
"""
import pytest
from sqlalchemy import text
from infrastructure.persistence.sqlite.database import Base
from infrastructure.persistence.sqlite.models_mapping import ensure_all_models_mapped


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
    # clean_db returns (session, user) tuple
    session, user = clean_db
    
    assert session is not None, "Clean database session should be available"
    
    # Try a simple operation using proper SQLAlchemy text() function
    # that doesn't rely on any particular table existing
    result = session.execute(text("SELECT 1")).scalar()
    assert result == 1, "Basic SQL query should work"
    
    # Verify user was created correctly
    assert user.username.startswith("clean_db_testuser_"), "Test user should have correct username prefix"
    
    # Verify we can query the user from the database directly
    result = session.execute(
        text("SELECT username FROM users WHERE id = :user_id"),
        {"user_id": user.id}
    ).scalar()
    assert result == user.username, "User should be queryable from the database"
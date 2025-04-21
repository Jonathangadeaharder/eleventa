"""
Pytest configuration for all tests.

This module provides fixtures for database sessions and other common test requirements.
"""
import pytest
import sqlalchemy
from sqlalchemy import delete, inspect, MetaData, Column, Integer, String, Boolean, ForeignKey, Float, DateTime, Numeric, Text
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session, registry, relationship
import sys
import os
import importlib
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# Ensure the project root is in the sys.path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import database components in correct order to handle circular imports
from infrastructure.persistence.sqlite.database import Base, SessionLocal, engine as app_engine, create_all_tables

# Import mappings AFTER Base is defined
import infrastructure.persistence.sqlite.models_mapping
from infrastructure.persistence.sqlite.models_mapping import ensure_all_models_mapped

# Use a completely in-memory database for tests
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    """Create and return a SQLAlchemy engine for testing."""
    print(f"\n=== Creating test engine with URL: {TEST_DB_URL} ===")
    engine = create_engine(
        TEST_DB_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    yield engine
    
    print("\n=== Disposing test engine ===")
    engine.dispose()

@pytest.fixture(scope="session")
def test_db_session_factory(test_engine):
    """Create a session factory for testing."""
    print("\n=== Creating test db session factory ===")
    factory = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    yield factory

@pytest.fixture(scope="session", autouse=True)
def setup_test_database(test_engine):
    """Create all tables in the test database ONCE per session."""
    print("\n=== Fixture 'setup_test_database' starting... ===")
    try:
        # Ensure mappings are loaded before creating tables
        ensure_all_models_mapped()
        print(f"Attempting to create tables on engine: {test_engine.url}")
        # Use the helper function from database.py
        create_all_tables(test_engine)
        print("Test database tables created successfully.")
    except Exception as e:
        pytest.fail(f"Failed to create test database tables: {e}")

    yield # Let tests run

    print("\n=== Fixture 'setup_test_database' tearing down (dropping tables)... ===")
    try:
        # Base.metadata.drop_all(test_engine) # Commented out to test hang
        # print("Test database tables dropped.")
        print("Skipping drop_all during teardown for testing hang.")
    except Exception as e:
        print(f"Warning: Error dropping test tables: {e}")

@pytest.fixture(scope="function")
def test_db_session(test_db_session_factory, setup_test_database): # Depend on setup
    """
    Create a session for each test function.
    Handles transaction rollback automatically.
    """
    session = test_db_session_factory()
    print(f"\n--- Test session {id(session)} started ---")
    try:
        yield session
    finally:
        session.rollback() # Rollback any uncommitted changes after test
        session.close()
        print(f"--- Test session {id(session)} closed ---")

@pytest.fixture(scope="function")
def clean_db(test_db_session):
    """Provides a session and ensures tables are empty before the test."""
    session = test_db_session # Get session from the existing fixture
    print("--- Cleaning DB tables for test ---")
    # Delete data from tables in reverse order of dependencies
    # Use Base.metadata.sorted_tables for correct order
    for table in reversed(Base.metadata.sorted_tables):
        try:
            session.execute(table.delete())
        except Exception as e:
            print(f"Warning: Could not delete from table {table.name}: {e}")
    try:
        session.commit() # Commit the deletions
    except Exception as e:
        print(f"Warning: Could not commit cleanup transaction: {e}")
        session.rollback()
    print("--- DB tables cleaned ---")
    yield session # Provide the clean session to the test
    # Rollback/close handled by test_db_session fixture's teardown

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

# Import the application's Base and metadata FIRST
from infrastructure.persistence.sqlite.database import Base, SessionLocal

# Import mappings AFTER Base is imported
import infrastructure.persistence.sqlite.models_mapping

# Explicitly ensure all models are properly mapped
from infrastructure.persistence.sqlite.models_mapping import ensure_all_models_mapped
ensure_all_models_mapped()

# Use a completely in-memory database for tests
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine():
    """Create and return a SQLAlchemy engine for testing."""
    engine = create_engine(
        TEST_DB_URL,
        echo=False,
        # Required for SQLite in-memory DBs with multiple threads/connections
        connect_args={"check_same_thread": False}
    )
    
    # Print engine info for debugging
    print(f"Created test engine with URL: {TEST_DB_URL}")
    
    yield engine
    
    # Clean up at the end of the session using application metadata
    print("Dropping all tables from Base.metadata")
    Base.metadata.drop_all(engine)
    engine.dispose() # Dispose of the engine connections

@pytest.fixture(scope="session")
def test_db_session_factory(test_engine):
    """Create a session factory for testing."""
    # Set up the session with the test engine
    factory = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    # Register the factory with the session_scope_provider if needed
    # session_scope_provider.set_default_session_factory(factory)
    yield factory

@pytest.fixture(scope="session")
def create_tables(test_engine):
    """Create all tables in the test database using application metadata."""
    # Make sure all models are mapped before creating tables
    ensure_all_models_mapped()
    
    # Verify existing tables before creation
    inspector = inspect(test_engine)
    existing_tables = inspector.get_table_names()
    print(f"Existing tables before creation: {existing_tables}")
    
    # Create all tables from the application metadata
    print("Creating all tables from Base.metadata")
    Base.metadata.create_all(bind=test_engine)
    
    # Verify that tables were created
    inspector = inspect(test_engine)
    created_tables = inspector.get_table_names()
    print(f"Created tables for testing: {created_tables}")
    
    yield

@pytest.fixture(scope="function")
def test_db_session(test_db_session_factory, create_tables):
    """
    Create a session for each test. Session will be rolled back at end of test.
    Depends on create_tables to ensure the schema exists.
    """
    # Open a new session
    session = test_db_session_factory()
    
    try:
        yield session
    finally:
        # Rollback any changes and close the session
        session.rollback() # Ensure clean state
        session.close()

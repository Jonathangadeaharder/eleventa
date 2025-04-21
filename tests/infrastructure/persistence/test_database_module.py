import pytest
from sqlalchemy import inspect, create_engine

import infrastructure.persistence.sqlite.database as db_module
from infrastructure.persistence.sqlite.database import (
    import_mappings,
    ensure_all_models_mapped,
    create_all_tables,
)
from infrastructure.persistence.sqlite.database import Base

@pytest.fixture(scope="module")
def temp_engine():
    # Use in-memory engine for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    yield engine
    engine.dispose()


def test_import_mappings_returns_models_module():
    # import_mappings should return the models_mapping module
    mod = import_mappings()
    import infrastructure.persistence.sqlite.models_mapping as mm
    assert mod is mm


def test_ensure_all_models_mapped():
    # Should return True and register tables in metadata
    result = ensure_all_models_mapped()
    assert result is True
    # Check that metadata has at least some expected tables
    tables = Base.metadata.tables.keys()
    assert 'departments' in tables
    assert 'products' in tables
    assert 'customers' in tables


def test_create_all_tables_creates_model_tables(temp_engine):
    # Drop any pre-existing tables
    Base.metadata.drop_all(bind=temp_engine)
    # Create tables in the temp_engine
    create_all_tables(temp_engine)
    # Inspect tables in the database
    inspector = inspect(temp_engine)
    db_tables = inspector.get_table_names()
    # Expect the Base metadata table names to appear
    expected = set(Base.metadata.tables.keys())
    assert expected.issubset(set(db_tables)), f"Missing tables: {expected - set(db_tables)}"


def test_init_db_calls_create_all(monkeypatch):
    calls = []

    # Monkeypatch ensure_all_models_mapped and create_all
    monkeypatch.setattr(db_module, 'ensure_all_models_mapped', lambda: calls.append('mapped') or True)
    monkeypatch.setattr(db_module.Base.metadata, 'create_all', lambda bind: calls.append('created'))

    # Call init_db and verify calls
    db_module.init_db()
    assert calls == ['mapped', 'created']

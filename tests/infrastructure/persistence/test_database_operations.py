import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from infrastructure.persistence.sqlite.database_operations import Database

@pytest.fixture
def mock_sqlite_connection():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


@patch('sqlite3.connect')
def test_database_initialization(mock_connect, mock_sqlite_connection):
    # Arrange
    conn, cursor = mock_sqlite_connection
    mock_connect.return_value = conn
    test_db_path = "test.db"
    
    # Act
    db = Database(test_db_path)
    
    # Assert
    mock_connect.assert_called_once_with(test_db_path)
    assert db.connection == conn


@patch('sqlite3.connect')
def test_execute_query(mock_connect, mock_sqlite_connection):
    # Arrange
    conn, cursor = mock_sqlite_connection
    mock_connect.return_value = conn
    db = Database("test.db")
    
    test_query = "SELECT * FROM test_table WHERE id = ?"
    test_params = (1,)
    
    # Act
    db.execute_query(test_query, test_params)
    
    # Assert
    cursor.execute.assert_called_once_with(test_query, test_params)
    conn.commit.assert_called_once()


@patch('sqlite3.connect')
def test_execute_query_exception(mock_connect, mock_sqlite_connection):
    # Arrange
    conn, cursor = mock_sqlite_connection
    mock_connect.return_value = conn
    cursor.execute.side_effect = sqlite3.Error("Test error")
    db = Database("test.db")
    
    # Act & Assert
    with pytest.raises(sqlite3.Error):
        db.execute_query("SELECT * FROM test_table", ())


@patch('sqlite3.connect')
def test_execute_query_with_return(mock_connect, mock_sqlite_connection):
    # Arrange
    conn, cursor = mock_sqlite_connection
    mock_connect.return_value = conn
    cursor.fetchall.return_value = [(1, "Test")]
    db = Database("test.db")
    
    # Act
    result = db.execute_query_with_return("SELECT * FROM test_table")
    
    # Assert
    assert result == [(1, "Test")]
    cursor.execute.assert_called_once()
    cursor.fetchall.assert_called_once()


@patch('sqlite3.connect')
def test_execute_many(mock_connect, mock_sqlite_connection):
    # Arrange
    conn, cursor = mock_sqlite_connection
    mock_connect.return_value = conn
    db = Database("test.db")
    
    test_query = "INSERT INTO test_table (id, name) VALUES (?, ?)"
    test_params = [(1, "Test1"), (2, "Test2")]
    
    # Act
    db.execute_many(test_query, test_params)
    
    # Assert
    cursor.executemany.assert_called_once_with(test_query, test_params)
    conn.commit.assert_called_once()


@patch('sqlite3.connect')
def test_get_last_row_id(mock_connect, mock_sqlite_connection):
    # Arrange
    conn, cursor = mock_sqlite_connection
    mock_connect.return_value = conn
    cursor.lastrowid = 42
    db = Database("test.db")
    
    # Act
    last_id = db.get_last_row_id()
    
    # Assert
    assert last_id == 42


@patch('sqlite3.connect')
def test_close_connection(mock_connect, mock_sqlite_connection):
    # Arrange
    conn, cursor = mock_sqlite_connection
    mock_connect.return_value = conn
    db = Database("test.db")
    
    # Act
    db.close_connection()
    
    # Assert
    conn.close.assert_called_once()


@patch('sqlite3.connect')
def test_transaction_operations(mock_connect, mock_sqlite_connection):
    # Arrange
    conn, cursor = mock_sqlite_connection
    mock_connect.return_value = conn
    db = Database("test.db")
    
    # Act - Begin transaction
    db.begin_transaction()
    
    # Assert
    assert db.in_transaction is True
    
    # Act - Commit transaction
    db.commit_transaction()
    
    # Assert
    assert db.in_transaction is False
    conn.commit.assert_called_once()
    
    # Reset mock
    conn.reset_mock()
    
    # Act - Rollback transaction
    db.begin_transaction()
    db.rollback_transaction()
    
    # Assert
    assert db.in_transaction is False
    conn.rollback.assert_called_once()


@patch('sqlalchemy.create_engine')
def test_create_engine_with_correct_url(mock_create_engine):
    """Test that the engine is created with the correct URL and arguments during module import."""
    # Arrange: Mock the DATABASE_URL
    test_url = "sqlite:///test_from_config.db"
    
    # We need to patch at the config module level, before database module imports it
    with patch('config.DATABASE_URL', test_url):
        # Clear any module that might be in sys.modules already
        import sys
        if 'infrastructure.persistence.sqlite.database' in sys.modules:
            del sys.modules['infrastructure.persistence.sqlite.database']
        
        # Now import the module, which triggers the create_engine call
        import infrastructure.persistence.sqlite.database as db_module

    # Assert: Verify that create_engine was called with the test URL
    mock_create_engine.assert_called()
    
    # Get the first positional argument (URL)
    args, kwargs = mock_create_engine.call_args
    
    # The test URL should be passed to create_engine
    assert args[0] == test_url
    
    # Check the keyword arguments
    assert "connect_args" in kwargs
    assert "check_same_thread" in kwargs["connect_args"]
    assert kwargs["connect_args"]["check_same_thread"] is False


@patch('sqlalchemy.create_engine')
@patch('sqlalchemy.orm.sessionmaker')
def test_session_creation(mock_sessionmaker, mock_create_engine):
    """Test that sessionmaker is configured correctly."""
    # Setup mocks
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    
    # Clear the module if it's already loaded
    import sys
    if 'infrastructure.persistence.sqlite.database' in sys.modules:
        del sys.modules['infrastructure.persistence.sqlite.database']
    
    # Import inside the test - this should trigger the sessionmaker call
    import infrastructure.persistence.sqlite.database as db_module
    
    # Verify sessionmaker configuration
    mock_sessionmaker.assert_called_with(
        autoflush=False, 
        bind=mock_engine
    )


@patch('sqlalchemy.create_engine')
@patch('infrastructure.persistence.utils.session_scope_provider.set_default_session_factory')
def test_session_scope_provider_setup(mock_set_default_factory, mock_create_engine):
    """Test that the session scope provider is configured correctly."""
    # Setup
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    
    # Clear the module if it's already loaded
    import sys
    if 'infrastructure.persistence.sqlite.database' in sys.modules:
        del sys.modules['infrastructure.persistence.sqlite.database']
    
    # Import inside the test - this should trigger the provider configuration
    import infrastructure.persistence.sqlite.database as db_module
    
    # Verify the provider was configured
    mock_set_default_factory.assert_called()


@patch('infrastructure.persistence.sqlite.database.ensure_all_models_mapped')
@patch('infrastructure.persistence.sqlite.table_deps.register_table_creation_events')
@patch('infrastructure.persistence.sqlite.database.Base.metadata.create_all')
def test_init_db(mock_create_all, mock_register_events, mock_ensure_mapped):
    """Test that init_db calls mapping, event registration, and table creation."""
    # Setup
    # No need to mock Base or metadata directly anymore
    mock_ensure_mapped.return_value = True 

    # Import inside the test
    from infrastructure.persistence.sqlite.database import init_db, engine # Need engine
    
    # Call the function
    init_db()
    
    # Verify behavior
    mock_ensure_mapped.assert_called_once()
    mock_register_events.assert_called_once() # Check event registration was called
    # Check create_all was called on the (real) metadata, bound to the engine
    mock_create_all.assert_called_once_with(bind=engine) 


@patch('infrastructure.persistence.sqlite.database.import_mappings')
def test_ensure_all_models_mapped(mock_import_mappings):
    """Test the ensure_all_models_mapped function."""
    # Setup
    mock_mappings = MagicMock()
    mock_mappings.ensure_all_models_mapped.return_value = True
    mock_import_mappings.return_value = mock_mappings
    
    # Import inside the test
    from infrastructure.persistence.sqlite.database import ensure_all_models_mapped
    
    # Call the function
    result = ensure_all_models_mapped()
    
    # Verify behavior
    mock_import_mappings.assert_called_once()
    mock_mappings.ensure_all_models_mapped.assert_called_once()
    assert result is True
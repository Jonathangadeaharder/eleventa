import os
import sys
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
import sqlalchemy.pool

# Import SessionScopeProvider
from infrastructure.persistence.utils import session_scope_provider

# Assuming config.py is in the root and the application runs from the root
# If running scripts directly from subdirs, path adjustments might be needed.
try:
    from config import DATABASE_URL
except ImportError:
    # Fallback for potential path issues during development/testing setup
    import sys
    import os
    # Add project root to path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from config import DATABASE_URL

# Create a declarative base directly
Base = declarative_base()

# Determine if we're using an in-memory database (typically for testing)
is_memory_db = ':memory:' in DATABASE_URL or 'mode=memory' in DATABASE_URL

# Use check_same_thread=False only for SQLite!
# It allows the connection to be shared across threads, which is fine for this
# simple setup but might require careful handling in complex multithreaded apps.
# For production with other DBs, you wouldn't need this.
engine_args = {}
if 'sqlite' in DATABASE_URL:
    engine_args["connect_args"] = {"check_same_thread": False}
    
    # For in-memory SQLite, set pooling behavior to maintain the same connection
    if is_memory_db:
        engine_args["poolclass"] = sqlalchemy.pool.StaticPool

engine = create_engine(DATABASE_URL, **engine_args)

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Register the SessionLocal with the session_scope_provider as the default factory
session_scope_provider.set_default_session_factory(SessionLocal)

# Import mappings AFTER Base is defined and AFTER engine/session creation
# This helps avoid circular imports
def import_mappings():
    """Import model mappings at runtime to avoid circular imports."""
    # Only import when needed to break circular dependencies
    import infrastructure.persistence.sqlite.models_mapping
    return infrastructure.persistence.sqlite.models_mapping

def ensure_all_models_mapped():
    """Wrapper to call ensure_all_models_mapped from models_mapping."""
    mappings = import_mappings()
    # Ensure the function exists in the imported module
    if hasattr(mappings, 'ensure_all_models_mapped'):
         return mappings.ensure_all_models_mapped()
    else:
         print("Warning: ensure_all_models_mapped function not found in models_mapping.")
         # Attempt to load models implicitly by importing
         import infrastructure.persistence.sqlite.models_mapping
         return True # Assume success if import works

def init_db():
    """Initializes the database by creating tables based on ORM models."""
    # First ensure all models are properly mapped by virtue of being imported
    # and inheriting from Base before this point.
    ensure_all_models_mapped() # Keep the verification step
    
    # Register table creation event hooks to control table order
    from infrastructure.persistence.sqlite.table_deps import register_table_creation_events
    register_table_creation_events(Base.metadata)

    # Create tables using SQLAlchemy metadata
    print(f"Creating/updating database tables defined in Base metadata ({len(Base.metadata.tables)} tables)...")
    try:
        Base.metadata.create_all(bind=engine) # Use create_all directly
        print("Database tables checked/created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise # Re-raise the exception

def create_all_tables(engine_instance):
    """Helper function to ensure all models are loaded before creating tables."""
    ensure_all_models_mapped()
    
    # Register table creation event hooks
    from infrastructure.persistence.sqlite.table_deps import register_table_creation_events
    register_table_creation_events(Base.metadata)
    
    registered_tables = list(Base.metadata.tables.keys())
    print(f"Creating all database tables with {len(registered_tables)} tables registered: {registered_tables}") # Log registered table names
    Base.metadata.create_all(bind=engine_instance)
    print("Database tables created successfully.")
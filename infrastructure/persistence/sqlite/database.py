import os
import sys
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

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

# Import mappings AFTER Base is defined but BEFORE engine/session creation
import infrastructure.persistence.sqlite.models_mapping

# Force model mapping to happen before engine creation
from infrastructure.persistence.sqlite.models_mapping import ensure_all_models_mapped
ensure_all_models_mapped()

# Use check_same_thread=False only for SQLite!
# It allows the connection to be shared across threads, which is fine for this
# simple setup but might require careful handling in complex multithreaded apps.
# For production with other DBs, you wouldn't need this.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Register the SessionLocal with the session_scope_provider as the default factory
session_scope_provider.set_default_session_factory(SessionLocal)

def init_db():
    """Initializes the database by creating tables based on ORM models."""
    # First ensure all models are properly mapped by virtue of being imported
    # and inheriting from Base before this point.
    ensure_all_models_mapped() # Keep the verification step

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
    print(f"Creating all database tables with {len(Base.metadata.tables)} tables registered...")
    Base.metadata.create_all(bind=engine_instance)
    print("Database tables created successfully.") 
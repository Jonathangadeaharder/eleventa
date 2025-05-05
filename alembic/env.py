import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add project root to sys.path to allow importing config and models
# This assumes alembic commands are run from the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the Base from your models definition
from infrastructure.persistence.sqlite.database import Base # Use the correct Base

# --- Crucial Change: Import the mapping file itself ---
# This ensures all ORM classes are defined before Base.metadata is used.
import infrastructure.persistence.sqlite.models_mapping

# Register table creation event hooks for proper table ordering
from infrastructure.persistence.sqlite.table_deps import register_table_creation_events
register_table_creation_events(Base.metadata)

# Import the Base from your models definition
# We need to define where Base lives. Let's assume it will eventually be tied
# to a central model definition, perhaps infrastructure.persistence.sqlite.database for now.
# If models are scattered, import them all here so Base registers them.
# No longer needed if models_mapping imports everything
# import infrastructure.persistence.sqlite.models_mapping
from config import DATABASE_URL # Import the database URL from config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata # Now Base.metadata should be fully populated

# other values from the config, defined by the needs of env.py,
# can be acquired:-
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Add the project root directory to the Python path
# This allows Alembic to find your models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your Base and models here
# Option 1: Import Base from database setup and all models individually
# from infrastructure.persistence.sqlite.database import Base
# from infrastructure.persistence.sqlite.models_mapping import ProductOrm, DepartmentOrm, InventoryMovementOrm, SaleOrm, SaleItemOrm # etc.

# Option 2: Create a central models module or import Base which has metadata populated
# Import Base which has metadata populated by models_mapping
# from infrastructure.persistence.sqlite.database import Base # Already imported above
# Import the mapping file itself to ensure all ORM classes are defined before Base.metadata is used.
# import infrastructure.persistence.sqlite.models_mapping # Already imported above
# Make sure all your ORM model files are imported somewhere before Base.metadata is used
# Often this happens implicitly if models_mapping imports them all,
# or if they are imported in the __init__.py of the models directory.
# Removing explicit model imports here as they are covered by importing models_mapping
# from infrastructure.persistence.sqlite.models_mapping import (
#     DepartmentOrm, ProductOrm, InventoryMovementOrm, SaleOrm, SaleItemOrm, CustomerOrm, CreditPaymentOrm, SupplierOrm, PurchaseOrderOrm, PurchaseOrderItemOrm # Add new ORM models
# )

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Priority: 1. Environment Variable, 2. alembic.ini, 3. config.py
    url = os.environ.get("DATABASE_URL")
    if not url:
        url = config.get_main_option("sqlalchemy.url")
    if not url:
        try:
            from config import DATABASE_URL as app_db_url
            url = app_db_url
        except ImportError:
            raise ImportError(
                "DATABASE_URL not found in environment, alembic.ini (sqlalchemy.url), or config.py"
            )

    # Ensure the config object has the correct URL if obtained from env or config.py
    config.set_main_option("sqlalchemy.url", url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Add this to detect column type changes
        render_as_batch=True # Add this for SQLite compatibility with ALTER statements
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Priority: 1. Environment Variable, 2. alembic.ini, 3. config.py
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        db_url = config.get_main_option("sqlalchemy.url")
    if not db_url:
        try:
            from config import DATABASE_URL as app_db_url
            db_url = app_db_url
        except ImportError:
            raise ImportError(
                "DATABASE_URL not found in environment, alembic.ini (sqlalchemy.url), or config.py"
            )

    # Ensure the config object has the correct URL for engine_from_config
    config.set_main_option("sqlalchemy.url", db_url)

    # Create engine configuration dictionary
    engine_config = config.get_section(config.config_ini_section, {})
    # engine_config['sqlalchemy.url'] = db_url # No longer needed, set_main_option covers it

    connectable = engine_from_config(
        engine_config, # Use the section from config object
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Add this to detect column type changes
            render_as_batch=True # Add this for SQLite compatibility with ALTER statements
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

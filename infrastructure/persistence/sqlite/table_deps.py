"""
SQLAlchemy Table Dependency Handler

This module provides functions to control table creation order using SQLAlchemy event hooks.
It addresses issues with custom types and foreign key dependencies that SQLAlchemy's
automatic dependency resolution might not handle correctly.
"""

from sqlalchemy import event, inspect


def create_tables_in_order(connection):
    """
    Create tables in a specific order to handle dependencies.

    This ensures tables with foreign key relationships are created in the correct order,
    particularly when using custom column types like SQLiteUUID.

    Args:
        connection: SQLAlchemy connection object
    """
    from infrastructure.persistence.sqlite.database import Base

    # Define explicit table creation order
    # Tables earlier in this list will be created before tables later in the list
    table_order = [
        "users",  # No UUID dependencies
        "departments",  # No UUID dependencies
        "customers",  # Has UUID primary key - must create before any table with customer_id
        "products",  # May depend on departments
        "invoices",  # May depend on customers
        "sales",  # Depends on customers
        "credit_payments",  # Depends on customers
        "sale_items",  # Depends on sales and products
        "inventory_movements",  # Depends on products
        "cash_drawer_entries",  # May depend on users
        # Add other tables as needed
    ]

    # Get registered tables from metadata
    metadata = Base.metadata
    tables = metadata.tables

    # Create tables in the specified order
    print(f"Creating tables in explicit order: {table_order}")
    for table_name in table_order:
        if table_name in tables:
            print(f"Creating table: {table_name}")
            tables[table_name].create(bind=connection, checkfirst=True)

    # DO NOT COMMIT HERE - Rely on outer transaction

    # Create any remaining tables not explicitly ordered
    existing_tables = set(inspect(connection).get_table_names())
    print(f"Current tables after ordered creation: {existing_tables}")

    remaining_tables = [
        table
        for table in metadata.sorted_tables
        if table.name not in existing_tables and table.name not in table_order
    ]

    if remaining_tables:
        print(f"Creating remaining tables: {[t.name for t in remaining_tables]}")
        for table in remaining_tables:
            if table.name not in existing_tables:
                print(f"Creating additional table: {table.name}")
                table.create(bind=connection, checkfirst=True)
        # DO NOT COMMIT HERE - Rely on outer transaction


# Store for holding tables during the creation process
_SAVED_TABLES = []


def register_table_creation_events(base_metadata):
    """
    Register SQLAlchemy event hooks to control table creation order.

    Args:
        base_metadata: SQLAlchemy metadata object (typically Base.metadata)
    """
    global _SAVED_TABLES
    print("Registering table creation event hooks")

    # Store original tables but don't attempt to modify the immutable dictionary
    @event.listens_for(base_metadata, "before_create")
    def before_create(target, connection, **kw):
        global _SAVED_TABLES
        print(f"Before create event: saving {len(target.tables)} tables")
        # Save original table list for later use
        _SAVED_TABLES = list(target.tables.values())

        # Prevent automatic table creation by telling SQLAlchemy we'll create manually
        return False

    # Use our custom ordered table creation in place of automatic creation
    @event.listens_for(base_metadata, "after_create")
    def after_create(target, connection, **kw):
        global _SAVED_TABLES
        print("After create event: creating tables in order")
        # Create tables in our controlled order
        create_tables_in_order(connection)
        # Clear saved tables after creation
        _SAVED_TABLES = []

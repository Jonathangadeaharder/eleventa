# SQLAlchemy Table Creation Order Fix Plan

## Problem Description

During database schema creation, we encounter the following error:

```
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column 'credit_payments.customer_id' could not find table 'customers' with which to generate a foreign key to target column 'id'
```

This error occurs because:
1. The `credit_payments` table has a foreign key to the `customers` table with a SQLiteUUID column type
2. The `customers` table has a UUID primary key
3. SQLAlchemy's dependency resolver is failing to determine the correct table creation order

## Root Cause Analysis

SQLAlchemy typically handles table creation order automatically based on foreign key dependencies. However, in this case, it's failing to correctly establish the dependency between the `credit_payments` and `customers` tables, likely due to:

1. Custom UUID type implementation (SQLiteUUID)
2. Circular dependencies between tables
3. Model declaration order in the code

## Solution Plan

### 1. Implement Event-based Table Creation Control

#### 1.1 Create Table Dependency Ordering Function

```python
def create_tables_in_order(engine):
    """Create tables in a specific order to handle dependencies."""
    from sqlalchemy import inspect, event
    from infrastructure.persistence.sqlite.database import Base
    
    # Define explicit table creation order
    table_order = [
        'users',
        'customers',      # Must come before credit_payments
        'departments',
        'products',
        'credit_payments',  # Depends on customers
        'sales',
        'sale_items',
        # Add other tables in dependency order
    ]
    
    # Get registered tables from metadata
    metadata = Base.metadata
    tables = metadata.tables
    
    # Create tables in specified order
    for table_name in table_order:
        if table_name in tables:
            tables[table_name].create(bind=engine)
    
    # Create any remaining tables not explicitly ordered
    existing_tables = set(inspect(engine).get_table_names())
    for table in metadata.sorted_tables:
        if table.name not in existing_tables:
            table.create(bind=engine)
```

#### 1.2 Apply Event Hooks to Control Table Creation

```python
def register_table_creation_events():
    """Register SQLAlchemy event hooks to control table creation order."""
    from sqlalchemy import event
    from infrastructure.persistence.sqlite.database import Base
    
    # Disable automatic table creation during create_all
    @event.listens_for(Base.metadata, 'before_create')
    def before_create(target, connection, **kw):
        # Save original table list but prevent automatic creation
        target._saved_tables = target.tables.values()
        target.tables.clear()
    
    # Use our custom table creation function after the standard process
    @event.listens_for(Base.metadata, 'after_create')
    def after_create(target, connection, **kw):
        # Restore tables and create them in our controlled order
        target.tables.update({table.name: table for table in target._saved_tables})
        create_tables_in_order(connection)
```

### 2. Modify Database Initialization Code

#### 2.1 Update Database Module Init Function

```python
def init_db():
    """Initializes the database by creating tables based on ORM models."""
    # Register table creation event hooks
    register_table_creation_events()
    
    # Ensure all models are properly mapped
    ensure_all_models_mapped()
    
    # Create tables using SQLAlchemy metadata
    print(f"Creating/updating database tables defined in Base metadata ({len(Base.metadata.tables)} tables)...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables checked/created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise
```

### 3. Testing Implementation

1. Create unit tests to verify table creation order
2. Test with the database initialization function
3. Verify foreign key constraints are properly established
4. Test custom UUID columns with foreign key relationships

### 4. Subtasks

1. **Analyze Model Dependencies:**
   - Map out all foreign key relationships with custom types
   - Identify any circular dependencies

2. **Implement Event Hook System:**
   - Create event listeners for table creation control
   - Implement ordered table creation function

3. **Update Database Init Code:**
   - Modify database initialization to use event hooks
   - Add detailed logging for table creation process

4. **Test and Verify:**
   - Create test cases for foreign key relationships
   - Verify tables are created in correct order
   - Test with both in-memory and file-based SQLite databases

5. **Documentation:**
   - Update documentation with explanation of table creation approach
   - Add comments to code for future maintenance

## Implementation Timeline

1. **Day 1:** Analysis and planning
2. **Day 2:** Implement event hooks and table ordering function
3. **Day 3:** Testing and validation
4. **Day 4:** Documentation and code review

## Risks and Mitigation

- **Risk:** Event hooks might interfere with Alembic migrations
  - **Mitigation:** Test migrations thoroughly, adapt hooks for Alembic context

- **Risk:** Other SQLAlchemy features might rely on automatic dependency resolution
  - **Mitigation:** Keep minimal changes, focus only on table creation order

- **Risk:** Future schema changes might require updating the explicit table order
  - **Mitigation:** Document the process for updating the table order 
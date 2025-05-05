# Database Test Refactoring Plan: Transactional Isolation

This plan outlines the steps to refactor the pytest setup for database tests to use a consistent and robust transactional isolation strategy with savepoints.

## Goal

Ensure each database test runs in complete isolation from others using a single in-memory database instance per test session, leveraging nested transactions (savepoints) for efficiency and reliability.

## Summary

✅ **Refactoring Status: COMPLETED**

All codebase changes needed for the transactional isolation strategy have been successfully implemented. The primary objectives were achieved:

1. Removed the old marker-based isolation approach
2. Implemented a session-scoped database engine fixture
3. Implemented a function-scoped test session fixture with proper transaction handling
4. Refactored all test files to use the new test_db_session fixture
5. Updated pytest configuration files to remove old markers and isolation options
6. ✅ Fixed the database schema creation order issue with custom event hooks

There are no remaining known issues.

## Granular Subtasks

### 1. Database Configuration (`infrastructure/persistence/sqlite/database.py`)

-   [x] **Verify In-Memory Setup:** Confirm that `DATABASE_URL` uses `sqlite:///:memory:` for the test environment.
-   [x] **Verify StaticPool:** Confirm that `StaticPool` is used when `DATABASE_URL` is in-memory (`poolclass=sqlalchemy.pool.StaticPool`).
-   [x] **Review `init_db`:** Ensure `init_db` correctly calls `map_models()` (or equivalent) and `Base.metadata.create_all(bind=engine)`. *Note: This function might be superseded by the session-scoped fixture.*

### 2. Global Test Fixture (`tests/conftest.py`)

-   [x] **Remove Old Hooks:** Delete `pytest_configure`, `pytest_collection_modifyitems`, and `pytest_runtest_setup` functions related to marker-based isolation.
-   [x] **Remove Global Setup:** Delete the global `models_mapping.map_models()` and `Base.metadata.create_all(bind=engine)` calls from the top level of `conftest.py`.
-   [x] **Create Session-Scoped Engine (`db_engine`)**:
    -   Define a new fixture `db_engine` with `scope="session"`.
    -   Inside `db_engine`:
        -   Get the `engine` instance from `database.py`.
        -   Ensure models are mapped (`models_mapping.map_models()` or equivalent via imports).
        -   Create all tables (`Base.metadata.create_all(bind=engine)` via `create_schema`).
        -   Yield the `engine`.
        -   *(Optional Cleanup: `Base.metadata.drop_all(bind=engine)` after yield if needed, handled by `engine.dispose()`)*
-   [x] **Refactor Function-Scoped Session (`test_db_session`)**:
    -   [x] Modify the existing `test_db_session` fixture (`scope="function"`).
    -   [x] It should take `db_engine` as an argument.
    -   [x] Inside `test_db_session`:
        -   [x] Establish a connection: `connection = db_engine.connect()`.
        -   [x] Begin a transaction: `transaction = connection.begin()`.
        -   [x] Create a session bound to the connection: `session = SessionLocal(bind=connection)`. 
        -   [x] Start a nested transaction (savepoint): `nested = connection.begin_nested()`.
        -   [x] Add an event listener to rollback the savepoint automatically when the session is committed or rolled back (`@event.listens_for(session, "after_transaction_end")`). *(Note: Listener removed, relying on outer transaction rollback for isolation)*
        -   [x] `yield session`.
    -   [x] After yield (in the fixture teardown):
        -   [x] Close the session: `session.close()`.
        -   [x] Rollback the outer transaction: `transaction.rollback()`.
        -   [x] Close the connection: `connection.close()`.
-   [x] **Remove `clean_db` fixture:** Delete the old `clean_db` fixture if it still exists.

### 3. Individual Repository Test Files (`tests/infrastructure/persistence/test_*.py`)

-   [x] **Remove Local `setup_database`:** Delete any `setup_database` or similarly named fixtures within each test file (e.g., `test_user_repository.py`, `test_department_repository.py`, etc.).
-   [x] **Remove `@pytest.mark.repository`:** Delete the `pytestmark = pytest.mark.repository` line or any `@pytest.mark.repository` decorators from test files or classes.
-   [x] **Ensure Usage of `test_db_session`:** Verify all test functions that interact with the database correctly use the `test_db_session` fixture. *(Refactored: `test_inventory_repository.py`, `test_database_module.py`, `test_database.py`, `test_customer_repository.py`, `test_sale_repository.py`)*
-   [x] **Refactor `test_sale_repository.py`**:
    -   [x] Remove the helper repository classes (`_HelperSqliteSaleRepository`, `_HelperSqliteDepartmentRepository`, `_HelperSqliteProductRepository`).
    -   [x] Remove helper functions using these classes (`create_department_helper`, `create_product_helper`, `create_customer_helper` specifically within this file if they use the helper repos).
    -   [x] Instantiate the *actual* repository classes (`SqliteSaleRepository`, `SqliteProductRepository`, etc.) within the test functions or a standard pytest fixture, passing `test_db_session`.
    -   [x] Adjust test logic to use the standard repositories and commit transactions via `test_db_session.commit()` where necessary within the test logic.

### 4. Pytest Configuration (`pytest.ini`)

-   [x] **Remove Isolation Options:** Delete the `xvs_repository_isolation = true` line or any other configuration related to the previous isolation attempts (like `-n` options if solely for isolation).
-   [x] **Remove Repository Marker:** Delete the `repository:` marker definition under `[pytest]` -> `markers`.

### 5. Verification

-   [x] **Run All Tests:** Execute `pytest` or `python -m pytest` from the root directory.
-   [x] **Confirm Pass:** ✅ Tests now pass with our table ordering solution
-   [x] **Check Speed:** Tests run faster with the new transaction-based isolation strategy

### 6. Fixed Issues

-   **Database Schema Creation Order:** We successfully fixed the issue with table creation order by implementing SQLAlchemy event hooks in a new module `infrastructure/persistence/sqlite/table_deps.py`. The solution:
    1. Creates tables in a controlled order with explicit dependencies
    2. Ensures the `customers` table is created before the `credit_payments` table 
    3. Uses event hooks to safely override SQLAlchemy's default creation order
    4. Works for both regular database initialization and test setup
    
    The implementation is documented in detail in `implementation_report.md`. 
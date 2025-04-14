## 4. Core Features (High-Level)

*   Product Management (CRUD, Departments, Catalog)
*   Inventory Management (Add Stock, Adjustments, Reports, Low Stock, Movements, Kardex)
*   Sales Processing (Add items, Calculate totals, Finalize sale, Multiple Payment Types, Customer Association)
*   Invoicing: Generate basic invoices from sales (Argentina-focused structure).
*   End of Day/Shift (Corte): Reconciliation report (Sales by payment type, Cash flow).
*   Advanced Reporting: Sales summaries (by period, department, customer), graphical representation.
*   Customer Management (CRUD, Credit Balance Tracking)
*   Customer Credits (Sales on credit, Payments on account)
*   Purchases (Suppliers, POs, Receiving Stock)
*   User Management: Basic multi-user support (Login, associating actions with user).
*   Receipt Printing: Generate and print basic sales receipts.
*   Application Configuration (Store info, basic settings).
*   Database Setup & Migrations.
*   UI Polish: Icons, specific widgets (filters), keyboard shortcuts, visual refinements.

## 5. Development Tasks (Tickets)

*(Instructions: Follow TDD. For each task, first review/write the tests described in "Tests (Write First - Red)". Then, implement the steps in "Implementation Steps" until the tests pass (Green). Finally, check the box.)*

---

### Phase 1: Project Foundation

*   **TASK-001: Project Setup & Dependencies**
    *   **Module:** Project Wide
    *   **Status:** `[x]`
    *   **Description:** Initialize the project structure, virtual environment, Git repository, and install core dependencies.
    *   **Tests (Write First - Red):**
        *   N/A (Manual setup verification). Verify `pip install -r requirements.txt` works. Verify basic `python main.py` runs without crashing (even if it does nothing yet).
    *   **Implementation Steps:**
        1.  Create the main project directory (`eleventa_clone/`).
        2.  Set up a Python virtual environment (`venv`).
        3.  Initialize a Git repository (`git init`, create `.gitignore`).
        4.  Create the top-level directories (`core`, `infrastructure`, `ui`, `tests`, `alembic`).
        5.  Create `requirements.txt` with `PySide6`, `SQLAlchemy`, `alembic`, `reportlab`, potentially `pyqtgraph`.
        6.  Install dependencies (`pip install -r requirements.txt`).
        7.  Create basic `main.py`, `config.py`.

*   **TASK-002: Database & ORM Setup (SQLAlchemy)**
    *   **Module:** Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Configure SQLAlchemy engine, session management, and declarative base. Set up the session scope utility.
    *   **Tests (Write First - Red):**
        *   `test_database_connection()`: Verify that `engine.connect()` successfully establishes a connection to the configured SQLite database file (it should create the file if it doesn't exist).
        *   `test_session_scope()`: Verify the `session_scope` context manager yields a valid SQLAlchemy `Session` object and closes it afterwards. Test commit on success and rollback on exception within the scope.
    *   **Implementation Steps:**
        1.  Define `DATABASE_URL` in `config.py`.
        2.  Create `infrastructure/persistence/sqlite/database.py`: Define `engine`, `SessionLocal`, `Base`.
        3.  Create `infrastructure/persistence/utils.py`: Implement the `session_scope` context manager.
        4.  Write tests in `tests/infrastructure/persistence/test_database.py`.

*   **TASK-003: Alembic Setup & Initial Migration**
    *   **Module:** Infrastructure (Persistence) / Project Wide
    *   **Status:** `[x]`
    *   **Description:** Initialize Alembic for database schema migrations and create the first (empty) migration.
    *   **Tests (Write First - Red):**
        *   N/A (Manual verification). Verify `alembic init alembic` runs. Verify `alembic revision -m "Initial setup"` runs. Verify `alembic upgrade head` runs without error (creates `alembic_version` table in the DB).
    *   **Implementation Steps:**
        1.  Run `alembic init alembic`.
        2.  Configure `alembic.ini` (set `sqlalchemy.url`).
        3.  Configure `alembic/env.py`: Import `Base` from `models_mapping.py`, set `target_metadata`, configure `run_migrations_online` to use `config.DATABASE_URL`.
        4.  Run `alembic revision -m "Initial setup"`.
        5.  Run `alembic upgrade head`.

---

### Phase 2: Product Module

*   **TASK-004: Domain Models - Product & Department**
    *   **Module:** Core (Models)
    *   **Status:** `[x]`
    *   **Description:** Define the data classes for `Product` and `Department`.
    *   **Tests (Write First - Red):**
        *   `test_department_creation()`: Assert a `Department` object can be created with expected attributes (id, name).
        *   `test_product_creation()`: Assert a `Product` object can be created with expected attributes (id, code, description, prices, department_id, stock levels, etc.) and default values.
    *   **Implementation Steps:**
        1.  Create `core/models/product.py`.
        2.  Define `dataclass Department`.
        3.  Define `dataclass Product`.
        4.  Write tests in `tests/core/models/test_product.py`.

*   **TASK-005: ORM Mapping - Product & Department**
    *   **Module:** Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Create SQLAlchemy ORM classes (`ProductOrm`, `DepartmentOrm`) mapping to database tables, including relationships. Generate migration.
    *   **Tests (Write First - Red):**
        *   N/A (Schema definition, tested via repository tests and migration). Verify `alembic revision --autogenerate -m "Add product and department tables"` detects the new models. Verify `alembic upgrade head` creates the tables correctly in the DB.
    *   **Implementation Steps:**
        1.  Create `infrastructure/persistence/sqlite/models_mapping.py`.
        2.  Define `DepartmentOrm(Base)` with columns and relationship to `ProductOrm`.
        3.  Define `ProductOrm(Base)` with columns and relationship to `DepartmentOrm`.
        4.  Run `alembic revision --autogenerate -m "Add product and department tables"`.
        5.  Review the generated migration script in `alembic/versions/`.
        6.  Run `alembic upgrade head`.

*   **TASK-006: Repository Interfaces - Product & Department**
    *   **Module:** Core (Interfaces)
    *   **Status:** `[x]`
    *   **Description:** Define abstract base classes (`IProductRepository`, `IDepartmentRepository`) specifying the contract for data access operations.
    *   **Tests (Write First - Red):**
        *   N/A (Interface definition).
    *   **Implementation Steps:**
        1.  Create `core/interfaces/repository_interfaces.py`.
        2.  Define `IDepartmentRepository(ABC)` with methods (`add`, `get_by_id`, `get_by_name`, `get_all`, `update`, `delete`).
        3.  Define `IProductRepository(ABC)` with methods (`add`, `get_by_id`, `get_by_code`, `get_all`, `update`, `delete`, `search`, `get_low_stock`, `update_stock`).

*   **TASK-007: Repository Implementation - Department**
    *   **Module:** Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Implement the `SqliteDepartmentRepository` class providing concrete database operations for Departments using SQLAlchemy.
    *   **Tests (Write First - Red):** (Use a test database/in-memory DB and `session_scope`)
        *   `test_add_department()`: Verify a department is added to DB and the returned object has an ID. Test duplicate name constraint.
        *   `test_get_department_by_id()`: Verify correct department retrieval and `None` for non-existent ID.
        *   `test_get_department_by_name()`: Verify correct department retrieval and `None` for non-existent name.
        *   `test_get_all_departments()`: Verify retrieval of all added departments, ordered by name.
        *   `test_update_department()`: Verify department name is updated in DB.
        *   `test_delete_department()`: Verify department is removed from DB. Test deletion of non-existent ID. (Add test for deleting department in use by products later).
    *   **Implementation Steps:**
        1.  In `infrastructure/persistence/sqlite/repositories.py`, create `SqliteDepartmentRepository(IDepartmentRepository)`.
        2.  Implement all methods using the injected `Session` (via `__init__` or `session_scope`) to query/manipulate `DepartmentOrm`. Include mapping between ORM and Core models.
        3.  Write tests in `tests/infrastructure/persistence/test_department_repository.py`.

*   **TASK-008: Repository Implementation - Product**
    *   **Module:** Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Implement the `SqliteProductRepository` class.
    *   **Tests (Write First - Red):** (Use a test database/in-memory DB and `session_scope`)
        *   `test_add_product()`: Verify product is added, ID assigned, relationships (department) handled. Test duplicate code constraint.
        *   `test_get_product_by_id()`: Verify retrieval, including eager loading of department. Test non-existent ID.
        *   `test_get_product_by_code()`: Verify retrieval by code. Test non-existent code.
        *   `test_get_all_products()`: Verify retrieval of all products, ordered.
        *   `test_update_product()`: Verify fields are updated correctly. Test updating non-existent product.
        *   `test_delete_product()`: Verify product deletion. Test non-existent ID. (Test deletion constraint based on stock later).
        *   `test_search_product()`: Verify search by code/description returns correct results.
        *   `test_update_stock()`: Verify only the stock quantity is updated.
        *   `test_get_low_stock()`: Verify returns products where `quantity_in_stock <= min_stock` and `uses_inventory=True`.
    *   **Implementation Steps:**
        1.  In `infrastructure/persistence/sqlite/repositories.py`, create `SqliteProductRepository(IProductRepository)`.
        2.  Implement all methods using the injected `Session` to query/manipulate `ProductOrm`. Include mapping between ORM and Core models. Use eager loading (`joinedload`) for departments where needed.
        3.  Write tests in `tests/infrastructure/persistence/test_product_repository.py`.

*   **TASK-009: Service Layer - ProductService**
    *   **Module:** Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Implement `ProductService` containing business logic for products and departments, orchestrating repository calls.
    *   **Tests (Write First - Red):** (Mock the repository interfaces)
        *   `test_add_product_success()`: Verify service calls `repo.add` after validation passes.
        *   `test_add_product_validation()`: Test required fields (code, desc), negative prices, duplicate code (mock `repo.get_by_code` to return existing), non-existent department ID. Assert `ValueError` is raised.
        *   `test_update_product_success()`: Verify service calls `repo.get_by_id` then `repo.update`.
        *   `test_update_product_validation()`: Test validation rules similar to `add`, including checking for code uniqueness conflict *excluding* the product being updated. Test updating non-existent product ID.
        *   `test_delete_product_success()`: Verify service calls `repo.delete`.
        *   `test_delete_product_with_stock()`: Mock `repo.get_by_id` to return a product with stock > 0 and `uses_inventory=True`. Verify `ValueError` with specific message is raised and `repo.delete` is NOT called.
        *   `test_delete_product_no_stock()`: Mock product with stock=0, verify `repo.delete` IS called.
        *   `test_delete_product_does_not_use_inventory()`: Mock product with `uses_inventory=False` and stock > 0, verify `repo.delete` IS called.
        *   `test_find_product()`: Verify calls `repo.search` or `repo.get_all`.
        *   `test_add_department_validation()`: Test empty name, duplicate name.
        *   `test_delete_department_logic()`: (Add test for checking product usage later). Verify calls `repo.delete`.
    *   **Implementation Steps:**
        1.  Create `core/services/product_service.py`.
        2.  Define `ProductService` with `__init__` accepting `IProductRepository` and `IDepartmentRepository` (Dependency Injection).
        3.  Implement methods (`add_product`, `update_product`, `delete_product`, `find_product`, `get_all_products`, `add_department`, `get_all_departments`, `delete_department`, etc.).
        4.  Include validation logic within service methods before calling repositories.
        5.  Use `session_scope` from `infrastructure.persistence.utils` if operations need to span multiple repository calls transactionally.
        6.  Write tests in `tests/core/services/test_product_service.py` using `unittest.mock`.

*   **TASK-010: UI - Main Window Shell & Navigation**
    *   **Module:** UI
    *   **Status:** `[x]`
    *   **Description:** Create the main application window (`QMainWindow`) with toolbar, status bar, and a `QStackedWidget` to hold different views. Implement basic navigation actions.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify window title is set. Verify toolbar actions exist. Verify clicking a toolbar action switches the `QStackedWidget` to the correct (placeholder) view index. Verify status bar exists.
    *   **Implementation Steps:**
        1.  Create `ui/main_window.py`.
        2.  Define `MainWindow(QMainWindow)`.
        3.  Set up `QStackedWidget` as the central widget area.
        4.  Create `QToolBar` and add `QAction` placeholders for Sales, Products, Inventory, etc.
        5.  Connect action triggers to a `switch_view` method.
        6.  Implement `switch_view` to change `stacked_widget.setCurrentIndex()`.
        7.  Add `QStatusBar`.
        8.  In `main.py`, instantiate and show the `MainWindow`. (Services will be passed later).

*   **TASK-011: UI - Product View (Display & Basic Actions)**
    *   **Module:** UI (Views, Models)
    *   **Status:** `[x]`
    *   **Description:** Create the `ProductsView` widget displaying products in a table. Implement buttons for New, Modify, Delete, Departments, and Search.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify the view loads. Verify product data (mocked initially) appears in the `QTableView`. Verify buttons exist. Verify typing in search triggers filtering (connects to service). Verify clicking 'New'/'Modify'/'Delete' calls the respective handler methods (print statements initially). Verify double-clicking a row calls the modify handler.
    *   **Implementation Steps:**
        1.  Create `ui/models/table_models.py` and define `ProductTableModel(QAbstractTableModel)`. Implement `rowCount`, `columnCount`, `data`, `headerData`. Add logic for displaying data, alignment, and low-stock highlighting in the `data` method.
        2.  Create `ui/views/products_view.py`.
        3.  Define `ProductsView(QWidget)`.
        4.  Add toolbar buttons (`QPushButton`), search (`QLineEdit`), and `QTableView`.
        5.  Instantiate `ProductTableModel` and set it on the table view.
        6.  Implement methods `refresh_products`, `add_new_product`, `modify_selected_product`, `delete_selected_product`, `manage_departments`, `filter_products`.
        7.  Connect button clicks and search text changes to these methods.
        8.  In `refresh_products`, call `product_service.find_product()` and update the table model (`model.update_data(products)`).
        9.  In `main_window.py`, instantiate `ProductsView` (passing `ProductService`) and add it to the `QStackedWidget`.

*   **TASK-012: UI - Department Dialog**
    *   **Module:** UI (Dialogs)
    *   **Status:** `[x]`
    *   **Description:** Create the `DepartmentDialog` for adding, (editing - optional), and deleting departments.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify dialog opens. Verify existing departments load into the `QListWidget`. Verify selecting a department populates the name field. Verify clicking 'Nuevo' calls the add logic. Verify clicking 'Eliminar' calls the delete logic after confirmation. Verify validation (empty name, duplicate name) shows error messages.
    *   **Implementation Steps:**
        1.  Create `ui/dialogs/department_dialog.py`.
        2.  Define `DepartmentDialog(QDialog)`.
        3.  Use `QHBoxLayout` with a `QListWidget` on the left and `QLineEdit`/`QPushButton`s on the right.
        4.  Implement `_load_departments` to fetch from `product_service` and populate the list.
        5.  Implement `_on_selection_changed` to update the form.
        6.  Implement `_save_department` (handles add/update) calling `product_service.add_department` (or update). Include validation.
        7.  Implement `_delete_department` calling `product_service.delete_department` after `ask_confirmation`.
        8.  Connect signals/slots.
        9.  In `ProductsView.manage_departments`, instantiate and `exec()` this dialog. Refresh product view afterwards if needed.

*   **TASK-013: UI - Product Dialog (Add/Modify)**
    *   **Module:** UI (Dialogs)
    *   **Status:** `[x]`
    *   **Description:** Create the `ProductDialog` for adding new products and modifying existing ones.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify dialog opens in 'New' or 'Modify' mode. Verify fields exist (code, desc, prices, dept combo, unit, inventory checkbox, stock levels). Verify departments load into combo box. Verify inventory fields enable/disable with checkbox. Verify validation (required fields, duplicates, negative numbers) shows errors. Verify saving calls the correct `product_service` method (`add_product` or `update_product`). Verify existing product data populates correctly in modify mode.
    *   **Implementation Steps:**
        1.  Create `ui/dialogs/product_dialog.py`.
        2.  Define `ProductDialog(QDialog)`.
        3.  Use `QFormLayout` for fields (`QLineEdit`, `QDoubleSpinBox`, `QComboBox`, `QCheckBox`).
        4.  Implement `_load_departments` to populate the combo box (add "- Sin Departamento -" option).
        5.  Implement `_populate_form` to fill fields when editing (`product` is passed in).
        6.  Implement `_toggle_inventory_fields` connected to the checkbox state.
        7.  Implement `accept` method: Get data from fields, perform validation (or rely on service validation), call `product_service.add_product` or `product_service.update_product`. Show errors via `show_error_message`. Call `super().accept()` only on success.
        8.  In `ProductsView.add_new_product` and `modify_selected_product`, instantiate and `exec()` this dialog. Refresh product list on success.

---

### Phase 3: Inventory Module

*   **TASK-014: Domain & ORM Models - InventoryMovement**
    *   **Module:** Core (Models), Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Define `InventoryMovement` dataclass and corresponding `InventoryMovementOrm` SQLAlchemy model. Generate migration.
    *   **Tests (Write First - Red):**
        *   `test_inventory_movement_creation()`: Assert `InventoryMovement` object creation.
        *   N/A for ORM (Schema definition). Verify `alembic revision --autogenerate -m "Add inventory movement table"` detects model. Verify `alembic upgrade head` creates table.
    *   **Implementation Steps:**
        1.  Create `core/models/inventory.py`, define `dataclass InventoryMovement`.
        2.  In `infrastructure/persistence/sqlite/models_mapping.py`, define `InventoryMovementOrm(Base)` with columns and relationship to `ProductOrm`.
        3.  Run `alembic revision --autogenerate -m "Add inventory movement table"`.
        4.  Review migration script.
        5.  Run `alembic upgrade head`.

*   **TASK-015: Repository Interface & Implementation - Inventory**
    *   **Module:** Core (Interfaces), Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Define `IInventoryRepository` and implement `SqliteInventoryRepository`.
    *   **Tests (Write First - Red):** (Use test DB)
        *   `test_add_movement()`: Verify movement is saved to DB with correct details.
        *   `test_get_movements_for_product()`: Verify returns only movements for the specified product ID.
        *   `test_get_all_movements()`: Verify returns all movements.
    *   **Implementation Steps:**
        1.  In `core/interfaces/repository_interfaces.py`, define `IInventoryRepository(ABC)` with methods (`add_movement`, `get_movements_for_product`, `get_all_movements`).
        2.  In `infrastructure/persistence/sqlite/repositories.py`, create `SqliteInventoryRepository(IInventoryRepository)`.
        3.  Implement methods using the `Session` to interact with `InventoryMovementOrm`. Map between ORM and Core models.
        4.  Write tests in `tests/infrastructure/persistence/test_inventory_repository.py`.

*   **TASK-016: Service Layer - InventoryService (Add/Adjust Stock)**
    *   **Module:** Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Implement `InventoryService` with logic for adding and adjusting inventory, updating product stock, and logging movements.
    *   **Tests (Write First - Red):** (Mock `IInventoryRepository`, `IProductRepository`)
        *   `test_add_inventory_success()`: Mock `product_repo.get_by_id`. Verify `product_repo.update_stock` is called with correct new quantity. Verify `inventory_repo.add_movement` is called with correct movement details (type, quantities, etc.). Test optional cost price update logic.
        *   `test_add_inventory_validation()`: Test adding <= 0 quantity. Test adding to non-existent product. Test adding to product not using inventory.
        *   `test_adjust_inventory_success()`: Similar to add, verify stock update and movement logging for both positive and negative adjustments.
        *   `test_adjust_inventory_validation()`: Test adjusting non-existent product, product not using inventory, negative final quantity.
        *   `test_decrease_stock_for_sale()`: Verify stock update and movement logging. Test insufficient stock scenario (should it raise error or allow negative based on config/logic?). Ensure it uses the *passed-in session* for transactional integrity with the sale.
    *   **Implementation Steps:**
        1.  Create `core/services/inventory_service.py`.
        2.  Define `InventoryService` accepting `IInventoryRepository` and `IProductRepository`.
        3.  Implement `add_inventory`, `adjust_inventory`, `decrease_stock_for_sale`.
        4.  Use `session_scope` to ensure product stock update and movement logging occur within the same transaction. For `decrease_stock_for_sale`, accept an optional `session` argument to participate in the calling transaction (e.g., from `SaleService`).
        5.  Implement `get_inventory_report`, `get_low_stock_products`, `get_inventory_movements` (mostly delegating to product/inventory repos initially).
        6.  Write tests in `tests/core/services/test_inventory_service.py`.

*   **TASK-017: UI - Inventory View (Tabs & Reports)**
    *   **Module:** UI (Views)
    *   **Status:** `[x]`
    *   **Description:** Create the `InventoryView` with a `QTabWidget` for different reports (General Report, Low Stock). Implement basic display.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify view loads with tabs. Verify clicking 'Reporte de Inventario' button fetches data via `inventory_service` and populates the general report table. Verify total cost/items labels update. Verify clicking 'Productos bajos' button fetches data and populates the low stock table. Verify the correct tab becomes active.
    *   **Implementation Steps:**
        1.  Create `ui/views/inventory_view.py`.
        2.  Define `InventoryView(QWidget)`.
        3.  Add toolbar buttons (`QPushButton`). Disable unimplemented ones initially.
        4.  Add `QTabWidget`.
        5.  Create separate `QWidget`s for each tab (`report_tab`, `low_stock_tab`).
        6.  Add `QTableView` and labels to the tabs. Reuse `ProductTableModel` initially for both tables.
        7.  Implement `refresh_inventory_report` and `refresh_low_stock_report` methods, calling the respective `inventory_service` methods and updating the corresponding table models and labels.
        8.  Connect toolbar buttons and `tab_widget.currentChanged` signal.
        9.  In `main_window.py`, instantiate `InventoryView` (passing services) and add to `QStackedWidget`.

*   **TASK-018: UI - Add Inventory Dialog**
    *   **Module:** UI (Dialogs)
    *   **Status:** `[x]`
    *   **Description:** Create the `AddInventoryDialog` to input quantity (and optionally cost) for adding stock to a selected product.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify dialog opens showing correct product info. Verify quantity/cost fields exist. Verify clicking 'Agregar Cantidad' calls `inventory_service.add_inventory` with correct parameters. Verify validation (quantity > 0) shows error.
    *   **Implementation Steps:**
        1.  Create `ui/dialogs/add_inventory_dialog.py`.
        2.  Define `AddInventoryDialog(QDialog)`.
        3.  Display product code/description/current stock (`QLabel`).
        4.  Add fields (`QDoubleSpinBox`) for quantity to add and optional new cost price. Add `QTextEdit` for notes.
        5.  Implement `accept` method: Get data, call `inventory_service.add_inventory`. Show errors. Call `super().accept()` on success.
        6.  In `InventoryView.add_inventory_item` (implement this slot), get the selected product from the active table, instantiate and `exec()` this dialog. Refresh the inventory view on success.

---

### Phase 4: Sales Module (Basic)

*   **TASK-019: Domain & ORM Models - Sale & SaleItem**
    *   **Module:** Core (Models), Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Define `Sale`, `SaleItem` dataclasses and corresponding ORM models (`SaleOrm`, `SaleItemOrm`). Generate migration.
    *   **Tests (Write First - Red):**
        *   `test_sale_item_creation()`: Assert `SaleItem` creation and subtotal calculation.
        *   `test_sale_creation()`: Assert `Sale` creation with list of items.
        *   N/A for ORM. Verify `alembic revision --autogenerate -m "Add sale and sale item tables"` detects models. Verify `alembic upgrade head` creates tables.
    *   **Implementation Steps:**
        1.  Create `core/models/sale.py`, define `dataclass SaleItem` and `dataclass Sale`.
        2.  In `infrastructure/persistence/sqlite/models_mapping.py`, define `SaleOrm(Base)` and `SaleItemOrm(Base)` with columns and relationships (one-to-many from Sale to SaleItem, many-to-one from SaleItem to Product). Use `cascade="all, delete-orphan"` on the Sale->Items relationship.
        3.  Run `alembic revision --autogenerate -m "Add sale and sale item tables"`.
        4.  Review migration script.
        5.  Run `alembic upgrade head`.

*   **TASK-020: Repository Interface & Implementation - Sale**
    *   **Module:** Core (Interfaces), Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Define `ISaleRepository` and implement `SqliteSaleRepository`.
    *   **Tests (Write First - Red):** (Use test DB)
        *   `test_add_sale()`: Verify sale header and all associated sale items are saved correctly to DB. Verify relationships are set up. Verify returned Sale object has IDs assigned.
    *   **Implementation Steps:**
        1.  In `core/interfaces/repository_interfaces.py`, define `ISaleRepository(ABC)` with `add_sale` method (add query methods later).
        2.  In `infrastructure/persistence/sqlite/repositories.py`, create `SqliteSaleRepository(ISaleRepository)`.
        3.  Implement `add_sale` using the `Session`. Ensure both `SaleOrm` and related `SaleItemOrm` objects are added and flushed correctly within the session scope. Map ORM models to Core models.
        4.  Write tests in `tests/infrastructure/persistence/test_sale_repository.py`.

*   **TASK-021: Service Layer - SaleService**
    *   **Module:** Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Implement `SaleService` to handle sale creation, orchestrating `SaleRepository` and `InventoryService` (for stock decrease) within a single transaction.
    *   **Tests (Write First - Red):** (Mock `ISaleRepository`, `IProductRepository`, `InventoryService`)
        *   `test_create_sale_success()`: Mock `product_repo.get_by_id` to return products. Verify `sale_repo.add_sale` is called with correctly constructed `Sale` and `SaleItem` objects. Mock `sale_repo.add_sale` to return a Sale with an ID. Verify `inventory_service.decrease_stock_for_sale` is called for *each* item in the sale, passing the correct product ID, quantity, sale ID, and *importantly*, the session object used by the service.
        *   `test_create_sale_validation()`: Test empty item list. Test item with non-existent product ID (mock `product_repo.get_by_id` returning None). Test item with zero/negative quantity.
        *   `test_create_sale_transactionality()`: Conceptually, ensure mocks show that if `inventory_service.decrease_stock_for_sale` raises an error, `sale_repo.add_sale` changes are rolled back (this is handled by `session_scope` if used correctly).
    *   **Implementation Steps:**
        1.  Create `core/services/sale_service.py`.
        2.  Define `SaleService` accepting `ISaleRepository`, `IProductRepository`, `InventoryService`.
        3.  Implement `create_sale` method (will be enhanced later for payment type, user, customer).
        4.  Use `session_scope` to manage the transaction. Inside the scope:
            *   Fetch product details using `product_repo` (re-instantiated with the session).
            *   Build `Sale` and `SaleItem` core model objects.
            *   Call `sale_repo.add_sale` (re-instantiated with the session).
            *   For each item in the *returned* sale (which now has IDs), call `inventory_service.decrease_stock_for_sale`, passing the *current session* from the scope.
        5.  Write tests in `tests/core/services/test_sale_service.py`.

*   **TASK-022: UI - Sales View (Basic Layout & Item Entry)**
    *   **Module:** UI (Views, Models)
    *   **Status:** `[x]`
    *   **Description:** Create the `SalesView` with product code entry, sale items table, total display, and action buttons. Implement adding items by code.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify layout: code entry, table, total, buttons. Verify entering a valid product code and pressing Enter/Add button calls `product_service.get_product_by_code`. If found, verify a new row appears in the `SaleItemTableModel` with correct product details and quantity 1. Verify the total label updates. Verify the code entry field clears and refocuses. Verify entering an invalid code shows a warning message.
    *   **Implementation Steps:**
        1.  In `ui/models/table_models.py`, create `SaleItemTableModel(QAbstractTableModel)`. Implement methods to display sale items and `add_item`, `remove_item`, `get_all_items`, `clear`.
        2.  Create `ui/views/sales_view.py`.
        3.  Define `SalesView(QWidget)`.
        4.  Add `QLineEdit` for code entry, `QTableView` with `SaleItemTableModel`, `QLabel` for total, `QPushButton`s for Add, Remove, Cancel, Finalize.
        5.  Implement `add_item_from_entry`: Get code, call `product_service.get_product_by_code`. If found, create `SaleItem` instance, add to table model using `model.add_item()`. Call `update_total()`. Clear/focus entry. Show warning if not found.
        6.  Implement `update_total`: Calculate sum from `model.get_all_items()` and update the total label.
        7.  Implement `_clear_sale`: Clear the model, update total, clear/focus entry.
        8.  Connect signals (entry `returnPressed`, add button `clicked`) to `add_item_from_entry`. Connect model signals (`rowsRemoved`, `modelReset`) to `update_total`.
        9.  In `main_window.py`, instantiate `SalesView` (passing services) and add to `QStackedWidget`. Set it as the initial view.

*   **TASK-023: UI - Sales View (Remove Item, Cancel, Finalize)**
    *   **Module:** UI (Views)
    *   **Status:** `[x]`
    *   **Description:** Implement functionality for removing items from the sale, canceling the entire sale, and finalizing the sale (basic version).
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify selecting an item and clicking 'Quitar Artículo' removes the row from the table and updates the total. Verify clicking 'Cancelar Venta' (after confirmation) clears the table and total. Verify clicking 'Finalizar Venta' (after confirmation) calls `sale_service.create_sale` with data from the table model. If successful, verify the table/total clears and an info message appears. If `sale_service` raises an error, verify an error message is shown and the sale is *not* cleared.
    *   **Implementation Steps:**
        1.  In `SalesView`, implement `remove_selected_item`: Get selected row index, call `model.remove_item(index)`.
        2.  Implement `cancel_current_sale`: Ask for confirmation, if yes, call `_clear_sale()`.
        3.  Implement `finalize_current_sale` (basic version): Get items from `model.get_all_items()`. If empty, show warning. Ask for confirmation. Prepare `items_data` list for the service. Call `sale_service.create_sale(items_data)` (will be enhanced later). On success, show info message and call `_clear_sale()`. On error, show error message.
        4.  Connect Remove, Cancel, Finalize button clicks to these methods.

---

### Phase 5: Customer & Purchases (Basic)

*   **TASK-024: Domain, ORM, Repo - Customer**
    *   **Module:** Core (Models, Interfaces), Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Define the `Customer` model, ORM mapping, repository interface (`ICustomerRepository`), and implementation (`SqliteCustomerRepository`) for basic CRUD operations. Include fields like name, phone, email, address, potentially a credit limit/balance.
    *   **Tests (Write First - Red):**
        *   `test_customer_creation()`: Test `Customer` dataclass.
        *   N/A for ORM: Verify Alembic migration generation/application for the `customers` table.
        *   `test_customer_repository_crud()`: Test `add`, `get_by_id`, `get_all`, `update`, `delete` methods of `SqliteCustomerRepository`. Test searching/finding customers.
    *   **Implementation Steps:**
        1.  Define `dataclass Customer` in `core/models/customer.py` (create file).
        2.  Define `CustomerOrm(Base)` in `infrastructure/persistence/sqlite/models_mapping.py`.
        3.  Generate and apply Alembic migration (`Add customer table`).
        4.  Define `ICustomerRepository(ABC)` in `core/interfaces/repository_interfaces.py`.
        5.  Implement `SqliteCustomerRepository(ICustomerRepository)` in `infrastructure/persistence/sqlite/repositories.py`.
        6.  Write tests for the repository in `tests/infrastructure/persistence/`.

*   **TASK-025: Service Layer - CustomerService**
    *   **Module:** Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Implement `CustomerService` to handle business logic related to customers (validation, orchestration).
    *   **Tests (Write First - Red):** (Mock `ICustomerRepository`)
        *   `test_add_customer_validation()`: Test required fields (e.g., name), format validation (e.g., email, phone - basic), duplicate checks if necessary.
        *   `test_update_customer_validation()`: Similar validation for updates.
        *   `test_delete_customer_logic()`: Test constraints (e.g., cannot delete customer with outstanding credit balance - requires credit feature).
        *   Verify service methods correctly call corresponding repository methods.
    *   **Implementation Steps:**
        1.  Create `core/services/customer_service.py`.
        2.  Define `CustomerService` accepting `ICustomerRepository`.
        3.  Implement methods like `add_customer`, `update_customer`, `delete_customer`, `find_customer`, `get_customer_by_id`, `get_all_customers`. Include validation logic.
        4.  Write tests in `tests/core/services/test_customer_service.py`.

*   **TASK-026: UI - Customer Management View**
    *   **Module:** UI (Views, Dialogs, Models)
    *   **Status:** `[x]`
    *   **Description:** Create a view similar to the Products view for managing customers (list, search, add, modify, delete).
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify a 'Clientes' action/view exists. Verify the view displays customers in a table. Verify search works. Verify Add/Modify buttons open a `CustomerDialog`. Verify Delete button works (with confirmation and checks).
    *   **Implementation Steps:**
        1.  Create `CustomerTableModel(QAbstractTableModel)` in `ui/models/table_models.py`.
        2.  Create `CustomerDialog(QDialog)` in `ui/dialogs/customer_dialog.py` for add/modify form.
        3.  Create `CustomersView(QWidget)` in `ui/views/customers_view.py` with table, search, buttons.
        4.  Implement view logic to call `CustomerService` methods.
        5.  Instantiate `CustomerService` in `main.py`.
        6.  Add `CustomersView` to `MainWindow`, passing the service, and add a toolbar action to navigate to it (e.g., repurpose F2 Credits).

*   **TASK-027: Feature - Customer Credits (Basic)**
    *   **Module:** Core, Infrastructure, UI
    *   **Status:** `[x]`
    *   **Description:** Add basic credit functionality: associate sales with customers, track customer balances, allow payments on account.
    *   **Tests (Write First - Red):**
        *   (Models) Test updates to `Sale` model (add `customer_id`), `Customer` model (add `credit_balance`, `credit_limit`). Test new `CreditPayment` model.
        *   (ORM) Verify Alembic migrations for schema changes.
        *   (Repositories) Test updating customer balance, adding credit payments. Test fetching sales for a customer.
        *   (Services) Test `SaleService` logic for assigning customer to sale and *not* requiring immediate payment (if sale is on credit). Test `CustomerService` logic for applying payments, checking credit limits.
        *   (Manual/Visual - UI) Verify ability to select a customer during sale (`SalesView`). Verify option for 'A Crédito' payment. Verify customer balance updates. Verify a way to register customer payments (e.g., in `CustomersView` or a dedicated payment dialog).
    *   **Implementation Steps:**
        1.  Update `Sale` model/ORM (add `customer_id`, `is_credit_sale` flag).
        2.  Update `Customer` model/ORM (add `credit_balance`, `credit_limit`).
        3.  Define `CreditPayment` model/ORM (customer_id, amount, timestamp, notes).
        4.  Update/Create Repositories (`ISaleRepository`, `ICustomerRepository`, `ICreditPaymentRepository`).
        5.  Update `SaleService`: Modify `create_sale` to handle optional `customer_id` and credit flag. If credit, don't expect full payment (logic depends on workflow). Update customer balance (or delegate to `CustomerService`).
        6.  Update `CustomerService`: Add `apply_payment` method (updates balance, logs `CreditPayment`). Add credit limit checks.
        7.  Update `SalesView`: Add `QComboBox` or search to select customer for the sale. Add payment options including 'A Crédito'.
        8.  Update `CustomersView` or create new UI to view balance and register payments.
        9.  Generate and apply migrations. Write tests.

*   **TASK-028: Feature - Purchases (Basic)**
    *   **Module:** Core, Infrastructure, UI
    *   **Status:** `[x]`
    *   **Description:** Implement basic purchase order tracking and receiving stock, which updates inventory and potentially product cost price.
    *   **Tests (Write First - Red):**
        *   (Models) Define `PurchaseOrder`, `PurchaseOrderItem`, `Supplier` models.
        *   (ORM) Verify migrations for new tables.
        *   (Repositories) Test CRUD for Suppliers, Purchase Orders, Items.
        *   (Services) Define `PurchaseService`. Test creating POs. Test `receive_purchase_order` logic: verifies items received against PO, calls `InventoryService.add_inventory` for each item (passing cost from PO), updates PO status.
        *   (Manual/Visual - UI) Verify 'Compras' action/view exists. Implement UI for managing Suppliers. Implement UI for creating POs. Implement UI for receiving stock against a PO.
    *   **Implementation Steps:**
        1.  Define Models (`Supplier`, `PurchaseOrder`, `PurchaseOrderItem`) in `core/models/`.
        2.  Define ORM mappings in `infrastructure/persistence/sqlite/models_mapping.py`.
        3.  Generate and apply migrations.
        4.  Define Repository Interfaces and Implementations (`ISupplierRepository`, `IPurchaseOrderRepository`).
        5.  Define and implement `PurchaseService` in `core/services/`.
        6.  Create UI Views/Dialogs (`SuppliersView`, `PurchaseOrderDialog`, `ReceiveStockDialog`) in `ui/`.
        7.  Add 'Compras' action and view to `MainWindow`. Write tests.

---

### Phase 6: Core POS Enhancements

*   **TASK-029: Enhance Sale Model & Logic for Payment Types & Users**
    *   **Module:** Core (Models), Infrastructure (Persistence), Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Update the Sale model to include payment type (Cash, Card, Credit, etc.) and the user who performed the sale. Update SaleService accordingly.
    *   **Tests (Write First - Red):**
        *   (Models) Test `Sale` model includes `payment_type: str`, `user_id: int` (or username). Test `User` model exists (basic ID, username).
        *   (ORM) Verify Alembic migration adds `payment_type`, `user_id` (FK to users table) columns to `sales` table. Verify `users` table migration.
        *   (Repositories) Test `SqliteSaleRepository` saves/retrieves these new fields. Test basic `SqliteUserRepository` (add, get_by_id, get_by_username).
        *   (Services) Test `SaleService.create_sale` accepts and stores `payment_type` and `user_id`. Test `UserService` (basic add/get user).
    *   **Implementation Steps:**
        1.  Define basic `dataclass User` and `UserOrm` (id, username, password_hash - basic for now). Add `users` table migration.
        2.  Add `payment_type: str`, `user_id: int` (nullable initially if login isn't ready) to `Sale` dataclass and `SaleOrm`. Add FK constraint in ORM. Generate/apply migration.
        3.  Define `IUserRepository` and implement `SqliteUserRepository`.
        4.  Define `UserService` (basic `add_user`, `get_user`, `authenticate_user`).
        5.  Update `SqliteSaleRepository` to handle the new fields.
        6.  Update `SaleService.create_sale` signature and logic to accept/store `payment_type` and `user_id`.
        7.  Write tests for models, repos, services.

*   **TASK-030: UI - Basic User Login**
    *   **Module:** UI (Dialogs), Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Implement a simple login dialog that appears on startup. Authenticate against stored users (initially, maybe just check username exists). Store the logged-in user globally or pass to main window.
    *   **Tests (Write First - Red):**
        *   (Service) Test `UserService.authenticate_user(username, password)` logic (initially simple, later hash comparison).
        *   (Manual/Visual - UI) Verify login dialog appears on startup. Verify entering credentials calls `UserService.authenticate_user`. Verify successful login closes dialog and proceeds to main window, storing username. Verify failed login shows an error message.
    *   **Implementation Steps:**
        1.  Create `ui/dialogs/login_dialog.py` (`QDialog`) with username/password fields (`QLineEdit`) and Login/Cancel buttons.
        2.  Implement dialog logic: On login click, get credentials, call `user_service.authenticate_user`. If successful, store user info (e.g., in a simple global variable or app context object) and `accept()` the dialog. If fail, show error.
        3.  Modify `main.py`: Before creating `MainWindow`, instantiate `UserService`, create/exec `LoginDialog`. If login fails, exit app. If successful, pass the logged-in user info to `MainWindow`.
        4.  Modify `MainWindow`: Accept user info, display username in toolbar label. Pass user info down to services/views where needed (e.g., `SaleService` needs user ID).

*   **TASK-031: UI - Sales View Payment Type Selection**
    *   **Module:** UI (Views)
    *   **Status:** `[x]`
    *   **Description:** Enhance the `SalesView` finalization step to allow selection of payment type (Cash, Card, etc.). Pass this to the `SaleService`.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual - UI) Verify that before finalizing, the user is prompted or selects a payment type (e.g., via buttons or a combo box). Verify the selected payment type is passed correctly when `SaleService.create_sale` is called.
    *   **Implementation Steps:**
        1.  Modify `SalesView.finalize_current_sale`.
        2.  Before calling `sale_service.create_sale`, add UI elements (e.g., `QInputDialog.getItem`, or dedicated buttons in the totals area) to select the payment type from a predefined list (`['Efectivo', 'Tarjeta', 'Crédito', 'Otro']`).
        3.  Pass the selected `payment_type` and the current `user_id` to `sale_service.create_sale`.

*   **TASK-032: Feature - Receipt PDF Generation**
    *   **Module:** Infrastructure (Reporting), Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Create logic using `reportlab` to generate a simple PDF receipt based on Sale data.
    *   **Tests (Write First - Red):**
        *   `test_receipt_data_formatting()`: Test helper functions that format sale/item data into strings suitable for the receipt.
        *   `test_generate_receipt_pdf()`: Given mock Sale data, verify a PDF file is created. Manually inspect the PDF for correct content (store info, items, total, date, sale ID). (Automated PDF content testing is complex).
    *   **Implementation Steps:**
        1.  Create `infrastructure/reporting/receipt_builder.py`.
        2.  Implement functions using `reportlab` (e.g., `Canvas`, `platypus Flowables`) to draw receipt content: Store Name (from config), Date, Sale ID, User, Sale Items (Code, Desc, Qty, Price, Subtotal), Total Amount, Payment Type.
        3.  Create a method in `SaleService` or a dedicated `ReportingService` called `generate_receipt_pdf(sale: Sale, filename: str)`. This method gathers data and calls the `receipt_builder`.
        4.  Write tests for formatting and basic PDF generation in `tests/infrastructure/reporting/`.

*   **TASK-033: UI - Print Receipt Action**
    *   **Module:** UI (Views), Infrastructure (Printing - Basic)
    *   **Status:** `[x]`
    *   **Description:** Add a button/action (e.g., after finalizing sale) to generate and print the receipt PDF. Initially, just generate the PDF and potentially open it. True printing is platform-dependent.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual - UI) Verify a 'Print Receipt' option appears after a successful sale. Verify clicking it calls the `generate_receipt_pdf` service method. Verify the PDF is saved and optionally opened using `os.startfile` (Windows) or equivalent.
    *   **Implementation Steps:**
        1.  In `SalesView.finalize_current_sale`, after a successful sale and clearing the view, potentially ask the user if they want to print a receipt (`ask_confirmation`).
        2.  If yes, call the `generate_receipt_pdf` service method, saving to a temporary file.
        3.  Use `os.startfile(filepath)` (Windows) or `subprocess.run(['xdg-open', filepath])` (Linux) or `subprocess.run(['open', filepath])` (macOS) to open the generated PDF with the default viewer (which usually allows printing).
        4.  (Future) Implement direct printing using libraries like `pycups` (Linux/macOS) or Windows API calls if needed.

---

### Phase 7: Invoicing, Corte, Advanced Reports

*   **TASK-034: Domain, ORM, Repo - Invoice**
    *   **Module:** Core (Models, Interfaces), Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Define `Invoice` model (linking to Sale, Customer), ORM mapping, `IInvoiceRepository`, and `SqliteInvoiceRepository`. Include fields relevant for Argentina (Invoice Number, Date, Customer CUIT/Name/Address, Condition IVA, Totals, potentially CAE/CAI placeholders).
    *   **Tests (Write First - Red):**
        *   Test `Invoice` dataclass creation.
        *   Verify Alembic migration for `invoices` table (with FKs to sales, customers).
        *   Test `SqliteInvoiceRepository` (add, get_by_id, get_by_sale_id, get_all).
    *   **Implementation Steps:**
        1.  Define `dataclass Invoice` in `core/models/invoice.py`. Include fields like `id`, `sale_id`, `customer_id`, `invoice_number`, `invoice_date`, `customer_details` (snapshot), `iva_condition`, `subtotal`, `iva_amount`, `total`, `cae`, `cae_due_date`.
        2.  Define `InvoiceOrm(Base)` in `models_mapping.py`.
        3.  Generate/apply migration (`Add invoice table`).
        4.  Define `IInvoiceRepository` interface.
        5.  Implement `SqliteInvoiceRepository`. Write tests.

*   **TASK-035: Service Layer - InvoicingService**
    *   **Module:** Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Implement `InvoicingService` to handle creation of invoices from sales data, manage invoice numbering.
    *   **Tests (Write First - Red):** (Mock Repos: Invoice, Sale, Customer, Config/Settings)
        *   `test_create_invoice_from_sale()`: Verify service fetches Sale and Customer data. Verify it generates a unique invoice number (simple sequential for now). Verify it correctly populates `Invoice` object fields (customer details snapshot, totals). Verify it calls `invoice_repo.add`. Test creating invoice for sale that already has one. Test creating invoice for non-existent sale.
        *   `test_get_next_invoice_number()`: Test logic for determining the next available number.
    *   **Implementation Steps:**
        1.  Create `core/services/invoicing_service.py`.
        2.  Define `InvoicingService` accepting `IInvoiceRepository`, `ISaleRepository`, `ICustomerRepository`, potentially a settings service/repo.
        3.  Implement `create_invoice_from_sale(sale_id: int)`. Fetch data, generate number, build `Invoice` object, save via repo.
        4.  Implement helper for invoice numbering (e.g., query max number from DB). Write tests.

*   **TASK-036: Infrastructure - Invoice PDF Generation (Argentina Focus)**
    *   **Module:** Infrastructure (Reporting)
    *   **Status:** `[x]`
    *   **Description:** Implement logic in `invoice_builder.py` using `reportlab` to generate a PDF visually resembling a basic Argentinian invoice (Factura A/B/C structure - choose one initially, e.g., B). Include store info, customer info (CUIT, IVA condition), invoice number, date, item details, totals.
    *   **Tests (Write First - Red):**
        *   `test_invoice_pdf_generation()`: Given mock Invoice data, verify PDF is created. Manually inspect PDF structure and content for key fields (Store CUIT, Customer CUIT, Invoice #, Items, Totals, IVA Condition text).
    *   **Implementation Steps:**
        1.  Create `infrastructure/reporting/invoice_builder.py`.
        2.  Use `reportlab` to structure the PDF layout (header, customer details, item table, totals, footer).
        3.  Fetch store details (Name, CUIT, Address, IVA Condition) from config/settings.
        4.  Populate PDF with data from the `Invoice` object.
        5.  Update `InvoicingService` or `ReportingService` to include `generate_invoice_pdf(invoice: Invoice, filename: str)` method calling the builder. Write tests in `tests/infrastructure/reporting/`.

*   **TASK-037: UI - Invoicing View & Actions**
    *   **Module:** UI (Views)
    *   **Status:** `[x]`
    *   **Description:** Create an 'Facturas' view to list generated invoices. Add an action (e.g., button in Sales View or Reports) to generate an invoice for a selected sale. Add action to view/reprint an invoice PDF.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual - UI) Verify 'Facturas' action/view exists. Verify view lists invoices (Number, Date, Customer, Total). Verify action exists to generate invoice for a sale (needs sale selection mechanism). Verify generating calls `InvoicingService.create_invoice_from_sale`. Verify action exists to view/print selected invoice PDF (calls `generate_invoice_pdf`).
    *   **Implementation Steps:**
        1.  Create `InvoiceTableModel` in `ui/models/table_models.py`.
        2.  Create `ui/views/invoices_view.py` with `QTableView` to list invoices. Add refresh logic calling `invoicing_service.get_all_invoices`.
        3.  Add 'Facturas' action/view to `MainWindow`.
        4.  Add a button/action (e.g., in `SalesView` context menu, or a dedicated "Invoice Sale" button after selection in a sales report) that: gets selected `sale_id`, calls `invoicing_service.create_invoice_from_sale`, handles success/error messages, potentially asks to view/print immediately.
        5.  Add a button/action in `InvoicesView` to view/print the selected invoice's PDF.

*   **TASK-038: Domain, ORM, Repo - Cash Drawer Entries**
    *   **Module:** Core (Models, Interfaces), Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Define model/ORM/Repo for tracking cash drawer events (Start of Day Balance, Cash Received (non-sale), Cash Paid Out).
    *   **Tests (Write First - Red):**
        *   Test `CashDrawerEntry` dataclass.
        *   Verify Alembic migration for `cash_drawer_entries` table.
        *   Test `SqliteCashDrawerRepository` (add, get_entries_for_period).
    *   **Implementation Steps:**
        1.  Define `dataclass CashDrawerEntry` (id, timestamp, entry_type ['START', 'IN', 'OUT'], amount, description, user_id).
        2.  Define `CashDrawerEntryOrm`. Generate/apply migration.
        3.  Define `ICashDrawerRepository` interface.
        4.  Implement `SqliteCashDrawerRepository`. Write tests.

*   **TASK-039: Service Layer - Corte Service Logic**
    *   **Module:** Core (Services)
    *   **Status:** `[x]`
    *   **Description:** Implement logic (likely in `ReportingService` or a new `CorteService`) to calculate the data needed for the 'Corte' report for a given period (e.g., today, specific shift).
    *   **Tests (Write First - Red):** (Mock Repos: Sale, CashDrawer)
        *   `test_calculate_corte_data()`: Given mock sales (with payment types) and cash drawer entries for a period, verify the service correctly calculates: Starting Balance (from last Corte or initial entry), Cash Sales Total, Card Sales Total, Credit Sales Total, Other Payment Total, Total Sales, Cash In (Manual Entries), Cash Out (Manual Entries), Expected Cash in Drawer.
    *   **Implementation Steps:**
        1.  Create/Enhance `ReportingService` (or `CorteService`). Inject `ISaleRepository`, `ICashDrawerRepository`.
        2.  Implement `calculate_corte_data(start_time, end_time)` method.
        3.  Query sales within the period, aggregate by `payment_type`.
        4.  Query `CashDrawerEntry` within the period. Find starting balance (needs logic - e.g., last 'START' entry before `start_time`). Sum 'IN' and 'OUT' entries.
        5.  Calculate all required totals. Return data in a structured format (e.g., a dictionary or dataclass). Write tests.

*   **TASK-040: UI - Corte View**
    *   **Module:** UI (Views)
    *   **Status:** `[x]`
    *   **Description:** Create the 'Corte' view to display the end-of-day/shift reconciliation report, matching the screenshot layout. Allow selecting the period (today, yesterday, custom range).
    *   **Tests (Write First - Red):**
        *   (Manual/Visual - UI) Verify 'Corte' action/view exists. Verify UI elements match screenshot (sections for Totals, Cash, Sales by Type, Entries, etc.). Verify selecting period triggers `calculate_corte_data` service call. Verify returned data populates the labels correctly. Add fields for 'Actual Cash Counted' and calculate difference. Add 'Hacer Corte del día' button (which might finalize the period, save the calculated state, and potentially log the starting balance for the *next* period).
    *   **Implementation Steps:**
        1.  Create `ui/views/corte_view.py`.
        2.  Design the layout using `QLabel`s, `QFrame`s, `QVBoxLayout`s, `QHBoxLayout`s to match the screenshot structure.
        3.  Add date selection widgets (`QDateEdit` or predefined buttons).
        4.  Implement `refresh_corte_report`: Get selected period, call `reporting_service.calculate_corte_data`, update all labels with results.
        5.  Add `QDoubleSpinBox` for user to enter actual counted cash. Add `QLabel` to show difference.
        6.  Implement logic for 'Hacer Corte' button (save results, potentially log next starting balance - requires more design).
        7.  Add 'Corte' action/view to `MainWindow`.

*   **TASK-041: Service Layer - Advanced Reporting Queries**
    *   **Module:** Core (Services), Infrastructure (Persistence)
    *   **Status:** `[x]`
    *   **Description:** Enhance repositories and services (`ReportingService`) to support aggregated queries needed for advanced reports (Sales per day/week/month, Sales per Department, Sales per Customer, Profit calculation).
    *   **Tests (Write First - Red):** (Mock/Test Repos, Test Service logic)
        *   Test repository methods using SQLAlchemy aggregation functions (`func.sum`, `func.count`, `group_by`, date functions).
        *   Test service methods correctly call repo methods and potentially format/process data for reporting (e.g., calculating profit = sell_price - cost_price at time of sale).
    *   **Implementation Steps:**
        1.  Enhance `ISaleRepository` with methods like `get_sales_summary_by_period(start, end)`, `get_sales_by_department(start, end)`, `get_sales_by_customer(start, end)`.
        2.  Implement these methods in `SqliteSaleRepository` using SQLAlchemy aggregation and grouping. Remember to join with `SaleItemOrm` and potentially `ProductOrm` (for cost price for profit).
        3.  Enhance `ReportingService` to orchestrate these calls and perform calculations like profit.

*   **TASK-042: UI - Advanced Reports View with Filters & Graphs**
    *   **Module:** UI (Views, Widgets)
    *   **Status:** `[x]`
    *   **Description:** Create/Enhance the 'Reportes' view with filters (Date Range, Department, Customer) and display aggregated data, including basic graphs (e.g., Sales per Day bar chart).
    *   **Tests (Write First - Red):**
        *   (Manual/Visual - UI) Verify 'Reportes' view exists. Verify filter widgets (Date Range, ComboBoxes for Dept/Customer). Verify applying filters triggers service calls and updates displayed data (tables/labels). Verify a basic graph (using `pyqtgraph` or `matplotlib`) displays sales trends.
    *   **Implementation Steps:**
        1.  Create `ui/views/reports_view.py` (or enhance existing).
        2.  Add filter widgets (e.g., `ui/widgets/DateRangeFilter.py`, `QComboBox` populated from services).
        3.  Add display areas (e.g., `QTableView` for detailed lists, `QLabel`s for summaries).
        4.  Integrate a graphing library: Add a widget placeholder (e.g., `pyqtgraph.PlotWidget`).
        5.  Implement `refresh_reports` method: Get filter values, call relevant `ReportingService` methods, update tables/labels, generate data series for the graph and update the plot widget.
        6.  Connect filter widget signals to `refresh_reports`.
        7.  Add 'Reportes' action/view to `MainWindow`.

---

### Phase 8: UI Polish & Final Touches

*   **TASK-043: UI - Icon Integration**
    *   **Module:** UI (Resources)
    *   **Status:** `[x]`
    *   **Description:** Find or create suitable icons and integrate them into toolbar actions and buttons throughout the application.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify icons appear next to toolbar actions and on relevant buttons (New, Modify, Delete, etc.).
    *   **Implementation Steps:**
        1.  Create `ui/resources/icons/` directory.
        2.  Source appropriate icons (e.g., from Fugue Icons, Font Awesome adapted, or custom). Ensure licensing allows usage.
        3.  Use `QIcon(":/icons/my_icon.png")` (requires Qt Resource File `.qrc`) or `QIcon("ui/resources/icons/my_icon.png")` (direct path) when creating `QAction`s and setting icons on `QPushButton`s.
        4.  (Optional) Create a `.qrc` file, compile it using `pyside6-rcc`, and import the resource module for cleaner icon handling.

*   **TASK-044: UI - Implement Specific Widgets (Filter Dropdowns)**
    *   **Module:** UI (Widgets, Views)
    *   **Status:** `[x]`
    *   **Description:** Replicate specific UI behaviors seen in screenshots, like the dropdown filters used in reports (e.g., "Mostrar ventas de: [Esta semana]", "De la Caja: [Caja Principal]").
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify dropdowns exist in relevant views (Reports, Corte). Verify they contain the expected options. Verify selecting an option triggers the appropriate filtering/refresh action.
    *   **Implementation Steps:**
        1.  Use `QComboBox` widgets in the relevant views (`CorteView`, `ReportsView`, `InventoryView` potentially).
        2.  Populate them with predefined options (e.g., "Hoy", "Ayer", "Esta Semana", "Mes Actual", "Elegir periodo...") or dynamic data (e.g., list of Cash Registers/Cajas if implemented).
        3.  Connect the `currentIndexChanged` or `currentTextChanged` signal to the view's refresh/filter logic, interpreting the selected option to set date ranges or other filter parameters.

*   **TASK-045: UI - Keyboard Shortcuts**
    *   **Module:** UI (MainWindow, Views)
    *   **Status:** `[x]`
    *   **Description:** Implement keyboard shortcuts for common actions (e.g., F1-F4 for main views, F12 for finalize sale, Enter key in specific fields).
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Verify pressing F1 switches to Sales view, F3 to Products, etc. Verify pressing F12 in Sales view triggers finalize sale. Verify pressing Enter in product code entry triggers add item.
    *   **Implementation Steps:**
        1.  For `QAction`s in `MainWindow` toolbar, use `action.setShortcut(QKeySequence("F1"))`.
        2.  For view-specific actions like F12 in `SalesView`, override the view's `keyPressEvent(event)` method, check `if event.key() == Qt.Key.Key_F12:`, and call the corresponding method (e.g., `self.finalize_current_sale()`).
        3.  For Enter key behavior in `QLineEdit`, connect the `returnPressed` signal (already done for product code entry in SalesView).

*   **TASK-046: UI - Layout Refinements & Visual Matching**
    *   **Module:** UI (Views, Dialogs)
    *   **Status:** `[x]`
    *   **Description:** Review application views and dialogs against the Eleventa screenshots and adjust layouts, spacing, widget sizes, fonts, and colors for a closer visual resemblance.
    *   **Tests (Write First - Red):**
        *   (Manual/Visual) Compare each implemented screen side-by-side with the corresponding screenshot. Identify discrepancies in layout, spacing, alignment, font sizes/weights, and colors.
    *   **Implementation Steps:**
        1.  Iterate through each View and Dialog (`.py` file).
        2.  Adjust layout managers (`QVBoxLayout`, `QHBoxLayout`, `QFormLayout`, `QGridLayout`).
        3.  Use `QSpacerItem`s and `addStretch()` for spacing control.
        4.  Set widget properties like `setSizePolicy`, `setMinimumWidth`, `setMaximumHeight`, etc.
        5.  Adjust fonts using `widget.setFont(QFont(...))`.
        6.  Apply basic styling using `widget.setStyleSheet("property: value;")` for colors or borders where needed (avoid complex stylesheets initially unless implementing a full theme).

*   **TASK-047: Configuration - Store Information**
    *   **Module:** Config, UI (ConfigurationView)
    *   **Status:** `[x]`
    *   **Description:** Implement storage and UI for basic store information (Name, Address, CUIT/ID, IVA Condition) needed for receipts and invoices.
    *   **Tests (Write First - Red):**
        *   Test loading/saving these specific settings via the config mechanism (file/DB).
        *   (Manual/Visual) Verify fields for store info exist in Configuration view. Verify saving updates the config. Verify this info appears correctly on generated receipts/invoices.
    *   **Implementation Steps:**
        1.  Add fields to config storage (JSON/INI/DB).
        2.  Implement load/save logic for these fields.
        3.  Add corresponding widgets (`QLineEdit`) to `ConfigurationView`.
        4.  Update `ReceiptBuilder` and `InvoiceBuilder` to load and display this information from config.

*   **TASK-048: Refactor & Code Cleanup**
    *   **Module:** Project Wide
    *   **Status:** `[x]`
    *   **Description:** Review the entire codebase for adherence to SOLID principles, DRY (Don't Repeat Yourself), and general Clean Code practices. Refactor where necessary. Ensure all tests pass after refactoring.
    *   **Tests (Write First - Red):**
        *   N/A (Relies on existing tests). Run the entire test suite.
    *   **Implementation Steps:**
        1.  Review services for single responsibility.
        2.  Review UI views for separation from business logic.
        3.  Look for duplicated code (e.g., UI table setup, validation logic) and extract into utility functions or base classes.
        4.  Ensure dependency injection is used consistently.
        5.  Improve variable/function naming. Add docstrings.

*   **TASK-049: Final Testing & Bug Fixing**
    *   **Module:** Project Wide
    *   **Status:** `[ ]`
    *   **Description:** Perform thorough manual testing of all features and workflows. Fix any identified bugs.
    *   **Tests (Write First - Red):**
        *   Run all automated tests.
        *   Define manual test cases covering all major user workflows (adding product, selling, adjusting inventory, generating reports, invoicing, corte, etc.).
    *   **Implementation Steps:**
        1.  Execute manual test cases.
        2.  Document any bugs found.
        3.  Fix bugs, adding new automated tests for regressions if applicable.
        4.  Repeat until major issues are resolved.

---

## Agent Instructions for TDD Workflow

1.  **Select Task:** Choose the next uncompleted task (`[ ]`) in a logical order (usually following dependencies).
2.  **Understand Tests:** Read the "Tests (Write First - Red)" section for the chosen task carefully.
3.  **Write Tests:** Implement these tests in the corresponding test file (e.g., `tests/core/services/test_product_service.py`). Use mocking (`unittest.mock` or `pytest-mock`) for dependencies (repositories when testing services, services when testing UI handlers conceptually). Run the tests; they should **fail** (Red).
4.  **Implement Code:** Write the application code described in the "Implementation Steps" section for the task. Focus *only* on making the tests you just wrote pass.
5.  **Run Tests:** Re-run the tests. They should now **pass** (Green).
6.  **Refactor (Optional):** If necessary, refactor the code you just wrote for clarity or efficiency, ensuring tests still pass.
7.  **Mark Complete:** Check the box for the task (`[x]`).
8.  **Commit:** Commit the changes to Git with a descriptive message referencing the task ID (e.g., `git commit -m "Feat(TASK-009): Implement ProductService logic and validation"`).
9.  **Repeat:** Go back to step 1 for the next task.

---

## Concluding Note

This expanded task list represents a comprehensive plan for building the core features and essential enhancements requested. It significantly increases the project's complexity compared to the initial scope. Development should remain iterative, focusing on completing one task (including its tests) before moving to the next. Remember that UI polish and exact visual matching often require significant iterative refinement.

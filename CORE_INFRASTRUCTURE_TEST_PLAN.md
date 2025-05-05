# Core & Infrastructure Test Plan

**Date:** 2025-04-21

## 1. Core Services

- [x] Write unit tests for all under‑covered services:
  - [x] `InvoicingService` (edge cases, error handling, concurrency)
  - [x] `ProductService` (CRUD, department management)
  - [x] `CustomerService` (add/update/delete, invalid input)
  - [x] Any other service below 80% coverage: `InventoryService`, `ReportingService`
- [x] Create `test_<service>_extra.py` files in `tests/core/services/` to simulate:
  - [x] Duplicate entries or race conditions via dummy repos
  - [x] Missing or invalid data
  - [x] Boundary values (e.g. zero amounts)

## 2. Repository Interfaces

- [ ] Add unit tests for repository logic:
  - [x] Invoice queries and pagination
  - [x] Credit payments repository (add/get/update)
  - [x] Customer query methods (search, filter)
  - [x] Department repository (add/get/update/delete)

## 3. Persistence Utilities & Database

- [ ] Cover `database.py`:
  - [ ] Connection open/close lifecycle
  - [ ] Migration helper functions
- [ ] Add tests for `database_operations.py`:
  - [ ] Custom type conversion (dates, decimal)
  - [ ] Transaction rollback on error

## 4. UI Non‑interactive Components

- [ ] Test all `TableModel` classes:
  - [ ] `rowCount()`, `columnCount()`, `data()` roles
  - [ ] Header data and alignment
- [ ] Test any pure‑logic dialog helpers:
  - [ ] Input validation functions
  - [ ] Formatting utilities (dates, currency)

## 5. UI Interactive Dialogs & Views

- [ ] Use `pytest-qt` (qtbot) to simulate signal/slot flows in dialogs:
  - [x] LoginDialog
    - [x] Test accept with valid credentials
    - [x] Test reject with invalid credentials
  - [x] ProductDialog
    - [x] Test add mode: fill fields and accept
    - [x] Test edit mode: load existing data and accept
  - [x] DepartmentDialog
    - [x] Test add mode: fill name and accept
    - [x] Test edit mode: load existing data and accept
  - [x] AddInventoryDialog
    - [x] Test fields presence and defaults
    - [x] Test valid addition and service call
    - [x] Test validation for non-positive quantity
  - [ ] Button clicks, field inputs, dialog acceptance/rejection
- [ ] Start with simplest dialogs (no external I/O):
  - [ ] Checkbox state changes
  - [ ] Text validators
  - [ ] Focus handling

## 6. UI Views & Screens

- [ ] Test main application views using pytest-qt:
  - [ ] ProductsView
    - [ ] Verify loading of products into table
    - [ ] Test filtering by department
    - [ ] Simulate 'Edit' action opens ProductDialog
    - [ ] Simulate 'Add' action opens ProductDialog
  - [ ] CustomersView
    - [ ] Verify loading of customers
    - [ ] Test search and filter functionality
  - [ ] SalesView
    - [ ] Verify loading of sales records
    - [ ] Test date range filter
  - [ ] CorteView (report generation)
    - [ ] Verify report UI renders correctly
    - [ ] Test export report functionality

## 7. Continuous Integration & Reporting

- [ ] Integrate `run_unified_tests.py` into CI pipeline (e.g., GitHub Actions)
- [ ] Publish coverage reports and HTML artifacts from CI runs
- [ ] Enforce minimum coverage thresholds (e.g., 80%) to fail builds

## 8. End-to-End Tests

- [x] Sales end-to-end flow: complete sale process and error handling (in `tests/integration/test_end_to_end_flows.py`)
- [x] Invoicing end-to-end flow: invoice generation from sale (in `tests/integration/test_end_to_end_flows.py`)
- [x] Concurrency scenarios: inventory updates during concurrent sales (in `tests/integration/test_end_to_end_flows.py`)
- [x] Simple product creation flow (in `tests/integration/test_end_to_end_flows.py`)

*This plan focuses on core & infrastructure testing first before moving to UI components.*

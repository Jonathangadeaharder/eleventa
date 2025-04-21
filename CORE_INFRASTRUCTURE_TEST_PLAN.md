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
  - [ ] Invoice queries and pagination
  - [ ] Credit payments repository (add/get/update)
  - [ ] Customer query methods (search, filter)

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
  - [ ] `LoginDialog`, `ProductDialog`, etc.
  - [ ] Button clicks, field inputs, dialog acceptance/rejection
- [ ] Start with simplest dialogs (no external I/O):
  - [ ] Checkbox state changes
  - [ ] Text validators
  - [ ] Focus handling

---
*This plan focuses on core & infrastructure testing first before moving to UI components.*

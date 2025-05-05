# Repository Fixes - Phase 2

## Overview

We've successfully fixed additional failing tests in two more repository test files:

1. `test_inventory_repository.py`
2. `test_user_repository.py`

## Issues Fixed

### 1. InventoryMovement Model Constructor

Fixed the `InventoryMovement` model by adding a constructor that accepts all parameters passed by the mapping function:

- Added `__init__` method accepting parameters like `product_id`, `user_id`, `timestamp`, etc.
- Allowed optional ID parameter to be passed through

### 2. User Model Improvements

Fixed the `User` model and its repository implementation:

- Added `password` property with getter/setter to handle plaintext passwords
- Added robust constructor accepting both `password` and `password_hash`
- Added `role` parameter handling (mapping to `is_admin`)
- Improved password hashing in repository with bcrypt

### 3. Password Hashing Implementation

Fixed the `SqliteUserRepository` to properly hash passwords:

- Added bcrypt hashing for plaintext passwords
- Modified repository to update domain model with the hashed password
- Fixed tests to verify proper bcrypt hashing

## Test Updates

1. Modified inventory repository tests to use the new constructor parameters
2. Updated user repository tests to verify proper password hashing
3. Fixed assertions to check for bcrypt hash patterns

## Remaining Issues

Several repository test files still have failures:

1. `test_sale_repository.py` - Issues with department and customer test fixtures
2. Database test files - Issues with table creation and test data

## Next Steps

1. Fix sale repository tests with properly isolated fixtures
2. Fix database test files, possibly updating the test database setup
3. Continue with remaining repository tests one by one

## Implementation Approach

The pattern for fixing these issues has been consistent:

1. Identify constructor parameter issues in model classes
2. Add proper constructors that accept all required parameters
3. Fix property handling for special cases (like passwords)
4. Update repository implementations to correctly transform data
5. Fix test assertions to verify proper behavior

Following these patterns will help resolve the remaining test failures. 
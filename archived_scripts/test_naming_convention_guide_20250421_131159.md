# Test Naming Convention Guide

This guide establishes consistent naming conventions for test files and functions within the project.

## Test Files

All test files should follow these conventions:

1. **Naming Pattern**: `test_<component_name>.py`
   - Always begin with `test_` prefix
   - Use the name of the module/component being tested
   - Use snake_case

2. **File Location**: Mirror the structure of the application
   - Place tests in a directory structure that matches the source code
   - Example: `core/models/user.py` → `tests/core/models/test_user.py`

## Test Functions

All test functions should follow these conventions:

1. **Naming Pattern**: `test_<functionality>_<scenario>_<expected_result>`
   - Always begin with `test_` prefix
   - Describe what is being tested, not how it's being tested
   - Focus on behavior, not implementation details
   - Clearly indicate the expected outcome
   - Use snake_case
   - Maximum length: 60 characters (for readability)

2. **Examples**:
   - `test_login_with_valid_credentials_succeeds`
   - `test_add_product_with_negative_price_raises_error`
   - `test_calculate_total_with_empty_cart_returns_zero`

3. **Avoid**:
   - Implementation details in names: `test_authenticate_method_calls_repo`
   - Vague names: `test_login_works`
   - Numbered test cases: `test_login_1`, `test_login_2`
   - Test prefixes in the name: `test_test_login`

## Parameters and Fixtures

1. **Fixture Names**: Should describe what they provide
   - `product_service` instead of `service`
   - `mock_user_repo` instead of `repo`

2. **Parametrized Tests**: Use clear parameter names
   - `@pytest.mark.parametrize("invalid_price, expected_error",...)`
   - Avoid generic names like `input` or `value`

## Test Class Names (If Using Classes)

If using test classes (though pytest style is preferred):

1. **Naming Pattern**: `Test<ComponentName>`
   - Use PascalCase
   - Begin with `Test` prefix
   - Do not include "Test" in the component name part
   - Example: `TestUserService` not `TestUserServiceTest`

## Consistency Exceptions

Some exceptions where different patterns are acceptable:

1. **Property-based tests**: May use `test_property_<description>`
2. **Integration tests**: May use `test_integration_<flows>`
3. **Performance tests**: May use `test_perf_<description>` 
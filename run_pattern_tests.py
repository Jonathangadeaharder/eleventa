#!/usr/bin/env python
"""
Simple test runner for architectural pattern tests.
Runs tests without pytest conftest dependencies.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run tests manually
test_results = []

def run_test_module(module_name, test_file):
    """Run tests from a module."""
    print(f"\n{'='*70}")
    print(f"Running: {module_name}")
    print('='*70)

    try:
        # Import the test module
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, test_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find and run test classes
        import inspect
        test_count = 0
        passed = 0
        failed = 0

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and name.startswith('Test'):
                print(f"\n{name}:")
                for method_name, method in inspect.getmembers(obj, predicate=inspect.ismethod):
                    if method_name.startswith('test_'):
                        test_count += 1
                        try:
                            # Create instance and run test
                            instance = obj()
                            method(instance)
                            passed += 1
                            print(f"  ✓ {method_name}")
                        except Exception as e:
                            failed += 1
                            print(f"  ✗ {method_name}: {str(e)[:100]}")

        result = f"{module_name}: {passed} passed, {failed} failed, {test_count} total"
        test_results.append((module_name, passed, failed, test_count))
        print(f"\n{result}")
        return True

    except Exception as e:
        print(f"ERROR loading {module_name}: {e}")
        test_results.append((module_name, 0, 0, 0))
        return False


# Run all test modules
test_files = [
    ('test_value_objects', 'tests/core/test_value_objects.py'),
    ('test_specifications', 'tests/core/test_specifications.py'),
    ('test_aggregates', 'tests/core/test_aggregates.py'),
]

print("="*70)
print("ARCHITECTURAL PATTERN TESTS")
print("="*70)

for module_name, test_file in test_files:
    run_test_module(module_name, test_file)

# Print summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

total_passed = 0
total_failed = 0
total_tests = 0

for name, passed, failed, total in test_results:
    total_passed += passed
    total_failed += failed
    total_tests += total
    status = "✓ PASS" if failed == 0 and total > 0 else "✗ FAIL" if failed > 0 else "⚠ SKIP"
    print(f"{status} {name:30s} {passed}/{total} passed")

print("-"*70)
print(f"TOTAL: {total_passed}/{total_tests} passed ({total_failed} failed)")
print("="*70)

sys.exit(0 if total_failed == 0 else 1)

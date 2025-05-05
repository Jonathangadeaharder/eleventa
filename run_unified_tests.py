#!/usr/bin/env python3
"""
Unified Test Runner for Eleventa Project

This script combines functionality from all test scripts into a single, flexible command-line tool.
It handles different test modes, proper Qt initialization, and provides detailed reporting.

Usage:
    python run_unified_tests.py                    # Run all tests with combined coverage report
    python run_unified_tests.py --no-gui           # Run non-GUI tests only
    python run_unified_tests.py --qt               # Run Qt tests only with proper setup
    python run_unified_tests.py --specific "path"  # Run specific test file or directory
    python run_unified_tests.py --integration      # Run only integration tests
    python run_unified_tests.py --unit             # Run only unit tests
    python run_unified_tests.py --coverage         # Generate coverage report
    python run_unified_tests.py --html-report      # Generate HTML coverage report
    python run_unified_tests.py --no-combined      # Disable combined coverage report (for specific test runs)
    python run_unified_tests.py --show-all-reports # Show individual coverage reports for each test run

Combines functionality from:
- run_all_tests.ps1
- run_qt_tests.py
- run_specific_test.py
- run_tests.py
"""

import os
import sys
import argparse
import subprocess
import platform
import tempfile
import shutil
import glob
import pytest # Import pytest
import time
import concurrent.futures # Import for parallel execution
from tqdm import tqdm # Import tqdm for progress bar
from colorama import Fore, Style, init as colorama_init # Import colorama for colored output

def set_qt_environment():
    """Set up the Qt environment for testing"""
    # Use offscreen platform during testing to avoid GUI-related crashes
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    
    # Add other Qt-specific environment variables if needed
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PySide6', 'plugins', 'platforms')
    
    # Disable QT warnings
    os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'
    
    # Add environmental variables to avoid potential race conditions in Qt tests
    os.environ['QT_FORCE_STDERR_LOGGING'] = '1'
    
    # Additional QPA settings to improve stability
    os.environ['QT_QPA_ENABLE_HIGHDPI_SCALING'] = '0'  # Disable high DPI scaling which can cause issues
    os.environ['QT_SCALE_FACTOR'] = '1'  # Force scaling factor to 1

def run_command(cmd, title=None, env=None, timeout=None, show_output=True):
    """Run a command, display its output, handle timeout, and optionally suppress output."""
    if title and show_output:
        print(f"\n{'-' * 80}\n{title}:\n{'-' * 80}")
    
    if show_output:
        print(f"Running: {cmd}")
        stdout_pipe = subprocess.PIPE
        stderr_pipe = subprocess.STDOUT
    else:
        # Capture output instead of displaying it live
        stdout_pipe = subprocess.PIPE
        stderr_pipe = subprocess.PIPE
        
    start_time = time.time()
    timed_out = False
    output_lines = []

    try:
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=stdout_pipe, 
            stderr=stderr_pipe,
            text=True,
            universal_newlines=True,
            env=env
        )
        
        if show_output:
            # Stream output line by line
            for line in iter(process.stdout.readline, ''):
                print(line.strip())
                output_lines.append(line) # Still capture for return if needed
            process.stdout.close()
            return_code = process.wait(timeout=timeout)
        else:
            # Capture all output after completion or timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
                if stdout:
                    output_lines.extend(stdout.splitlines())
                if stderr:
                    # If stderr wasn't redirected to stdout, capture it too
                    output_lines.extend(stderr.splitlines())
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate() # Drain pipes
                return_code = -1 # Indicate timeout
                timed_out = True
                output_lines.append(f"--- Command timed out after {timeout} seconds ---")
                if stdout:
                    output_lines.extend(stdout.splitlines())
                if stderr:
                    output_lines.extend(stderr.splitlines())

        success = return_code == 0
        elapsed = time.time() - start_time

        if show_output:
            status_msg = "timed out" if timed_out else ("succeeded" if success else "failed")
            print(f"\nCommand {status_msg} (rc={return_code}) in {elapsed:.2f}s")
        
        return success, timed_out, "\n".join(output_lines)

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Error executing command: {e}"
        if show_output:
            print(error_msg)
            print(f"\nCommand failed due to exception in {elapsed:.2f}s")
            
        output_lines.append(error_msg)
        return False, False, "\n".join(output_lines)

def _run_single_qt_test(test_file, args_list, env):
    """Helper function to run a single Qt test file, designed for parallel execution."""
    print(f"\nStarting Qt test file: {test_file}")
    
    # Ensure project root is in PYTHONPATH for the subprocess
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Assuming this script is in the root
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = project_root
        
    print(f"  [DEBUG] Setting PYTHONPATH for subprocess: {env.get('PYTHONPATH', 'Not Set')}") # Added debug print

    cmd = ["python", "-m", "pytest", test_file, "-v"]
    if args_list:
        cmd.extend(args_list)
    cmd_str = " ".join(cmd)
    
    # Use run_command which handles output streaming
    success, timed_out, output = run_command(cmd_str, title=f"Running Qt Test: {test_file}", env=env)
    return test_file, success, timed_out, output

def parse_arguments():
    """Parse command line arguments for the test runner"""
    parser = argparse.ArgumentParser(description="Unified Test Runner for Eleventa Project")
    # Group for test selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Run all tests")
    group.add_argument("--no-gui", action="store_true", help="Skip GUI tests")
    group.add_argument("--qt", action="store_true", help="Run only Qt-based tests")
    group.add_argument("--specific", type=str, help="Run a specific test file or directory")
    group.add_argument("--integration", action="store_true", help="Run integration tests")
    group.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--failfast", "-x", action="store_true", help="Stop on first failure")
    parser.add_argument(
        "-n", 
        dest='parallel', # Explicitly set destination attribute
        type=int, 
        help=f"Number of parallel processes. Defaults to half CPU cores ({os.cpu_count() // 2}). Uses all cores ({os.cpu_count()}) if flag is present without a number.",
        nargs='?', # Make the argument optional with an optional value
        const=os.cpu_count(), # Value if flag is present but no number is given
        default=max(1, os.cpu_count() // 2) # Default if flag is absent (ensure at least 1)
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=20, 
        help="Timeout in seconds for each individual test process (default: 20)"
    )

    args = parser.parse_args()
    
    # If no specific test type is selected, default to running all tests
    if not any([args.all, args.qt, args.specific, args.integration, args.unit, args.no_gui]):
        args.all = True
        
    return args

def create_coverage_config():
    """Create a coverage configuration file to suppress warnings and improve output"""
    # Create a coverage configuration file
    config_file = ".coveragerc"
    with open(config_file, "w") as f:
        f.write("""[run]
source = .
omit = 
    */site-packages/*
    */dist-packages/*
    */tests/*
    */.venv/*
    */venv/*
    setup.py
    
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError

[html]
directory = htmlcov
""")
    return config_file

def run_qt_tests(args_list=None, parallel_count=1):
    """
    Run all Qt tests individually using a process pool for parallel execution.
    Each test is run in its own process with proper Qt environment setup.
    """
    print("\n====== Running Qt UI Tests ======")

    # Set up environment for Qt tests
    env = os.environ.copy()
    env["PYTEST_QT_API"] = "pyside6"
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_SCALE_FACTOR"] = "1.0"  # Fix scaling issues

    # Prepare arguments list
    if args_list is None:
        args_list = []

    # Find all Qt test files in the tests/ui directory
    qt_test_files = []
    test_dir = "tests/ui"
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_file = os.path.join(root, file)
                qt_test_files.append(test_file)

    if not qt_test_files:
        print("No Qt test files found in the tests/ui directory.")
        return True  # No tests to run, so consider it a success

    num_tests = len(qt_test_files)
    print(f"Found {num_tests} Qt test files to run in parallel (max_workers={parallel_count})")

    # Track success/failure of all tests
    all_passed = True
    successful_tests = []
    failed_tests = []

    # Use ProcessPoolExecutor to run tests in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=parallel_count) as executor:
        # Submit all test runs to the executor
        future_to_test = {executor.submit(_run_single_qt_test, test_file, args_list, env): test_file for test_file in qt_test_files}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_test):
            test_file = future_to_test[future]
            try:
                _, success, timed_out, output = future.result() # Get the result tuple (test_file, success, timed_out, output)
                if success:
                    successful_tests.append(test_file)
                    print(f"✓ {test_file} PASSED")
                else:
                    failed_tests.append(test_file)
                    all_passed = False
                    print(f"✗ {test_file} FAILED")
            except Exception as exc:
                print(f'Test {test_file} generated an exception: {exc}')
                failed_tests.append(test_file)
                all_passed = False

    # Summary
    print("\n====== Qt Tests Summary ======")
    print(f"Total Qt test files: {num_tests}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed Qt test files:")
        for test in failed_tests:
            print(f"  - {test}")

    return all_passed

def run_test_with_isolation(test_id, args, show_output=True):
    """Run a single test in isolation to avoid issues with Qt event loop and resources"""
    print(f"Running in isolation: {test_id}")
    
    # Set up environment variables for Qt tests
    env = os.environ.copy()
    env["PYTEST_QT_API"] = "pyside6"
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_SCALE_FACTOR"] = "1.0"  # Fix scaling issues
    
    # Build the command
    cmd = ["python", "-m", "pytest", test_id, "-v"]
    if args:
        cmd.extend(args)
    
    # Run the test
    command_str = " ".join(cmd)
    return run_command(command_str, title=f"Test {test_id}", env=env, show_output=show_output)

def main():
    """Main entry point for the test runner"""
    # Clear terminal for better readability
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Create .coveragerc file if coverage is enabled
    if args.coverage:
        create_coverage_config()
    
    # Build base pytest arguments based on command line options
    pytest_args = []
    
    # Add coverage options if requested
    if args.coverage:
        pytest_args.extend(["--cov=eleventa", "--cov-report=term"])
        if args.html_report:
            pytest_args.append("--cov-report=html")
    
    # Add verbosity if requested
    if args.verbose:
        pytest_args.append("-v")
    
    # Add failfast if requested
    if args.failfast:
        pytest_args.append("-xvs")
    
    # Add parallel execution option if requested and > 1
    if args.parallel and args.parallel > 1:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # Determine which test sets to run
    unit_tests_enabled = args.all or args.unit
    integration_tests_enabled = args.all or args.integration
    qt_tests_enabled = args.all or args.qt
    specific_test = args.specific
    
    all_tests_passed = True
    
    if specific_test:
        # Run a specific test or test file
        print(f"Running specific test: {specific_test}")
        if specific_test.startswith("tests/ui/"):
            # Use special Qt runner for UI tests
            env = os.environ.copy()
            env["PYTEST_QT_API"] = "pyside6"
            env["QT_QPA_PLATFORM"] = "offscreen"
            env["QT_SCALE_FACTOR"] = "1.0"  # Fix scaling issues
            # Note: pytest-xdist is NOT applied to specific Qt tests due to potential environment conflicts
            test_success = run_command(f"python -m pytest {specific_test} {' '.join([arg for arg in pytest_args if arg != '-n' and arg != str(args.parallel)])}", 
                                      title=f"Specific test: {specific_test}", 
                                      env=env)
            all_tests_passed = all_tests_passed and test_success
        else:
            # Standard testing for non-Qt tests
            test_success = run_command(f"python -m pytest {specific_test} {' '.join(pytest_args)}", 
                                      title=f"Specific test: {specific_test}")
            all_tests_passed = all_tests_passed and test_success
    else:
        # Run test suites as requested
        
        # Unit tests
        if unit_tests_enabled:
            # Apply parallel option to unit tests
            unit_success = run_command(f"python -m pytest tests/unit {' '.join(pytest_args)}", 
                                      title="Running Unit Tests")
            all_tests_passed = all_tests_passed and unit_success
            print()  # Add space between test suites
        
        # Integration tests
        if integration_tests_enabled:
            # Apply parallel option to integration tests
            integration_success = run_command(f"python -m pytest tests/integration {' '.join(pytest_args)}",
                                            title="Running Integration Tests")
            all_tests_passed = all_tests_passed and integration_success
            print()  # Add space between test suites
        
        # Qt tests with parallel execution if requested
        if qt_tests_enabled and not args.no_gui:
            # Exclude xdist args (-n) but pass our parallel count
            qt_args = [arg for arg in pytest_args if not arg.startswith('-n') and not arg.isdigit()]
            qt_success = run_qt_tests(args_list=qt_args, parallel_count=args.parallel)
            all_tests_passed = all_tests_passed and qt_success
            print()  # Add space between test suites
    
    # Print summary of all test results
    print(f"\n{'-'*80}")
    if all_tests_passed:
        print("All requested tests passed successfully!")
    else:
        print("Some tests failed. See the above output for details.")
    print(f"{'-'*80}")
    
    # Return appropriate exit code
    sys.exit(0 if all_tests_passed else 1)

if __name__ == "__main__":
    # Ensure Qt environment is set early
    set_qt_environment() 
    sys.exit(main())

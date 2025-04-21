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

def set_qt_environment():
    """Set up the Qt environment for testing"""
    # Fix for "This plugin does not support propagateSizeHints()" warning on Windows
    if platform.system() == 'Windows':
        os.environ['QT_QPA_PLATFORM'] = 'windows:darkmode=0'
    
    # Add other Qt-specific environment variables if needed
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys.prefix, 'Lib', 'site-packages', 'PySide6', 'plugins', 'platforms')
    
    # Disable QT warnings
    os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.qpa.*=false'

def run_command(cmd, description, env=None, show_output=True):
    """Run a command and print its output"""
    if show_output:
        print(f"\n{'-'*80}\n{description}:\n{'-'*80}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, env=env, 
                               capture_output=not show_output)
        return True
    except subprocess.CalledProcessError as e:
        if show_output:
            print(f"Error running command: {e}")
        return False

def create_coverage_config():
    """Create a proper .coveragerc file with appropriate exclusions"""
    with open('.coveragerc', 'w') as f:
        f.write("[run]\n")
        f.write("source = .\n")
        f.write("parallel = True\n")
        f.write("data_file = .coverage\n")
        f.write("\n[report]\n")
        f.write("# Exclude patterns\n")
        f.write("exclude_lines =\n")
        f.write("    pragma: no cover\n")
        f.write("    def __repr__\n")
        f.write("    raise NotImplementedError\n")
        f.write("    pass\n")
        f.write("    raise ImportError\n")
        f.write("\n# Files to omit from reporting\n")
        f.write("omit =\n")
        f.write("    */site-packages/*\n")
        f.write("    */dist-packages/*\n")
        f.write("    */pyscript*\n")
        f.write("    */shibokensupport/*\n")
        f.write("    */signature_bootstrap.py\n")
        f.write("    */test_*.py\n")
        f.write("\n[paths]\n")
        f.write("source =\n")
        f.write("    .\n")
        f.write("\n[html]\n")
        f.write("directory = htmlcov\n")

def main():
    parser = argparse.ArgumentParser(description="Unified test runner for Eleventa")
    parser.add_argument("--no-gui", action="store_true", help="Run only non-GUI tests")
    parser.add_argument("--qt", action="store_true", help="Run only Qt-based tests")
    parser.add_argument("--specific", type=str, help="Run a specific test file or directory")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--no-combined", action="store_true", help="Disable combined coverage report")
    parser.add_argument("--show-all-reports", action="store_true", help="Show individual coverage reports for each test run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--failfast", "-x", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    # Set up Qt environment for all test types
    set_qt_environment()
    
    # Base pytest command
    pytest_cmd = "python -m pytest"
    
    # Add options
    if args.verbose:
        pytest_cmd += " -v"
    if args.failfast:
        pytest_cmd += " -x"
    
    # Determine if we should use combined reporting
    # Default to combined coverage when running all tests
    running_all_tests = not (args.no_gui or args.qt or args.specific or args.integration or args.unit)
    use_combined_report = running_all_tests and not args.no_combined
    
    # Set up coverage configuration to suppress warnings and improve output
    create_coverage_config()
    
    # Add coverage options if requested
    coverage_enabled = args.coverage or args.html_report or use_combined_report
    show_individual_reports = args.show_all_reports
    
    # Create base coverage directory
    if use_combined_report:
        # Use a fixed directory so we can clean up old files if needed
        cov_dir = os.path.join(os.getcwd(), ".coverage_data")
        if os.path.exists(cov_dir):
            # Clean up old coverage files
            for f in glob.glob(os.path.join(cov_dir, ".coverage.*")):
                os.remove(f)
        else:
            os.makedirs(cov_dir)
        print(f"Using coverage data directory: {cov_dir}")
    
    if coverage_enabled:
        pytest_cmd += " --cov=."
        # Additional options to suppress warnings
        pytest_cmd += " --no-cov-on-fail"
        
        if args.html_report and not use_combined_report:
            pytest_cmd += " --cov-report=html"
        elif not use_combined_report and not show_individual_reports:
            pytest_cmd += " --cov-report=term"
        else:
            # Suppress intermediate coverage reports
            pytest_cmd += " --cov-report="
    
    # Setup environment for coverage
    test_env = os.environ.copy()
    # Suppress coverage warnings
    test_env["PYTHONWARNINGS"] = "ignore::Warning"
    
    # Determine what to run based on arguments
    if args.specific:
        # Run a specific test file or directory
        target = args.specific
        if not os.path.exists(target):
            print(f"Error: '{target}' does not exist.")
            return 1
        
        cmd = f"{pytest_cmd} {target}"
        if use_combined_report:
            test_env["COVERAGE_FILE"] = os.path.join(cov_dir, ".coverage.specific")
            cmd += " --cov-report=" if not show_individual_reports else ""
        return 0 if run_command(cmd, f"Running specific tests in {target}", env=test_env) else 1
    
    elif args.qt:
        # Run Qt tests with proper setup
        cmd = f"{pytest_cmd} tests/test_cash_drawer_dialogs_copy.py ui/test_login.py ui/test_login_dialog.py"
        if use_combined_report:
            test_env["COVERAGE_FILE"] = os.path.join(cov_dir, ".coverage.qt")
            cmd += " --cov-report=" if not show_individual_reports else ""
        return 0 if run_command(cmd, "Running Qt-specific tests", env=test_env) else 1
    
    elif args.no_gui:
        # Run tests excluding GUI/Qt tests
        cmd = f"{pytest_cmd} tests/core tests/infrastructure"
        if use_combined_report:
            test_env["COVERAGE_FILE"] = os.path.join(cov_dir, ".coverage.nogui")
            cmd += " --cov-report=" if not show_individual_reports else ""
        return 0 if run_command(cmd, "Running non-GUI tests", env=test_env) else 1
    
    elif args.integration:
        # Run only integration tests
        cmd = f"{pytest_cmd} -m integration"
        if use_combined_report:
            test_env["COVERAGE_FILE"] = os.path.join(cov_dir, ".coverage.integration")
            cmd += " --cov-report=" if not show_individual_reports else ""
        return 0 if run_command(cmd, "Running integration tests", env=test_env) else 1
    
    elif args.unit:
        # Run only unit tests
        cmd = f"{pytest_cmd} -m 'not integration'"
        if use_combined_report:
            test_env["COVERAGE_FILE"] = os.path.join(cov_dir, ".coverage.unit")
            cmd += " --cov-report=" if not show_individual_reports else ""
        return 0 if run_command(cmd, "Running unit tests", env=test_env) else 1
    
    else:
        # Run all tests in the correct order to prevent Qt issues
        success = True
        
        # Setup environment to maintain coverage data between runs if needed
        if use_combined_report:
            if not os.path.exists(cov_dir):
                os.makedirs(cov_dir)
        
        # 1. Run unit tests first (non-GUI)
        unit_cmd = f"{pytest_cmd} tests/core tests/infrastructure"
        if use_combined_report:
            test_env["COVERAGE_FILE"] = os.path.join(cov_dir, ".coverage.core")
        success = run_command(unit_cmd, "Running core and infrastructure tests", env=test_env) and success
        
        # 2. Run integration tests
        integration_cmd = f"{pytest_cmd} integration"
        if use_combined_report:
            test_env["COVERAGE_FILE"] = os.path.join(cov_dir, ".coverage.integration")
        success = run_command(integration_cmd, "Running integration tests", env=test_env) and success
        
        # 3. Run Qt tests last (most likely to have issues)
        qt_cmd = f"{pytest_cmd} tests/test_cash_drawer_dialogs_copy.py ui/test_login.py ui/test_login_dialog.py"
        if use_combined_report:
            test_env["COVERAGE_FILE"] = os.path.join(cov_dir, ".coverage.gui")
        success = run_command(qt_cmd, "Running GUI tests", env=test_env) and success
        
        # If combining coverage, generate the combined report
        if use_combined_report and success:
            print("\n" + "-"*80)
            print("Generating combined coverage report:")
            print("-"*80)
            
            # Copy the .coveragerc to the coverage directory
            if os.path.exists('.coveragerc'):
                shutil.copy('.coveragerc', cov_dir)
            
            # Set working directory to coverage directory
            os.chdir(cov_dir)
            
            # Combine coverage data
            combine_success = run_command("coverage combine", "Combining coverage data")
            
            # Return to original directory
            os.chdir('..')
            
            if not combine_success:
                print("Failed to combine coverage data. Check if coverage files exist.")
                # Try with explicit file pattern
                coverage_files = glob.glob(os.path.join(cov_dir, ".coverage.*"))
                if coverage_files:
                    files_arg = " ".join(coverage_files)
                    combine_success = run_command(f"coverage combine {files_arg}", "Retrying with explicit files")
            
            if combine_success:
                # Copy the combined coverage file to the main directory
                if os.path.exists(os.path.join(cov_dir, ".coverage")):
                    shutil.copy(os.path.join(cov_dir, ".coverage"), ".coverage")
                
                # Generate reports
                if args.html_report:
                    run_command("coverage html", "Generating HTML coverage report")
                
                # Always show the text report for combined coverage
                print("\nGenerating coverage report. This may take a moment...")
                run_command("coverage report", "Combined coverage report")
            
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 
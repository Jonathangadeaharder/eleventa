#!/usr/bin/env python3
"""
Test runner script to separate UI tests from other tests.
"""
import os
import sys
import subprocess
import argparse

def run_command(cmd, title=None):
    """Run a command and display its output"""
    if title:
        print(f"\n{'-' * 80}\n{title}:\n{'-' * 80}")
    
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run tests excluding UI tests")
    parser.add_argument("--with-ui", action="store_true", help="Also run UI tests (may fail)")
    parser.add_argument("--only-ui", action="store_true", help="Run only UI tests")
    args = parser.parse_args()
    
    success = True
    
    if args.only_ui:
        # Run only UI tests
        print("\n--- Running UI tests only ---")
        success = run_command("pytest tests/ui", title="UI Tests")
    elif args.with_ui:
        # Run all tests
        print("\n--- Running all tests ---")
        success = run_command("pytest", title="All Tests")
    else:
        # Run non-UI tests only
        print("\n--- Running non-UI tests only ---")
        success = run_command("pytest -k \"not ui\"", title="Non-UI Tests")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
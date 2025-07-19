#!/usr/bin/env python3
"""
Qt Resource Compilation Script for Eleventa

This script compiles Qt resource files (.qrc) into Python modules (.py)
using pyside6-rcc, preparing the application for packaging with PyInstaller.

Usage:
    python scripts/compile_resources.py
    
The script will:
1. Locate all .qrc files in the project
2. Compile them using pyside6-rcc
3. Generate corresponding .py resource modules
4. Verify the compilation was successful
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def find_project_root():
    """Find the project root directory."""
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "main.py").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root")


def find_qrc_files(project_root):
    """Find all .qrc files in the project."""
    qrc_files = []
    for root, dirs, files in os.walk(project_root):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.qrc'):
                qrc_files.append(Path(root) / file)
    
    return qrc_files


def compile_qrc_file(qrc_path, output_path=None, verbose=False):
    """Compile a single .qrc file to a .py file using pyside6-rcc."""
    if output_path is None:
        output_path = qrc_path.with_suffix('.py')
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build the pyside6-rcc command
    cmd = [
        'pyside6-rcc',
        '-o', str(output_path),
        str(qrc_path)
    ]
    
    if verbose:
        print(f"Compiling: {qrc_path} -> {output_path}")
        print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=qrc_path.parent  # Run from the directory containing the .qrc file
        )
        
        if verbose and result.stdout:
            print(f"stdout: {result.stdout}")
        
        return True, None
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to compile {qrc_path}: {e.stderr}"
        return False, error_msg
    except FileNotFoundError:
        error_msg = "pyside6-rcc not found. Make sure PySide6 is installed and in PATH."
        return False, error_msg


def verify_compilation(py_path):
    """Verify that the compiled Python resource file is valid."""
    if not py_path.exists():
        return False, f"Output file {py_path} does not exist"
    
    try:
        # Try to read the file and check for expected content
        with open(py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for expected Qt resource signatures
        if 'qt_resource_data' not in content:
            return False, f"File {py_path} does not contain qt_resource_data"
        
        if 'from PySide6 import QtCore' not in content:
            return False, f"File {py_path} does not import QtCore"
        
        return True, None
        
    except Exception as e:
        return False, f"Error reading {py_path}: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Compile Qt resource files for Eleventa application"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check if resources need recompilation'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force recompilation even if .py files are newer'
    )
    
    args = parser.parse_args()
    
    try:
        project_root = find_project_root()
        if args.verbose:
            print(f"Project root: {project_root}")
        
        # Find all .qrc files
        qrc_files = find_qrc_files(project_root)
        
        if not qrc_files:
            print("No .qrc files found in the project.")
            return 0
        
        if args.verbose:
            print(f"Found {len(qrc_files)} .qrc file(s):")
            for qrc_file in qrc_files:
                print(f"  {qrc_file}")
        
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for qrc_file in qrc_files:
            output_file = qrc_file.with_suffix('.py')
            
            # Check if compilation is needed
            needs_compilation = args.force
            if not needs_compilation:
                if not output_file.exists():
                    needs_compilation = True
                elif qrc_file.stat().st_mtime > output_file.stat().st_mtime:
                    needs_compilation = True
            
            if args.check_only:
                if needs_compilation:
                    print(f"NEEDS COMPILATION: {qrc_file}")
                else:
                    print(f"UP TO DATE: {qrc_file}")
                continue
            
            if not needs_compilation:
                if args.verbose:
                    print(f"SKIPPING (up to date): {qrc_file}")
                skipped_count += 1
                continue
            
            # Compile the resource file
            success, error = compile_qrc_file(qrc_file, output_file, args.verbose)
            
            if success:
                # Verify the compilation
                verify_success, verify_error = verify_compilation(output_file)
                if verify_success:
                    print(f"✓ Successfully compiled: {qrc_file}")
                    success_count += 1
                else:
                    print(f"✗ Compilation succeeded but verification failed: {verify_error}")
                    error_count += 1
            else:
                print(f"✗ Failed to compile {qrc_file}: {error}")
                error_count += 1
        
        # Summary
        if not args.check_only:
            print(f"\nSummary:")
            print(f"  Successful: {success_count}")
            print(f"  Failed: {error_count}")
            print(f"  Skipped: {skipped_count}")
            print(f"  Total: {len(qrc_files)}")
        
        return 0 if error_count == 0 else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
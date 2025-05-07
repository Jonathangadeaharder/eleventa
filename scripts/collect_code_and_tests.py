#!/usr/bin/env python3
"""
Script to collect all relevant source code files, their content, and pytest results.
The output is copied to the clipboard for easy sharing with an LLM for analysis.

Usage:
    python collect_code_and_tests.py
    python collect_code_and_tests.py --skip-tests   # Skip running pytest
    python collect_code_and_tests.py --max-size 5   # Limit output to ~5MB
"""

import os
import sys
import argparse
import subprocess
import pyperclip
from tqdm import tqdm
from datetime import datetime

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Collect source code and test results for LLM analysis")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running pytest")
    parser.add_argument("--max-size", type=int, default=10, help="Maximum size of output in MB (default: 10)")
    return parser.parse_args()

def get_project_info():
    """
    Gather basic information about the project
    
    Returns:
        str: Summary of project information
    """
    # Count total Python files
    py_files = 0
    test_files = 0
    for root, _, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                if 'test_' in file or file.startswith('test_'):
                    test_files += 1
                else:
                    py_files += 1
    
    # Get top-level directories
    top_dirs = [d for d in next(os.walk('.'))[1] if not d.startswith('.') and d != 'venv']
    
    # Get Git information if available
    git_info = "Git information not available"
    try:
        result = subprocess.run(['git', 'log', '-1', '--pretty=format:%h - %an, %ar: %s'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            git_info = f"Latest commit: {result.stdout}"
    except:
        pass
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""
=== PROJECT SUMMARY ===
Timestamp: {timestamp}
Project structure: {', '.join(top_dirs)}
Python files: {py_files}
Test files: {test_files}
{git_info}
"""

def find_relevant_source_code():
    """
    Find all relevant source code files in the project directory.
    
    Returns:
        list: Paths to relevant source code files
    """
    relevant_files = []
    ignore_dirs = [
        'venv', '.venv', 'env', '.env', '__pycache__', 
        '.git', 'build', 'dist', '.pytest_cache', 'htmlcov',
        '.coverage_data'
    ]
    
    # File extensions to include
    include_extensions = [
        '.py',      # Python files
        '.json',    # JSON configuration files
        '.ini',     # INI configuration files
        '.md',      # Markdown documentation
        '.yaml',    # YAML files
        '.yml',     # YAML files
    ]
    
    # Files to explicitly include regardless of extension
    important_files = [
        'conftest.py',
        'pytest.ini',
        'alembic.ini',
        'config.py',
        'app_config.json',
        'README.md',
    ]
    
    print("Finding relevant source code files...")
    for root, dirs, files in os.walk('.'):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, '.')
            
            # Include based on extension
            _, ext = os.path.splitext(file)
            if ext in include_extensions:
                # Skip test files for Python (they'll be analyzed through pytest output)
                if ext == '.py' and ('test_' in file or file.startswith('test_')) and 'conftest.py' not in file:
                    continue
                relevant_files.append(rel_path)
            
            # Include important files regardless of extension
            elif file in important_files:
                relevant_files.append(rel_path)
    
    return sorted(relevant_files)  # Sort for consistent output

def read_file_content(file_path):
    """
    Read the content of a file.
    
    Args:
        file_path (str): Path to the file to read
        
    Returns:
        str: Content of the file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            # Try with a different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file with latin-1 encoding: {str(e)}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def run_pytest():
    """
    Run tests using run_unified_tests.py and capture the output.
    
    Returns:
        str: test output
    """
    print("Running tests using run_unified_tests.py...")
    try:
        # Run the unified test runner with verbose output
        result = subprocess.run(
            ['pytest', '-x', '--verbose'],
            capture_output=True,
            text=True,
            timeout=600  # 10-minute timeout (increased from 5 minutes)
        )
        return f"=== TEST OUTPUT ===\nExit code: {result.returncode}\n\n{result.stdout}\n\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "=== TEST OUTPUT ===\nTest execution timed out after 10 minutes."
    except Exception as e:
        return f"=== TEST OUTPUT ===\nError running tests: {str(e)}"

def get_project_structure():
    """
    Generate a tree-like representation of the project structure
    
    Returns:
        str: Tree-like structure of project directories
    """
    dirs_to_ignore = ['venv', '.venv', 'env', '.env', '__pycache__', '.git', 'build', 'dist', 
                      '.pytest_cache', 'htmlcov', '.coverage_data']
    
    output = ["=== PROJECT STRUCTURE ==="]
    
    def get_tree(directory, prefix=""):
        entries = sorted([entry for entry in os.listdir(directory) 
                         if os.path.isdir(os.path.join(directory, entry)) 
                         and not entry.startswith('.') 
                         and entry not in dirs_to_ignore])
        
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            output.append(f"{prefix}{'└── ' if is_last else '├── '}{entry}/")
            path = os.path.join(directory, entry)
            get_tree(path, prefix + ('    ' if is_last else '│   '))
    
    get_tree(".")
    return "\n".join(output)

def write_output_to_file(document, filename="codebase_and_tests.txt"):
    """Write the document to a file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(document)
        print(f"Output written to {filename}")
        return True
    except Exception as e:
        print(f"Error writing to file {filename}: {str(e)}")
        return False

def main():
    args = parse_arguments()
    
    # Start with project summary
    document = [get_project_info()]
    
    # Add project structure
    document.append(get_project_structure())
    document.append("\n" + "-" * 80 + "\n")
    
    # Find relevant source code files
    source_files = find_relevant_source_code()
    
    if not source_files:
        print("No relevant source code files found!")
        return
    
    print(f"Found {len(source_files)} relevant source code files.")
    
    # Add file section header
    document.append("=== PROJECT SOURCE CODE ===\n")
    
    # Track total size to avoid exceeding max size
    current_size = sum(len(section) for section in document)
    max_size = args.max_size * 1024 * 1024  # Convert MB to bytes
    
    # Read content of each file
    print(f"Reading file contents (limiting to ~{args.max_size}MB total)...")
    file_count = 0
    skipped_files = []
    
    for file_path in tqdm(source_files):
        # Read file content
        content = read_file_content(file_path)
        
        # Calculate new size after adding this file
        file_section = f"=== FILE: {file_path} ===\n{content}\n\n{'-' * 80}\n\n"
        new_size = current_size + len(file_section)
        
        # Check if we'd exceed max size
        if new_size > max_size:
            skipped_files.append(file_path)
            continue
        
        # Add file to document
        document.append(file_section)
        current_size = new_size
        file_count += 1
    
    print(f"Added {file_count} files to output, skipped {len(skipped_files)} due to size limit.")
    if skipped_files:
        skipped_files_list = '\n'.join(skipped_files[:10])
        if len(skipped_files) > 10:
            skipped_files_list += f"\n... and {len(skipped_files) - 10} more"
        document.append(f"=== SKIPPED FILES (due to size limit) ===\n{skipped_files_list}\n\n{'-' * 80}\n")
    
    # Run pytest unless skipped
    if not args.skip_tests:
        pytest_output = run_pytest()
        document.append(pytest_output)
    else:
        document.append("=== TEST OUTPUT ===\nSkipped running tests (--skip-tests flag was used)")
    
    # Combine all content
    full_document = "\n".join(document)
    
    # Copy to clipboard
    print("Copying document to clipboard...")
    try:
        pyperclip.copy(full_document)
        print("Done! Full document copied to clipboard.")
    except Exception as e:
        print(f"Error copying to clipboard: {str(e)}")
        write_output_to_file(full_document)
    
    print(f"Total document size: {len(full_document) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    main() 
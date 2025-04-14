import os
import sys
import pyperclip
from tqdm import tqdm

def collect_py_files(directory='.'):
    """
    Recursively collect all .py files from the given directory, ignoring venv folders
    
    Args:
        directory (str): The directory to search in. Defaults to current directory.
        
    Returns:
        list: List of paths to .py files
    """
    py_files = []
    # Folders to ignore (common virtual environment folder names)
    ignore_dirs = ['venv', 'env', '.venv', '.env', 'virtualenv', '.virtualenv', '__pycache__']
    
    print("Scanning directories for .py files...")
    
    # First, collect all directories to scan (excluding ignored ones)
    all_dirs = []
    for root, dirs, _ in os.walk(directory):
        # Remove ignored directories from dirs to prevent os.walk from traversing them
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        all_dirs.append(root)
    
    # Now scan for files with a progress bar
    for root in tqdm(all_dirs, desc="Scanning directories"):
        for file in os.listdir(root):
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path) and file.endswith('.py'):
                py_files.append(file_path)
                
    return py_files

def create_file_content_document(file_paths):
    """
    Create a document with sections for each file and its content
    
    Args:
        file_paths (list): List of file paths
        
    Returns:
        str: The formatted document
    """
    document = []
    
    print("Creating document from files...")
    for file_path in tqdm(file_paths, desc="Processing files"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Add file name as section title
            document.append(f"# {file_path}")
            document.append("")  # Empty line after title
            
            # Add file content
            document.append(content)
            
            # Add separator between files
            document.append("\n" + "-" * 80 + "\n")
        except Exception as e:
            document.append(f"# {file_path}")
            document.append("")
            document.append(f"Error reading file: {str(e)}")
            document.append("\n" + "-" * 80 + "\n")
    
    return "\n".join(document)

def main():
    # Get the directory from command line argument or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    print(f"Searching for Python files in: {os.path.abspath(directory)}")
    print(f"(Ignoring virtual environment folders)")
    
    # Collect all Python files
    py_files = collect_py_files(directory)
    
    if not py_files:
        print("No Python files found!")
        return
    
    print(f"Found {len(py_files)} Python files.")
    
    # Create the document
    document = create_file_content_document(py_files)
    
    print("Copying document to clipboard...")
    # Copy to clipboard
    pyperclip.copy(document)
    
    print("Document created and copied to clipboard!")
    print(f"Total document size: {len(document)} characters")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Application Packaging Preparation Script for Eleventa

This script prepares the Eleventa application for packaging with PyInstaller
by performing all necessary compilation and setup steps.

Usage:
    python scripts/prepare_for_packaging.py [options]
    
The script will:
1. Compile Qt resource files (.qrc -> .py)
2. Verify all dependencies are available
3. Check for missing files or resources
4. Prepare data directory structure
5. Generate packaging configuration hints
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import List, Dict, Tuple

# Import our resource compilation script
sys.path.insert(0, str(Path(__file__).parent))
from compile_resources import find_project_root, find_qrc_files, compile_qrc_file, verify_compilation


def check_dependencies():
    """Check if all required dependencies are installed."""
    # Map package names to their import names
    required_packages = {
        'PySide6': 'PySide6',
        'SQLAlchemy': 'sqlalchemy',
        'bcrypt': 'bcrypt',
        'alembic': 'alembic'
    }
    
    missing_packages = []
    installed_packages = {}
    
    for display_name, import_name in required_packages.items():
        try:
            result = subprocess.run(
                [sys.executable, '-c', f'import {import_name}; print({import_name}.__version__)'],
                capture_output=True,
                text=True,
                check=True
            )
            installed_packages[display_name] = result.stdout.strip()
        except (subprocess.CalledProcessError, ImportError):
            missing_packages.append(display_name)
    
    return installed_packages, missing_packages


def check_pyside6_tools():
    """Check if PySide6 tools are available."""
    tools = ['pyside6-rcc', 'pyside6-uic']
    available_tools = {}
    missing_tools = []
    
    for tool in tools:
        try:
            result = subprocess.run(
                [tool, '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            available_tools[tool] = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing_tools.append(tool)
    
    return available_tools, missing_tools


def find_data_files(project_root: Path) -> List[Tuple[str, List[str]]]:
    """Find data files that need to be included in the package."""
    data_files = []
    
    # Database migration files
    alembic_dir = project_root / 'alembic'
    if alembic_dir.exists():
        alembic_files = []
        for root, dirs, files in os.walk(alembic_dir):
            for file in files:
                if file.endswith(('.py', '.mako')):
                    rel_path = os.path.relpath(os.path.join(root, file), project_root)
                    alembic_files.append(rel_path)
        if alembic_files:
            data_files.append(('alembic', alembic_files))
    
    # Configuration files
    config_files = []
    for config_file in ['alembic.ini', 'app_config.json']:
        config_path = project_root / config_file
        if config_path.exists():
            config_files.append(str(config_path.relative_to(project_root)))
    if config_files:
        data_files.append(('config', config_files))
    
    # UI style files
    ui_dir = project_root / 'ui'
    if ui_dir.exists():
        style_files = []
        for style_file in ui_dir.rglob('*.qss'):
            rel_path = style_file.relative_to(project_root)
            style_files.append(str(rel_path))
        if style_files:
            data_files.append(('ui_styles', style_files))
    
    return data_files


def check_resource_imports(project_root: Path) -> List[str]:
    """Check for proper resource imports in Python files."""
    issues = []
    
    # Find Python files that might import resources
    python_files = list(project_root.rglob('*.py'))
    
    for py_file in python_files:
        if 'test' in str(py_file) or '__pycache__' in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for resource imports
            if 'import ui.resources' in content or 'from ui.resources import' in content:
                # This is good - explicit resource import
                continue
            elif 'QIcon(' in content and 'resources' not in content:
                # Potential issue - using QIcon without importing resources
                issues.append(f"{py_file}: Uses QIcon but may not import resources")
                
        except Exception as e:
            issues.append(f"{py_file}: Error reading file - {e}")
    
    return issues


def generate_pyinstaller_hints(project_root: Path, data_files: List[Tuple[str, List[str]]]) -> Dict:
    """Generate hints for PyInstaller configuration."""
    hints = {
        'hidden_imports': [
            'ui.resources.resources',
            'PySide6.QtCore',
            'PySide6.QtWidgets',
            'PySide6.QtGui',
            'SQLAlchemy',
            'alembic',
            'bcrypt'
        ],
        'datas': [],
        'binaries': [],
        'excludes': [
            'tkinter',
            'matplotlib',
            'numpy',
            'scipy'
        ]
    }
    
    # Add data files
    for category, files in data_files:
        for file_path in files:
            src = str(project_root / file_path)
            dst = os.path.dirname(file_path) or '.'
            hints['datas'].append((src, dst))
    
    # Add resource files specifically
    resource_dir = project_root / 'ui' / 'resources'
    if resource_dir.exists():
        # Include compiled resource files
        for py_file in resource_dir.glob('*.py'):
            if py_file.name != '__init__.py':
                hints['hidden_imports'].append(f'ui.resources.{py_file.stem}')
    
    return hints


def create_build_info(project_root: Path) -> Dict:
    """Create build information for debugging."""
    import datetime
    
    build_info = {
        'build_time': datetime.datetime.now().isoformat(),
        'python_version': sys.version,
        'platform': sys.platform,
        'project_root': str(project_root),
    }
    
    # Add git information if available
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0:
            build_info['git_commit'] = result.stdout.strip()
    except FileNotFoundError:
        pass
    
    return build_info


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Eleventa application for packaging"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--skip-resources',
        action='store_true',
        help='Skip Qt resource compilation'
    )
    parser.add_argument(
        '--output-hints',
        type=str,
        help='Output PyInstaller hints to specified file'
    )
    
    args = parser.parse_args()
    
    try:
        project_root = find_project_root()
        print(f"Preparing Eleventa application for packaging...")
        print(f"Project root: {project_root}")
        print()
        
        # Step 1: Check dependencies
        print("1. Checking dependencies...")
        installed_packages, missing_packages = check_dependencies()
        
        if missing_packages:
            print(f"   ✗ Missing packages: {', '.join(missing_packages)}")
            print("   Please install missing packages before packaging.")
            return 1
        else:
            print("   ✓ All required packages are installed")
            if args.verbose:
                for package, version in installed_packages.items():
                    print(f"     {package}: {version}")
        
        # Step 2: Check PySide6 tools
        print("\n2. Checking PySide6 tools...")
        available_tools, missing_tools = check_pyside6_tools()
        
        if missing_tools:
            print(f"   ✗ Missing tools: {', '.join(missing_tools)}")
            print("   Please ensure PySide6 tools are in PATH.")
            return 1
        else:
            print("   ✓ All required PySide6 tools are available")
            if args.verbose:
                for tool, version in available_tools.items():
                    print(f"     {tool}: {version}")
        
        # Step 3: Compile Qt resources
        if not args.skip_resources:
            print("\n3. Compiling Qt resources...")
            qrc_files = find_qrc_files(project_root)
            
            if not qrc_files:
                print("   ! No .qrc files found")
            else:
                success_count = 0
                for qrc_file in qrc_files:
                    output_file = qrc_file.with_suffix('.py')
                    success, error = compile_qrc_file(qrc_file, output_file, args.verbose)
                    
                    if success:
                        verify_success, verify_error = verify_compilation(output_file)
                        if verify_success:
                            print(f"   ✓ Compiled: {qrc_file.name}")
                            success_count += 1
                        else:
                            print(f"   ✗ Verification failed: {verify_error}")
                    else:
                        print(f"   ✗ Failed: {error}")
                
                if success_count == len(qrc_files):
                    print(f"   ✓ All {success_count} resource files compiled successfully")
                else:
                    print(f"   ✗ {len(qrc_files) - success_count} resource files failed to compile")
                    return 1
        
        # Step 4: Find data files
        print("\n4. Identifying data files...")
        data_files = find_data_files(project_root)
        
        if data_files:
            print(f"   ✓ Found {len(data_files)} data file categories")
            if args.verbose:
                for category, files in data_files:
                    print(f"     {category}: {len(files)} files")
        else:
            print("   ! No additional data files found")
        
        # Step 5: Check resource imports
        print("\n5. Checking resource imports...")
        import_issues = check_resource_imports(project_root)
        
        if import_issues:
            print(f"   ! Found {len(import_issues)} potential issues:")
            for issue in import_issues:
                print(f"     {issue}")
        else:
            print("   ✓ No resource import issues found")
        
        # Step 6: Generate PyInstaller hints
        print("\n6. Generating packaging hints...")
        hints = generate_pyinstaller_hints(project_root, data_files)
        build_info = create_build_info(project_root)
        
        packaging_config = {
            'pyinstaller_hints': hints,
            'build_info': build_info
        }
        
        if args.output_hints:
            output_path = Path(args.output_hints)
            with open(output_path, 'w') as f:
                json.dump(packaging_config, f, indent=2)
            print(f"   ✓ Packaging hints saved to: {output_path}")
        else:
            hints_file = project_root / 'packaging_hints.json'
            with open(hints_file, 'w') as f:
                json.dump(packaging_config, f, indent=2)
            print(f"   ✓ Packaging hints saved to: {hints_file}")
        
        print("\n✓ Application preparation completed successfully!")
        print("\nNext steps:")
        print("1. Review the generated packaging_hints.json file")
        print("2. Create a PyInstaller spec file using the hints")
        print("3. Run PyInstaller to create the executable")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
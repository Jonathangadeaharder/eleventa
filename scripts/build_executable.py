#!/usr/bin/env python3
"""
Build Script for Eleventa Application

This script automates the complete build process for creating a distributable
executable of the Eleventa application using PyInstaller.

Usage:
    python scripts/build_executable.py [options]
    
The script will:
1. Prepare the application for packaging (compile resources, check dependencies)
2. Run PyInstaller to create the executable
3. Verify the build was successful
4. Provide information about the created executable
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
import time

# Import our preparation script
sys.path.insert(0, str(Path(__file__).parent))
from prepare_for_packaging import find_project_root


def run_command(cmd, cwd=None, verbose=False):
    """Run a command and return success status and output."""
    if verbose:
        print(f"Running: {' '.join(cmd)}")
        if cwd:
            print(f"Working directory: {cwd}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        
        if verbose and result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        return True, result.stdout, None
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed with exit code {e.returncode}"
        if e.stderr:
            error_msg += f"\nSTDERR: {e.stderr}"
        if e.stdout:
            error_msg += f"\nSTDOUT: {e.stdout}"
        
        return False, e.stdout, error_msg
    except FileNotFoundError as e:
        return False, None, f"Command not found: {e}"


def check_pyinstaller():
    """Check if PyInstaller is available."""
    try:
        result = subprocess.run(
            ['pyinstaller', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, None


def clean_build_directories(project_root, verbose=False):
    """Clean previous build artifacts."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            if verbose:
                print(f"Removing: {dir_path}")
            shutil.rmtree(dir_path)
    
    # Also clean .pyc files
    for pyc_file in project_root.rglob('*.pyc'):
        if verbose:
            print(f"Removing: {pyc_file}")
        pyc_file.unlink()


def clean_dist_directory(project_root, verbose=False):
    """Clean only the dist directory to prevent PyInstaller conflicts."""
    dist_dir = project_root / 'dist'
    
    if dist_dir.exists():
        if verbose:
            print(f"Removing dist directory: {dist_dir}")
        shutil.rmtree(dist_dir)


def get_executable_info(project_root):
    """Get information about the created executable."""
    dist_dir = project_root / 'dist'
    
    if not dist_dir.exists():
        return None
    
    # Look for the executable
    exe_files = list(dist_dir.glob('*.exe'))
    if exe_files:
        exe_file = exe_files[0]
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        return {
            'path': exe_file,
            'size_mb': round(size_mb, 2),
            'exists': True
        }
    
    # Look for directory distribution
    app_dirs = [d for d in dist_dir.iterdir() if d.is_dir()]
    if app_dirs:
        app_dir = app_dirs[0]
        exe_file = app_dir / 'eleventa.exe'
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            return {
                'path': exe_file,
                'size_mb': round(size_mb, 2),
                'exists': True,
                'directory': app_dir
            }
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Build Eleventa application executable"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build directories before building'
    )
    parser.add_argument(
        '--skip-preparation',
        action='store_true',
        help='Skip the preparation step (assume already done)'
    )
    parser.add_argument(
        '--spec-file',
        type=str,
        default='eleventa.spec',
        help='PyInstaller spec file to use (default: eleventa.spec)'
    )
    parser.add_argument(
        '--console',
        action='store_true',
        help='Build with console window (useful for debugging)'
    )
    
    args = parser.parse_args()
    
    try:
        project_root = find_project_root()
        print(f"Building Eleventa application...")
        print(f"Project root: {project_root}")
        print()
        
        # Step 1: Check PyInstaller
        print("1. Checking PyInstaller...")
        pyinstaller_available, pyinstaller_version = check_pyinstaller()
        
        if not pyinstaller_available:
            print("   ✗ PyInstaller not found")
            print("   Please install PyInstaller: pip install pyinstaller")
            return 1
        else:
            print(f"   ✓ PyInstaller available: {pyinstaller_version}")
        
        # Step 2: Clean build directories
        if args.clean:
            print("\n2. Cleaning build directories...")
            clean_build_directories(project_root, args.verbose)
            print("   ✓ Build directories cleaned")
        else:
            print("\n2. Cleaning dist directory (preventing PyInstaller conflicts)...")
            clean_dist_directory(project_root, args.verbose)
            print("   ✓ Dist directory cleaned (use --clean to clean all build directories)")
        
        # Step 3: Prepare application
        if not args.skip_preparation:
            print("\n3. Preparing application for packaging...")
            
            prep_cmd = [sys.executable, 'scripts/prepare_for_packaging.py']
            if args.verbose:
                prep_cmd.append('--verbose')
            
            success, output, error = run_command(prep_cmd, cwd=project_root, verbose=args.verbose)
            
            if not success:
                print(f"   ✗ Preparation failed: {error}")
                return 1
            else:
                print("   ✓ Application prepared successfully")
        else:
            print("\n3. Skipping preparation (use --skip-preparation to skip)")
        
        # Step 4: Check spec file
        print("\n4. Checking spec file...")
        spec_file = project_root / args.spec_file
        
        if not spec_file.exists():
            print(f"   ✗ Spec file not found: {spec_file}")
            print("   Please create a spec file or use the default eleventa.spec")
            return 1
        else:
            print(f"   ✓ Using spec file: {spec_file}")
        
        # Step 5: Build with PyInstaller
        print("\n5. Building executable with PyInstaller...")
        
        build_cmd = ['pyinstaller']
        
        if args.console:
            # Modify spec file temporarily for console build
            print("   Note: Building with console window for debugging")
        
        build_cmd.append(str(spec_file))
        
        print(f"   Running PyInstaller...")
        start_time = time.time()
        
        success, output, error = run_command(build_cmd, cwd=project_root, verbose=args.verbose)
        
        build_time = time.time() - start_time
        
        if not success:
            print(f"   ✗ Build failed: {error}")
            return 1
        else:
            print(f"   ✓ Build completed in {build_time:.1f} seconds")
        
        # Step 6: Verify build
        print("\n6. Verifying build...")
        exe_info = get_executable_info(project_root)
        
        if not exe_info:
            print("   ✗ No executable found in dist directory")
            return 1
        else:
            print(f"   ✓ Executable created: {exe_info['path']}")
            print(f"   ✓ Size: {exe_info['size_mb']} MB")
            
            if 'directory' in exe_info:
                print(f"   ✓ Directory distribution: {exe_info['directory']}")
        
        # Step 7: Final summary
        print("\n" + "="*50)
        print("✓ BUILD SUCCESSFUL!")
        print("="*50)
        print(f"Executable: {exe_info['path']}")
        print(f"Size: {exe_info['size_mb']} MB")
        print(f"Build time: {build_time:.1f} seconds")
        print()
        print("Next steps:")
        print("1. Test the executable thoroughly")
        print("2. Check that all features work correctly")
        print("3. Verify database operations and file access")
        print("4. Test on a clean system without Python installed")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
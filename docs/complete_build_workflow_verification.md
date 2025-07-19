# Complete Build Workflow and Verification Guide for Eleventa

This document provides a comprehensive guide for the complete build workflow of the Eleventa application, including verification steps and troubleshooting.

## Overview

The Eleventa build process consists of three main stages:
1. **Resource Preparation**: Compile Qt resources (.qrc → .py)
2. **Application Freezing**: Create executable bundle with PyInstaller
3. **Installer Creation**: Generate setup.exe with Inno Setup

## Part I: Prerequisites and Environment Setup

### 1.1 Required Tools

- **Python 3.11+** with PySide6 installed
- **PyInstaller** for application packaging
- **Inno Setup Compiler** for installer creation
- **pyside6-rcc** (included with PySide6)

### 1.2 Verification Commands

```powershell
# Verify Python and PySide6
python --version
python -c "import PySide6; print(f'PySide6 version: {PySide6.__version__}')"

# Verify PyInstaller
pyinstaller --version

# Verify pyside6-rcc
pyside6-rcc --version

# Verify Inno Setup (check installation directory)
dir "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

## Part II: Step-by-Step Build Process

### 2.1 Stage 1: Resource Compilation

#### Manual Method
```powershell
# Navigate to project root
cd c:\Users\Jonandrop\Documents\eleventa

# Compile Qt resources
pyside6-rcc ui/resources/resources.qrc -o ui/resources/resources.py
```

#### Automated Method
```powershell
# Use the provided script
python scripts/compile_resources.py --verbose
```

#### Verification Steps
1. **Check output file exists**:
   ```powershell
   dir ui\resources\resources.py
   ```

2. **Verify file content**:
   ```powershell
   findstr "qt_resource_data" ui\resources\resources.py
   findstr "from PySide6 import QtCore" ui\resources\resources.py
   ```

3. **Test import**:
   ```powershell
   python -c "from ui.resources import resources; print('Resources imported successfully')"
   ```

### 2.2 Stage 2: Application Freezing

#### Manual Method
```powershell
# Run PyInstaller with spec file
pyinstaller eleventa.spec
```

#### Automated Method
```powershell
# Use the build script
python scripts/build_executable.py --verbose
```

#### Verification Steps
1. **Check build completion**:
   ```powershell
   dir dist\Eleventa
   dir dist\Eleventa\Eleventa.exe
   ```

2. **Verify executable size** (should be reasonable, typically 50-200MB):
   ```powershell
   powershell "Get-ChildItem 'dist\Eleventa\Eleventa.exe' | Select-Object Name, @{Name='SizeMB';Expression={[math]::Round($_.Length/1MB,2)}}"
   ```

3. **Test executable launch**:
   ```powershell
   # Quick test (should start without errors)
   dist\Eleventa\Eleventa.exe --help
   ```

4. **Check dependencies bundled**:
   ```powershell
   dir dist\Eleventa\*.dll
   dir dist\Eleventa\PySide6
   ```

### 2.3 Stage 3: Installer Creation

#### Manual Method
```powershell
# Compile with Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" Eleventa_setup.iss
```

#### Verification Steps
1. **Check installer creation**:
   ```powershell
   dir installer\Eleventa_Setup_v1.0.0.exe
   ```

2. **Verify installer size** (should include all application files):
   ```powershell
   powershell "Get-ChildItem 'installer\Eleventa_Setup_v1.0.0.exe' | Select-Object Name, @{Name='SizeMB';Expression={[math]::Round($_.Length/1MB,2)}}"
   ```

## Part III: Complete Automated Workflow

### 3.1 Full Build Script

Create a complete build script that runs all stages:

```powershell
# complete_build.ps1
Write-Host "Starting Eleventa complete build process..." -ForegroundColor Green

# Stage 1: Compile Resources
Write-Host "\n=== Stage 1: Compiling Resources ===" -ForegroundColor Yellow
python scripts/compile_resources.py --verbose
if ($LASTEXITCODE -ne 0) {
    Write-Host "Resource compilation failed!" -ForegroundColor Red
    exit 1
}

# Stage 2: Build Executable
Write-Host "\n=== Stage 2: Building Executable ===" -ForegroundColor Yellow
python scripts/build_executable.py --verbose --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "Executable build failed!" -ForegroundColor Red
    exit 1
}

# Stage 3: Create Installer
Write-Host "\n=== Stage 3: Creating Installer ===" -ForegroundColor Yellow
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" Eleventa_setup.iss
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installer creation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "\n=== Build Complete! ===" -ForegroundColor Green
Write-Host "Installer created: installer\Eleventa_Setup_v1.0.0.exe" -ForegroundColor Green
```

### 3.2 Consolidated Build Checklist

#### Pre-Build Checklist
- [ ] All dependencies installed (Python, PySide6, PyInstaller, Inno Setup)
- [ ] Project directory clean (no temporary files)
- [ ] All source code committed and saved
- [ ] Configuration files updated (app_config.json, etc.)

#### Build Process Checklist
- [ ] **Stage 1**: Resources compiled successfully
  - [ ] `ui/resources/resources.py` exists and contains expected content
  - [ ] No compilation errors in output
  - [ ] Resources can be imported in Python

- [ ] **Stage 2**: Executable created successfully
  - [ ] `dist/Eleventa/Eleventa.exe` exists
  - [ ] Executable size is reasonable (50-200MB)
  - [ ] All required DLLs and dependencies bundled
  - [ ] Application starts without immediate crashes

- [ ] **Stage 3**: Installer created successfully
  - [ ] `installer/Eleventa_Setup_v1.0.0.exe` exists
  - [ ] Installer size includes all application files
  - [ ] Installer can be run without errors

#### Post-Build Verification
- [ ] Test installation on clean system
- [ ] Verify application functionality after installation
- [ ] Check uninstaller works correctly
- [ ] Validate desktop shortcuts and start menu entries

## Part IV: Troubleshooting Common Issues

### 4.1 Resource Compilation Issues

**Problem**: `pyside6-rcc not found`
```powershell
# Solution: Ensure PySide6 is properly installed
pip install --upgrade PySide6
# Or reinstall if needed
pip uninstall PySide6
pip install PySide6
```

**Problem**: Resource file not found
```powershell
# Solution: Check file paths and working directory
dir ui\resources\resources.qrc
# Ensure running from project root
```

### 4.2 PyInstaller Issues

**Problem**: Missing modules in executable
```python
# Solution: Add to hiddenimports in eleventa.spec
hiddenimports=[
    'ui.resources.resources',
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    # Add any missing modules here
]
```

**Problem**: Executable too large
```python
# Solution: Add exclusions in eleventa.spec
excludes=[
    'tkinter',
    'matplotlib',
    'numpy',
    'scipy',
    # Add unnecessary modules here
]
```

### 4.3 Inno Setup Issues

**Problem**: Files not found during installer compilation
```ini
; Solution: Verify source paths in Eleventa_setup.iss
[Files]
Source: "dist\Eleventa\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
```

**Problem**: Installer requires admin privileges
```ini
; Solution: Adjust privileges in setup section
[Setup]
PrivilegesRequired=lowest  ; Change from 'admin' if not needed
```

## Part V: Advanced Verification

### 5.1 Automated Testing Script

```powershell
# test_build.ps1
Write-Host "Testing Eleventa build..." -ForegroundColor Green

# Test 1: Resource compilation
if (Test-Path "ui\resources\resources.py") {
    Write-Host "✓ Resources compiled" -ForegroundColor Green
} else {
    Write-Host "✗ Resources missing" -ForegroundColor Red
    exit 1
}

# Test 2: Executable exists
if (Test-Path "dist\Eleventa\Eleventa.exe") {
    Write-Host "✓ Executable created" -ForegroundColor Green
} else {
    Write-Host "✗ Executable missing" -ForegroundColor Red
    exit 1
}

# Test 3: Installer exists
if (Test-Path "installer\Eleventa_Setup_v1.0.0.exe") {
    Write-Host "✓ Installer created" -ForegroundColor Green
} else {
    Write-Host "✗ Installer missing" -ForegroundColor Red
    exit 1
}

Write-Host "All tests passed!" -ForegroundColor Green
```

### 5.2 File Integrity Verification

```powershell
# Check critical files are included in distribution
$criticalFiles = @(
    "dist\Eleventa\Eleventa.exe",
    "dist\Eleventa\alembic.ini",
    "dist\Eleventa\app_config.json",
    "dist\Eleventa\ui\style.qss"
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file" -ForegroundColor Red
    }
}
```

## Part VI: Performance and Optimization

### 6.1 Build Time Optimization

- Use `--skip-preparation` flag when resources haven't changed
- Implement incremental builds by checking file timestamps
- Use build caching for dependencies

### 6.2 Size Optimization

- Regularly review and update `excludes` list in spec file
- Use UPX compression (enabled in current spec)
- Remove unused resources and dependencies

### 6.3 Build Monitoring

```powershell
# Monitor build sizes over time
$buildInfo = @{
    'Date' = Get-Date -Format 'yyyy-MM-dd HH:mm'
    'ExeSize' = (Get-ChildItem 'dist\Eleventa\Eleventa.exe').Length / 1MB
    'InstallerSize' = (Get-ChildItem 'installer\Eleventa_Setup_v1.0.0.exe').Length / 1MB
}

$buildInfo | ConvertTo-Json | Out-File -Append build_history.json
```

## Conclusion

This comprehensive workflow ensures a reliable and repeatable build process for the Eleventa application. Following these verification steps helps catch issues early and maintains build quality across different environments.

For any issues not covered in this guide, check the individual script documentation in the `scripts/` directory or refer to the official documentation for PyInstaller and Inno Setup.
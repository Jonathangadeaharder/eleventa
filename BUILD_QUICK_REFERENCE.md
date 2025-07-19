# Eleventa Build Process - Quick Reference

## 🚀 One-Command Complete Build

```powershell
# Complete automated build (recommended)
.\scripts\complete_build.ps1 -Clean -Verbose

# Build without installer (if Inno Setup not available)
.\scripts\complete_build.ps1 -Clean -SkipInstaller

# Quick rebuild (skip resource compilation)
.\scripts\complete_build.ps1 -SkipResources
```

## 📋 Manual Step-by-Step Process

### Step 1: Compile Resources
```powershell
# Method 1: Direct command
pyside6-rcc ui/resources/resources.qrc -o ui/resources/resources.py

# Method 2: Using script
python scripts/compile_resources.py --verbose
```

### Step 2: Build Executable
```powershell
# Method 1: Direct PyInstaller
pyinstaller eleventa.spec

# Method 2: Using script
python scripts/build_executable.py --verbose --clean
```

### Step 3: Create Installer
```powershell
# Using Inno Setup Compiler
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" Eleventa_setup.iss
```

## ✅ Verification Commands

```powershell
# Quick verification
.\scripts\test_build.ps1

# Detailed verification with execution test
.\scripts\test_build.ps1 -Detailed -TestExecution

# Generate verification report
.\scripts\test_build.ps1 -Detailed -ExportReport
```

## 📁 Expected Output Files

- **Resources**: `ui/resources/resources.py`
- **Executable**: `dist/Eleventa/Eleventa.exe`
- **Installer**: `installer/Eleventa_Setup_v1.0.0.exe`

## 🔧 Prerequisites Check

```powershell
# Check all prerequisites
python --version
pyinstaller --version
pyside6-rcc --version
dir "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

## 🐛 Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|----------|
| `pyside6-rcc not found` | `pip install --upgrade PySide6` |
| `pyinstaller not found` | `pip install pyinstaller` |
| Resources not found | Run from project root directory |
| Executable too large | Review `excludes` in `eleventa.spec` |
| Missing dependencies | Add to `hiddenimports` in `eleventa.spec` |

## 📊 Build Size Guidelines

- **Resources**: ~50-500 KB
- **Executable**: ~50-200 MB
- **Installer**: ~60-250 MB

## 🔄 Development Workflow

```powershell
# During development (quick rebuild)
.\scripts\complete_build.ps1 -SkipInstaller

# Before release (full build with verification)
.\scripts\complete_build.ps1 -Clean -Verbose
.\scripts\test_build.ps1 -Detailed -ExportReport
```

## 📖 Detailed Documentation

For comprehensive information, see:
- `docs/complete_build_workflow_verification.md`
- `docs/qt_resource_compilation_guide.md`

---

**Last Updated**: $(Get-Date -Format 'yyyy-MM-dd')
**Build Scripts Location**: `scripts/`
**Configuration Files**: `eleventa.spec`, `Eleventa_setup.iss`
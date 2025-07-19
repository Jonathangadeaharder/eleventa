# Qt Resource Compilation Guide for Eleventa

This guide provides detailed instructions for compiling Qt resources and preparing the Eleventa application for packaging with PyInstaller.

## Overview

Qt resources (icons, stylesheets, etc.) defined in `.qrc` files must be compiled into Python modules before the application can be packaged. This process transforms external resource files into importable Python code that PyInstaller can automatically detect and bundle.

## Resource Structure

The Eleventa application uses the following resource structure:

```
ui/resources/
├── __init__.py              # Package initialization
├── resources.qrc            # Qt resource definition file
├── resources.py             # Compiled resource module (generated)
└── icons/                   # Icon files
    ├── sales.png
    ├── products.png
    ├── inventory.png
    └── ... (other icons)
```

## Resource Definition File (resources.qrc)

The `ui/resources/resources.qrc` file defines which resources should be compiled:

```xml
<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource prefix="/icons">
        <file>icons/sales.png</file>
        <file>icons/products.png</file>
        <file>icons/inventory.png</file>
        <!-- ... other icon files ... -->
    </qresource>
</RCC>
```

## Compilation Process

### Manual Compilation

To manually compile Qt resources using PySide6 tools:

```bash
# Navigate to the resources directory
cd ui/resources

# Compile the .qrc file to a .py file
pyside6-rcc -o resources.py resources.qrc
```

### Automated Compilation Scripts

Two scripts have been created to automate the compilation and preparation process:

#### 1. Resource Compilation Script

**File:** `scripts/compile_resources.py`

**Purpose:** Compiles all `.qrc` files in the project to Python modules.

**Usage:**
```bash
# Basic compilation
python scripts/compile_resources.py

# Verbose output
python scripts/compile_resources.py --verbose

# Force recompilation even if files are up to date
python scripts/compile_resources.py --force

# Check which files need compilation without compiling
python scripts/compile_resources.py --check-only
```

**Features:**
- Automatically finds all `.qrc` files in the project
- Only recompiles when source files are newer than compiled files
- Verifies compilation success
- Provides detailed error reporting

#### 2. Packaging Preparation Script

**File:** `scripts/prepare_for_packaging.py`

**Purpose:** Comprehensive preparation for PyInstaller packaging.

**Usage:**
```bash
# Full preparation with verbose output
python scripts/prepare_for_packaging.py --verbose

# Skip resource compilation (if already done)
python scripts/prepare_for_packaging.py --skip-resources

# Output packaging hints to custom file
python scripts/prepare_for_packaging.py --output-hints my_hints.json
```

**What it does:**
1. **Dependency Check:** Verifies all required packages are installed
2. **Tool Check:** Ensures PySide6 tools are available
3. **Resource Compilation:** Compiles Qt resources using the compilation script
4. **Data File Discovery:** Identifies additional files needed for packaging
5. **Import Analysis:** Checks for proper resource imports in Python files
6. **Hint Generation:** Creates PyInstaller configuration hints

## Using Compiled Resources

### Importing Resources

To use compiled resources in your Python code:

```python
# Import the compiled resources module
from ui.resources import resources

# Or import it directly
import ui.resources.resources

# Now you can use QIcon with resource paths
from PySide6.QtGui import QIcon
icon = QIcon(":/icons/sales.png")
```

### Resource Path Format

Resource paths use the Qt resource system format:
- Prefix: `:/icons/` (as defined in the .qrc file)
- File: `sales.png` (the actual filename)
- Full path: `:/icons/sales.png`

### Example Usage in Main Window

```python
from PySide6.QtWidgets import QMainWindow, QAction
from PySide6.QtGui import QIcon
from ui.resources import resources  # Import compiled resources

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create action with icon from resources
        sales_action = QAction(QIcon(":/icons/sales.png"), "Sales", self)
        
        # Add to toolbar
        toolbar = self.addToolBar("Main")
        toolbar.addAction(sales_action)
```

## Database Migration Integration

The application now includes automatic database migration support using Alembic. The `main.py` file has been updated to:

1. **Import migration modules**: Added imports for `alembic.config.Config` and `alembic.command`
2. **Import DATABASE_URL**: Uses the dynamically generated database URL from `config.py`
3. **Replace init_db() with run_migrations()**: The application now runs Alembic migrations instead of creating tables directly

### Migration Function

The `run_migrations()` function in `main.py`:
- Detects if running as a PyInstaller bundle (`sys.frozen`)
- Locates Alembic configuration and scripts in the appropriate directory
- Runs migrations programmatically using the dynamic database URL
- Handles errors gracefully and exits if migrations fail

### Key Benefits

- **Automatic schema updates**: Database schema is automatically updated on application startup
- **Version control**: Database changes are tracked through Alembic migration files
- **Deployment ready**: Works in both development and packaged environments
- **User data preservation**: Existing user data is preserved during schema updates

## Packaging with PyInstaller

### Generated Packaging Hints

The preparation script generates a `packaging_hints.json` file with PyInstaller configuration:

```json
{
  "pyinstaller_hints": {
    "hidden_imports": [
      "ui.resources.resources",
      "PySide6.QtCore",
      "PySide6.QtWidgets",
      "PySide6.QtGui"
    ],
    "datas": [
      ["path/to/alembic.ini", "."],
      ["path/to/app_config.json", "."]
    ],
    "excludes": [
      "tkinter",
      "matplotlib"
    ]
  }
}
```

### Creating a PyInstaller Spec File

Use the hints to create a PyInstaller spec file:

```python
# eleventa.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('alembic.ini', '.'),
        ('app_config.json', '.'),
        ('ui/style.qss', 'ui'),
    ],
    hiddenimports=[
        'ui.resources.resources',
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'sqlalchemy',
        'alembic',
        'bcrypt',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='eleventa',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

### Building the Executable

```bash
# Using the spec file
pyinstaller eleventa.spec

# Or using command line with hints
pyinstaller --onefile --windowed \
    --hidden-import ui.resources.resources \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtWidgets \
    --hidden-import PySide6.QtGui \
    --add-data "alembic.ini;." \
    --add-data "app_config.json;." \
    --exclude-module tkinter \
    main.py
```

## Troubleshooting

### Common Issues

1. **Missing Icons in Packaged Application**
   - Ensure resources are compiled before packaging
   - Verify resource imports in Python files
   - Check that `ui.resources.resources` is in hidden imports

2. **Resource Compilation Fails**
   - Verify PySide6 is installed: `pip install PySide6`
   - Check that `pyside6-rcc` is in PATH
   - Ensure all icon files referenced in .qrc exist

3. **Import Errors**
   - Make sure `ui/resources/__init__.py` exists
   - Verify the resources module is imported before using QIcon
   - Check Python path includes the project root

### Verification Steps

1. **Check Resource Compilation:**
   ```bash
   python scripts/compile_resources.py --check-only
   ```

2. **Verify Resource Import:**
   ```python
   python -c "from ui.resources import resources; print('Resources imported successfully')"
   ```

3. **Test Icon Loading:**
   ```python
   python -c "from PySide6.QtGui import QIcon; from ui.resources import resources; icon = QIcon(':/icons/sales.png'); print('Icon loaded:', not icon.isNull())"
   ```

## Best Practices

1. **Always compile resources before packaging**
2. **Import resources early in your application startup**
3. **Use the preparation script to verify everything is ready**
4. **Keep resource paths consistent with .qrc definitions**
5. **Test the packaged application thoroughly**

## Integration with Build Process

To integrate resource compilation into your build process:

1. **Add to requirements-dev.txt:**
   ```
   PySide6>=6.5.0
   ```

2. **Create a build script:**
   ```bash
   #!/bin/bash
   # build.sh
   
   echo "Preparing application for packaging..."
   python scripts/prepare_for_packaging.py --verbose
   
   echo "Creating PyInstaller package..."
   pyinstaller eleventa.spec
   
   echo "Build complete!"
   ```

3. **Add to CI/CD pipeline:**
   ```yaml
   # .github/workflows/build.yml
   - name: Prepare for packaging
     run: python scripts/prepare_for_packaging.py
   
   - name: Build executable
     run: pyinstaller eleventa.spec
   ```

This comprehensive approach ensures that Qt resources are properly compiled and the application is ready for distribution as a standalone executable.
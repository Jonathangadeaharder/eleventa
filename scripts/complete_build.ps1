#!/usr/bin/env powershell
<#
.SYNOPSIS
    Complete build script for Eleventa application

.DESCRIPTION
    This script automates the complete build process for the Eleventa application:
    1. Compiles Qt resources (.qrc -> .py)
    2. Creates executable bundle with PyInstaller
    3. Generates installer with Inno Setup

.PARAMETER Clean
    Clean build directories before building

.PARAMETER SkipResources
    Skip resource compilation (assume already done)

.PARAMETER SkipInstaller
    Skip installer creation (only build executable)

.PARAMETER Verbose
    Enable verbose output

.EXAMPLE
    .\scripts\complete_build.ps1
    
.EXAMPLE
    .\scripts\complete_build.ps1 -Clean -Verbose
    
.EXAMPLE
    .\scripts\complete_build.ps1 -SkipInstaller
#>

param(
    [switch]$Clean,
    [switch]$SkipResources,
    [switch]$SkipInstaller,
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if a command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to run a command and check result
function Invoke-BuildCommand {
    param(
        [string]$Command,
        [string]$Arguments = "",
        [string]$WorkingDirectory = $PWD,
        [string]$Description = "Running command"
    )
    
    Write-ColorOutput "  $Description..." "Cyan"
    
    if ($Verbose) {
        Write-ColorOutput "    Command: $Command $Arguments" "Gray"
        Write-ColorOutput "    Working Directory: $WorkingDirectory" "Gray"
    }
    
    try {
        if ($Arguments) {
            $result = Start-Process -FilePath $Command -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -Wait -PassThru -NoNewWindow
        } else {
            $result = Start-Process -FilePath $Command -WorkingDirectory $WorkingDirectory -Wait -PassThru -NoNewWindow
        }
        
        if ($result.ExitCode -eq 0) {
            Write-ColorOutput "    [OK] Success" "Green"
            return $true
        } else {
            Write-ColorOutput "    [FAIL] Failed with exit code: $($result.ExitCode)" "Red"
            return $false
        }
    }
    catch {
        Write-ColorOutput "    [FAIL] Error: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Main build process
try {
    Write-ColorOutput "\n=== Eleventa Complete Build Process ===" "Green"
    Write-ColorOutput "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Gray"
    
    # Check prerequisites
    Write-ColorOutput "\n=== Checking Prerequisites ===" "Yellow"
    
    $prerequisites = @(
        @{Name="Python"; Command="python"; Args="--version"},
        @{Name="PyInstaller"; Command="pyinstaller"; Args="--version"},
        @{Name="pyside6-rcc"; Command="pyside6-rcc"; Args="--version"}
    )
    
    foreach ($prereq in $prerequisites) {
        if (Test-Command $prereq.Command) {
            try {
                $version = & $prereq.Command $prereq.Args.Split(' ') 2>$null
                Write-ColorOutput "  [OK] $($prereq.Name): $($version -join ' ')" "Green"
            }
            catch {
                Write-ColorOutput "  [OK] $($prereq.Name): Available" "Green"
            }
        } else {
            Write-ColorOutput "  [FAIL] $($prereq.Name): Not found" "Red"
            throw "$($prereq.Name) is required but not found in PATH"
        }
    }
    
    # Check Inno Setup (optional for installer)
    $innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $innoSetupPath) {
        Write-ColorOutput "  [OK] Inno Setup: Available" "Green"
        $hasInnoSetup = $true
    } else {
        Write-ColorOutput "  [WARN] Inno Setup: Not found (installer creation will be skipped)" "Yellow"
        $hasInnoSetup = $false
        $SkipInstaller = $true
    }
    
    # Stage 1: Resource Compilation
    if (-not $SkipResources) {
        Write-ColorOutput "\n=== Stage 1: Compiling Resources ===" "Yellow"
        
        $resourceArgs = @("scripts\compile_resources.py")
        if ($Verbose) { $resourceArgs += "--verbose" }
        
        $success = Invoke-BuildCommand -Command "python" -Arguments ($resourceArgs -join " ") -Description "Compiling Qt resources"
        
        if (-not $success) {
            throw "Resource compilation failed"
        }
        
        # Verify resource compilation
        if (Test-Path "ui\resources\resources.py") {
            Write-ColorOutput "  [OK] Resources compiled successfully" "Green"
        } else {
            throw "Resource compilation completed but output file not found"
        }
    } else {
        Write-ColorOutput "\n=== Stage 1: Skipping Resource Compilation ===" "Yellow"
        Write-ColorOutput "  ⚠ Assuming resources are already compiled" "Yellow"
    }
    
    # Stage 2: Executable Building
    Write-ColorOutput "\n=== Stage 2: Building Executable ===" "Yellow"
    
    $buildArgs = @("scripts\build_executable.py")
    if ($Verbose) { $buildArgs += "--verbose" }
    if ($Clean) { $buildArgs += "--clean" }
    if ($SkipResources) { $buildArgs += "--skip-preparation" }
    
    $success = Invoke-BuildCommand -Command "python" -Arguments ($buildArgs -join " ") -Description "Building executable with PyInstaller"
    
    if (-not $success) {
        throw "Executable build failed"
    }
    
    # Verify executable creation
    $exePath = "dist\Eleventa\Eleventa.exe"
    if (Test-Path $exePath) {
        $exeSize = [math]::Round((Get-ChildItem $exePath).Length / 1MB, 2)
        Write-ColorOutput "  [OK] Executable created: $exeSize MB" "Green"
    } else {
        throw "Executable build completed but output file not found"
    }
    
    # Stage 3: Installer Creation
    if (-not $SkipInstaller -and $hasInnoSetup) {
        Write-ColorOutput "\n=== Stage 3: Creating Installer ===" "Yellow"
        
        $success = Invoke-BuildCommand -Command $innoSetupPath -Arguments "Eleventa_setup.iss" -Description "Creating installer with Inno Setup"
        
        if (-not $success) {
            throw "Installer creation failed"
        }
        
        # Verify installer creation
        $installerPath = "installer\Eleventa_Setup_v1.0.0.exe"
        if (Test-Path $installerPath) {
            $installerSize = [math]::Round((Get-ChildItem $installerPath).Length / 1MB, 2)
            Write-ColorOutput "  [OK] Installer created: $installerSize MB" "Green"
        } else {
            throw "Installer creation completed but output file not found"
        }
    } else {
        Write-ColorOutput "\n=== Stage 3: Skipping Installer Creation ===" "Yellow"
        if ($SkipInstaller) {
            Write-ColorOutput "  [WARN] Installer creation was skipped by request" "Yellow"
        } else {
            Write-ColorOutput "  [WARN] Inno Setup not available" "Yellow"
        }
    }
    
    # Build Summary
    Write-ColorOutput "\n=== Build Complete! ===" "Green"
    Write-ColorOutput "Completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Gray"
    
    Write-ColorOutput "\nBuild Artifacts:" "Cyan"
    
    if (Test-Path "ui\resources\resources.py") {
        Write-ColorOutput "  [OK] Compiled resources: ui\resources\resources.py" "Green"
    }
    
    if (Test-Path $exePath) {
        $exeSize = [math]::Round((Get-ChildItem $exePath).Length / 1MB, 2)
        Write-ColorOutput "  [OK] Executable: $exePath ($exeSize MB)" "Green"
    }
    
    $installerPath = "installer\Eleventa_Setup_v1.0.0.exe"
    if (Test-Path $installerPath) {
        $installerSize = [math]::Round((Get-ChildItem $installerPath).Length / 1MB, 2)
        Write-ColorOutput "  [OK] Installer: $installerPath ($installerSize MB)" "Green"
    }
    
    Write-ColorOutput "\nBuild completed successfully!" "Green"
    
}
catch {
    Write-ColorOutput "\n=== Build Failed! ===" "Red"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Failed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Gray"
    exit 1
}
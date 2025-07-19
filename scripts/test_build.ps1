#!/usr/bin/env powershell
<#
.SYNOPSIS
    Build verification script for Eleventa application

.DESCRIPTION
    This script performs comprehensive testing and verification of the Eleventa build process:
    1. Verifies all build artifacts exist
    2. Checks file integrity and sizes
    3. Tests basic functionality
    4. Validates installer components

.PARAMETER Detailed
    Perform detailed analysis of build artifacts

.PARAMETER TestExecution
    Test executable launch (may show GUI briefly)

.PARAMETER ExportReport
    Export verification report to file

.EXAMPLE
    .\scripts\test_build.ps1
    
.EXAMPLE
    .\scripts\test_build.ps1 -Detailed -ExportReport
    
.EXAMPLE
    .\scripts\test_build.ps1 -TestExecution
#>

param(
    [switch]$Detailed,
    [switch]$TestExecution,
    [switch]$ExportReport
)

# Set error action preference
$ErrorActionPreference = "Continue"

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to test file existence and get info
function Test-BuildArtifact {
    param(
        [string]$Path,
        [string]$Description,
        [int]$MinSizeKB = 0,
        [int]$MaxSizeMB = 1000
    )
    
    $result = @{
        Path = $Path
        Description = $Description
        Exists = $false
        SizeMB = 0
        Status = "FAIL"
        Message = ""
    }
    
    if (Test-Path $Path) {
        $file = Get-ChildItem $Path
        $sizeMB = [math]::Round($file.Length / 1MB, 2)
        $sizeKB = [math]::Round($file.Length / 1KB, 2)
        
        $result.Exists = $true
        $result.SizeMB = $sizeMB
        
        # Check size constraints
        if ($sizeKB -lt $MinSizeKB) {
            $result.Status = "WARN"
            $result.Message = "File too small ($sizeKB KB < $MinSizeKB KB)"
        } elseif ($sizeMB -gt $MaxSizeMB) {
            $result.Status = "WARN"
            $result.Message = "File too large ($sizeMB MB > $MaxSizeMB MB)"
        } else {
            $result.Status = "PASS"
            $result.Message = "$sizeMB MB"
        }
    } else {
        $result.Message = "File not found"
    }
    
    return $result
}

# Function to test Python import
function Test-PythonImport {
    param([string]$Module)
    
    try {
        $output = python -c "import $Module; print('OK')" 2>&1
        if ($output -match "OK") {
            return $true
        } else {
            return $false
        }
    }
    catch {
        return $false
    }
}

# Function to test executable
function Test-Executable {
    param([string]$ExePath)
    
    if (-not (Test-Path $ExePath)) {
        return @{Success = $false; Message = "Executable not found"}
    }
    
    try {
        # Test with --version flag (if supported)
        $process = Start-Process -FilePath $ExePath -ArgumentList "--version" -Wait -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
        
        if ($process.ExitCode -eq 0) {
            return @{Success = $true; Message = "Executable responds to --version"}
        } else {
            # Try basic launch test (quick exit)
            $process = Start-Process -FilePath $ExePath -Wait -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
            
            # If it doesn't crash immediately, consider it working
            if ($process.ExitCode -ne -1) {
                return @{Success = $true; Message = "Executable launches without immediate crash"}
            } else {
                return @{Success = $false; Message = "Executable crashes on launch"}
            }
        }
    }
    catch {
        return @{Success = $false; Message = "Error testing executable: $($_.Exception.Message)"}
    }
}

# Main verification process
try {
    Write-ColorOutput "\n=== Eleventa Build Verification ===" "Green"
    Write-ColorOutput "Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Gray"
    
    $verificationResults = @()
    $overallStatus = "PASS"
    
    # Test 1: Resource Compilation
    Write-ColorOutput "\n=== Test 1: Resource Compilation ===" "Yellow"
    
    $resourceTest = Test-BuildArtifact -Path "ui\resources\resources.py" -Description "Compiled Qt Resources" -MinSizeKB 10
    $verificationResults += $resourceTest
    
    if ($resourceTest.Status -eq "PASS") {
        Write-ColorOutput "  ✓ $($resourceTest.Description): $($resourceTest.Message)" "Green"
        
        # Test resource import
        if (Test-PythonImport "ui.resources.resources") {
            Write-ColorOutput "  ✓ Resources can be imported in Python" "Green"
        } else {
            Write-ColorOutput "  ✗ Resources cannot be imported in Python" "Red"
            $overallStatus = "FAIL"
        }
        
        # Check resource content
        if ($Detailed) {
            $content = Get-Content "ui\resources\resources.py" -Raw
            if ($content -match "qt_resource_data") {
                Write-ColorOutput "  ✓ Contains qt_resource_data" "Green"
            } else {
                Write-ColorOutput "  ✗ Missing qt_resource_data" "Red"
                $overallStatus = "FAIL"
            }
            
            if ($content -match "from PySide6 import QtCore") {
                Write-ColorOutput "  ✓ Contains PySide6 import" "Green"
            } else {
                Write-ColorOutput "  ✗ Missing PySide6 import" "Red"
                $overallStatus = "FAIL"
            }
        }
    } else {
        Write-ColorOutput "  ✗ $($resourceTest.Description): $($resourceTest.Message)" "Red"
        $overallStatus = "FAIL"
    }
    
    # Test 2: Executable Creation
    Write-ColorOutput "\n=== Test 2: Executable Creation ===" "Yellow"
    
    $exeTest = Test-BuildArtifact -Path "dist\Eleventa\Eleventa.exe" -Description "Main Executable" -MinSizeKB 10000 -MaxSizeMB 500
    $verificationResults += $exeTest
    
    if ($exeTest.Status -eq "PASS") {
        Write-ColorOutput "  ✓ $($exeTest.Description): $($exeTest.Message)" "Green"
        
        # Test executable functionality
        if ($TestExecution) {
            Write-ColorOutput "  Testing executable launch..." "Cyan"
            $execTest = Test-Executable -ExePath "dist\Eleventa\Eleventa.exe"
            
            if ($execTest.Success) {
                Write-ColorOutput "  ✓ $($execTest.Message)" "Green"
            } else {
                Write-ColorOutput "  ✗ $($execTest.Message)" "Red"
                $overallStatus = "FAIL"
            }
        }
        
        # Check critical dependencies
        if ($Detailed) {
            $criticalFiles = @(
                "dist\Eleventa\alembic.ini",
                "dist\Eleventa\app_config.json",
                "dist\Eleventa\ui\style.qss"
            )
            
            foreach ($file in $criticalFiles) {
                if (Test-Path $file) {
                    Write-ColorOutput "  ✓ Critical file: $file" "Green"
                } else {
                    Write-ColorOutput "  ✗ Missing critical file: $file" "Red"
                    $overallStatus = "FAIL"
                }
            }
            
            # Check for PySide6 dependencies
            if (Test-Path "dist\Eleventa\PySide6") {
                Write-ColorOutput "  ✓ PySide6 dependencies bundled" "Green"
            } else {
                Write-ColorOutput "  ✗ PySide6 dependencies missing" "Red"
                $overallStatus = "FAIL"
            }
        }
    } elseif ($exeTest.Status -eq "WARN") {
        Write-ColorOutput "  ⚠ $($exeTest.Description): $($exeTest.Message)" "Yellow"
        if ($overallStatus -eq "PASS") { $overallStatus = "WARN" }
    } else {
        Write-ColorOutput "  ✗ $($exeTest.Description): $($exeTest.Message)" "Red"
        $overallStatus = "FAIL"
    }
    
    # Test 3: Installer Creation
    Write-ColorOutput "\n=== Test 3: Installer Creation ===" "Yellow"
    
    $installerTest = Test-BuildArtifact -Path "installer\Eleventa_Setup_v1.0.0.exe" -Description "Setup Installer" -MinSizeKB 5000 -MaxSizeMB 1000
    $verificationResults += $installerTest
    
    if ($installerTest.Status -eq "PASS") {
        Write-ColorOutput "  ✓ $($installerTest.Description): $($installerTest.Message)" "Green"
    } elseif ($installerTest.Status -eq "WARN") {
        Write-ColorOutput "  ⚠ $($installerTest.Description): $($installerTest.Message)" "Yellow"
        if ($overallStatus -eq "PASS") { $overallStatus = "WARN" }
    } else {
        Write-ColorOutput "  ⚠ $($installerTest.Description): $($installerTest.Message) (Optional)" "Yellow"
        # Installer is optional, don't fail overall status
    }
    
    # Test 4: Build Consistency
    if ($Detailed) {
        Write-ColorOutput "\n=== Test 4: Build Consistency ===" "Yellow"
        
        # Check if spec file exists and is valid
        if (Test-Path "eleventa.spec") {
            Write-ColorOutput "  ✓ PyInstaller spec file exists" "Green"
        } else {
            Write-ColorOutput "  ✗ PyInstaller spec file missing" "Red"
            $overallStatus = "FAIL"
        }
        
        # Check if setup script exists
        if (Test-Path "Eleventa_setup.iss") {
            Write-ColorOutput "  ✓ Inno Setup script exists" "Green"
        } else {
            Write-ColorOutput "  ✗ Inno Setup script missing" "Red"
            $overallStatus = "FAIL"
        }
        
        # Check build scripts
        $buildScripts = @(
            "scripts\compile_resources.py",
            "scripts\build_executable.py",
            "scripts\complete_build.ps1"
        )
        
        foreach ($script in $buildScripts) {
            if (Test-Path $script) {
                Write-ColorOutput "  ✓ Build script: $script" "Green"
            } else {
                Write-ColorOutput "  ✗ Missing build script: $script" "Red"
                $overallStatus = "FAIL"
            }
        }
    }
    
    # Summary
    Write-ColorOutput "\n=== Verification Summary ===" "Cyan"
    
    $passCount = ($verificationResults | Where-Object { $_.Status -eq "PASS" }).Count
    $warnCount = ($verificationResults | Where-Object { $_.Status -eq "WARN" }).Count
    $failCount = ($verificationResults | Where-Object { $_.Status -eq "FAIL" }).Count
    
    Write-ColorOutput "Tests Passed: $passCount" "Green"
    if ($warnCount -gt 0) {
        Write-ColorOutput "Tests with Warnings: $warnCount" "Yellow"
    }
    if ($failCount -gt 0) {
        Write-ColorOutput "Tests Failed: $failCount" "Red"
    }
    
    # Overall result
    switch ($overallStatus) {
        "PASS" {
            Write-ColorOutput "\n✓ Overall Status: BUILD VERIFIED" "Green"
            $exitCode = 0
        }
        "WARN" {
            Write-ColorOutput "\n⚠ Overall Status: BUILD VERIFIED WITH WARNINGS" "Yellow"
            $exitCode = 0
        }
        "FAIL" {
            Write-ColorOutput "\n✗ Overall Status: BUILD VERIFICATION FAILED" "Red"
            $exitCode = 1
        }
    }
    
    # Export report if requested
    if ($ExportReport) {
        $reportPath = "build_verification_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        
        $report = @{
            Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
            OverallStatus = $overallStatus
            TestResults = $verificationResults
            Summary = @{
                Passed = $passCount
                Warnings = $warnCount
                Failed = $failCount
            }
        }
        
        $report | ConvertTo-Json -Depth 3 | Out-File -FilePath $reportPath -Encoding UTF8
        Write-ColorOutput "\nVerification report exported to: $reportPath" "Cyan"
    }
    
    Write-ColorOutput "\nVerification completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Gray"
    
    exit $exitCode
    
}
catch {
    Write-ColorOutput "\n=== Verification Error! ===" "Red"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    Write-ColorOutput "Failed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Gray"
    exit 1
}
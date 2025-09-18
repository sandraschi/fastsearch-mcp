# Build script for FastSearch MCP Installer
# Requires: Visual Studio 2022, WiX Toolset, CMake, Python 3.8+

param (
    [string]$Configuration = "Release",
    [string]$OutputDir = "installer",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$scriptPath = $PSScriptRoot
$solutionDir = "$scriptPath\"
$wixDir = "$scriptPath\wix"
$installerDir = "$solutionDir\$OutputDir"

# Create output directory if it doesn't exist
if (-not (Test-Path -Path $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir | Out-Null
}

# Build the project if not skipped
if (-not $SkipBuild) {
    Write-Host "Building FastSearch MCP in $Configuration mode..." -ForegroundColor Cyan
    
    # Build the C++ service
    Write-Host "Building C++ service..." -ForegroundColor Cyan
    $buildDir = "$solutionDir\service\build"
    
    if (-not (Test-Path -Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }
    
    Push-Location $buildDir
    
    # Configure CMake if needed
    if (-not (Test-Path -Path "CMakeCache.txt")) {
        cmake .. -G "Visual Studio 17 2022" -A x64
        if ($LASTEXITCODE -ne 0) {
            Write-Error "CMake configuration failed"
            exit $LASTEXITCODE
        }
    }
    
    # Build the project
    cmake --build . --config $Configuration
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit $LASTEXITCODE
    }
    
    Pop-Location
    
    # Verify C++ service binary exists
    $serviceExe = "$buildDir\bin\$Configuration\FastSearchServiceNew.exe"
    if (-not (Test-Path -Path $serviceExe)) {
        Write-Error "C++ service binary not found: $serviceExe"
        exit 1
    }
    
    Write-Host "✅ C++ service built successfully" -ForegroundColor Green
    
    # Verify Python MCP bridge files exist
    Write-Host "Verifying Python MCP bridge files..." -ForegroundColor Cyan
    $pythonFiles = @(
        "$solutionDir\src\fastsearch_mcp\server.py",
        "$solutionDir\src\fastsearch_mcp\__init__.py",
        "$solutionDir\src\fastsearch_mcp\service_client.py"
    )
    
    foreach ($file in $pythonFiles) {
        if (-not (Test-Path -Path $file)) {
            Write-Error "Required Python file not found: $file"
            exit 1
        }
    }
    
    Write-Host "✅ Python MCP bridge files verified" -ForegroundColor Green
    
    # Verify PowerShell scripts exist
    Write-Host "Verifying PowerShell management scripts..." -ForegroundColor Cyan
    $psFiles = @(
        "$solutionDir\install-service.ps1",
        "$solutionDir\fix-service.ps1",
        "$solutionDir\service-control.bat"
    )
    
    foreach ($file in $psFiles) {
        if (-not (Test-Path -Path $file)) {
            Write-Error "Required PowerShell script not found: $file"
            exit 1
        }
    }
    
    Write-Host "✅ PowerShell management scripts verified" -ForegroundColor Green
}

# Check for WiX Toolset
Write-Host "Checking for WiX Toolset..." -ForegroundColor Cyan
try {
    $wixVersion = & candle.exe -? 2>&1 | Select-String "WiX Toolset"
    if ($wixVersion) {
        Write-Host "✅ WiX Toolset found: $wixVersion" -ForegroundColor Green
    } else {
        Write-Error "WiX Toolset not found. Please install WiX Toolset v3.11 or later."
        exit 1
    }
} catch {
    Write-Error "WiX Toolset not found. Please install WiX Toolset v3.11 or later."
    exit 1
}

# Build the MSI installer
Write-Host "Building MSI installer..." -ForegroundColor Cyan
Push-Location $wixDir

# Compile WiX source files
$wixFiles = @("Product.wxs", "Bundle.wxs")
foreach ($wixFile in $wixFiles) {
    Write-Host "Compiling $wixFile..." -ForegroundColor Yellow
    & candle.exe "$wixFile" -dSolutionDir="$solutionDir" -dConfiguration="$Configuration"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to compile $wixFile"
        Pop-Location
        exit $LASTEXITCODE
    }
}

# Link the MSI
Write-Host "Linking MSI installer..." -ForegroundColor Yellow
& light.exe "Product.wixobj" -o "$installerDir\FastSearchMCP.msi" -ext WixUIExtension -ext WixUtilExtension
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to link MSI installer"
    Pop-Location
    exit $LASTEXITCODE
}

# Link the Bundle (EXE installer)
Write-Host "Linking Bundle installer..." -ForegroundColor Yellow
& light.exe "Bundle.wixobj" -o "$installerDir\FastSearchMCP.exe" -ext WixUIExtension -ext WixUtilExtension -ext WixBalExtension
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to link Bundle installer"
    Pop-Location
    exit $LASTEXITCODE
}

Pop-Location

# Verify installer files were created
$msiFile = "$installerDir\FastSearchMCP.msi"
$exeFile = "$installerDir\FastSearchMCP.exe"

if (Test-Path -Path $msiFile) {
    $msiSize = (Get-Item $msiFile).Length
    Write-Host "✅ MSI installer created: $msiFile ($([math]::Round($msiSize/1MB, 2)) MB)" -ForegroundColor Green
} else {
    Write-Error "MSI installer not created"
    exit 1
}

if (Test-Path -Path $exeFile) {
    $exeSize = (Get-Item $exeFile).Length
    Write-Host "✅ Bundle installer created: $exeFile ($([math]::Round($exeSize/1MB, 2)) MB)" -ForegroundColor Green
} else {
    Write-Error "Bundle installer not created"
    exit 1
}

Write-Host ""
Write-Host "🎉 FastSearch MCP Installer Build Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Installers created:"
Write-Host "  📦 MSI: $msiFile" -ForegroundColor Cyan
Write-Host "  📦 EXE: $exeFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "The EXE installer includes:"
Write-Host "  • Python 3.8+ Runtime (if needed)"
Write-Host "  • Visual C++ Redistributable"
Write-Host "  • FastSearch MCP Service (C++ + Python MCP Bridge)"
Write-Host "  • PowerShell Management Scripts"
Write-Host "  • Documentation"
Write-Host ""
Write-Host "Ready for distribution! 🚀" -ForegroundColor Green
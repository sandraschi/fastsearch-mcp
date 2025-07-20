# Build script for FastSearch MCP Installer
# Requires: Rust, WiX Toolset

param (
    [string]$Configuration = "Release",
    [string]$OutputDir = "installer",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$scriptPath = $PSScriptRoot
$solutionDir = "$scriptPath\"
$wixDir = "$scriptPath\wix"
$targetDir = "$solutionDir\target\$Configuration"
$installerDir = "$solutionDir\$OutputDir"

# Create output directory if it doesn't exist
if (-not (Test-Path -Path $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir | Out-Null
}

# Build the project if not skipped
if (-not $SkipBuild) {
    Write-Host "Building FastSearch MCP in $Configuration mode..." -ForegroundColor Cyan
    cargo build --$Configuration
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

# Verify WiX is installed
$wixPath = "C:\Program Files (x86)\WiX Toolset v3.11\bin"
if (-not (Test-Path -Path $wixPath)) {
    $wixPath = "C:\Program Files\WiX Toolset v3.11\bin"
}

if (-not (Test-Path -Path $wixPath)) {
    Write-Error "WiX Toolset not found. Please install WiX Toolset v3.11 or later."
    Write-Host "Download from: https://wixtoolset.org/releases/" -ForegroundColor Yellow
    exit 1
}

# Set environment variables
$env:Path = "$wixPath;$env:Path"
$env:SolutionDir = $solutionDir

# Compile the WiX source
Write-Host "Compiling installer..." -ForegroundColor Cyan
$wxsFile = "$wixDir\Product.wxs"
$wixobjFile = "$installerDir\FastSearchMCP.wixobj"
$msiFile = "$installerDir\FastSearchMCP.msi"

# Compile WiX source
candle.exe -nologo -out "$wixobjFile" "$wxsFile"
if ($LASTEXITCODE -ne 0) {
    Write-Error "WiX compilation failed"
    exit $LASTEXITCODE
}

# Link the MSI
light.exe -nologo -out "$msiFile" "$wixobjFile" -ext WixUIExtension
if ($LASTEXITCODE -ne 0) {
    Write-Error "MSI linking failed"
    exit $LASTEXITCODE
}

# Create a bootstrapper (optional, requires WiX Bal extension)
$bundleWxs = "$wixDir\Bundle.wxs"
if (Test-Path $bundleWxs) {
    Write-Host "Creating bootstrapper..." -ForegroundColor Cyan
    $bundleObj = "$installerDir\Bundle.wixobj"
    $bundleExe = "$installerDir\FastSearchMCP-Setup.exe"
    
    candle.exe -nologo -out "$bundleObj" "$bundleWxs"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Bootstrapper compilation failed"
        exit $LASTEXITCODE
    }
    
    light.exe -nologo -out "$bundleExe" "$bundleObj" -ext WixBalExtension -ext WixUIExtension
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Bootstrapper linking failed"
        exit $LASTEXITCODE
    }
}

Write-Host "`nInstallation package created successfully!" -ForegroundColor Green
Write-Host "MSI Installer: $msiFile" -ForegroundColor Yellow
if (Test-Path $bundleExe) {
    Write-Host "Bootstrapper: $bundleExe" -ForegroundColor Yellow
}

# Open the output directory
explorer $installerDir

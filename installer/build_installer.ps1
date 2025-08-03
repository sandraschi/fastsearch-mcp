# Build script for FastSearch MCP Service Installer
# Requires WiX Toolset to be installed

param (
    [string]$Configuration = "Release",
    [string]$Platform = "x64",
    [string]$OutputDir = "$PSScriptRoot\..\dist"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Create output directory if it doesn't exist
if (-not (Test-Path -Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Build the service
Write-Host "Building FastSearch MCP Service..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\..\service"
$buildOutput = cargo build --release 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed with errors:" -ForegroundColor Red
    $buildOutput | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    exit 1
}

# Verify the service binary was built
$serviceBinary = "$PSScriptRoot\..\service\target\release\fastsearch-service.exe"
if (-not (Test-Path -Path $serviceBinary)) {
    Write-Host "Error: Service binary not found at $serviceBinary" -ForegroundColor Red
    exit 1
}

# Set WiX environment variables if not already set
$env:WIX = "C:\Program Files (x86)\WiX Toolset v3.11"
if (-not (Test-Path -Path $env:WIX)) {
    $env:WIX = "C:\Program Files\WiX Toolset v3.11"
}

if (-not (Test-Path -Path $env:WIX)) {
    Write-Host "Error: WiX Toolset not found. Please install WiX Toolset v3.11 or later." -ForegroundColor Red
    exit 1
}

# Create a temporary directory for the installer files
$tempDir = "$env:TEMP\FastSearchMCP-Installer"
if (Test-Path -Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force | Out-Null
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy the service binary to the temp directory
Copy-Item -Path $serviceBinary -Destination $tempDir\fastsearch-service.exe

# Compile the WiX source files
Write-Host "Compiling installer..." -ForegroundColor Cyan
$wxsFile = "$PSScriptRoot\Product.wxs"
$wixobjFile = "$tempDir\FastSearchMCP.wixobj"
$msiFile = "$OutputDir\FastSearchMCP-Setup.msi"

# Run candle.exe to compile the WiX source
& "$env:WIX\bin\candle.exe" -nologo "-dSourceDir=$tempDir" "-dConfiguration=$Configuration" "-dPlatform=$Platform" -out "$wixobjFile" "$wxsFile"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to compile WiX source files" -ForegroundColor Red
    exit 1
}

# Run light.exe to link the installer
& "$env:WIX\bin\light.exe" -nologo -ext WixUIExtension -ext WixUtilExtension -out "$msiFile" "$wixobjFile"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to link the MSI package" -ForegroundColor Red
    exit 1
}

# Clean up
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "`nInstaller created successfully at: $msiFile" -ForegroundColor Green
Write-Host "`nTo install the service, run the MSI as Administrator." -ForegroundColor Cyan

# Build script for FastSearch MCP Service Executable

# Set error action preference
$ErrorActionPreference = "Stop"

# Check if PyInstaller is installed
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Cyan
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install PyInstaller"
        exit 1
    }
}

# Create output directory
$outputDir = "$PSScriptRoot\dist"
if (-not (Test-Path -Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Build the service executable
Write-Host "Building FastSearch MCP Service executable..." -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot

# Run PyInstaller with the spec file
pyinstaller --clean --noconfirm build_service.spec

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build service executable"
    exit 1
}

# Verify the executable was created
$serviceExe = "$PSScriptRoot\dist\FastSearchService.exe"
if (Test-Path -Path $serviceExe) {
    Write-Host "Service executable created successfully: $serviceExe" -ForegroundColor Green
} else {
    Write-Error "Failed to create service executable"
    exit 1
}

# Copy required files to dist directory
$requiredFiles = @(
    "$PSScriptRoot\src\fastsearch_service_python\*.py",
    "$PSScriptRoot\README.md",
    "$PSScriptRoot\requirements.txt"
)

foreach ($file in $requiredFiles) {
    if (Test-Path -Path $file) {
        Copy-Item -Path $file -Destination "$outputDir\" -Force -Recurse -ErrorAction SilentlyContinue
    }
}

Write-Host "`nBuild completed successfully!" -ForegroundColor Green
Write-Host "Service executable: $serviceExe" -ForegroundColor Yellow
Write-Host "Output directory: $outputDir" -ForegroundColor Yellow

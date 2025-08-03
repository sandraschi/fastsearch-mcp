# FastSearch MCP Package Script
# This script builds and packages the FastSearch MCP for distribution

# Stop on first error
$ErrorActionPreference = "Stop"

# Configuration
$version = "2.0.0"
$projectRoot = $PSScriptRoot
$buildDir = "$projectRoot\target\release"
$distDir = "$projectRoot\dist"
$packageName = "fastsearch-mcp"

# Create distribution directory if it doesn't exist
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}

Write-Host "🚀 Building FastSearch MCP v$version" -ForegroundColor Cyan

# Build the project in release mode
try {
    Write-Host "🔨 Building release version..." -NoNewline
    Push-Location $projectRoot
    cargo build --release
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed with exit code $LASTEXITCODE"
    }
    Write-Host " ✅" -ForegroundColor Green
} catch {
    Write-Host " ❌" -ForegroundColor Red
    Write-Error "Build failed: $_"
    exit 1
}

# Verify build artifacts
$requiredFiles = @(
    "$buildDir\fastsearch-mcp-bridge.exe",
    "$projectRoot\dxt_manifest.json",
    "$projectRoot\README.md",
    "$projectRoot\LICENSE"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Error "Required file not found: $file"
        exit 1
    }
}

# Create package directory
$packageDir = "$distDir\$packageName-$version"
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Copy files to package directory
Write-Host "📦 Creating package..." -NoNewline

# Copy main files
Copy-Item "$buildDir\fastsearch-mcp-bridge.exe" -Destination $packageDir
Copy-Item "$projectRoot\dxt_manifest.json" -Destination $packageDir
Copy-Item "$projectRoot\README.md" -Destination $packageDir
Copy-Item "$projectRoot\LICENSE" -Destination $packageDir

# Copy icons if they exist
$iconsDir = "$projectRoot\icons"
if (Test-Path $iconsDir) {
    $destIcons = "$packageDir\icons"
    New-Item -ItemType Directory -Path $destIcons | Out-Null
    Copy-Item "$iconsDir\*" -Destination $destIcons -Recurse
}

# Create DXT package using dxt pack
Write-Host " ✅" -ForegroundColor Green
Write-Host "📦 Creating DXT package..." -NoNewline

try {
    Push-Location $packageDir
    dxt pack --output "$distDir\$packageName-$version.dxt"
    if ($LASTEXITCODE -ne 0) {
        throw "DXT pack failed with exit code $LASTEXITCODE"
    }
    Write-Host " ✅" -ForegroundColor Green
} catch {
    Write-Host " ❌" -ForegroundColor Red
    Write-Error "Failed to create DXT package: $_"
    exit 1
} finally {
    Pop-Location
}

# Create a zip archive for distribution
Write-Host "📦 Creating ZIP archive..." -NoNewline
$zipPath = "$distDir\$packageName-$version.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Compress-Archive -Path "$packageDir\*" -DestinationPath $zipPath -CompressionLevel Optimal
Write-Host " ✅" -ForegroundColor Green

# Clean up
Remove-Item -Recurse -Force $packageDir

Write-Host "\n✨ Package created successfully!" -ForegroundColor Green
Write-Host "📦 DXT package: $distDir\$packageName-$version.dxt"
Write-Host "📦 ZIP archive: $zipPath"
Write-Host "\nTo install, run: dxt install $distDir\$packageName-$version.dxt" -ForegroundColor Cyan

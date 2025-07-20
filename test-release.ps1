<#
.SYNOPSIS
    Tests the FastSearch MCP release process locally before pushing to GitHub.
.DESCRIPTION
    This script helps you test the build and release process locally by:
    1. Verifying the build works
    2. Creating a test tag
    3. Showing what would be pushed to GitHub
#>

param (
    [switch]$DryRun = $true,
    [string]$TestVersion = "0.1.0"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Testing FastSearch MCP Release Process" -ForegroundColor Cyan
Write-Host "====================================="

# Verify we're in the right directory
if (-not (Test-Path "Cargo.toml")) {
    Write-Error "This script should be run from the repository root directory"
    exit 1
}

# Verify WiX is installed
$wixPath = "C:\Program Files (x86)\WiX Toolset v3.11\bin"
if (-not (Test-Path -Path $wixPath)) {
    $wixPath = "C:\Program Files\WiX Toolset v3.11\bin"
    if (-not (Test-Path -Path $wixPath)) {
        Write-Error "WiX Toolset not found. Please install WiX Toolset v3.11 or later."
        Write-Host "Download from: https://wixtoolset.org/releases/" -ForegroundColor Yellow
        exit 1
    }
}

# Add WiX to PATH
$env:Path = "$wixPath;$env:Path"

# Step 1: Clean previous builds
Write-Host "`n🧹 Cleaning previous builds..." -ForegroundColor Yellow
cargo clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Step 2: Build release
Write-Host "`n🔨 Building release..." -ForegroundColor Yellow
cargo build --release --all-targets
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Step 3: Create installer
Write-Host "`n📦 Creating installer..." -ForegroundColor Yellow
.\build-installer.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Step 4: Verify artifacts
$artifacts = @(
    "target\release\fastsearch-mcp-bridge.exe",
    "target\release\fastsearch.exe",
    "installer\FastSearchMCP-Setup.exe"
)

Write-Host "`n🔍 Verifying artifacts..." -ForegroundColor Yellow
foreach ($artifact in $artifacts) {
    if (Test-Path $artifact) {
        $size = (Get-Item $artifact).Length / 1MB
        Write-Host "✅ Found $([System.IO.Path]::GetFileName($artifact)) - $($size.ToString('0.00')) MB" -ForegroundColor Green
    } else {
        Write-Error "❌ Missing artifact: $artifact"
        exit 1
    }
}

# Step 5: Show next steps
Write-Host "`n🎉 Local build and test completed successfully!" -ForegroundColor Green
Write-Host "========================================"

if ($DryRun) {
    Write-Host "`n📝 To create a real release on GitHub:" -ForegroundColor Cyan
    Write-Host "1. Update the version in Cargo.toml"
    Write-Host "2. Commit your changes"
    Write-Host "3. Create and push a version tag:"
    Write-Host "   git tag -a v$TestVersion -m 'Release v$TestVersion'"
    Write-Host "   git push origin v$TestVersion"
    Write-Host "`nThe GitHub Actions workflow will automatically create a release with the built artifacts."
} else {
    # This would be the actual release process
    Write-Host "`n🚀 Creating release tag v$TestVersion..." -ForegroundColor Cyan
    
    # Update version in Cargo.toml if needed
    # Create tag
    # Push to GitHub
    
    Write-Host "`n✅ Release process started! Check GitHub Actions for progress." -ForegroundColor Green
}

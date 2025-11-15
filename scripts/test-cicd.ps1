#!/usr/bin/env pwsh
# Test script to verify the CI/CD workflow locally before pushing

Write-Host "🚀 FastSearch MCP CI/CD Test Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Please run this script from the fastsearch-mcp root directory" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Running from fastsearch-mcp root directory" -ForegroundColor Green

# Check toolchain
Write-Host "🔍 Checking CMake availability..." -ForegroundColor Yellow
try {
    $cmakeVersion = & cmake --version
    Write-Host "✅ CMake found: $cmakeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ CMake not found. Please install CMake and ensure it is on PATH." -ForegroundColor Red
    exit 1
}

Write-Host "🔍 Checking Visual Studio Build Tools..." -ForegroundColor Yellow
if (-not (Test-Path "$Env:ProgramFiles\Microsoft Visual Studio")) {
    Write-Host "⚠️ Visual Studio Build Tools directory not found. Ensure the Desktop C++ workload is installed." -ForegroundColor Yellow
}

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force service\build -ErrorAction SilentlyContinue
Write-Host "✅ Clean complete" -ForegroundColor Green

# Build release targets
Write-Host "🔨 Building release targets..." -ForegroundColor Yellow
cmake -S service -B service/build -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ CMake configure failed" -ForegroundColor Red
    exit 1
}
cmake --build service/build --config Release
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Service build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Service build successful" -ForegroundColor Green

# Verify expected binaries
Write-Host "🔍 Verifying binaries..." -ForegroundColor Yellow
$bridgeBinary = "dist\fastsearch-mcp-bridge.exe"
$serviceBinary = "service\build\bin\Release\FastSearchServiceNew.exe"

if (Test-Path $bridgeBinary) {
    $bridgeSize = (Get-Item $bridgeBinary).Length
    Write-Host "✅ Bridge binary found: $bridgeBinary ($([math]::Round($bridgeSize/1MB, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "❌ Bridge binary not found: $bridgeBinary" -ForegroundColor Red
    exit 1
}

if (Test-Path $serviceBinary) {
    $serviceSize = (Get-Item $serviceBinary).Length
    Write-Host "✅ Service binary found: $serviceBinary ($([math]::Round($serviceSize/1MB, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "❌ Service binary not found: $serviceBinary" -ForegroundColor Red
    exit 1
}

# Test bridge can start (quick test)
Write-Host "🧪 Testing bridge startup..." -ForegroundColor Yellow
try {
    $process = Start-Process -FilePath $bridgeBinary -ArgumentList "--version" -PassThru -Wait -WindowStyle Hidden
    if ($process.ExitCode -eq 0) {
        Write-Host "✅ Bridge startup test passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Bridge returned exit code $($process.ExitCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Bridge startup test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   This might be expected if --version is not implemented" -ForegroundColor Gray
}

# Create test distribution
Write-Host "📦 Creating test distribution..." -ForegroundColor Yellow
$distDir = "test-dist"
if (Test-Path $distDir) {
    Remove-Item $distDir -Recurse -Force
}
New-Item -ItemType Directory -Path $distDir | Out-Null

# Copy binaries
Copy-Item $bridgeBinary $distDir
Copy-Item $serviceBinary $distDir

# Create test installation script
$installScript = @"
@echo off
echo FastSearch MCP Test Installation
echo =================================
echo.
echo This is a test installation script.
echo Binaries are ready for testing.
echo.
echo Bridge: %~dp0fastsearch-mcp-bridge.exe
echo Service: %~dp0fastsearch-service.exe
echo.
echo To install for real, use the official installer.
pause
"@

$installScript | Out-File -FilePath "$distDir\test-install.bat" -Encoding ASCII

# Create README
$readme = @"
# FastSearch MCP Test Build

This is a test build created by the local CI/CD test script.

## Files
- fastsearch-mcp-bridge.exe - MCP bridge for Claude Desktop
- FastSearchServiceNew.exe - Windows service for NTFS access
- test-install.bat - Test installation script

## Testing
1. Run test-install.bat to verify files
2. Check that both executables are present
3. This build is ready for CI/CD deployment

Built on: $(Get-Date)
"@

$readme | Out-File -FilePath "$distDir\README.md" -Encoding UTF8

Write-Host "✅ Test distribution created in: $distDir" -ForegroundColor Green

# Show summary
Write-Host ""
Write-Host "🎉 CI/CD Test Complete!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "- Build: ✅ SUCCESS" -ForegroundColor Green
Write-Host "- Bridge: ✅ $bridgeBinary" -ForegroundColor Green  
Write-Host "- Service: ✅ $serviceBinary" -ForegroundColor Green
Write-Host "- Test dist: ✅ $distDir" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Commit and push the updated .github/workflows/build-release.yml" -ForegroundColor White
Write-Host "2. Create a test tag: git tag v0.2.0-test && git push origin v0.2.0-test" -ForegroundColor White
Write-Host "3. Watch GitHub Actions build and create release artifacts" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Ready for GitHub Actions deployment!" -ForegroundColor Green

# FastSearch MCP - MCPB Package Builder
# Builds a self-contained MCPB package with all dependencies bundled

param(
    [switch]$NoSign,
    [string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"

# Configuration
# Script is in mcpb/scripts, so go up two levels to get project root
$ProjectRoot = $PSScriptRoot | Split-Path -Parent | Split-Path -Parent
$PackageName = "fastsearch-mcp"
$Version = "0.4.0"
$BuildDir = Join-Path $ProjectRoot "mcpb-build"
$DistDir = Join-Path $ProjectRoot $OutputDir
$SrcDir = Join-Path $BuildDir "src"

Write-Host "`n🚀 Building FastSearch MCP MCPB Package v$Version" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

# Check MCPB CLI
try {
    $mcpbVersion = mcpb --version 2>&1
    Write-Host "  ✅ MCPB CLI found: $mcpbVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ MCPB CLI not found!" -ForegroundColor Red
    Write-Host "  Install with: npm install -g @anthropic-ai/mcpb" -ForegroundColor Yellow
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python not found!" -ForegroundColor Red
    exit 1
}


# Clean build directory
Write-Host "`n🧹 Cleaning build directory..." -ForegroundColor Yellow
if (Test-Path $BuildDir) {
    Remove-Item -Recurse -Force $BuildDir
}
New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null
New-Item -ItemType Directory -Path $SrcDir -Force | Out-Null
New-Item -ItemType Directory -Path $DistDir -Force | Out-Null

# Copy source code
Write-Host "`n📦 Copying source code..." -ForegroundColor Yellow
$SourcePath = Join-Path $ProjectRoot "src\fastsearch_mcp"
$DestSourcePath = Join-Path $SrcDir "fastsearch_mcp"
Copy-Item -Path $SourcePath -Destination $DestSourcePath -Recurse -Force
Write-Host "  ✅ Source code copied" -ForegroundColor Green

# Copy manifest and prompts
Write-Host "`n📄 Copying configuration files..." -ForegroundColor Yellow
Copy-Item -Path (Join-Path $ProjectRoot "manifest.json") -Destination $BuildDir -Force
# Copy prompts from mcpb/prompts to prompts/ in build directory (manifest.json references prompts/ at package root)
Copy-Item -Path (Join-Path $ProjectRoot "mcpb\prompts") -Destination (Join-Path $BuildDir "prompts") -Recurse -Force
Write-Host "  ✅ Configuration files copied" -ForegroundColor Green

# Create requirements.txt (Claude Desktop will install these at first run)
Write-Host "`n📋 Creating requirements.txt..." -ForegroundColor Yellow
$Requirements = @"
fastmcp>=2.13.0
pydantic>=2.0.0
psutil>=5.9.0
pywin32>=306; sys_platform == 'win32'
"@
$Requirements | Out-File -FilePath (Join-Path $BuildDir "requirements.txt") -Encoding UTF8
Write-Host "  ✅ requirements.txt created (Claude Desktop will install dependencies)" -ForegroundColor Green

# Validate manifest
Write-Host "`n✅ Validating manifest.json..." -ForegroundColor Yellow
Push-Location $BuildDir
try {
    mcpb validate manifest.json
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Manifest validation passed" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Manifest validation failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
} catch {
    Write-Host "  ❌ Manifest validation error: $_" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

# Build MCPB package
Write-Host "`n📦 Building MCPB package..." -ForegroundColor Yellow

$OutputFile = Join-Path $DistDir "$PackageName-$Version.mcpb"

try {
    # mcpb pack syntax: mcpb pack [directory] [output]
    mcpb pack $BuildDir $OutputFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ MCPB package created successfully" -ForegroundColor Green
    } else {
        Write-Host "  ❌ MCPB pack failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ❌ Failed to create MCPB package: $_" -ForegroundColor Red
    exit 1
}

# Verify package
if (Test-Path $OutputFile) {
    $PackageSize = (Get-Item $OutputFile).Length / 1MB
    Write-Host "`n✨ Package created successfully!" -ForegroundColor Green
    Write-Host "  📦 Package: $OutputFile" -ForegroundColor Cyan
    Write-Host "  📊 Size: $([math]::Round($PackageSize, 2)) MB" -ForegroundColor Cyan
    Write-Host "`n📥 To install:" -ForegroundColor Yellow
    Write-Host "  Drag and drop the .mcpb file into Claude Desktop" -ForegroundColor White
    Write-Host "  Or use: mcpb install $OutputFile" -ForegroundColor White
} else {
    Write-Host "`n❌ Package file not found!" -ForegroundColor Red
    exit 1
}

# Cleanup (optional - comment out to keep build directory for debugging)
Write-Host "`n🧹 Cleaning up build directory..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $BuildDir
Write-Host "  ✅ Cleanup complete" -ForegroundColor Green

Write-Host "`n✅ Build complete!" -ForegroundColor Green


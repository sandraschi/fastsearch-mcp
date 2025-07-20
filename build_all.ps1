# Build script for FastSearch MCP components

# Function to build a specific component
function Build-Component {
    param (
        [string]$componentName,
        [string]$componentPath
    )
    
    Write-Host "Building $componentName..." -ForegroundColor Cyan
    Set-Location -Path $componentPath
    
    $buildOutput = cargo build --release 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$componentName built successfully!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "Failed to build $componentName :(" -ForegroundColor Red
        $buildOutput | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        return $false
    }
}

# Main build process
Write-Host "Starting FastSearch MCP build process..." -ForegroundColor Yellow

# Build shared library first
if (-not (Build-Component -componentName "Shared Library" -componentPath "shared")) {
    exit 1
}

# Build the service
if (-not (Build-Component -componentName "Service" -componentPath "service")) {
    exit 1
}

# Build the bridge
if (-not (Build-Component -componentName "Bridge" -componentPath "bridge")) {
    exit 1
}

# Check if all binaries were created
$bridgeBinary = ".\bridge\target\release\fastsearch-mcp-bridge.exe"
$serviceBinary = ".\service\target\release\fastsearch-service.exe"

if ((Test-Path $bridgeBinary) -and (Test-Path $serviceBinary)) {
    Write-Host "\nBuild completed successfully!" -ForegroundColor Green
    Write-Host "- Bridge: $((Get-Item $bridgeBinary).FullName)" -ForegroundColor Cyan
    Write-Host "- Service: $((Get-Item $serviceBinary).FullName)" -ForegroundColor Cyan
    
    # Copy binaries to bin directory
    if (-not (Test-Path ".\bin")) {
        New-Item -ItemType Directory -Path ".\bin" | Out-Null
    }
    
    Copy-Item -Path $bridgeBinary -Destination ".\bin\" -Force
    Copy-Item -Path $serviceBinary -Destination ".\bin\" -Force
    
    Write-Host "\nBinaries copied to .\bin\" -ForegroundColor Green
} else {
    Write-Host "\nBuild completed with missing binaries." -ForegroundColor Yellow
    if (-not (Test-Path $bridgeBinary)) { Write-Host "- Missing: $bridgeBinary" -ForegroundColor Red }
    if (-not (Test-Path $serviceBinary)) { Write-Host "- Missing: $serviceBinary" -ForegroundColor Red }
    exit 1
}

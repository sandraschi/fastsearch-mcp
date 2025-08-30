# Build FastSearch MCP (C++ Service and Python Bridge)

# Store the current directory to return to later
$originalDir = Get-Location

try {
    # Build C++ Service
    Write-Host "Building C++ Service..." -ForegroundColor Cyan

    # Create build directory if it doesn't exist
    $buildDir = "service\build"
    if (-not (Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }

    # Configure and build the service
    Set-Location $buildDir
    cmake .. -G "Visual Studio 17 2022" -A x64
    cmake --build . --config Release

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to build C++ service"
    }

    # Build Python Bridge
    Write-Host "`nBuilding Python Bridge..." -ForegroundColor Cyan
    Set-Location "$originalDir\fastsearch_mcp_bridge"

    # Create virtual environment if it doesn't exist
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }

    # Activate virtual environment and install dependencies
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install Python dependencies"
    }

    # Create bin directory if it doesn't exist
    $binDir = "$originalDir\bin"
    if (-not (Test-Path $binDir)) {
        New-Item -ItemType Directory -Path $binDir | Out-Null
        Write-Host "Created bin directory at: $binDir" -ForegroundColor Cyan
    }

    # Copy service executable to bin directory
    $serviceExe = "$originalDir\service\build\bin\Release\FastSearchService.exe"
    if (Test-Path $serviceExe) {
        Copy-Item -Path $serviceExe -Destination $binDir -Force
        Write-Host "Copied FastSearchService.exe to: $binDir" -ForegroundColor Green
    }

    Write-Host "`nBuild completed successfully!" -ForegroundColor Green
    Write-Host "Service executable: $serviceExe" -ForegroundColor Green
    Write-Host "Python bridge is ready in: $originalDir\fastsearch_mcp_bridge" -ForegroundColor Green
}
catch {
    Write-Error "Build failed: $_"
    exit 1
}
finally {
    # Always return to the original directory
    Set-Location $originalDir
}

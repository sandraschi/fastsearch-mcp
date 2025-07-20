# Build script for FastSearch MCP Service

# Change to the service directory
Set-Location -Path $PSScriptRoot\service

# Build the service in release mode
Write-Host "Building FastSearch MCP Service..."
$buildOutput = cargo build --release 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful!" -ForegroundColor Green
    
    # Show where the binary was created
    $binaryPath = "$PSScriptRoot\service\target\release\fastsearch-service.exe"
    if (Test-Path $binaryPath) {
        Write-Host "Binary created at: $binaryPath" -ForegroundColor Cyan
    } else {
        Write-Host "Warning: Could not find the built binary at expected location." -ForegroundColor Yellow
    }
} else {
    Write-Host "Build failed with errors:" -ForegroundColor Red
    $buildOutput | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    exit 1
}

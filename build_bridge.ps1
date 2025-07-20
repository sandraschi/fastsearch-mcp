# Build script for FastSearch MCP Bridge

# Change to the bridge directory
Set-Location -Path $PSScriptRoot\bridge

# Build the bridge in release mode
Write-Host "Building FastSearch MCP Bridge..."
$buildOutput = cargo build --release 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful!" -ForegroundColor Green
    
    # Show where the binary was created
    $binaryPath = "$PSScriptRoot\bridge\target\release\fastsearch-mcp-bridge.exe"
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

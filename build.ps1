# Build script for FastSearch MCP Service

# Change to the service directory
Set-Location -Path $PSScriptRoot\service

# Build the Python service
Write-Host "Setting up FastSearch MCP Service..."

# Install Python dependencies
$pythonDir = "$PSScriptRoot\service\src\fastsearch_service_python"
Write-Host "Installing Python dependencies..."
pip install -r "$pythonDir\requirements.txt"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Setup completed successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Setup failed with errors:" -ForegroundColor Red
    exit 1
}

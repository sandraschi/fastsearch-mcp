# Setup DebugView to capture OutputDebugStringW messages from FastSearch service
# DebugView is a free tool from Microsoft Sysinternals

$debugViewUrl = "https://download.sysinternals.com/files/DebugView.zip"
$debugViewZip = "$env:TEMP\DebugView.zip"
$debugViewDir = "$env:LOCALAPPDATA\DebugView"
$debugViewExe = "$debugViewDir\Dbgview.exe"

Write-Host "============================================================" -ForegroundColor Green
Write-Host "DebugView Setup for FastSearch Service" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Check if DebugView already exists
if (Test-Path $debugViewExe) {
    Write-Host "[INFO] DebugView already installed at: $debugViewExe" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Starting DebugView..." -ForegroundColor Cyan
    
    # Start DebugView with capture enabled
    Start-Process $debugViewExe -ArgumentList "/t" -WindowStyle Normal
    Write-Host "[OK] DebugView started with capture enabled" -ForegroundColor Green
    Write-Host ""
    Write-Host "DebugView is now capturing OutputDebugString messages." -ForegroundColor Cyan
    Write-Host "Look for messages prefixed with '[FastSearch]'" -ForegroundColor Cyan
    exit 0
}

# Download DebugView
Write-Host "Downloading DebugView from Sysinternals..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $debugViewUrl -OutFile $debugViewZip -UseBasicParsing
    Write-Host "[OK] Download complete" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to download DebugView: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual download:" -ForegroundColor Yellow
    Write-Host "1. Visit: https://docs.microsoft.com/en-us/sysinternals/downloads/debugview" -ForegroundColor Yellow
    Write-Host "2. Download DebugView.zip" -ForegroundColor Yellow
    Write-Host "3. Extract to: $debugViewDir" -ForegroundColor Yellow
    exit 1
}

# Extract DebugView
Write-Host "Extracting DebugView..." -ForegroundColor Cyan
if (-not (Test-Path $debugViewDir)) {
    New-Item -ItemType Directory -Path $debugViewDir -Force | Out-Null
}

try {
    Expand-Archive -Path $debugViewZip -DestinationPath $debugViewDir -Force
    Write-Host "[OK] Extraction complete" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to extract DebugView: $_" -ForegroundColor Red
    Write-Host "You may need to extract manually." -ForegroundColor Yellow
    exit 1
}

# Clean up zip file
Remove-Item $debugViewZip -ErrorAction SilentlyContinue

# Verify DebugView exists
if (-not (Test-Path $debugViewExe)) {
    Write-Host "[ERROR] DebugView executable not found after extraction" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] DebugView installed successfully" -ForegroundColor Green
Write-Host ""

# Start DebugView
Write-Host "Starting DebugView..." -ForegroundColor Cyan
Start-Process $debugViewExe -ArgumentList "/t" -WindowStyle Normal
Write-Host "[OK] DebugView started with capture enabled" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "DebugView Setup Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "DebugView is now capturing OutputDebugString messages." -ForegroundColor Cyan
Write-Host "Look for messages prefixed with '[FastSearch]'" -ForegroundColor Cyan
Write-Host ""
Write-Host "To use DebugView manually:" -ForegroundColor Yellow
Write-Host "1. Run: $debugViewExe" -ForegroundColor Gray
Write-Host "2. Enable: Capture -> Capture Win32" -ForegroundColor Gray
Write-Host "3. Enable: Capture -> Capture Global Win32" -ForegroundColor Gray
Write-Host "4. Filter: Enter '[FastSearch]' in the filter box" -ForegroundColor Gray


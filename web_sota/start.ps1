# Webapp Start - Standardized SOTA (Auto-Repaired V2.5)
$WebPort = 10844
$BackendPort = 10845
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 1. Kill any process squatting on the ports
Write-Host "Checking for port squatters on $WebPort and $BackendPort..." -ForegroundColor Yellow
$pids = Get-NetTCPConnection -LocalPort $WebPort, $BackendPort -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 4 } | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($p in $pids) {
    Write-Host "Found squatter (PID: $p). Terminating..." -ForegroundColor Red
    try { Stop-Process -Id $p -Force -ErrorAction Stop } catch { Write-Host "Warning: Could not terminate PID $p." -ForegroundColor Gray }
}

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start the Python backend (Background) from project root so fastsearch_mcp is importable
Write-Host "Starting Python backend on port $BackendPort ..." -ForegroundColor Cyan
$backendCmd = "Set-Location '$ProjectRoot'; uv run uvicorn fastsearch_mcp.server:app --host 127.0.0.1 --port $BackendPort --log-level info"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 4. Wait for backend to be listening (avoid ECONNREFUSED when frontend loads)
$healthUrl = "http://127.0.0.1:$BackendPort/health"
$maxAttempts = 30
$attempt = 0
do {
    $attempt++
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { break }
    } catch { }
    if ($attempt -ge $maxAttempts) {
        Write-Host "WARNING: Backend did not respond at $healthUrl after ${maxAttempts}s. Frontend may show connection errors." -ForegroundColor Yellow
        break
    }
} while ($true)
if ($attempt -lt $maxAttempts) {
    Write-Host "Backend ready at port $BackendPort." -ForegroundColor Green
}

# 5. Run server (Vite dev)
Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green
Set-Location $PSScriptRoot

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
npm run dev -- --port $WebPort --host




# Stop FastSearch service with admin privileges
# This script will request UAC elevation

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator." -ForegroundColor Yellow
    exit 1
}

Write-Host "Stopping FastSearch service..." -ForegroundColor Cyan

# Stop the service
try {
    $service = Get-Service -Name "FastSearchMCP" -ErrorAction Stop
    Write-Host "Service Status: $($service.Status)" -ForegroundColor Yellow
    
    if ($service.Status -eq "Running") {
        Write-Host "Stopping service..." -ForegroundColor Cyan
        Stop-Service -Name "FastSearchMCP" -Force -ErrorAction Stop
        # HARDENED 2026-09-17: was a blind Start-Sleep -Seconds 3 before the single
        # status check below - a service that takes slightly longer to stop was
        # reported inaccurately. Poll instead (TRAPS_AND_PITFALLS.md #36).
        $stopWaitSec = 10
        $stopElapsed = 0
        do {
            Start-Sleep -Milliseconds 500
            $stopElapsed += 0.5
            $service.Refresh()
        } while ($stopElapsed -lt $stopWaitSec -and $service.Status -eq "Running")
        Write-Host "Service Status: $($service.Status)" -ForegroundColor Green
    } else {
        Write-Host "Service is already stopped" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] Service not found or already stopped: $_" -ForegroundColor Yellow
}

# Kill any remaining processes
Write-Host ""
Write-Host "Checking for remaining processes..." -ForegroundColor Cyan
$processes = Get-Process -Name "FastSearchServiceNew" -ErrorAction SilentlyContinue
if ($processes) {
    Write-Host "Found $($processes.Count) process(es), killing..." -ForegroundColor Yellow
    foreach ($proc in $processes) {
        Write-Host "  Killing process ID: $($proc.Id)" -ForegroundColor Gray
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    # HARDENED 2026-09-17: was a blind Start-Sleep -Seconds 2 before the
    # remaining-process check below - poll instead so a slightly slower kill
    # doesn't get misreported as "could not be stopped" (TRAPS_AND_PITFALLS.md #36).
    $killWaitSec = 10
    $killElapsed = 0
    while ($killElapsed -lt $killWaitSec -and (Get-Process -Name "FastSearchServiceNew" -ErrorAction SilentlyContinue)) {
        Start-Sleep -Milliseconds 500
        $killElapsed += 0.5
    }

    # Verify they're gone
    $remaining = Get-Process -Name "FastSearchServiceNew" -ErrorAction SilentlyContinue
    if ($remaining) {
        Write-Host "[ERROR] Some processes could not be stopped" -ForegroundColor Red
        foreach ($proc in $remaining) {
            Write-Host "  Process ID $($proc.Id) still running" -ForegroundColor Red
        }
    } else {
        Write-Host "[OK] All processes stopped" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] No processes found" -ForegroundColor Green
}

Write-Host ""
Write-Host "Service stopped successfully!" -ForegroundColor Green

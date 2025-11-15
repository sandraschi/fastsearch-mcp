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
        Start-Sleep -Seconds 3
        $service.Refresh()
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
    Start-Sleep -Seconds 2
    
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

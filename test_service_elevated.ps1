# Test FastSearch Service with UAC Elevation
# This script will prompt for elevation if needed and test the service

param(
    [switch]$ReadLogsOnly
)

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges." -ForegroundColor Yellow
    Write-Host "Restarting with elevation..." -ForegroundColor Yellow
    
    # Restart script with elevation
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -ReadLogsOnly:`$$ReadLogsOnly" -Wait
    exit
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "FastSearch Service Test (Running as Administrator)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Read logs first
Write-Host "1. Reading Windows Event Logs for FastSearchMCP..." -ForegroundColor Cyan
Write-Host ""

try {
    # Use Get-WinEvent to read Application log
    $logs = Get-WinEvent -LogName Application -MaxEvents 100 -ErrorAction SilentlyContinue | 
        Where-Object { $_.ProviderName -like "*FastSearch*" -or $_.Message -like "*FastSearch*" } |
        Select-Object -First 20
    
    if ($logs) {
        Write-Host "Found $($logs.Count) log entries:" -ForegroundColor Green
        Write-Host ""
        foreach ($log in $logs) {
            $time = $log.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
            $level = $log.LevelDisplayName
            $id = $log.Id
            $message = $log.Message -replace "`r`n", " " -replace "`n", " "
            if ($message.Length -gt 150) {
                $message = $message.Substring(0, 150) + "..."
            }
            Write-Host "[$time] $level (ID: $id)" -ForegroundColor $(if ($level -eq "Error") { "Red" } elseif ($level -eq "Warning") { "Yellow" } else { "White" })
            Write-Host "  $message" -ForegroundColor Gray
            Write-Host ""
        }
    } else {
        Write-Host "No log entries found for FastSearchMCP" -ForegroundColor Yellow
        Write-Host ""
    }
} catch {
    Write-Host "Error reading logs: $_" -ForegroundColor Red
    Write-Host ""
}

if ($ReadLogsOnly) {
    Write-Host "Log reading complete. Exiting." -ForegroundColor Green
    exit
}

# Test service status
Write-Host "2. Checking Service Status..." -ForegroundColor Cyan
$service = Get-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Service Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Yellow" })
    Write-Host "Service Name: $($service.Name)" -ForegroundColor White
    Write-Host "Display Name: $($service.DisplayName)" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "Service not found!" -ForegroundColor Red
    Write-Host ""
    exit
}

# Try to start service
if ($service.Status -ne "Running") {
    Write-Host "3. Starting Service..." -ForegroundColor Cyan
    try {
        Start-Service -Name "FastSearchMCP" -ErrorAction Stop
        Write-Host "Service start command sent." -ForegroundColor Green
        Start-Sleep -Seconds 5
        
        $service.Refresh()
        if ($service.Status -eq "Running") {
            Write-Host "Service is now RUNNING!" -ForegroundColor Green
        } else {
            Write-Host "Service status: $($service.Status)" -ForegroundColor Yellow
        }
        Write-Host ""
    } catch {
        Write-Host "Error starting service: $_" -ForegroundColor Red
        Write-Host ""
    }
} else {
    Write-Host "3. Service is already running." -ForegroundColor Green
    Write-Host ""
}

# Read logs after start attempt
Write-Host "4. Reading Event Logs (AFTER start attempt)..." -ForegroundColor Cyan
Write-Host ""
Start-Sleep -Seconds 2

try {
    $logsAfter = Get-WinEvent -LogName Application -MaxEvents 50 -ErrorAction SilentlyContinue | 
        Where-Object { 
            ($_.ProviderName -like "*FastSearch*" -or $_.Message -like "*FastSearch*") -and
            $_.TimeCreated -gt (Get-Date).AddMinutes(-2)
        } |
        Select-Object -First 10
    
    if ($logsAfter) {
        Write-Host "Found $($logsAfter.Count) recent log entries:" -ForegroundColor Green
        Write-Host ""
        foreach ($log in $logsAfter) {
            $time = $log.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
            $level = $log.LevelDisplayName
            $id = $log.Id
            $message = $log.Message -replace "`r`n", " " -replace "`n", " "
            Write-Host "[$time] $level (ID: $id)" -ForegroundColor $(if ($level -eq "Error") { "Red" } elseif ($level -eq "Warning") { "Yellow" } else { "White" })
            Write-Host "  $message" -ForegroundColor Gray
            Write-Host ""
        }
    } else {
        Write-Host "No new log entries found" -ForegroundColor Yellow
        Write-Host ""
    }
} catch {
    Write-Host "Error reading logs: $_" -ForegroundColor Red
    Write-Host ""
}

# Test pipe connection if service is running
$service.Refresh()
if ($service.Status -eq "Running") {
    Write-Host "5. Testing Pipe Connection..." -ForegroundColor Cyan
    Write-Host ""
    
    python -c "import sys; sys.path.insert(0, 'src'); import asyncio; from fastsearch_mcp.pipe_client import test_pipe_connection; result = asyncio.run(test_pipe_connection()); print(f'Pipe connection: {\"SUCCESS\" if result else \"FAILED\"}')"
    Write-Host ""
}

# Stop service
Write-Host "6. Stopping Service..." -ForegroundColor Cyan
try {
    if ($service.Status -eq "Running") {
        Stop-Service -Name "FastSearchMCP" -ErrorAction Stop
        Write-Host "Service stop command sent." -ForegroundColor Green
        Start-Sleep -Seconds 2
        $service.Refresh()
        Write-Host "Service status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Stopped") { "Green" } else { "Yellow" })
    } else {
        Write-Host "Service is already stopped." -ForegroundColor Yellow
    }
    Write-Host ""
} catch {
    Write-Host "Error stopping service: $_" -ForegroundColor Red
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "Test Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green


# Full service test with elevation and log reading
# This will prompt for UAC if needed

param(
    [switch]$SkipStartStop
)

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Requesting elevation..." -ForegroundColor Yellow
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process powershell -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -SkipStartStop:`$$SkipStartStop" -Wait
    exit
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "FastSearch Service Full Test (Admin Mode)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# 1. Read existing logs
Write-Host "1. Reading existing Event Logs..." -ForegroundColor Cyan
Write-Host ""

# Check Application log
$appLogs = Get-WinEvent -LogName Application -MaxEvents 200 -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.Message -like "*FastSearch*" -or 
        $_.ProviderName -like "*FastSearch*" -or
        $_.Message -like "*FastSearchMCP*"
    } | Select-Object -First 20

if ($appLogs) {
    Write-Host "Found $($appLogs.Count) entries in Application log:" -ForegroundColor Green
    foreach ($log in $appLogs) {
        $time = $log.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
        $level = $log.LevelDisplayName
        $id = $log.Id
        $source = $log.ProviderName
        $msg = ($log.Message -replace "`r`n", " " -replace "`n", " ").Substring(0, [Math]::Min(150, $log.Message.Length))
        Write-Host "  [$time] $level (ID: $id) [$source]" -ForegroundColor $(if ($level -eq "Error") { "Red" } elseif ($level -eq "Warning") { "Yellow" } else { "White" })
        Write-Host "    $msg" -ForegroundColor Gray
    }
} else {
    Write-Host "No entries found in Application log" -ForegroundColor Yellow
}

# Check System log for service events
Write-Host ""
Write-Host "Checking System log for service events..." -ForegroundColor Cyan
$sysLogs = Get-WinEvent -LogName System -MaxEvents 200 -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.Message -like "*FastSearch*" -or
        $_.Id -eq 7034 -or  # Service stopped unexpectedly
        $_.Id -eq 7035 -or  # Service start/stop
        $_.Id -eq 7000 -or  # Service start failure
        $_.Id -eq 7001      # Service start timeout
    } | Select-Object -First 10

if ($sysLogs) {
    Write-Host "Found $($sysLogs.Count) relevant entries in System log:" -ForegroundColor Green
    foreach ($log in $sysLogs) {
        $time = $log.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
        $level = $log.LevelDisplayName
        $id = $log.Id
        $msg = ($log.Message -replace "`r`n", " " -replace "`n", " ").Substring(0, [Math]::Min(150, $log.Message.Length))
        Write-Host "  [$time] $level (ID: $id)" -ForegroundColor $(if ($level -eq "Error") { "Red" } else { "Yellow" })
        Write-Host "    $msg" -ForegroundColor Gray
    }
} else {
    Write-Host "No relevant entries in System log" -ForegroundColor Yellow
}

Write-Host ""

if ($SkipStartStop) {
    Write-Host "Skipping service start/stop (log reading only)" -ForegroundColor Yellow
    exit
}

# 2. Check service status
Write-Host "2. Service Status:" -ForegroundColor Cyan
$service = Get-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "  Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Yellow" })
} else {
    Write-Host "  Service not found!" -ForegroundColor Red
    exit
}
Write-Host ""

# 3. Start service
Write-Host "3. Starting Service..." -ForegroundColor Cyan
if ($service.Status -ne "Running") {
    try {
        Start-Service -Name "FastSearchMCP" -ErrorAction Stop
        Write-Host "  Start command sent" -ForegroundColor Green
        Start-Sleep -Seconds 5
        $service.Refresh()
        Write-Host "  Status after start: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
    } catch {
        Write-Host "  Error: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  Service already running" -ForegroundColor Green
}
Write-Host ""

# 4. Read logs after start
Write-Host "4. Reading Logs After Start..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
$newLogs = Get-WinEvent -LogName Application -MaxEvents 50 -ErrorAction SilentlyContinue | 
    Where-Object { 
        ($_.Message -like "*FastSearch*" -or $_.ProviderName -like "*FastSearch*") -and
        $_.TimeCreated -gt (Get-Date).AddMinutes(-2)
    } | Select-Object -First 10

if ($newLogs) {
    Write-Host "  Found $($newLogs.Count) new entries:" -ForegroundColor Green
    foreach ($log in $newLogs) {
        $time = $log.TimeCreated.ToString("HH:mm:ss")
        $level = $log.LevelDisplayName
        $id = $log.Id
        $msg = ($log.Message -replace "`r`n", " " -replace "`n", " ").Substring(0, [Math]::Min(200, $log.Message.Length))
        Write-Host "    [$time] $level (ID: $id): $msg" -ForegroundColor $(if ($level -eq "Error") { "Red" } else { "White" })
    }
} else {
    Write-Host "  No new log entries" -ForegroundColor Yellow
}
Write-Host ""

# 5. Test pipe if running
$service.Refresh()
if ($service.Status -eq "Running") {
    Write-Host "5. Testing Pipe Connection..." -ForegroundColor Cyan
    python -c "import sys; sys.path.insert(0, 'src'); import asyncio; from fastsearch_mcp.pipe_client import test_pipe_connection; result = asyncio.run(test_pipe_connection()); print(f'  Pipe connection: {\"SUCCESS\" if result else \"FAILED\"}')"
    Write-Host ""
}

# 6. Stop service
Write-Host "6. Stopping Service..." -ForegroundColor Cyan
if ($service.Status -eq "Running") {
    try {
        Stop-Service -Name "FastSearchMCP" -ErrorAction Stop
        Write-Host "  Stop command sent" -ForegroundColor Green
        Start-Sleep -Seconds 2
        $service.Refresh()
        Write-Host "  Status after stop: $($service.Status)" -ForegroundColor Green
    } catch {
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "Test Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green


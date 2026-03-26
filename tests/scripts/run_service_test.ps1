# Simple service test script
Write-Host "============================================================" -ForegroundColor Green
Write-Host "FastSearch Service Test" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Check service status
Write-Host "1. Current Service Status:" -ForegroundColor Cyan
$service = Get-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "   Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Yellow" })
    Write-Host "   Name: $($service.Name)" -ForegroundColor White
} else {
    Write-Host "   Service not found!" -ForegroundColor Red
    exit
}
Write-Host ""

# Read existing logs
Write-Host "2. Reading Existing Logs:" -ForegroundColor Cyan
$logs = Get-WinEvent -LogName Application -MaxEvents 500 -ErrorAction SilentlyContinue | 
    Where-Object { 
        $_.Message -like "*FastSearch*" -or 
        $_.ProviderName -like "*FastSearch*"
    } | Select-Object -First 10

if ($logs) {
    Write-Host "   Found $($logs.Count) log entries:" -ForegroundColor Green
    foreach ($log in $logs) {
        $time = $log.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
        $level = $log.LevelDisplayName
        $id = $log.Id
        $msg = $log.Message.Substring(0, [Math]::Min(150, $log.Message.Length))
        Write-Host "   [$time] $level (ID: $id)" -ForegroundColor $(if ($level -eq "Error") { "Red" } else { "White" })
        Write-Host "      $msg" -ForegroundColor Gray
    }
} else {
    Write-Host "   No log entries found" -ForegroundColor Yellow
}
Write-Host ""

# Start service
Write-Host "3. Starting Service..." -ForegroundColor Cyan
if ($service.Status -ne "Running") {
    try {
        Start-Service -Name "FastSearchMCP" -ErrorAction Stop
        Write-Host "   Start command sent" -ForegroundColor Green
        Start-Sleep -Seconds 5
        $service.Refresh()
        Write-Host "   Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
    } catch {
        Write-Host "   Error: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   Service already running" -ForegroundColor Green
}
Write-Host ""

# Read logs after start
Write-Host "4. Reading Logs After Start:" -ForegroundColor Cyan
Start-Sleep -Seconds 2
$newLogs = Get-WinEvent -LogName Application -MaxEvents 100 -ErrorAction SilentlyContinue | 
    Where-Object { 
        ($_.Message -like "*FastSearch*" -or $_.ProviderName -like "*FastSearch*") -and
        $_.TimeCreated -gt (Get-Date).AddMinutes(-2)
    } | Select-Object -First 10

if ($newLogs) {
    Write-Host "   Found $($newLogs.Count) new entries:" -ForegroundColor Green
    foreach ($log in $newLogs) {
        $time = $log.TimeCreated.ToString("HH:mm:ss")
        $level = $log.LevelDisplayName
        $id = $log.Id
        $msg = $log.Message.Substring(0, [Math]::Min(300, $log.Message.Length))
        Write-Host "   [$time] $level (ID: $id)" -ForegroundColor $(if ($level -eq "Error") { "Red" } else { "White" })
        Write-Host "      $msg" -ForegroundColor Gray
    }
} else {
    Write-Host "   No new log entries" -ForegroundColor Yellow
}
Write-Host ""

# Test pipe
$service.Refresh()
if ($service.Status -eq "Running") {
    Write-Host "5. Testing Pipe Connection:" -ForegroundColor Cyan
    python -c "import sys; sys.path.insert(0, 'src'); import asyncio; from fastsearch_mcp.pipe_client import test_pipe_connection; result = asyncio.run(test_pipe_connection()); print(f'   Pipe: {\"SUCCESS\" if result else \"FAILED\"}')"
    Write-Host ""
}

# Stop service
Write-Host "6. Stopping Service:" -ForegroundColor Cyan
if ($service.Status -eq "Running") {
    Stop-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    $service.Refresh()
    Write-Host "   Status: $($service.Status)" -ForegroundColor Green
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "Test Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green


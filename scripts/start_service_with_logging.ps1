# Start the service and monitor logs in real-time
# Requires administrator privileges

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires administrator privileges!" -ForegroundColor Red
    exit 1
}

Write-Host "============================================================" -ForegroundColor Green
Write-Host "Starting FastSearch Service with Log Monitoring" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Check if service exists
$service = Get-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
if (-not $service) {
    Write-Host "[ERROR] Service 'FastSearchMCP' not found!" -ForegroundColor Red
    Write-Host "Please install the service first." -ForegroundColor Yellow
    exit 1
}

# Stop service if running
if ($service.Status -eq "Running") {
    Write-Host "Stopping existing service..." -ForegroundColor Cyan
    Stop-Service -Name "FastSearchMCP" -Force
    Start-Sleep -Seconds 2
}

# Clear old logs (optional - comment out if you want to keep history)
Write-Host "Checking for recent logs..." -ForegroundColor Cyan
$recentLogs = Get-EventLog -LogName Application -Source "FastSearchMCP" -Newest 5 -ErrorAction SilentlyContinue
if ($recentLogs) {
    Write-Host "Found $($recentLogs.Count) recent log entries" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting service..." -ForegroundColor Cyan
try {
    Start-Service -Name "FastSearchMCP" -ErrorAction Stop
    Write-Host "[OK] Service start command issued" -ForegroundColor Green
    
    # Wait a bit for service to start
    Start-Sleep -Seconds 3
    
    # Check service status
    $service.Refresh()
    Write-Host "Service Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
    
    if ($service.Status -ne "Running") {
        Write-Host ""
        Write-Host "[ERROR] Service failed to start!" -ForegroundColor Red
        Write-Host "Checking System Event Log for crash details..." -ForegroundColor Yellow
        Write-Host ""
        
        $crashLog = Get-EventLog -LogName System -Source "Service Control Manager" -Newest 10 -ErrorAction SilentlyContinue | 
            Where-Object { $_.Message -like "*FastSearch*" } | 
            Select-Object -First 1
        
        if ($crashLog) {
            Write-Host "Crash Event:" -ForegroundColor Red
            Write-Host "  Time: $($crashLog.TimeGenerated)" -ForegroundColor Gray
            Write-Host "  Type: $($crashLog.EntryType)" -ForegroundColor Gray
            Write-Host "  Message: $($crashLog.Message)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "Reading Application Event Log..." -ForegroundColor Yellow
        $appLogs = Get-EventLog -LogName Application -Source "FastSearchMCP" -Newest 10 -ErrorAction SilentlyContinue
        if ($appLogs) {
            Write-Host "Found $($appLogs.Count) Application log entries:" -ForegroundColor Green
            foreach ($log in $appLogs) {
                $time = $log.TimeGenerated.ToString("HH:mm:ss.fff")
                $type = $log.EntryType
                $msg = $log.Message.Substring(0, [Math]::Min(200, $log.Message.Length))
                Write-Host "  [$time] $type : $msg" -ForegroundColor $(if ($type -eq "Error") { "Red" } elseif ($type -eq "Warning") { "Yellow" } else { "White" })
            }
        } else {
            Write-Host "No Application log entries found" -ForegroundColor Yellow
            Write-Host "(Service may have crashed before logging)" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "TIP: Check DebugView for OutputDebugString messages" -ForegroundColor Cyan
        Write-Host "     Run: scripts\setup_debugview.ps1" -ForegroundColor Gray
        
        exit 1
    }
    
    Write-Host ""
    Write-Host "Service is running! Reading logs..." -ForegroundColor Green
    Write-Host ""
    
    # Wait a moment for logs to be written
    Start-Sleep -Seconds 2
    
    # Read Application logs
    $appLogs = Get-EventLog -LogName Application -Source "FastSearchMCP" -Newest 20 -ErrorAction SilentlyContinue
    if ($appLogs) {
        Write-Host "Application Event Log entries:" -ForegroundColor Cyan
        Write-Host ""
        foreach ($log in $appLogs) {
            $time = $log.TimeGenerated.ToString("HH:mm:ss.fff")
            $type = $log.EntryType
            $id = $log.EventID
            $msg = $log.Message
            $color = if ($type -eq "Error") { "Red" } elseif ($type -eq "Warning") { "Yellow" } else { "Green" }
            Write-Host "  [$time] $type (ID: $id)" -ForegroundColor $color
            Write-Host "    $msg" -ForegroundColor Gray
            Write-Host ""
        }
    } else {
        Write-Host "No Application log entries found yet" -ForegroundColor Yellow
        Write-Host "(Service may not have logged anything yet)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "[SUCCESS] Service started and logs read successfully!" -ForegroundColor Green
    
} catch {
    Write-Host "[ERROR] Failed to start service: $_" -ForegroundColor Red
    exit 1
}


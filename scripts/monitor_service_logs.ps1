# Real-time service log monitor
# Keeps running and shows new log entries as they appear

Write-Host "============================================================" -ForegroundColor Green
Write-Host "FastSearch Service - Real-Time Log Monitor" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

# Get the latest log entry timestamp to start from
$lastTime = Get-Date
$lastEventId = 0

# Check service status
$service = Get-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Service Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq "Running") { "Green" } else { "Red" })
} else {
    Write-Host "Service Status: Not Found" -ForegroundColor Red
}
Write-Host ""

Write-Host "Monitoring logs (showing new entries as they appear)..." -ForegroundColor Cyan
Write-Host ""

# Function to display log entry
function Show-LogEntry {
    param($log)
    
    $time = $log.TimeGenerated.ToString("HH:mm:ss.fff")
    $type = $log.EntryType
    $id = $log.EventID
    
    # Extract message (handle the Windows Event Log format)
    $message = $log.Message
    if ($message -match "The following information is part of the event:'(.+)'") {
        $message = $matches[1]
    } elseif ($message.Length -gt 200) {
        $message = $message.Substring(0, 200) + "..."
    }
    
    $color = switch ($type) {
        "Error" { "Red" }
        "Warning" { "Yellow" }
        "Information" { "Green" }
        default { "White" }
    }
    
    Write-Host "[$time] " -NoNewline -ForegroundColor Gray
    Write-Host "$type " -NoNewline -ForegroundColor $color
    Write-Host "(ID: $id) " -NoNewline -ForegroundColor Gray
    Write-Host $message -ForegroundColor White
}

# Show recent logs first
Write-Host "--- Recent Log Entries ---" -ForegroundColor Cyan
$recentLogs = Get-EventLog -LogName Application -Source "FastSearchMCP" -Newest 5 -ErrorAction SilentlyContinue
if ($recentLogs) {
    foreach ($log in $recentLogs) {
        Show-LogEntry $log
        $lastTime = $log.TimeGenerated
        $lastEventId = $log.Index
    }
} else {
    Write-Host "No recent log entries found" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "--- Waiting for new entries ---" -ForegroundColor Cyan
Write-Host ""

# Monitor loop
try {
    while ($true) {
        Start-Sleep -Milliseconds 500
        
        # Check for new Application logs
        $newLogs = Get-EventLog -LogName Application -Source "FastSearchMCP" -ErrorAction SilentlyContinue | 
            Where-Object { 
                $_.TimeGenerated -gt $lastTime -or 
                ($_.TimeGenerated -eq $lastTime -and $_.Index -gt $lastEventId)
            } | 
            Sort-Object TimeGenerated, Index
        
        if ($newLogs) {
            foreach ($log in $newLogs) {
                Show-LogEntry $log
                $lastTime = $log.TimeGenerated
                $lastEventId = $log.Index
            }
        }
        
        # Check service status changes
        $currentService = Get-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
        if ($currentService -and $service) {
            if ($currentService.Status -ne $service.Status) {
                $oldStatus = $service.Status
                $newStatus = $currentService.Status
                Write-Host "[$(Get-Date -Format 'HH:mm:ss.fff')] " -NoNewline -ForegroundColor Gray
                Write-Host "Service Status Changed: " -NoNewline -ForegroundColor Yellow
                Write-Host "$oldStatus -> $newStatus" -ForegroundColor $(if ($newStatus -eq "Running") { "Green" } else { "Red" })
                $service = $currentService
            }
        }
        
        # Check System logs for crashes
        $systemLogs = Get-EventLog -LogName System -Source "Service Control Manager" -Newest 1 -ErrorAction SilentlyContinue | 
            Where-Object { 
                $_.Message -like "*FastSearch*" -and 
                $_.TimeGenerated -gt $lastTime 
            }
        
        if ($systemLogs) {
            foreach ($log in $systemLogs) {
                $time = $log.TimeGenerated.ToString("HH:mm:ss.fff")
                Write-Host "[$time] " -NoNewline -ForegroundColor Gray
                Write-Host "SYSTEM " -NoNewline -ForegroundColor Magenta
                Write-Host "$($log.EntryType) " -NoNewline -ForegroundColor $(if ($log.EntryType -eq "Error") { "Red" } else { "Yellow" })
                $msg = $log.Message.Substring(0, [Math]::Min(200, $log.Message.Length))
                Write-Host $msg -ForegroundColor White
                $lastTime = $log.TimeGenerated
            }
        }
    }
} catch {
    Write-Host ""
    Write-Host "Monitoring stopped: $_" -ForegroundColor Red
}


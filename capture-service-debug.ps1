# Capture OutputDebugString messages from FastSearch service
# Run this BEFORE starting the service, then start the service in another window

Write-Host "FastSearch MCP Service Debug Output Capture" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will capture OutputDebugString messages from the service." -ForegroundColor Yellow
Write-Host "Start the service in another elevated PowerShell window with:" -ForegroundColor Yellow
Write-Host "  .\install-service.ps1 start" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop capturing..." -ForegroundColor Cyan
Write-Host ""

# Use dbgview or check Event Viewer for OutputDebugString
# For now, we'll monitor the service process and check logs

$ServiceName = "FastSearchMCP"

while ($true) {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq "Running") {
        $process = Get-Process -Name FastSearchServiceNew -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Service is RUNNING (PID: $($process.Id))" -ForegroundColor Green
        }
    } elseif ($service -and $service.Status -eq "Stopped") {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Service is STOPPED" -ForegroundColor Red
        
        # Check for new error logs
        $errors = Get-EventLog -LogName Application -Newest 5 -ErrorAction SilentlyContinue | 
            Where-Object { 
                $_.Source -eq $ServiceName -and 
                $_.TimeGenerated -gt (Get-Date).AddSeconds(-5) 
            }
        
        if ($errors) {
            foreach ($err in $errors) {
                $msg = if ($err.Message -match "The following information is part of the event:'(.*)'") { 
                    $matches[1] 
                } else { 
                    $err.Message 
                }
                Write-Host "  [$($err.TimeGenerated.ToString('HH:mm:ss'))] [$($err.EntryType)] $msg" -ForegroundColor $(if ($err.EntryType -eq 'Error') { 'Red' } else { 'Yellow' })
            }
        }
    }
    
    Start-Sleep -Seconds 1
}


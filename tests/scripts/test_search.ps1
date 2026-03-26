# Quick diagnostic script for FastSearch
Write-Host "Testing FastSearch Service..." -ForegroundColor Cyan

# Check service status
$service = Get-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
if ($service) {
    Write-Host "Service Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Red' })
} else {
    Write-Host "Service not found!" -ForegroundColor Red
    exit 1
}

# Check if pipe exists (requires service to be running)
Write-Host "`nTesting named pipe connection..." -ForegroundColor Cyan
try {
    $pipe = New-Object System.IO.Pipes.NamedPipeClientStream('.', 'FastSearchMCP', [System.IO.Pipes.PipeDirection]::InOut, [System.IO.Pipes.PipeOptions]::None)
    $pipe.Connect(1000)  # 1 second timeout
    Write-Host "Pipe connection: SUCCESS" -ForegroundColor Green
    $pipe.Close()
} catch {
    Write-Host "Pipe connection: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# Check recent service logs
Write-Host "`nRecent service events:" -ForegroundColor Cyan
Get-EventLog -LogName Application -Source "FastSearchMCP" -Newest 3 -ErrorAction SilentlyContinue | ForEach-Object {
    $color = switch ($_.EntryType) {
        'Error' { 'Red' }
        'Warning' { 'Yellow' }
        default { 'White' }
    }
    Write-Host "[$($_.EntryType)] $($_.TimeGenerated): $($_.Message.Substring(0, [Math]::Min(80, $_.Message.Length)))" -ForegroundColor $color
}

Write-Host "`nDone." -ForegroundColor Cyan


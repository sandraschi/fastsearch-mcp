# Rebuild, install, start, test, and read logs for FastSearch service
# Requires admin privileges

Write-Host "============================================================" -ForegroundColor Green
Write-Host "FastSearch Service - Rebuild, Install, Test, Logs" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

$exe = "service\build\bin\Release\FastSearchServiceNew.exe"

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Uninstall existing service
Write-Host "1. Uninstalling existing service (if any)..." -ForegroundColor Cyan
if (Get-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue) {
    Stop-Service -Name "FastSearchMCP" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    & $exe --uninstall 2>&1 | Out-Null
    Start-Sleep -Seconds 2
}
Write-Host "   Done" -ForegroundColor Green
Write-Host ""

# Install service
Write-Host "2. Installing service..." -ForegroundColor Cyan
& $exe --install
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Service installed" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Installation failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Start service
Write-Host "3. Starting service..." -ForegroundColor Cyan
Start-Service -Name "FastSearchMCP" -ErrorAction Stop
Start-Sleep -Seconds 5
$svc = Get-Service -Name "FastSearchMCP"
Write-Host "   Status: $($svc.Status)" -ForegroundColor $(if ($svc.Status -eq "Running") { "Green" } else { "Red" })
if ($svc.Status -ne "Running") {
    Write-Host "   [ERROR] Service failed to start" -ForegroundColor Red
    Write-Host ""
    Write-Host "Reading System Event Log for errors..." -ForegroundColor Yellow
    Get-EventLog -LogName System -Source "Service Control Manager" -Newest 10 -ErrorAction SilentlyContinue | 
        Where-Object { $_.Message -like "*FastSearch*" } | 
        Select-Object -First 3 TimeGenerated, EntryType, @{Name='Message';Expression={$_.Message.Substring(0,[Math]::Min(300,$_.Message.Length))}} | 
        Format-List
    exit 1
}
Write-Host ""

# Test pipe connection
Write-Host "4. Testing pipe connection..." -ForegroundColor Cyan
python -c "import sys; sys.path.insert(0, 'src'); import asyncio; from fastsearch_mcp.pipe_client import NamedPipeClient; async def test(): client = NamedPipeClient(); await client.connect(); print('   [OK] Pipe connected'); result = await client.send_request({'command': 'ping'}); print(f'   [OK] Ping: {result}'); await client.disconnect(); asyncio.run(test())"
Write-Host ""

# Read logs
Write-Host "5. Reading service logs..." -ForegroundColor Cyan
python tests\read_service_logs.py
Write-Host ""

# Read System logs
Write-Host "6. Reading System Event Log..." -ForegroundColor Cyan
$systemLogs = Get-EventLog -LogName System -Source "Service Control Manager" -Newest 20 -ErrorAction SilentlyContinue | 
    Where-Object { $_.Message -like "*FastSearch*" } | 
    Select-Object -First 5

if ($systemLogs) {
    Write-Host "   Found $($systemLogs.Count) entries:" -ForegroundColor Green
    foreach ($log in $systemLogs) {
        $time = $log.TimeGenerated.ToString("HH:mm:ss")
        $type = $log.EntryType
        $msg = $log.Message.Substring(0, [Math]::Min(200, $log.Message.Length))
        Write-Host "   [$time] $type : $msg" -ForegroundColor $(if ($type -eq "Error") { "Red" } else { "White" })
    }
} else {
    Write-Host "   No System log entries found" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "Test Complete" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green


# Rebuild and restart service with admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires administrator privileges!" -ForegroundColor Red
    exit 1
}

$projectRoot = "d:\Dev\repos\fastsearch-mcp"
$serviceDir = "$projectRoot\service"
$exe = "$serviceDir\build\bin\Release\FastSearchServiceNew.exe"

Write-Host "Stopping service..." -ForegroundColor Cyan
Stop-Service -Name "FastSearchMCP" -Force -ErrorAction SilentlyContinue
Get-Process -Name "FastSearchServiceNew" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

Write-Host "Rebuilding..." -ForegroundColor Cyan
Set-Location $serviceDir
cmake --build build --config Release 2>&1 | Select-Object -Last 10

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Build successful" -ForegroundColor Green
    
    Write-Host "Reinstalling service..." -ForegroundColor Cyan
    & $exe --uninstall 2>&1 | Out-Null
    Start-Sleep -Seconds 1
    & $exe --install
    Start-Sleep -Seconds 1
    
    Write-Host "Starting service..." -ForegroundColor Cyan
    Start-Service -Name "FastSearchMCP"
    Start-Sleep -Seconds 3
    
    $svc = Get-Service -Name "FastSearchMCP"
    Write-Host "Service Status: $($svc.Status)" -ForegroundColor $(if ($svc.Status -eq "Running") { "Green" } else { "Red" })
} else {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
}


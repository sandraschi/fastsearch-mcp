# Register FastSearchMCP as an event source in Windows Event Log
# Requires administrator privileges

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator." -ForegroundColor Yellow
    exit 1
}

$eventSourceName = "FastSearchMCP"
$logName = "Application"
$registryPath = "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\$logName\$eventSourceName"

Write-Host "Registering event source: $eventSourceName" -ForegroundColor Cyan
Write-Host ""

# Get the service executable path
$serviceExe = "D:\Dev\repos\fastsearch-mcp\service\build\bin\Release\FastSearchServiceNew.exe"
if (-not (Test-Path $serviceExe)) {
    Write-Host "[ERROR] Service executable not found: $serviceExe" -ForegroundColor Red
    Write-Host "Please build the service first." -ForegroundColor Yellow
    exit 1
}

$serviceExe = Resolve-Path $serviceExe

try {
    # Create the registry key if it doesn't exist
    if (-not (Test-Path $registryPath)) {
        New-Item -Path $registryPath -Force | Out-Null
        Write-Host "[OK] Created registry key: $registryPath" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Registry key already exists: $registryPath" -ForegroundColor Yellow
    }

    # Set the EventMessageFile to point to the service executable
    Set-ItemProperty -Path $registryPath -Name "EventMessageFile" -Value $serviceExe -Type ExpandString -Force
    Write-Host "[OK] Set EventMessageFile to: $serviceExe" -ForegroundColor Green

    # Set TypesSupported (bitmask: 1=Error, 2=Warning, 4=Information, 8=SuccessAudit, 16=FailureAudit)
    # We support Error (1), Warning (2), and Information (4) = 7
    Set-ItemProperty -Path $registryPath -Name "TypesSupported" -Value 7 -Type DWord -Force
    Write-Host "[OK] Set TypesSupported to 7 (Error, Warning, Information)" -ForegroundColor Green

    # Set CategoryCount (0 = no categories)
    Set-ItemProperty -Path $registryPath -Name "CategoryCount" -Value 0 -Type DWord -Force
    Write-Host "[OK] Set CategoryCount to 0" -ForegroundColor Green

    Write-Host ""
    Write-Host "[SUCCESS] Event source '$eventSourceName' registered successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The service can now write to the Windows Event Log." -ForegroundColor Cyan
    Write-Host "Registry path: $registryPath" -ForegroundColor Gray

} catch {
    Write-Host "[ERROR] Failed to register event source: $_" -ForegroundColor Red
    exit 1
}


# FastSearch MCP Service Installation Script
# Usage:
#   Install:   .\install_service.ps1 -Action install
#   Uninstall: .\install_service.ps1 -Action uninstall
#   Start:     .\install_service.ps1 -Action start
#   Stop:      .\install_service.ps1 -Action stop

param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("install", "uninstall", "start", "stop")]
    [string]$Action
)

$ErrorActionPreference = "Stop"

# Service configuration
$serviceName = "FastSearchMCP"
$serviceDisplayName = "FastSearch MCP Service"
$serviceDescription = "Provides fast file search capabilities using MFT"

# Try multiple possible paths for the service executable
$possiblePaths = @(
    "$PSScriptRoot\build\bin\Release\FastSearchServiceNew.exe",
    "$PSScriptRoot\dist\FastSearchService.exe",
    "$PSScriptRoot\..\service\build\bin\Release\FastSearchServiceNew.exe"
)

$serviceExePath = $null
foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $serviceExePath = $path
        break
    }
}

if (-not $serviceExePath) {
    Write-Error "Service executable not found. Checked paths:"
    foreach ($path in $possiblePaths) {
        Write-Host "  - $path" -ForegroundColor Yellow
    }
    exit 1
}

# Check if running as administrator
function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Error "This script must be run as an administrator"
    exit 1
}

# Install the service
function Install-Service {
    if (Get-Service $serviceName -ErrorAction SilentlyContinue) {
        Write-Host "Service is already installed." -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path $serviceExePath)) {
        Write-Error "Service executable not found at $serviceExePath. Please build the service first."
        exit 1
    }

    try {
        # Create the service
        New-Service -Name $serviceName `
                   -BinaryPathName "`"$serviceExePath`"" `
                   -DisplayName $serviceDisplayName `
                   -Description $serviceDescription `
                   -StartupType Automatic `
                   -ErrorAction Stop

        # Set service to auto-restart on failure
        $service = Get-WmiObject -Class Win32_Service -Filter "Name='$serviceName'"
        $service.Change($null, $null, $null, $null, $null, $null, $null, $null, $null, $null, $null) | Out-Null
        
        Write-Host "Service installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to install service: $_"
        exit 1
    }
}

# Uninstall the service
function Uninstall-Service {
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "Service is not installed." -ForegroundColor Yellow
        return
    }

    # Stop the service if running
    if ($service.Status -eq 'Running') {
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
    }

    try {
        # Delete the service
        $service | Remove-Service -Force -ErrorAction Stop
        Write-Host "Service uninstalled successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to uninstall service: $_"
        exit 1
    }
}

# Start the service
function Start-ServiceEx {
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Error "Service is not installed."
        exit 1
    }

    if ($service.Status -eq 'Running') {
        Write-Host "Service is already running." -ForegroundColor Yellow
        return
    }

    try {
        Start-Service -Name $serviceName -ErrorAction Stop
        Write-Host "Service started successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to start service: $_"
        exit 1
    }
}

# Stop the service
function Stop-ServiceEx {
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Error "Service is not installed."
        exit 1
    }

    if ($service.Status -eq 'Stopped') {
        Write-Host "Service is already stopped." -ForegroundColor Yellow
        return
    }

    try {
        Stop-Service -Name $serviceName -Force -ErrorAction Stop
        Write-Host "Service stopped successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to stop service: $_"
        exit 1
    }
}

# Main script execution
switch ($Action) {
    "install" { Install-Service }
    "uninstall" { Uninstall-Service }
    "start" { Start-ServiceEx }
    "stop" { Stop-ServiceEx }
    default { Write-Error "Invalid action specified" }
}

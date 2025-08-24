<#
.SYNOPSIS
    Uninstalls the FastSearch MCP Bridge Windows service.

.DESCRIPTION
    This script uninstalls the FastSearch MCP Bridge Windows service and cleans up
    related files and configurations. It handles:
    - Stopping and removing the Windows service
    - Removing firewall rules
    - Cleaning up installation directory
    - Removing environment variables

.PARAMETER InstallDir
    The installation directory of the service.
    Default: "$env:ProgramFiles\FastSearchMCP"

.PARAMETER ServiceName
    The name of the Windows service.
    Default: "FastSearchMCP"

.EXAMPLE
    .\uninstall_service.ps1
    Uninstalls the service with default settings.

.EXAMPLE
    .\uninstall_service.ps1 -InstallDir "C:\FastSearch"
    Uninstalls the service from a custom directory.
#>

[CmdletBinding()]
param(
    [string]$InstallDir = "$env:ProgramFiles\FastSearchMCP",
    [string]$ServiceName = "FastSearchMCP",
    [switch]$Force
)

# Check if running as administrator
function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Error "This script requires administrator privileges. Please run as administrator."
    exit 1
}

# Stop and remove the service
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($service) {
    Write-Host "Stopping service '$ServiceName'..." -ForegroundColor Cyan
    try {
        Stop-Service -Name $ServiceName -Force -ErrorAction Stop
        Write-Host "Service stopped successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to stop service: $_"
        if (-not $Force) {
            $continue = Read-Host "Continue with uninstallation? (Y/N)"
            if ($continue -ne 'Y') {
                Write-Host "Uninstallation aborted by user" -ForegroundColor Yellow
                exit 1
            }
        }
    }

    # Try to uninstall using NSSM first
    $nssmPath = Join-Path $env:TEMP "nssm.exe"
    if (Test-Path $nssmPath) {
        Write-Host "Removing service using NSSM..." -ForegroundColor Cyan
        & $nssmPath remove $ServiceName confirm
    } else {
        # Fall back to pywin32
        $serviceScriptPath = Join-Path $InstallDir "fastsearch_mcp_service.py"
        if (Test-Path $serviceScriptPath) {
            Write-Host "Removing service using pywin32..." -ForegroundColor Cyan
            $pythonPath = (Get-Command python).Source
            & $pythonPath "$serviceScriptPath" remove
        } else {
            # Last resort: use sc.exe
            Write-Host "Removing service using sc.exe..." -ForegroundColor Cyan
            sc.exe delete $ServiceName | Out-Null
        }
    }
    
    Start-Sleep -Seconds 2  # Give the service time to be removed
    
    # Verify service is removed
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Warning "Failed to remove service. You may need to remove it manually."
    } else {
        Write-Host "Service removed successfully" -ForegroundColor Green
    }
} else {
    Write-Host "Service '$ServiceName' not found" -ForegroundColor Yellow
}

# Remove firewall rules
Write-Host "Removing firewall rules..." -ForegroundColor Cyan
$firewallRuleName = "FastSearch MCP Bridge"
$firewallRule = Get-NetFirewallRule -DisplayName $firewallRuleName -ErrorAction SilentlyContinue

if ($firewallRule) {
    try {
        Remove-NetFirewallRule -DisplayName $firewallRuleName -ErrorAction Stop
        Write-Host "Firewall rules removed successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to remove firewall rules: $_"
    }
} else {
    Write-Host "No firewall rules found" -ForegroundColor Yellow
}

# Remove from PATH
Write-Host "Updating system PATH..." -ForegroundColor Cyan
$currentPath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
if ($currentPath -like "*$InstallDir*") {
    try {
        $newPath = ($currentPath -split ';' | Where-Object { $_ -ne $InstallDir }) -join ';'
        [Environment]::SetEnvironmentVariable('Path', $newPath, 'Machine')
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        Write-Host "Removed from system PATH" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to update system PATH: $_"
    }
}

# Remove desktop shortcut
$desktopShortcut = "$env:USERPROFILE\Desktop\$ServiceName.lnk"
if (Test-Path $desktopShortcut) {
    try {
        Remove-Item -Path $desktopShortcut -Force -ErrorAction Stop
        Write-Host "Removed desktop shortcut" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to remove desktop shortcut: $_"
    }
}

# Remove installation directory
if (Test-Path $InstallDir) {
    if (-not $Force) {
        $removeFiles = Read-Host "Remove installation directory '$InstallDir'? (Y/N)"
    }
    
    if ($Force -or $removeFiles -eq 'Y') {
        try {
            Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction Stop
            Write-Host "Installation directory removed" -ForegroundColor Green
        } catch {
            Write-Warning "Failed to remove installation directory: $_"
            Write-Warning "You may need to close any open files or folders in '$InstallDir' and try again."
        }
    } else {
        Write-Host "Installation directory preserved: $InstallDir" -ForegroundColor Yellow
    }
}

# Clean up NSSM
if (Test-Path $nssmPath) {
    try {
        Remove-Item -Path $nssmPath -Force -ErrorAction Stop
    } catch {
        Write-Warning "Failed to remove NSSM: $_"
    }
}

Write-Host "`nUninstallation complete!" -ForegroundColor Green
Write-Host "Some files may need to be removed manually." -ForegroundColor Yellow

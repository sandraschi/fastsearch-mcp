<#
.SYNOPSIS
    Installs and configures the FastSearch MCP Bridge as a Windows service.

.DESCRIPTION
    This script installs the FastSearch MCP Bridge as a Windows service with the
    appropriate configuration. It handles:
    - Python environment setup
    - Service installation
    - Firewall rules
    - Logging configuration
    - Automatic startup

.PARAMETER InstallDir
    The directory where the service will be installed.
    Default: "$env:ProgramFiles\FastSearchMCP"

.PARAMETER ServiceName
    The name of the Windows service.
    Default: "FastSearchMCP"

.PARAMETER ServiceDisplayName
    The display name of the Windows service.
    Default: "FastSearch MCP Bridge"

.PARAMETER ServiceDescription
    The description of the Windows service.
    Default: "Provides fast NTFS file system indexing and search capabilities via MCP 2.11.3 protocol."

.EXAMPLE
    .\setup_service.ps1
    Installs the service with default settings.

.EXAMPLE
    .\setup_service.ps1 -InstallDir "C:\FastSearch"
    Installs the service to a custom directory.
#>

[CmdletBinding()]
param(
    [string]$InstallDir = "$env:ProgramFiles\FastSearchMCP",
    [string]$ServiceName = "FastSearchMCP",
    [string]$ServiceDisplayName = "FastSearch MCP Bridge",
    [string]$ServiceDescription = "Provides fast NTFS file system indexing and search capabilities via MCP 2.11.3 protocol.",
    [switch]$Force
)

#region Helper Functions
function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-PythonInstalled {
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match 'Python 3\.[0-9]+\.[0-9]+') {
            return $true
        }
    } catch {
        return $false
    }
    return $false
}

function Install-Python {
    Write-Host "Python not found. Installing Python 3.11..." -ForegroundColor Yellow
    
    $pythonInstallerUrl = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe"
    $installerPath = "$env:TEMP\python_installer.exe"
    
    try {
        # Download Python installer
        Write-Host "Downloading Python installer..."
        Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath
        
        # Install Python silently
        Write-Host "Installing Python..."
        $installArgs = @(
            "/quiet",
            "InstallAllUsers=1",
            "PrependPath=1",
            "Include_test=0",
            "CompileAll=1"
        )
        
        $process = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -ne 0) {
            throw "Python installation failed with exit code $($process.ExitCode)"
        }
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        # Verify installation
        if (-not (Test-PythonInstalled)) {
            throw "Python installation verification failed"
        }
        
        Write-Host "Python installed successfully" -ForegroundColor Green
        return $true
    } catch {
        Write-Error "Failed to install Python: $_"
        return $false
    } finally {
        # Clean up installer
        if (Test-Path $installerPath) {
            Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Install-PythonPackage {
    param(
        [string]$PackageName,
        [string]$Version = ""
    )
    
    $packageSpec = if ($Version) { "$PackageName==$Version" } else { $PackageName }
    
    Write-Host "Installing Python package: $packageSpec"
    $pipArgs = @(
        "install",
        "--upgrade",
        "--no-warn-script-location",
        $packageSpec
    )
    
    $process = Start-Process -FilePath "python" -ArgumentList "-m pip $pipArgs" -Wait -NoNewWindow -PassThru
    
    if ($process.ExitCode -ne 0) {
        throw "Failed to install Python package: $packageSpec"
    }
}
#endregion

#region Main Script
# Check if running as administrator
if (-not (Test-Administrator)) {
    Write-Error "This script requires administrator privileges. Please run as administrator."
    exit 1
}

# Check Python installation
if (-not (Test-PythonInstalled)) {
    if (-not $Force) {
        $installPython = Read-Host "Python is not installed. Do you want to install Python 3.11? (Y/N)"
        if ($installPython -ne 'Y') {
            Write-Host "Python is required. Exiting." -ForegroundColor Red
            exit 1
        }
    }
    
    if (-not (Install-Python)) {
        Write-Error "Failed to install Python. Exiting."
        exit 1
    }
}

# Install required Python packages
Write-Host "Installing required Python packages..." -ForegroundColor Cyan
$requiredPackages = @(
    "pywin32",
    "psutil",
    "pypiwin32"
)

try {
    foreach ($package in $requiredPackages) {
        Install-PythonPackage -PackageName $package
    }
} catch {
    Write-Error "Failed to install required Python packages: $_"
    exit 1
}

# Create installation directory
Write-Host "Creating installation directory: $InstallDir" -ForegroundColor Cyan
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Copy files
Write-Host "Copying files..." -ForegroundColor Cyan
$sourceDir = Split-Path -Parent $PSScriptRoot
$destinationDir = $InstallDir

# Copy only necessary files
$filesToCopy = @(
    "fastsearch_mcp_bridge\src\fastsearch_mcp",
    "requirements.txt",
    "README.md",
    "LICENSE"
)

foreach ($file in $filesToCopy) {
    $sourcePath = Join-Path $sourceDir $file
    $destPath = Join-Path $destinationDir $file
    
    if (Test-Path $sourcePath) {
        Write-Host "Copying $file..."
        if (Test-Path -Path $sourcePath -PathType Container) {
            # Copy directory
            if (-not (Test-Path (Split-Path $destPath -Parent))) {
                New-Item -ItemType Directory -Path (Split-Path $destPath -Parent) -Force | Out-Null
            }
            Copy-Item -Path "$sourcePath\*" -Destination $destPath -Recurse -Force
        } else {
            # Copy file
            Copy-Item -Path $sourcePath -Destination $destPath -Force
        }
    } else {
        Write-Warning "Source file not found: $sourcePath"
    }
}

# Create service executable
$serviceScript = @"
import sys
import os
import servicemanager
import win32event
import win32service
import win32serviceutil
from fastsearch_mcp.cli import main as mcp_main

class FastSearchMCPService(win32serviceutil.ServiceFramework):
    _svc_name_ = "$ServiceName"
    _svc_display_name_ = "$ServiceDisplayName"
    _svc_description_ = "$ServiceDescription"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
    
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
    
    def main(self):
        # Change to the installation directory
        os.chdir(r"$InstallDir")
        
        # Configure logging
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join("$InstallDir", "fastsearch_mcp.log")),
                logging.StreamHandler()
            ]
        )
        
        # Start the MCP server
        mcp_main()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FastSearchMCPService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(FastSearchMCPService)
"@

$serviceScriptPath = Join-Path $InstallDir "fastsearch_mcp_service.py"
Set-Content -Path $serviceScriptPath -Value $serviceScript -Encoding UTF8

# Install the service
Write-Host "Installing Windows service..." -ForegroundColor Cyan
$pythonPath = (Get-Command python).Source
$servicePath = "$pythonPath \"$serviceScriptPath\""

# Create a batch file to run the service
$batchContent = @"
@echo off
"$pythonPath" "$serviceScriptPath" %*
"@

$batchPath = Join-Path $InstallDir "start_service.cmd"
Set-Content -Path $batchPath -Value $batchContent -Encoding ASCII

# Install the service
$serviceArgs = @(
    "--startup", "auto",
    "--name", $ServiceName,
    "--display-name", $ServiceDisplayName,
    "--description", $ServiceDescription,
    "--python", "$pythonPath",
    "--add-python-path",
    "--stop-timeout", "30",
    "--startup", "auto",
    "--user", "LocalSystem"
)

# Use NSSM (Non-Sucking Service Manager) if available, otherwise use pywin32
$nssmPath = Join-Path $env:TEMP "nssm.exe"
$useNssm = $false

try {
    # Try to download NSSM
    Invoke-WebRequest -Uri "https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip" -OutFile "$env:TEMP\nssm.zip"
    Expand-Archive -Path "$env:TEMP\nssm.zip" -DestinationPath "$env:TEMP\nssm" -Force
    $nssmExe = Get-ChildItem -Path "$env:TEMP\nssm" -Filter "nssm.exe" -Recurse | Select-Object -First 1
    
    if ($nssmExe) {
        Copy-Item -Path $nssmExe.FullName -Destination $nssmPath -Force
        $useNssm = $true
        
        # Install service using NSSM
        & $nssmPath install $ServiceName $pythonPath "$serviceScriptPath"
        & $nssmPath set $ServiceName AppDirectory "$InstallDir"
        & $nssmPath set $ServiceName Description "$ServiceDescription"
        & $nssmPath set $ServiceName Start SERVICE_AUTO_START
        
        Write-Host "Service installed using NSSM" -ForegroundColor Green
    }
} catch {
    Write-Warning "Failed to use NSSM, falling back to pywin32: $_"
    $useNssm = $false
}

if (-not $useNssm) {
    # Fall back to pywin32
    Write-Host "Installing service using pywin32..." -ForegroundColor Yellow
    & $pythonPath -m pip install pywin32
    & $pythonPath "$serviceScriptPath" install
}

# Configure firewall
Write-Host "Configuring Windows Firewall..." -ForegroundColor Cyan
$firewallRuleName = "FastSearch MCP Bridge"
$firewallRule = Get-NetFirewallRule -DisplayName $firewallRuleName -ErrorAction SilentlyContinue

if (-not $firewallRule) {
    New-NetFirewallRule `
        -DisplayName $firewallRuleName `
        -Direction Inbound `
        -Program "$pythonPath" `
        -Action Allow `
        -Profile Any `
        -Description "Allow inbound connections to FastSearch MCP Bridge" | Out-Null
    
    Write-Host "Firewall rule added" -ForegroundColor Green
}

# Start the service
Write-Host "Starting service..." -ForegroundColor Cyan
if ($useNssm) {
    & $nssmPath start $ServiceName
} else {
    Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $?) {
        & $pythonPath "$serviceScriptPath" start
    }
}

# Verify service is running
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service -and $service.Status -eq 'Running') {
    Write-Host "Service installed and started successfully" -ForegroundColor Green
    
    # Create desktop shortcut
    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut("$env:USERPROFILE\Desktop\$ServiceDisplayName.lnk")
    $shortcut.TargetPath = "$pythonPath"
    $shortcut.Arguments = "-m fastsearch_mcp.cli"
    $shortcut.WorkingDirectory = $InstallDir
    $shortcut.IconLocation = (Get-Command python).Source
    $shortcut.Description = "$ServiceDisplayName"
    $shortcut.Save()
    
    Write-Host "Desktop shortcut created" -ForegroundColor Green
} else {
    Write-Warning "Service installed but could not be started. Please start it manually."
}

Write-Host "`nInstallation complete!" -ForegroundColor Green
Write-Host "Service installed to: $InstallDir"
Write-Host "Logs will be written to: $InstallDir\fastsearch_mcp.log"
Write-Host "`nYou can manage the service using the Services application or with these commands:"
Write-Host "  Start:    Start-Service $ServiceName"
Write-Host "  Stop:     Stop-Service $ServiceName"
Write-Host "  Restart:  Restart-Service $ServiceName"
Write-Host "  Status:   Get-Service $ServiceName"
Write-Host "  Uninstall: & '$pythonPath' '$serviceScriptPath' remove"

# Add to PATH
$currentPath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
if ($currentPath -notlike "*$InstallDir*") {
    [Environment]::SetEnvironmentVariable('Path', "$currentPath;$InstallDir", 'Machine')
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    Write-Host "`nAdded $InstallDir to system PATH" -ForegroundColor Green
}

# Clean up
if (Test-Path "$env:TEMP\nssm.zip") { Remove-Item "$env:TEMP\nssm.zip" -Force }
if (Test-Path "$env:TEMP\nssm") { Remove-Item "$env:TEMP\nssm" -Recurse -Force }

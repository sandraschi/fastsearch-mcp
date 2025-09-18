# FastSearch MCP Service Installer
# This script installs the FastSearch MCP Windows service with proper UAC handling

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "uninstall", "start", "stop", "status", "help")]
    [string]$Action = "help"
)

# Configuration
$ServiceName = "FastSearchMCP"
$ServiceDisplayName = "FastSearch MCP Service"
$ServiceDescription = "Provides fast file search capabilities using direct NTFS MFT access"
$ServiceExecutable = "service\build\bin\Release\FastSearchService.exe"
$ServicePath = Resolve-Path $ServiceExecutable -ErrorAction SilentlyContinue

# Colors for output
$SuccessColor = "Green"
$ErrorColor = "Red"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-ServiceExists {
    param([string]$ServiceName)
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    return $service -ne $null
}

function Get-ServiceStatus {
    param([string]$ServiceName)
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        return @{
            Exists = $true
            Status = $service.Status
            StartType = $service.StartType
        }
    }
    catch {
        return @{
            Exists = $false
            Status = $null
            StartType = $null
        }
    }
}

function Install-Service {
    Write-ColorOutput "Installing FastSearch MCP Service..." $InfoColor
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-ColorOutput "ERROR: Administrator privileges required for service installation!" $ErrorColor
        Write-ColorOutput "Please run PowerShell as Administrator and try again." $WarningColor
        return $false
    }
    
    # Check if service executable exists
    if (-not $ServicePath) {
        Write-ColorOutput "ERROR: Service executable not found at: $ServiceExecutable" $ErrorColor
        Write-ColorOutput "Please build the service first using: cmake --build service\build --config Release" $WarningColor
        return $false
    }
    
    # Check if service already exists
    if (Test-ServiceExists $ServiceName) {
        Write-ColorOutput "Service '$ServiceName' already exists. Uninstalling first..." $WarningColor
        Uninstall-Service
    }
    
    # Install the service
    Write-ColorOutput "Installing service from: $ServicePath" $InfoColor
    try {
        & $ServicePath --install
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Service installed successfully!" $SuccessColor
            Write-ColorOutput "Service Name: $ServiceName" $InfoColor
            Write-ColorOutput "Display Name: $ServiceDisplayName" $InfoColor
            Write-ColorOutput "Description: $ServiceDescription" $InfoColor
            return $true
        }
        else {
            Write-ColorOutput "❌ Service installation failed (exit code: $LASTEXITCODE)" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Service installation failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Uninstall-Service {
    Write-ColorOutput "Uninstalling FastSearch MCP Service..." $InfoColor
    
    # Check if running as administrator
    if (-not (Test-Administrator)) {
        Write-ColorOutput "ERROR: Administrator privileges required for service uninstallation!" $ErrorColor
        Write-ColorOutput "Please run PowerShell as Administrator and try again." $WarningColor
        return $false
    }
    
    # Check if service exists
    if (-not (Test-ServiceExists $ServiceName)) {
        Write-ColorOutput "Service '$ServiceName' does not exist." $WarningColor
        return $true
    }
    
    # Stop the service first if it's running
    $status = Get-ServiceStatus $ServiceName
    if ($status.Status -eq "Running") {
        Write-ColorOutput "Stopping service first..." $InfoColor
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
    }
    
    # Uninstall the service
    try {
        & $ServicePath --uninstall
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Service uninstalled successfully!" $SuccessColor
            return $true
        }
        else {
            Write-ColorOutput "❌ Service uninstallation failed (exit code: $LASTEXITCODE)" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Service uninstallation failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Start-Service {
    Write-ColorOutput "Starting FastSearch MCP Service..." $InfoColor
    
    # Check if service exists
    if (-not (Test-ServiceExists $ServiceName)) {
        Write-ColorOutput "ERROR: Service '$ServiceName' does not exist!" $ErrorColor
        Write-ColorOutput "Please install the service first using: .\install-service.ps1 install" $WarningColor
        return $false
    }
    
    # Start the service
    try {
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 2
        
        $status = Get-ServiceStatus $ServiceName
        if ($status.Status -eq "Running") {
            Write-ColorOutput "✅ Service started successfully!" $SuccessColor
            return $true
        }
        else {
            Write-ColorOutput "❌ Service failed to start. Status: $($status.Status)" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Service start failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Stop-Service {
    Write-ColorOutput "Stopping FastSearch MCP Service..." $InfoColor
    
    # Check if service exists
    if (-not (Test-ServiceExists $ServiceName)) {
        Write-ColorOutput "Service '$ServiceName' does not exist." $WarningColor
        return $true
    }
    
    # Stop the service
    try {
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
        
        $status = Get-ServiceStatus $ServiceName
        if ($status.Status -eq "Stopped") {
            Write-ColorOutput "✅ Service stopped successfully!" $SuccessColor
            return $true
        }
        else {
            Write-ColorOutput "❌ Service failed to stop. Status: $($status.Status)" $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Service stop failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Show-ServiceStatus {
    Write-ColorOutput "FastSearch MCP Service Status" $InfoColor
    Write-ColorOutput "=============================" $InfoColor
    
    $status = Get-ServiceStatus $ServiceName
    
    if ($status.Exists) {
        Write-ColorOutput "Service Name: $ServiceName" $InfoColor
        Write-ColorOutput "Status: $($status.Status)" $(if ($status.Status -eq "Running") { $SuccessColor } else { $WarningColor })
        Write-ColorOutput "Start Type: $($status.StartType)" $InfoColor
        
        # Test pipe connection
        Write-ColorOutput "`nTesting pipe connection..." $InfoColor
        try {
            $pipeName = "\\.\pipe\FastSearchMCPService"
            $pipe = New-Object System.IO.Pipes.NamedPipeClientStream($pipeName)
            $pipe.Connect(1000)  # 1 second timeout
            $pipe.Close()
            Write-ColorOutput "✅ Pipe connection successful!" $SuccessColor
        }
        catch {
            Write-ColorOutput "❌ Pipe connection failed: $($_.Exception.Message)" $ErrorColor
        }
    }
    else {
        Write-ColorOutput "Service '$ServiceName' is not installed." $WarningColor
    }
}

function Show-Help {
    Write-ColorOutput "FastSearch MCP Service Installer" $InfoColor
    Write-ColorOutput "===============================" $InfoColor
    Write-ColorOutput ""
    Write-ColorOutput "Usage: .\install-service.ps1 [action]" $InfoColor
    Write-ColorOutput ""
    Write-ColorOutput "Actions:" $InfoColor
    Write-ColorOutput "  install    - Install the service (requires UAC)" $InfoColor
    Write-ColorOutput "  uninstall  - Uninstall the service (requires UAC)" $InfoColor
    Write-ColorOutput "  start      - Start the service" $InfoColor
    Write-ColorOutput "  stop       - Stop the service" $InfoColor
    Write-ColorOutput "  status     - Show service status" $InfoColor
    Write-ColorOutput "  help       - Show this help" $InfoColor
    Write-ColorOutput ""
    Write-ColorOutput "Examples:" $InfoColor
    Write-ColorOutput "  .\install-service.ps1 install" $InfoColor
    Write-ColorOutput "  .\install-service.ps1 status" $InfoColor
    Write-ColorOutput "  .\install-service.ps1 start" $InfoColor
    Write-ColorOutput ""
    Write-ColorOutput "Architecture:" $InfoColor
    Write-ColorOutput "  • C++ Windows Service: Runs with UAC privileges for NTFS access" $InfoColor
    Write-ColorOutput "  • Python MCP Bridge: Runs without UAC, communicates via named pipes" $InfoColor
    Write-ColorOutput "  • Named Pipe: \\.\pipe\FastSearchMCPService" $InfoColor
}

# Main execution
switch ($Action.ToLower()) {
    "install" {
        Install-Service
    }
    "uninstall" {
        Uninstall-Service
    }
    "start" {
        Start-Service
    }
    "stop" {
        Stop-Service
    }
    "status" {
        Show-ServiceStatus
    }
    "help" {
        Show-Help
    }
    default {
        Write-ColorOutput "Unknown action: $Action" $ErrorColor
        Show-Help
    }
}

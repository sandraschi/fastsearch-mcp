# FastSearch MCP Service Installer
# This script installs the FastSearch MCP Windows service with proper UAC handling

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "uninstall", "start", "stop", "status", "diagnose", "help")]
    [string]$Action = "help"
)

# Configuration
$ServiceName = "FastSearchMCP"
$ServiceDisplayName = "FastSearch MCP Service"
$ServiceDescription = "Provides fast file search capabilities using direct NTFS MFT access"
$ServiceExecutable = "service\build\bin\Release\FastSearchServiceNew.exe"
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
    return $null -ne $service
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
        $output = & $ServicePath --install 2>&1
        $exitCode = $LASTEXITCODE
        
        # Check for error messages in output
        if ($output -match "failed|error|Error") {
            Write-ColorOutput "⚠️  Service installation warnings:" $WarningColor
            Write-ColorOutput $output $WarningColor
        }
        
        if ($exitCode -eq 0) {
            Write-ColorOutput "✅ Service installed successfully!" $SuccessColor
            Write-ColorOutput "Service Name: $ServiceName" $InfoColor
            Write-ColorOutput "Display Name: $ServiceDisplayName" $InfoColor
            Write-ColorOutput "Description: $ServiceDescription" $InfoColor
            return $true
        }
        else {
            Write-ColorOutput "❌ Service installation failed (exit code: $exitCode)" $ErrorColor
            Write-ColorOutput $output $ErrorColor
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
        $output = & $ServicePath --uninstall 2>&1
        $exitCode = $LASTEXITCODE
        
        # Check for error messages in output
        if ($output -match "failed|error|Error") {
            Write-ColorOutput "⚠️  Service uninstallation warnings:" $WarningColor
            Write-ColorOutput $output $WarningColor
        }
        
        if ($exitCode -eq 0) {
            Write-ColorOutput "✅ Service uninstalled successfully!" $SuccessColor
            return $true
        }
        else {
            Write-ColorOutput "❌ Service uninstallation failed (exit code: $exitCode)" $ErrorColor
            Write-ColorOutput $output $ErrorColor
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Service uninstallation failed: $($_.Exception.Message)" $ErrorColor
        return $false
    }
}

function Start-FastSearchService {
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

function Stop-FastSearchService {
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

function Resolve-ServiceIssues {
    Write-ColorOutput "Diagnosing FastSearch MCP Service Issues..." $InfoColor
    Write-ColorOutput "=============================================" $InfoColor
    
    # Check if service exists but is in a bad state
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-ColorOutput "Service exists with status: $($service.Status)" $InfoColor
        
        # Get detailed service info
        try {
            $serviceInfo = Get-CimInstance -ClassName Win32_Service -Filter "Name='$ServiceName'"
            Write-ColorOutput "`nService Details:" $InfoColor
            Write-ColorOutput "  Path: $($serviceInfo.PathName)" $InfoColor
            Write-ColorOutput "  Account: $($serviceInfo.StartName)" $InfoColor
            Write-ColorOutput "  State: $($serviceInfo.State)" $InfoColor
            Write-ColorOutput "  Process ID: $($serviceInfo.ProcessId)" $InfoColor
        }
        catch {
            Write-ColorOutput "⚠️  Could not retrieve detailed service info" $WarningColor
        }
        
        if ($service.Status -eq "Stopped") {
            Write-ColorOutput "`nAttempting to start service..." $InfoColor
            try {
                Start-Service -Name $ServiceName
                Start-Sleep -Seconds 3
                $newStatus = Get-Service -Name $ServiceName
                Write-ColorOutput "Service status after start: $($newStatus.Status)" $InfoColor
                
                if ($newStatus.Status -ne "Running") {
                    Write-ColorOutput "`n⚠️  Service failed to start. Checking event logs..." $WarningColor
                    try {
                        $events = Get-WinEvent -LogName Application -MaxEvents 10 -ErrorAction SilentlyContinue | 
                            Where-Object { 
                                $_.ProviderName -eq $ServiceName -or 
                                $_.Message -like "*$ServiceName*" 
                            } | 
                            Sort-Object TimeCreated -Descending | 
                            Select-Object -First 3
                        
                        if ($events) {
                            Write-ColorOutput "Recent events:" $InfoColor
                            foreach ($event in $events) {
                                $levelColor = if ($event.LevelDisplayName -eq "Error") { $ErrorColor } else { $WarningColor }
                                Write-ColorOutput "  [$($event.TimeCreated)] [$($event.LevelDisplayName)]" $levelColor
                                Write-ColorOutput "    $($event.Message.Substring(0, [Math]::Min(100, $event.Message.Length)))..." $InfoColor
                            }
                        }
                    }
                    catch {
                        Write-ColorOutput "  Could not read event logs: $($_.Exception.Message)" $WarningColor
                    }
                }
            }
            catch {
                Write-ColorOutput "Failed to start service: $($_.Exception.Message)" $ErrorColor
            }
        }
    }
    else {
        Write-ColorOutput "Service is not installed" $WarningColor
    }
    
    # Check for orphaned service entries
    Write-ColorOutput "`nChecking for service registry entries..." $InfoColor
    try {
        $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$ServiceName"
        if (Test-Path $regPath) {
            Write-ColorOutput "✅ Service registry entry exists" $SuccessColor
            $regValues = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
            if ($regValues) {
                Write-ColorOutput "  ImagePath: $($regValues.ImagePath)" $InfoColor
            }
        }
        else {
            Write-ColorOutput "❌ Service registry entry not found" $ErrorColor
        }
    }
    catch {
        Write-ColorOutput "❌ Cannot access service registry: $($_.Exception.Message)" $ErrorColor
    }
    
    # Check executable
    Write-ColorOutput "`nChecking service executable..." $InfoColor
    if ($ServicePath) {
        if (Test-Path $ServicePath) {
            Write-ColorOutput "✅ Executable found: $ServicePath" $SuccessColor
            $fileInfo = Get-Item $ServicePath
            Write-ColorOutput "  Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" $InfoColor
            Write-ColorOutput "  Modified: $($fileInfo.LastWriteTime)" $InfoColor
        }
        else {
            Write-ColorOutput "❌ Executable not found: $ServicePath" $ErrorColor
        }
    }
    else {
        Write-ColorOutput "⚠️  Service executable path not resolved" $WarningColor
    }
    
    # Suggest solutions
    Write-ColorOutput "`nRecommended solutions:" $InfoColor
    Write-ColorOutput "1. Check event logs: .\read-service-logs.ps1" $InfoColor
    Write-ColorOutput "2. Run comprehensive test: .\test-service-comprehensive.ps1" $InfoColor
    Write-ColorOutput "3. Debug startup: .\debug-service-startup.ps1" $InfoColor
    Write-ColorOutput "4. Wait 30 seconds and try again (Windows cleanup delay)" $InfoColor
    Write-ColorOutput "5. Restart Windows to clear service state" $InfoColor
    Write-ColorOutput "6. Use sc.exe to manually delete: sc delete $ServiceName" $InfoColor
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
    Write-ColorOutput "  diagnose   - Diagnose service installation issues" $InfoColor
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
        Start-FastSearchService
    }
    "stop" {
        Stop-FastSearchService
    }
    "status" {
        Show-ServiceStatus
    }
    "diagnose" {
        Resolve-ServiceIssues
    }
    "help" {
        Show-Help
    }
    default {
        Write-ColorOutput "Unknown action: $Action" $ErrorColor
        Show-Help
    }
}

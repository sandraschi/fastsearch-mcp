# Comprehensive Service Testing Script
# Tests all aspects of the FastSearch MCP service installation and operation

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "install", "start", "stop", "status", "logs", "pipe", "uninstall", "help")]
    [string]$Test = "all"
)

$ServiceName = "FastSearchMCP"
$ServiceExecutable = "service\build\bin\Release\FastSearchServiceNew.exe"
$PipeName = "\\.\pipe\FastSearchMCPService"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-ServiceInstallation {
    Write-ColorOutput "`n=== Testing Service Installation ===" "Cyan"
    
    if (-not (Test-Administrator)) {
        Write-ColorOutput "⚠️  Administrator privileges required for installation test" "Yellow"
        return $false
    }
    
    if (-not (Test-Path $ServiceExecutable)) {
        Write-ColorOutput "❌ Service executable not found: $ServiceExecutable" "Red"
        Write-ColorOutput "   Please build the service first" "Yellow"
        return $false
    }
    
    Write-ColorOutput "✅ Service executable found: $ServiceExecutable" "Green"
    
    # Check if service exists
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-ColorOutput "✅ Service is installed" "Green"
        Write-ColorOutput "   Status: $($service.Status)" "Cyan"
        Write-ColorOutput "   Start Type: $($service.StartType)" "Cyan"
        return $true
    } else {
        Write-ColorOutput "⚠️  Service is not installed" "Yellow"
        return $false
    }
}

function Test-ServiceStart {
    Write-ColorOutput "`n=== Testing Service Start ===" "Cyan"
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-ColorOutput "❌ Service is not installed" "Red"
        return $false
    }
    
    if ($service.Status -eq "Running") {
        Write-ColorOutput "✅ Service is already running" "Green"
        return $true
    }
    
    try {
        Write-ColorOutput "Starting service..." "Cyan"
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 3
        
        $service = Get-Service -Name $ServiceName
        if ($service.Status -eq "Running") {
            Write-ColorOutput "✅ Service started successfully" "Green"
            return $true
        } else {
            Write-ColorOutput "❌ Service failed to start. Status: $($service.Status)" "Red"
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Service start failed: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Test-ServiceStop {
    Write-ColorOutput "`n=== Testing Service Stop ===" "Cyan"
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-ColorOutput "⚠️  Service is not installed" "Yellow"
        return $true
    }
    
    if ($service.Status -eq "Stopped") {
        Write-ColorOutput "✅ Service is already stopped" "Green"
        return $true
    }
    
    try {
        Write-ColorOutput "Stopping service..." "Cyan"
        Stop-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 2
        
        $service = Get-Service -Name $ServiceName
        if ($service.Status -eq "Stopped") {
            Write-ColorOutput "✅ Service stopped successfully" "Green"
            return $true
        } else {
            Write-ColorOutput "⚠️  Service stop incomplete. Status: $($service.Status)" "Yellow"
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ Service stop failed: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Test-ServiceStatus {
    Write-ColorOutput "`n=== Service Status ===" "Cyan"
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-ColorOutput "❌ Service is not installed" "Red"
        return $false
    }
    
    Write-ColorOutput "Service Name: $($service.Name)" "Cyan"
    Write-ColorOutput "Display Name: $($service.DisplayName)" "Cyan"
    Write-ColorOutput "Status: $($service.Status)" $(if ($service.Status -eq "Running") { "Green" } else { "Yellow" })
    Write-ColorOutput "Start Type: $($service.StartType)" "Cyan"
    Write-ColorOutput "Service Type: $($service.ServiceType)" "Cyan"
    
    # Get detailed service info
    try {
        $serviceInfo = Get-CimInstance -ClassName Win32_Service -Filter "Name='$ServiceName'"
        if ($serviceInfo) {
            Write-ColorOutput "`nDetailed Information:" "Cyan"
            Write-ColorOutput "  Path: $($serviceInfo.PathName)" "Cyan"
            Write-ColorOutput "  Account: $($serviceInfo.StartName)" "Cyan"
            Write-ColorOutput "  Process ID: $($serviceInfo.ProcessId)" "Cyan"
            Write-ColorOutput "  State: $($serviceInfo.State)" "Cyan"
        }
    }
    catch {
        Write-ColorOutput "⚠️  Could not retrieve detailed service info" "Yellow"
    }
    
    return $true
}

function Test-ServiceLogs {
    Write-ColorOutput "`n=== Service Event Logs ===" "Cyan"
    
    try {
        $events = Get-WinEvent -LogName Application -MaxEvents 50 -ErrorAction SilentlyContinue | 
            Where-Object { $_.ProviderName -eq $ServiceName -or $_.Message -like "*$ServiceName*" }
        
        if ($events) {
            Write-ColorOutput "Found $($events.Count) recent events:" "Cyan"
            foreach ($event in $events | Select-Object -First 10) {
                $level = switch ($event.LevelDisplayName) {
                    "Error" { "Red" }
                    "Warning" { "Yellow" }
                    default { "Green" }
                }
                Write-ColorOutput "  [$($event.TimeCreated)] [$($event.LevelDisplayName)] $($event.Message.Substring(0, [Math]::Min(100, $event.Message.Length)))..." $level
            }
        } else {
            Write-ColorOutput "⚠️  No recent events found for service" "Yellow"
        }
    }
    catch {
        Write-ColorOutput "❌ Error reading event logs: $($_.Exception.Message)" "Red"
    }
}

function Test-PipeConnection {
    Write-ColorOutput "`n=== Testing Named Pipe Connection ===" "Cyan"
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service -or $service.Status -ne "Running") {
        Write-ColorOutput "⚠️  Service must be running to test pipe connection" "Yellow"
        return $false
    }
    
    try {
        Write-ColorOutput "Attempting to connect to pipe: $PipeName" "Cyan"
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "FastSearchMCPService", [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(2000)  # 2 second timeout
        
        Write-ColorOutput "✅ Pipe connection successful!" "Green"
        $pipe.Close()
        return $true
    }
    catch {
        Write-ColorOutput "❌ Pipe connection failed: $($_.Exception.Message)" "Red"
        return $false
    }
}

function Test-ServiceUninstall {
    Write-ColorOutput "`n=== Testing Service Uninstall ===" "Cyan"
    
    if (-not (Test-Administrator)) {
        Write-ColorOutput "⚠️  Administrator privileges required for uninstall test" "Yellow"
        return $false
    }
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-ColorOutput "✅ Service is not installed (nothing to uninstall)" "Green"
        return $true
    }
    
    Write-ColorOutput "⚠️  Uninstall test skipped (use install-service.ps1 uninstall to actually uninstall)" "Yellow"
    return $true
}

function Show-Help {
    Write-ColorOutput "FastSearch MCP Service Comprehensive Test Suite" "Cyan"
    Write-ColorOutput "================================================" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "Usage: .\test-service-comprehensive.ps1 [test]" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "Tests:" "Cyan"
    Write-ColorOutput "  all       - Run all tests (default)" "Cyan"
    Write-ColorOutput "  install   - Test service installation" "Cyan"
    Write-ColorOutput "  start     - Test service start" "Cyan"
    Write-ColorOutput "  stop      - Test service stop" "Cyan"
    Write-ColorOutput "  status    - Show service status" "Cyan"
    Write-ColorOutput "  logs      - Show service event logs" "Cyan"
    Write-ColorOutput "  pipe      - Test named pipe connection" "Cyan"
    Write-ColorOutput "  uninstall - Test service uninstall (dry run)" "Cyan"
    Write-ColorOutput "  help      - Show this help" "Cyan"
}

# Main execution
Write-ColorOutput "FastSearch MCP Service Comprehensive Test Suite" "Cyan"
Write-ColorOutput "================================================" "Cyan"

switch ($Test.ToLower()) {
    "all" {
        Test-ServiceInstallation
        Test-ServiceStatus
        Test-ServiceLogs
        Test-ServiceStart
        Start-Sleep -Seconds 2
        Test-PipeConnection
        Test-ServiceStop
    }
    "install" {
        Test-ServiceInstallation
    }
    "start" {
        Test-ServiceStart
    }
    "stop" {
        Test-ServiceStop
    }
    "status" {
        Test-ServiceStatus
    }
    "logs" {
        Test-ServiceLogs
    }
    "pipe" {
        Test-PipeConnection
    }
    "uninstall" {
        Test-ServiceUninstall
    }
    "help" {
        Show-Help
    }
    default {
        Write-ColorOutput "Unknown test: $Test" "Red"
        Show-Help
    }
}


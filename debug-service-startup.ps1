# Debug Service Startup Issues
# Comprehensive diagnostic tool for service startup problems

param(
    [Parameter(Mandatory=$false)]
    [switch]$Detailed
)

$ServiceName = "FastSearchMCP"
$ServiceExecutable = "service\build\bin\Release\FastSearchServiceNew.exe"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

Write-ColorOutput "FastSearch MCP Service Startup Debugger" "Cyan"
Write-ColorOutput "=======================================" "Cyan"
Write-ColorOutput ""

# Check 1: Administrator privileges
Write-ColorOutput "[1/8] Checking administrator privileges..." "Cyan"
if (Test-Administrator) {
    Write-ColorOutput "  ✅ Running with administrator privileges" "Green"
} else {
    Write-ColorOutput "  ⚠️  Not running as administrator (some checks may fail)" "Yellow"
}
Write-ColorOutput ""

# Check 2: Service executable exists
Write-ColorOutput "[2/8] Checking service executable..." "Cyan"
if (Test-Path $ServiceExecutable) {
    $fileInfo = Get-Item $ServiceExecutable
    Write-ColorOutput "  ✅ Executable found: $ServiceExecutable" "Green"
    Write-ColorOutput "    Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" "Cyan"
    Write-ColorOutput "    Modified: $($fileInfo.LastWriteTime)" "Cyan"
} else {
    Write-ColorOutput "  ❌ Executable not found: $ServiceExecutable" "Red"
    Write-ColorOutput "    Please build the service first" "Yellow"
}
Write-ColorOutput ""

# Check 3: Service registration
Write-ColorOutput "[3/8] Checking service registration..." "Cyan"
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($service) {
    Write-ColorOutput "  ✅ Service is registered" "Green"
    Write-ColorOutput "    Status: $($service.Status)" "Cyan"
    Write-ColorOutput "    Start Type: $($service.StartType)" "Cyan"
    
    # Get detailed service info
    try {
        $serviceInfo = Get-CimInstance -ClassName Win32_Service -Filter "Name='$ServiceName'"
        Write-ColorOutput "    Path: $($serviceInfo.PathName)" "Cyan"
        Write-ColorOutput "    Account: $($serviceInfo.StartName)" "Cyan"
        
        # Check if path matches
        $expectedPath = (Resolve-Path $ServiceExecutable -ErrorAction SilentlyContinue).Path
        if ($serviceInfo.PathName -like "*$expectedPath*") {
            Write-ColorOutput "    ✅ Path matches executable" "Green"
        } else {
            Write-ColorOutput "    ⚠️  Path may not match executable" "Yellow"
            Write-ColorOutput "      Expected: $expectedPath" "Yellow"
            Write-ColorOutput "      Actual: $($serviceInfo.PathName)" "Yellow"
        }
    }
    catch {
        Write-ColorOutput "    ⚠️  Could not retrieve detailed service info" "Yellow"
    }
} else {
    Write-ColorOutput "  ❌ Service is not registered" "Red"
    Write-ColorOutput "    Run: .\install-service.ps1 install" "Yellow"
}
Write-ColorOutput ""

# Check 4: Dependencies
Write-ColorOutput "[4/8] Checking dependencies..." "Cyan"
if (Test-Path $ServiceExecutable) {
    try {
        $dependencies = (Get-Command $ServiceExecutable -ErrorAction Stop).DLLs
        Write-ColorOutput "  ✅ Executable can be queried" "Green"
    }
    catch {
        Write-ColorOutput "  ⚠️  Could not query executable dependencies" "Yellow"
    }
}
Write-ColorOutput ""

# Check 5: Event logs
Write-ColorOutput "[5/8] Checking recent event logs..." "Cyan"
try {
    $recentEvents = Get-WinEvent -LogName Application -MaxEvents 20 -ErrorAction SilentlyContinue | 
        Where-Object { 
            $_.ProviderName -eq $ServiceName -or 
            $_.Message -like "*$ServiceName*" 
        } | 
        Sort-Object TimeCreated -Descending | 
        Select-Object -First 5
    
    if ($recentEvents) {
        Write-ColorOutput "  Found $($recentEvents.Count) recent events:" "Cyan"
        foreach ($event in $recentEvents) {
            $levelColor = switch ($event.LevelDisplayName) {
                "Error" { "Red" }
                "Warning" { "Yellow" }
                default { "Green" }
            }
            Write-ColorOutput "    [$($event.TimeCreated)] [$($event.LevelDisplayName)] $($event.Message.Substring(0, [Math]::Min(80, $event.Message.Length)))..." $levelColor
        }
    } else {
        Write-ColorOutput "  ⚠️  No recent events found" "Yellow"
    }
}
catch {
    Write-ColorOutput "  ⚠️  Could not read event logs" "Yellow"
}
Write-ColorOutput ""

# Check 6: Test executable directly
Write-ColorOutput "[6/8] Testing executable directly..." "Cyan"
if (Test-Path $ServiceExecutable) {
    try {
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $ServiceExecutable
        $processInfo.Arguments = "--help"
        $processInfo.UseShellExecute = $false
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        $process.Start() | Out-Null
        $output = $process.StandardOutput.ReadToEnd()
        $process.WaitForExit(2000)
        
        if ($process.ExitCode -eq 0) {
            Write-ColorOutput "  ✅ Executable runs successfully (exit code: $($process.ExitCode))" "Green"
        } else {
            Write-ColorOutput "  ⚠️  Executable exited with code: $($process.ExitCode)" "Yellow"
        }
    }
    catch {
        Write-ColorOutput "  ❌ Error testing executable: $($_.Exception.Message)" "Red"
    }
} else {
    Write-ColorOutput "  ⚠️  Cannot test - executable not found" "Yellow"
}
Write-ColorOutput ""

# Check 7: Named pipe
Write-ColorOutput "[7/8] Checking named pipe..." "Cyan"
if ($service -and $service.Status -eq "Running") {
    try {
        $pipe = New-Object System.IO.Pipes.NamedPipeClientStream(".", "FastSearchMCPService", [System.IO.Pipes.PipeDirection]::InOut)
        $pipe.Connect(1000)
        $pipe.Close()
        Write-ColorOutput "  ✅ Named pipe is accessible" "Green"
    }
    catch {
        Write-ColorOutput "  ⚠️  Named pipe not accessible: $($_.Exception.Message)" "Yellow"
    }
} else {
    Write-ColorOutput "  ⚠️  Service not running - cannot test pipe" "Yellow"
}
Write-ColorOutput ""

# Check 8: Recommendations
Write-ColorOutput "[8/8] Recommendations..." "Cyan"
$recommendations = @()

if (-not (Test-Path $ServiceExecutable)) {
    $recommendations += "Build the service: cd service; cmake --build build --config Release"
}

if (-not $service) {
    $recommendations += "Install the service: .\install-service.ps1 install"
}

if ($service -and $service.Status -ne "Running") {
    $recommendations += "Start the service: .\install-service.ps1 start"
    $recommendations += "Check event logs: .\scripts\read-service-logs.ps1"
}

if ($recommendations.Count -eq 0) {
    Write-ColorOutput "  ✅ No issues detected - service should be working" "Green"
} else {
    Write-ColorOutput "  Suggested actions:" "Yellow"
    foreach ($rec in $recommendations) {
        Write-ColorOutput "    • $rec" "Cyan"
    }
}

Write-ColorOutput ""
Write-ColorOutput "Debugging complete!" "Cyan"


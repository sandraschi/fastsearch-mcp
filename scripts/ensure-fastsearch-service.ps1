# Ensure FastSearchMCP Windows service is running and the named pipe responds.
# Usage:
#   .\ensure-fastsearch-service.ps1                 # health check + start if stopped
#   .\ensure-fastsearch-service.ps1 -InstallWatchdog # register 5-minute scheduled task
#   .\ensure-fastsearch-service.ps1 -ConfigureRecovery # SCM auto-restart on failure (admin)

param(
    [switch]$InstallWatchdog,
    [switch]$ConfigureRecovery,
    [switch]$RestartIfHung
)

$ErrorActionPreference = "Stop"

$ServiceName = "FastSearchMCP"
$PipeName = "\\.\pipe\FastSearchMCP"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$TaskName = "FastSearchMCP-Watchdog"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Set-ServiceFailureRecovery {
    if (-not (Test-Administrator)) {
        Write-Error "Administrator privileges required to configure service recovery."
    }

    & sc.exe failure $ServiceName reset= 86400 actions= restart/60000/restart/60000/restart/60000
    if ($LASTEXITCODE -ne 0) {
        Write-Error "sc.exe failure failed with exit code $LASTEXITCODE"
    }

    & sc.exe failureflag $ServiceName 1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "sc.exe failureflag returned exit code $LASTEXITCODE (continuing)"
    }

    Write-Host "Configured $ServiceName to auto-restart on failure." -ForegroundColor Green
}

function Test-PipePing {
    Push-Location $RepoRoot
    try {
        $output = uv run python -c @"
import asyncio, json
from fastsearch_mcp.service_ensure import ensure_service_available

async def main():
    result = await ensure_service_available(start_if_needed=False)
    print(json.dumps(result))

asyncio.run(main())
"@
        return ($output | ConvertFrom-Json)
    }
    finally {
        Pop-Location
    }
}

function Ensure-ServiceRunning {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Error "Service '$ServiceName' is not installed. Run install-service.ps1 install first."
    }

    if ($service.Status -ne "Running") {
        Write-Host "Starting $ServiceName (was $($service.Status))..." -ForegroundColor Yellow
        Start-Service -Name $ServiceName
        Start-Sleep -Seconds 2
    }

    $ping = Test-PipePing
    if ($ping.success) {
        Write-Host "FastSearch pipe OK ($PipeName)." -ForegroundColor Green
        return
    }

    if ($RestartIfHung -and (Get-Service $ServiceName).Status -eq "Running") {
        Write-Host "Service running but pipe failed; restarting hung service..." -ForegroundColor Yellow
        Restart-Service -Name $ServiceName -Force
        Start-Sleep -Seconds 3
        $ping = Test-PipePing
        if ($ping.success) {
            Write-Host "FastSearch pipe OK after restart." -ForegroundColor Green
            return
        }
    }

    Write-Error "FastSearch pipe unavailable: $($ping.error_message)"
}

function Install-WatchdogTask {
    if (-not (Test-Administrator)) {
        Write-Error "Administrator privileges required to install the watchdog scheduled task."
    }

    $scriptPath = Join-Path $PSScriptRoot "ensure-fastsearch-service.ps1"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -RestartIfHung"
    $triggerBoot = New-ScheduledTaskTrigger -AtStartup
    # Daily + 5-minute repetition for 24h (Task Scheduler rejects TimeSpan.MaxValue in XML)
    $triggerRepeat = New-ScheduledTaskTrigger -Daily -At "00:00" -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Hours 24)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($triggerBoot, $triggerRepeat) -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "Installed scheduled task '$TaskName' (every 5 minutes + at startup)." -ForegroundColor Green
}

if ($ConfigureRecovery) {
    Set-ServiceFailureRecovery
}

if ($InstallWatchdog) {
    Install-WatchdogTask
}

Ensure-ServiceRunning

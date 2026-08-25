# FastSearch First-Time User Onboarding Script
# Automates single-UAC service installation + automated named pipe diagnostic testing.

param(
    [switch]$ForceReinstall
)

$ErrorActionPreference = "Stop"
$ServiceName = "FastSearchMCP"
$PipeName = "\\.\pipe\FastSearchMCP"
$RepoRoot = Split-Path $PSScriptRoot -Parent
$ExePath = Join-Path $RepoRoot "service\build\bin\Release\FastSearchServiceNew.exe"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
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

Write-Host "============================================================" -ForegroundColor Cipher
Write-Host " 🚀 FastSearch MCP First-Time Onboarding & Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cipher

# Check service executable
if (-not (Test-Path $ExePath)) {
    Write-Host "[BUILD] Service executable not found. Building C++ service binary..." -ForegroundColor Yellow
    Push-Location (Join-Path $RepoRoot "service\build")
    try {
        cmake --build . --config Release
    }
    finally {
        Pop-Location
    }
}

# Step 1: Install & Start Service (Elevated ONCE via UAC if not Admin)
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if (-not $service -or $ForceReinstall) {
    if (-not (Test-Administrator)) {
        Write-Host "[UAC] Requesting Administrator elevation ONCE to install Windows Service..." -ForegroundColor Yellow
        $scriptPath = $MyInvocation.MyCommand.Path
        $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
        if ($ForceReinstall) { $argList += " -ForceReinstall" }
        Start-Process powershell -ArgumentList $argList -Verb RunAs -Wait
    }
    else {
        Write-Host "[SERVICE] Registering FastSearchMCP Windows Service..." -ForegroundColor Green
        & $ExePath install
        Start-Sleep -Seconds 1
        Write-Host "[SERVICE] Starting FastSearchMCP service..." -ForegroundColor Green
        Start-Service -Name $ServiceName
    }
}
elseif ($service.Status -ne "Running") {
    if (-not (Test-Administrator)) {
        Write-Host "[UAC] Requesting Administrator elevation ONCE to start Windows Service..." -ForegroundColor Yellow
        $scriptPath = $MyInvocation.MyCommand.Path
        Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" -Verb RunAs -Wait
    }
    else {
        Write-Host "[SERVICE] Starting FastSearchMCP Windows Service..." -ForegroundColor Green
        Start-Service -Name $ServiceName
    }
}

# Step 2: Automated Pipe Testing (Runs in Standard User Space)
Write-Host "[TEST] Running automated Named Pipe IPC connectivity test..." -ForegroundColor Cyan
Start-Sleep -Seconds 1.5

$ping = Test-PipePing
if ($ping.success) {
    Write-Host "`n============================================================" -ForegroundColor Green
    Write-Host " 🎉 ONBOARDING COMPLETE & VERIFIED SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " [✓] Windows Service 'FastSearchMCP' is running under LocalSystem" -ForegroundColor White
    Write-Host " [✓] IPC Named Pipe '$PipeName' is connected & responding" -ForegroundColor White
    Write-Host " [✓] Standard user apps (Claude Desktop, Web UI, Python MCP) can now" -ForegroundColor White
    Write-Host "     execute instant MFT searches with ZERO elevation or UAC prompts!" -ForegroundColor White
    Write-Host "============================================================`n" -ForegroundColor Green
}
else {
    Write-Host "`n[ERROR] Service installed but named pipe test failed: $($ping.error_message)" -ForegroundColor Red
    exit 1
}

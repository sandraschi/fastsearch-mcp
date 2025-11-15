<#
.SYNOPSIS
    Downloads and installs Visual Studio 2022 Community with the C++ desktop workload for FastSearch development.

.DESCRIPTION
    Retrieves the official Visual Studio Community bootstrapper, installs the Desktop development with C++ workload,
    and includes recommended components (Windows SDK, CMake tools, etc.). Requires elevated PowerShell.

.PARAMETER DownloadUrl
    Source URL for the Visual Studio bootstrapper. Defaults to the current release channel.

.PARAMETER BootstrapperPath
    Local path where the bootstrapper executable will be stored.

.PARAMETER ForceDownload
    Redownloads the bootstrapper even if the file already exists at BootstrapperPath.

.PARAMETER AdditionalComponents
    Optional component IDs to install alongside the native desktop workload.

.PARAMETER Quiet
    Install silently without UI. By default the installer runs in passive mode with minimal UI.

.EXAMPLE
    .\scripts\install-visualstudio-community.ps1

.EXAMPLE
    .\scripts\install-visualstudio-community.ps1 -AdditionalComponents Microsoft.VisualStudio.Component.CppClang.ClangCl -Quiet
#>
[CmdletBinding()]
param(
    [string]$DownloadUrl = "https://aka.ms/vs/17/release/vs_community.exe",
    [string]$BootstrapperPath = "$env:TEMP\vs_community.exe",
    [switch]$ForceDownload,
    [string[]]$AdditionalComponents = @("Microsoft.VisualStudio.Component.VC.CMake.Project"),
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
        throw "This script must be run from an elevated PowerShell session."
    }
}

function Download-Bootstrapper {
    param(
        [string]$Uri,
        [string]$Destination
    )

    Write-Host "Downloading Visual Studio bootstrapper from $Uri ..."
    Invoke-WebRequest -Uri $Uri -OutFile $Destination -UseBasicParsing
    Write-Host "Download complete: $Destination"
}

function Get-ArgumentList {
    param(
        [string[]]$Components,
        [switch]$Silent
    )

    $args = New-Object System.Collections.Generic.List[string]
    $args.Add("--installWhileDownloading")
    $args.Add("--wait")
    if ($Silent) {
        $args.Add("--quiet")
        $args.Add("--norestart")
    } else {
        $args.Add("--passive")
        $args.Add("--norestart")
    }

    $args.Add("--add")
    $args.Add("Microsoft.VisualStudio.Workload.NativeDesktop")
    $args.Add("--includeRecommended")

    foreach ($component in $Components) {
        if ([string]::IsNullOrWhiteSpace($component)) {
            continue
        }
        $args.Add("--add")
        $args.Add($component)
    }

    return $args.ToArray()
}

try {
    Assert-Administrator

    if ($ForceDownload -or -not (Test-Path -LiteralPath $BootstrapperPath)) {
        if (Test-Path -LiteralPath $BootstrapperPath -and $ForceDownload) {
            Remove-Item -LiteralPath $BootstrapperPath -Force
        }
        Download-Bootstrapper -Uri $DownloadUrl -Destination $BootstrapperPath
    } else {
        Write-Host "Bootstrapper already exists at $BootstrapperPath. Use -ForceDownload to redownload."
    }

    if (-not (Test-Path -LiteralPath $BootstrapperPath)) {
        throw "Bootstrapper not found at $BootstrapperPath."
    }

    $argumentList = Get-ArgumentList -Components $AdditionalComponents -Silent:$Quiet
    Write-Host "Launching Visual Studio installer..."
    Write-Host "Arguments: $($argumentList -join ' ')"

    $process = Start-Process -FilePath $BootstrapperPath -ArgumentList $argumentList -Wait -PassThru

    if ($process.ExitCode -ne 0) {
        throw "Visual Studio installer exited with code $($process.ExitCode). Review logs in `%ProgramData%\Microsoft\VisualStudio\Packages\_Instances`."
    }

    Write-Host "Visual Studio Community installation completed successfully."
    Write-Host "If prompted to reboot, complete the restart before debugging the FastSearch service."
} catch {
    Write-Error $_
    exit 1
}


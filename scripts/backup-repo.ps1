#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automated repository backup using Windows native compression with SOTA error handling
    
.DESCRIPTION
    Creates a compressed ZIP backup of the repository and saves to:
    1. Desktop\repo backup\
    2. N:\backup\dev\repos\
    3. OneDrive\repo-backups\
    
    Features:
    - Individual error handling per backup location
    - Retry logic with exponential backoff
    - Disk space validation
    - Progress reporting for large backups
    - Partial success handling (continues if one destination fails)
    - Detailed error logging
    - Integrity verification after creation
    - Graceful cleanup on failures
    
    Excludes:
    - .venv/ (virtual environments)
    - __pycache__/ (Python cache)
    - .ruff_cache/, .mypy_cache/, .pytest_cache/
    - node_modules/ (if any)
    - dist/, build/ (build artifacts)
    - VirtualBox files (*.vdi, *.vmdk, *.vbox)
    - Test artifacts (MagicMock/, sandboxes/, quarantine/)
    - Logs (*.log)
    
.PARAMETER IncludeBuild
    Include dist/ and build/ folders (default: false)
    
.PARAMETER MaxRetries
    Maximum number of retry attempts for failed operations (default: 3)
    
.PARAMETER RetryDelaySeconds
    Initial delay between retries in seconds (default: 2)
    
.EXAMPLE
    .\scripts\backup-repo.ps1
    # Creates backup in Desktop\repo backup, N:\backup\dev\repos, and OneDrive
    
.EXAMPLE
    .\scripts\backup-repo.ps1 -IncludeBuild
    # Creates backup including build artifacts
    
.EXAMPLE
    .\scripts\backup-repo.ps1 -MaxRetries 5 -RetryDelaySeconds 5
    # Custom retry configuration for unreliable network drives
#>

[CmdletBinding()]
param(
    [switch]$IncludeBuild = $false,
    [int]$MaxRetries = 3,
    [int]$RetryDelaySeconds = 2
)

# Set error action preference for better error handling
$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction'] = 'Stop'

# Initialize error tracking and logging
$script:ErrorLog = @()
$script:BackupResults = @{}
$script:StartTime = Get-Date
$script:TotalFilesProcessed = 0
$script:TotalFilesFailed = 0

#region Helper Functions

function Write-ErrorLog {
    param(
        [string]$Message,
        [string]$Category = "Error",
        [Exception]$Exception = $null
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Category] $Message"
    if ($Exception) {
        $logEntry += "`n  Exception: $($Exception.GetType().FullName)"
        $logEntry += "`n  Message: $($Exception.Message)"
        $logEntry += "`n  StackTrace: $($Exception.StackTrace)"
    }
    $script:ErrorLog += $logEntry
    Write-Host $logEntry -ForegroundColor $(if ($Category -eq "Error") { "Red" } elseif ($Category -eq "Warning") { "Yellow" } else { "Gray" })
}

function Test-DiskSpace {
    param(
        [string]$Path,
        [long]$RequiredBytes
    )
    try {
        $drive = (Get-Item $Path).PSDrive.Name
        $driveInfo = Get-PSDrive $drive -ErrorAction Stop
        $availableBytes = $driveInfo.Free
        
        if ($availableBytes -lt $RequiredBytes) {
            Write-ErrorLog "Insufficient disk space on $drive`: Available: $([math]::Round($availableBytes / 1MB, 2)) MB, Required: $([math]::Round($RequiredBytes / 1MB, 2)) MB" "Warning"
            return $false
        }
        return $true
    } catch {
        Write-ErrorLog "Failed to check disk space for $Path`: $_" "Warning" $_
        # Assume OK if we can't check (network drives, etc.)
        return $true
    }
}

function Test-PathAccess {
    param(
        [string]$Path,
        [string]$Operation = "Write"
    )
    try {
        $parentPath = Split-Path $Path -Parent
        if (-not (Test-Path $parentPath)) {
            Write-ErrorLog "Parent directory does not exist: $parentPath" "Error"
            return $false
        }
        
        # Test write access by creating a temporary file
        if ($Operation -eq "Write") {
            $testFile = Join-Path $parentPath ".backup-test-$(Get-Random).tmp"
            try {
                New-Item -ItemType File -Path $testFile -Force | Out-Null
                Remove-Item $testFile -Force -ErrorAction SilentlyContinue
                return $true
            } catch {
                Write-ErrorLog "No write access to $parentPath`: $_" "Error" $_
                return $false
            }
        }
        return $true
    } catch {
        Write-ErrorLog "Failed to test path access for $Path`: $_" "Error" $_
        return $false
    }
}

function Invoke-WithRetry {
    param(
        [scriptblock]$ScriptBlock,
        [string]$OperationName,
        [int]$MaxRetries = 3,
        [int]$InitialDelaySeconds = 2
    )
    
    $attempt = 0
    $delay = $InitialDelaySeconds
    
    while ($attempt -le $MaxRetries) {
        try {
            return & $ScriptBlock
        } catch {
            $attempt++
            if ($attempt -gt $MaxRetries) {
                Write-ErrorLog "Operation '$OperationName' failed after $MaxRetries retries" "Error" $_
                throw
            }
            
            Write-ErrorLog "Operation '$OperationName' failed (attempt $attempt/$MaxRetries). Retrying in $delay seconds..." "Warning" $_
            Start-Sleep -Seconds $delay
            $delay = [math]::Min($delay * 2, 60) # Exponential backoff, max 60 seconds
        }
    }
}

function New-BackupZip {
    param(
        [string]$ZipPath,
        [array]$Files,
        [string]$RepoRoot,
        [string]$BackupName
    )
    
    $zip = $null
    $filesAdded = 0
    $filesFailed = 0
    
    try {
        # Remove existing backup if present
        if (Test-Path $ZipPath) {
            Write-Host "    Removing existing backup file..." -ForegroundColor Gray
            Remove-Item $ZipPath -Force -ErrorAction Stop
        }
        
        # Create ZIP archive
        $zip = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
        
        $totalFiles = $Files.Count
        $processedFiles = 0
        
        foreach ($file in $Files) {
            $processedFiles++
            $script:TotalFilesProcessed++
            
            # Progress reporting for large backups
            if ($totalFiles -gt 100 -and $processedFiles % 100 -eq 0) {
                $percent = [math]::Round(($processedFiles / $totalFiles) * 100, 1)
                Write-Host "    Progress: $percent% ($processedFiles/$totalFiles files)" -ForegroundColor Gray
            }
            
            try {
                # Get relative path from repo root
                $relativePath = $file.FullName.Substring($repoRoot.Length + 1)
                # Use forward slashes for ZIP standard
                $zipPath = $relativePath -replace '\\', '/'
                
                # Add file to archive with full path
                [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                    $zip, 
                    $file.FullName, 
                    $zipPath, 
                    [System.IO.Compression.CompressionLevel]::Optimal
                ) | Out-Null
                
                $filesAdded++
            } catch {
                $filesFailed++
                $script:TotalFilesFailed++
                Write-ErrorLog "Failed to add file to archive: $($file.FullName)" "Warning" $_
                # Continue with next file instead of failing entire backup
            }
        }
        
        # Dispose ZIP archive
        $zip.Dispose()
        $zip = $null
        
        # Verify backup file was created and is valid
        if (-not (Test-Path $ZipPath)) {
            throw "Backup file was not created: $ZipPath"
        }
        
        $backupSize = (Get-Item $ZipPath).Length
        if ($backupSize -eq 0) {
            throw "Backup file is empty: $ZipPath"
        }
        
        # Verify ZIP integrity by attempting to open it
        try {
            $verifyZip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
            $entryCount = $verifyZip.Entries.Count
            $verifyZip.Dispose()
            
            if ($entryCount -eq 0) {
                throw "Backup file contains no entries: $ZipPath"
            }
        } catch {
            throw "Backup file integrity check failed: $($_.Message)"
        }
        
        return @{
            Success = $true
            FilesAdded = $filesAdded
            FilesFailed = $filesFailed
            BackupSize = $backupSize
        }
        
    } catch {
        Write-ErrorLog "Failed to create backup ZIP: $ZipPath" "Error" $_
        if ($zip) {
            try {
                $zip.Dispose()
            } catch {
                Write-ErrorLog "Failed to dispose ZIP archive" "Warning" $_
            }
        }
        
        # Cleanup partial backup file
        if (Test-Path $ZipPath) {
            try {
                Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
            } catch {
                Write-ErrorLog "Failed to cleanup partial backup file: $ZipPath" "Warning" $_
            }
        }
        
        throw
    }
}

function Save-ErrorLog {
    param([string]$LogPath)
    try {
        $logContent = "Backup Error Log`n"
        $logContent += "==================`n"
        $logContent += "Start Time: $($script:StartTime)`n"
        $logContent += "End Time: $(Get-Date)`n"
        $logContent += "Duration: $((Get-Date) - $script:StartTime)`n"
        $logContent += "`nErrors:`n"
        $logContent += ($script:ErrorLog -join "`n`n")
        
        $logContent | Out-File -FilePath $LogPath -Encoding UTF8 -ErrorAction Stop
        Write-Host "`n📝 Error log saved to: $LogPath" -ForegroundColor Cyan
    } catch {
        Write-Host "⚠️  Failed to save error log: $_" -ForegroundColor Yellow
    }
}

#endregion

#region Main Script

Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   📦 Repository Backup (SOTA Error Handling) 📦        ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

# Validate we're in a repository
try {
    $isRepo = (Test-Path "pyproject.toml") -or (Test-Path ".git") -or (Test-Path "package.json")
    if (-not $isRepo) {
        Write-ErrorLog "Must run from repository root (need pyproject.toml, .git, or package.json)" "Error"
        exit 1
    }
} catch {
    Write-ErrorLog "Failed to validate repository location" "Error" $_
    exit 1
}

# Get repository information
try {
    $repoName = (Get-Item .).Name
    $repoRoot = (Get-Item .).FullName
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $backupName = "${repoName}_backup_${timestamp}.zip"
} catch {
    Write-ErrorLog "Failed to get repository information" "Error" $_
    exit 1
}

# Define backup destinations
try {
    $desktopBackup = Join-Path (Join-Path ([Environment]::GetFolderPath("Desktop")) "repo backup") $repoName
    $nDriveBackup = Join-Path "N:\backup\dev\repos2" $repoName
    $oneDriveRoot = Join-Path $env:OneDrive "repo-backups"
    $oneDriveBackup = Join-Path $oneDriveRoot $repoName
    
    $backupDestinations = @(
        @{ Name = "Desktop"; Path = $desktopBackup; BackupPath = (Join-Path $desktopBackup $backupName); Enabled = $true }
        @{ Name = "N: Drive"; Path = $nDriveBackup; BackupPath = (Join-Path $nDriveBackup $backupName); Enabled = $true }
        @{ Name = "OneDrive"; Path = $oneDriveBackup; BackupPath = (Join-Path $oneDriveBackup $backupName); Enabled = $true }
    )
} catch {
    Write-ErrorLog "Failed to define backup destinations" "Error" $_
    exit 1
}

# Display configuration
Write-Host "📋 Backup Configuration:" -ForegroundColor Cyan
Write-Host "  Repository:    $repoName" -ForegroundColor White
Write-Host "  Timestamp:     $timestamp" -ForegroundColor White
Write-Host "  Include build: $(if($IncludeBuild){'Yes'}else{'No'})" -ForegroundColor White
Write-Host "  Max retries:   $MaxRetries" -ForegroundColor White
Write-Host "  Retry delay:   $RetryDelaySeconds seconds" -ForegroundColor White
Write-Host ""

# Ensure backup directories exist and validate access
foreach ($dest in $backupDestinations) {
    try {
        if (-not (Test-Path $dest.Path)) {
            Write-Host "  Creating directory: $($dest.Path)" -ForegroundColor Gray
            New-Item -ItemType Directory -Path $dest.Path -Force | Out-Null
        }
        
        # Test write access
        if (-not (Test-PathAccess -Path $dest.BackupPath -Operation "Write")) {
            Write-ErrorLog "No write access to $($dest.Name) backup location: $($dest.Path)" "Error"
            $dest.Enabled = $false
            continue
        }
        
        Write-Host "  ✅ $($dest.Name): $($dest.Path)" -ForegroundColor Green
    } catch {
        Write-ErrorLog "Failed to setup $($dest.Name) backup location: $($dest.Path)" "Error" $_
        $dest.Enabled = $false
    }
}

# Filter out disabled destinations
$backupDestinations = $backupDestinations | Where-Object { $_.Enabled }

if ($backupDestinations.Count -eq 0) {
    Write-ErrorLog "No valid backup destinations available" "Error"
    exit 1
}

# Define exclusions
$exclusions = @(
    ".venv", "venv", "env", ".env",
    "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "htmlcov",
    "node_modules",
    "*.pyc", "*.pyo", "*.pyd",
    ".DS_Store", "Thumbs.db",
    ".windsurf", ".cursor",
    "*.log",
    ".vbox", "*.vdi", "*.vmdk", "*.vhd", "*.vbox-prev",
    "MagicMock", "sandboxes", "quarantine", "analysis", "backups",
    "*.dxt"
)

$excludeLargeTestFiles = @(
    "samples/metadata.db",
    "samples/test_library.db",
    "test_data/*.db"
)

$exclusions += $excludeLargeTestFiles

if (-not $IncludeBuild) {
    $exclusions += @("dist", "build", "*.whl", "*.tar.gz")
}

Write-Host "🚫 Excluding:" -ForegroundColor Yellow
foreach ($excl in $exclusions) {
    Write-Host "  - $excl" -ForegroundColor Gray
}
Write-Host ""

# Analyze repository size
Write-Host "📊 Analyzing repository size..." -ForegroundColor Cyan

try {
    $allFiles = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        # Skip symlinks/ReparsePoints (cause access denied errors)
        -not ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
    }
    
    $totalSize = ($allFiles | Measure-Object -Property Length -Sum).Sum
    
    # Filter files to backup
    $backupFiles = $allFiles | Where-Object {
        $file = $_
        $shouldExclude = $false
        
        foreach ($excl in $exclusions) {
            $pattern = $excl -replace '\*', '.*' -replace '\.', '\.'
            if ($file.FullName -match $pattern -or $file.FullName -match [regex]::Escape($excl)) {
                $shouldExclude = $true
                break
            }
        }
        
        -not $shouldExclude
    }
    
    $backupSize = ($backupFiles | Measure-Object -Property Length -Sum).Sum
    $excludedSize = $totalSize - $backupSize
    
    Write-Host "  Total size:    $([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor White
    Write-Host "  Excluded:      $([math]::Round($excludedSize / 1MB, 2)) MB" -ForegroundColor Red
    Write-Host "  Backup size:   $([math]::Round($backupSize / 1MB, 2)) MB" -ForegroundColor Green
    Write-Host "  Files:         $($backupFiles.Count)" -ForegroundColor White
    if ($totalSize -gt 0) {
        Write-Host "  Reduction:     $([math]::Round(($excludedSize / $totalSize) * 100, 1))%" -ForegroundColor Cyan
    }
    Write-Host ""
    
    # Estimate compressed size (assume 50% compression ratio)
    $estimatedCompressedSize = $backupSize * 0.5
    
    # Validate disk space for all destinations
    foreach ($dest in $backupDestinations) {
        if (-not (Test-DiskSpace -Path $dest.Path -RequiredBytes $estimatedCompressedSize)) {
            Write-ErrorLog "Insufficient disk space for $($dest.Name) backup" "Warning"
            # Don't disable, let it try and fail gracefully
        }
    }
    
} catch {
    Write-ErrorLog "Failed to analyze repository" "Error" $_
    exit 1
}

# Create backups
Write-Host "🔄 Creating backups..." -ForegroundColor Cyan
Write-Host ""

$successfulBackups = 0
$failedBackups = 0

foreach ($dest in $backupDestinations) {
    Write-Host "  → $($dest.Name) backup..." -ForegroundColor Gray
    
    try {
        $result = Invoke-WithRetry -ScriptBlock {
            New-BackupZip -ZipPath $dest.BackupPath -Files $backupFiles -RepoRoot $repoRoot -BackupName $backupName
        } -OperationName "$($dest.Name) backup" -MaxRetries $MaxRetries -InitialDelaySeconds $RetryDelaySeconds
        
        $script:BackupResults[$dest.Name] = $result
        $successfulBackups++
        
        $backupSizeMB = [math]::Round($result.BackupSize / 1MB, 2)
        Write-Host "  ✅ $($dest.Name) backup complete: $backupSizeMB MB ($($result.FilesAdded) files)" -ForegroundColor Green
        
        if ($result.FilesFailed -gt 0) {
            Write-Host "    ⚠️  Warning: $($result.FilesFailed) files failed to add" -ForegroundColor Yellow
        }
        
    } catch {
        $failedBackups++
        $script:BackupResults[$dest.Name] = @{ Success = $false; Error = $_.Exception.Message }
        Write-ErrorLog "Failed to create $($dest.Name) backup" "Error" $_
        Write-Host "  ❌ $($dest.Name) backup failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Summary
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $(if ($failedBackups -eq 0) { "Green" } else { "Yellow" })
Write-Host "║              📦 Backup Summary 📦                        ║" -ForegroundColor $(if ($failedBackups -eq 0) { "Green" } else { "Yellow" })
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $(if ($failedBackups -eq 0) { "Green" } else { "Yellow" })
Write-Host ""

if ($successfulBackups -gt 0) {
    Write-Host "✅ Successful backups: $successfulBackups" -ForegroundColor Green
    foreach ($dest in $backupDestinations) {
        if ($script:BackupResults[$dest.Name].Success) {
            $result = $script:BackupResults[$dest.Name]
            $backupSizeMB = [math]::Round($result.BackupSize / 1MB, 2)
            Write-Host "  • $($dest.Name): $backupSizeMB MB at $($dest.BackupPath)" -ForegroundColor White
        }
    }
    Write-Host ""
}

if ($failedBackups -gt 0) {
    Write-Host "❌ Failed backups: $failedBackups" -ForegroundColor Red
    foreach ($dest in $backupDestinations) {
        if (-not $script:BackupResults[$dest.Name].Success) {
            Write-Host "  • $($dest.Name): $($script:BackupResults[$dest.Name].Error)" -ForegroundColor Red
        }
    }
    Write-Host ""
}

Write-Host "📊 Statistics:" -ForegroundColor Cyan
Write-Host "  Files processed: $script:TotalFilesProcessed" -ForegroundColor White
Write-Host "  Files failed:    $script:TotalFilesFailed" -ForegroundColor $(if ($script:TotalFilesFailed -eq 0) { "Green" } else { "Yellow" })
Write-Host "  Duration:        $((Get-Date) - $script:StartTime)" -ForegroundColor White
Write-Host ""

# Save error log if there were errors
if ($script:ErrorLog.Count -gt 0 -or $failedBackups -gt 0) {
    $logPath = Join-Path $env:TEMP "backup-error-log-${timestamp}.txt"
    Save-ErrorLog -LogPath $logPath
}

# Exit with appropriate code
if ($successfulBackups -eq 0) {
    Write-Host "❌ All backups failed!" -ForegroundColor Red
    exit 1
} elseif ($failedBackups -gt 0) {
    Write-Host "⚠️  Some backups failed, but $successfulBackups succeeded" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "✅ All backups completed successfully!`n" -ForegroundColor Green
    exit 0
}

#endregion

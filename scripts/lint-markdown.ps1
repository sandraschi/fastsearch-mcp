# Script to lint and fix markdown files
# Requires: markdownlint-cli (npm install -g markdownlint-cli)
# Usage: .\scripts\lint-markdown.ps1 [-Fix]

[CmdletBinding()]
param (
    [switch]$Fix = $false
)

$ErrorActionPreference = "Stop"

# Check if markdownlint is installed
$markdownLintCmd = Get-Command markdownlint -ErrorAction SilentlyContinue
if (-not $markdownLintCmd) {
    Write-Error "markdownlint-cli is not installed. Please install it with: npm install -g markdownlint-cli"
    exit 1
}

# Define markdown files to check
$markdownFiles = @(
    "README.md"
    "CHANGELOG.md"
    "docs\\*.md"
)

# Filter out non-existent files and patterns
$filesToCheck = @()
foreach ($pattern in $markdownFiles) {
    if ($pattern -like '*\*') {
        # Handle wildcard patterns
        $matchingFiles = Get-ChildItem -Path $pattern -File -ErrorAction SilentlyContinue
        if ($matchingFiles) {
            $filesToCheck += $matchingFiles.FullName
        }
    } elseif (Test-Path $pattern -PathType Leaf) {
        # Handle specific files
        $filesToCheck += (Resolve-Path $pattern).Path
    }
}

# Create .markdownlint.json if it doesn't exist
$configFile = "$PSScriptRoot\..\.markdownlint.json"
if (-not (Test-Path $configFile)) {
    $configJson = @'
{
  "default": true,
  "line-length": 120,
  "no-inline-html": false,
  "no-duplicate-heading": {
    "siblings_only": true
  },
  "no-bare-urls": false,
  "fenced-code-language": false,
  "blanks-around-headers": false,
  "no-multiple-blanks": false,
  "no-trailing-spaces": false
}
'@
    $configJson | Out-File -FilePath $configFile -Encoding utf8 -NoNewline
    Write-Host "Created default .markdownlint.json configuration file" -ForegroundColor Green
}

# Run markdownlint
$allPassed = $true
foreach ($file in $filesToCheck) {
    Write-Host "Linting $file..." -ForegroundColor Cyan
    
    try {
        $lintArgs = @(
            "--config", $configFile,
            "$file"
        )
        
        if ($Fix) {
            $lintArgs += "--fix"
        }
        
        & markdownlint @lintArgs
        
        if ($LASTEXITCODE -ne 0) {
            $allPassed = $false
            if (-not $Fix) {
                Write-Host "  Issues found in $(Split-Path $file -Leaf). Run with -Fix to automatically fix some issues." -ForegroundColor Yellow
            } else {
                Write-Host "  Applied fixes to $(Split-Path $file -Leaf)" -ForegroundColor Green
            }
        } else {
            Write-Host "  No issues found in $(Split-Path $file -Leaf)" -ForegroundColor Green
        }
    } catch {
        $allPassed = $false
        Write-Error "Error linting $file : $_"
    }
}

# Exit with appropriate status
if (-not $allPassed) {
    Write-Host "\nSome markdown files have issues. Check the output above for details." -ForegroundColor Red
    exit 1
}

Write-Host "\nAll markdown files passed linting!" -ForegroundColor Green
exit 0

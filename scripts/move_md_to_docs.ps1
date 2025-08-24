# Script to move markdown files from root to docs directory

# Define source and destination paths
$repoRoot = Split-Path -Parent $PSScriptRoot
$docsDir = Join-Path $repoRoot "docs"

# List of markdown files to move
$mdFiles = @(
    "ACKNOWLEDGMENTS.md",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "DEVELOPMENT.md",
    "DXT_PACKAGING_GUIDE.md",
    "INSTALL.md",
    "MAINTAINERS.md",
    "MCP_ECOSYSTEM.md",
    "PACKAGING.md",
    "RELEASING.md",
    "RELEASE_TEMPLATE.md",
    "ROADMAP.md",
    "SECURITY.md",
    "SUPPORT.md",
    "VIBECODER_MANIFESTO.md",
    "WEB_API.md"
)

# Ensure docs directory exists
if (-not (Test-Path $docsDir)) {
    New-Item -ItemType Directory -Path $docsDir | Out-Null
    Write-Host "Created docs directory at $docsDir"
}

# Move each markdown file
foreach ($file in $mdFiles) {
    $source = Join-Path $repoRoot $file
    $destination = Join-Path $docsDir $file
    
    if (Test-Path $source) {
        Move-Item -Path $source -Destination $destination -Force
        Write-Host "Moved $file to docs/"
    } else {
        Write-Host "File not found: $file" -ForegroundColor Yellow
    }
}

Write-Host "\nMarkdown files have been moved to the docs directory." -ForegroundColor Green

# Build script for FastSearch MCP Installer
# Requires: Visual Studio 2022, WiX Toolset, CMake

param (
    [string]$Configuration = "Release",
    [string]$OutputDir = "installer",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$scriptPath = $PSScriptRoot
$solutionDir = "$scriptPath\"
$wixDir = "$scriptPath\wix"
# Removed Python directory reference as it's no longer needed
$installerDir = "$solutionDir\$OutputDir"

# Create output directory if it doesn't exist
if (-not (Test-Path -Path $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir | Out-Null
}

# Build the project if not skipped
if (-not $SkipBuild) {
    Write-Host "Building FastSearch MCP in $Configuration mode..." -ForegroundColor Cyan
    
    # Build the C++ service
    Write-Host "Building C++ service..." -ForegroundColor Cyan
    $buildDir = "$solutionDir\service\build"
    
    if (-not (Test-Path -Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }
    
    Push-Location $buildDir
    
    # Configure CMake if needed
    if (-not (Test-Path -Path "CMakeCache.txt")) {
        cmake .. -G "Visual Studio 17 2022" -A x64
        if ($LASTEXITCODE -ne 0) {
            Write-Error "CMake configuration failed"
            exit $LASTEXITCODE
        }
    }
    
    # Build the project
    cmake --build . --config $Configuration
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit $LASTEXITCODE
    }
    
    Pop-Location
}

# Verify prerequisites
$prerequisites = @(
    @{ Name = "WiX Toolset"; Path = @("C:\Program Files (x86)\WiX Toolset v3.14\bin", "C:\Program Files\WiX Toolset v3.14\bin"); Url = "https://wixtoolset.org/releases/" },
    @{ Name = "Visual Studio 2022"; Path = @("C:\Program Files\Microsoft Visual Studio\2022\Community", "C:\Program Files\Microsoft Visual Studio\2022\Professional"); Url = "https://visualstudio.microsoft.com/downloads/" },
    @{ Name = "CMake"; Path = @("C:\Program Files\CMake\bin"); Url = "https://cmake.org/download/" }
)

foreach ($prereq in $prerequisites) {
    $found = $false
    foreach ($path in $prereq.Path) {
        if (Test-Path -Path $path) {
            $found = $true
            if ($prereq.Name -eq "WiX Toolset") {
                $wixPath = $path
            }
            break
        }
    }
    
    if (-not $found) {
        Write-Error "$($prereq.Name) not found. Please install $($prereq.Name)."
        Write-Host "Download from: $($prereq.Url)" -ForegroundColor Yellow
        exit 1
    }
}

# Set environment variables
$env:Path = "$wixPath;$env:Path"
$env:Path = "$env:Path;C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin"
$env:Path = "$env:Path;C:\Program Files\CMake\bin"
$env:SolutionDir = $solutionDir
$env:Configuration = $Configuration

# Compile the WiX source
Write-Host "Compiling installer..." -ForegroundColor Cyan
$wxsFile = "$wixDir\Product.wxs"
$wixobjFile = "$installerDir\FastSearchMCP.wixobj"
$msiFile = "$installerDir\FastSearchMCP.msi"

# Get the service executable path
$serviceExePath = "$solutionDir\service\build\$Configuration\FastSearchService.exe"
if (-not (Test-Path -Path $serviceExePath)) {
    Write-Error "Service executable not found at $serviceExePath"
    exit 1
}

# Compile WiX source with preprocessor variables
$solutionDirEscaped = $solutionDir.Replace('\', '\\')
$serviceDir = (Get-Item $serviceExePath).Directory.FullName.Replace('\', '\\')

candle.exe -nologo `
    -dSolutionDir="$solutionDirEscaped" `
    -dServiceDir="$serviceDir" `
    -dConfiguration=$Configuration `
    -out "$wixobjFile" "$wxsFile"

if ($LASTEXITCODE -ne 0) {
    Write-Error "WiX compilation failed"
    exit $LASTEXITCODE
}

# Link the MSI
Write-Host "Linking MSI package..." -ForegroundColor Cyan
light.exe -nologo -out "$msiFile" "$wixobjFile" -ext WixUIExtension -ext WixUtilExtension
if ($LASTEXITCODE -ne 0) {
    Write-Error "MSI linking failed"
    exit $LASTEXITCODE
}

# Create a bootstrapper (optional, requires WiX Bal extension)
$bundleWxs = "$wixDir\Bundle.wxs"
if (Test-Path $bundleWxs) {
    Write-Host "Creating bootstrapper..." -ForegroundColor Cyan
    $bundleObj = "$installerDir\Bundle.wixobj"
    $bundleExe = "$installerDir\FastSearchMCP-Setup.exe"
    
    candle.exe -nologo -out "$bundleObj" "$bundleWxs"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Bootstrapper compilation failed"
        exit $LASTEXITCODE
    }
    
    light.exe -nologo -out "$bundleExe" "$bundleObj" -ext WixBalExtension -ext WixUIExtension
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Bootstrapper linking failed"
        exit $LASTEXITCODE
    }
}

Write-Host "`nInstallation package created successfully!" -ForegroundColor Green
Write-Host "MSI Installer: $msiFile" -ForegroundColor Yellow
if (Test-Path $bundleExe) {
    Write-Host "Bootstrapper: $bundleExe" -ForegroundColor Yellow
}

# Open the output directory
explorer $installerDir

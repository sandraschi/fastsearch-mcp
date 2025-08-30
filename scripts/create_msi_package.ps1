param(
    [string]$Version,
    [string]$Platform,
    [string]$OutputDir,
    [string]$ProjectDir = ".",
    [string]$WixBinDir = "wix"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Create output directory if it doesn't exist
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Paths
$wxsFile = Join-Path $ProjectDir "$WixBinDir\Product.wxs"
$wixobjFile = Join-Path $OutputDir "FastSearchMCP.wixobj"
$msiFile = Join-Path $OutputDir "FastSearchMCP-$Version-$Platform.msi"

# Update version in WXS file
$wxsContent = Get-Content -Path $wxsFile -Raw
$wxsContent = $wxsContent -replace 'Version="[^"]*"', "Version=`"$Version`""
$wxsContent | Set-Content -Path $wxsFile

# Compile WXS file
Write-Host "Compiling WXS file..."
& "$env:WIX\bin\candle.exe" -nologo -out "$wixobjFile" -ext WixUtilExtension "$wxsFile"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to compile WXS file"
}

# Link the MSI
Write-Host "Linking MSI..."
& "$env:WIX\bin\light.exe" -nologo -out "$msiFile" -ext WixUIExtension -ext WixUtilExtension "$wixobjFile"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to link MSI"
}

Write-Host "MSI package created: $msiFile"

# Create-Installer.ps1
# Creates a Windows installer for FastSearch MCP

param(
    [string]$Version = "1.0.0",
    [string]$OutputDir = "$PSScriptRoot\dist",
    [switch]$SkipBuild
)

# Error handling
$ErrorActionPreference = "Stop"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

# Check for WiX Toolset
$wixPath = "${env:ProgramFiles(x86)}\WiX Toolset v3.11\bin"
if (-not (Test-Path $wixPath)) {
    Write-Host "WiX Toolset v3.11 is required but not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Add WiX to PATH
$env:Path = "$wixPath;$env:Path"

# Create output directories
$tempDir = "$env:TEMP\FastSearchMCP"
$binDir = "$tempDir\bin"
$configDir = "$tempDir\config"

if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}

New-Item -ItemType Directory -Path $binDir -Force | Out-Null
New-Item -ItemType Directory -Path $configDir -Force | Out-Null

# Build the service if not skipped
if (-not $SkipBuild) {
    Write-Host "Building FastSearch MCP Service..." -ForegroundColor Cyan
    & "$PSScriptRoot\build.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed. See errors above." -ForegroundColor Red
        exit 1
    }
}

# Copy service binary
$serviceBinary = "$PSScriptRoot\service\target\release\fastsearch-service.exe"
if (-not (Test-Path $serviceBinary)) {
    Write-Host "Service binary not found at $serviceBinary. Did the build succeed?" -ForegroundColor Red
    exit 1
}
Copy-Item -Path $serviceBinary -Destination $binDir\

# Copy Python bridge
$bridgeDir = "$PSScriptRoot\bridge"
if (-not (Test-Path $bridgeDir)) {
    Write-Host "Bridge directory not found at $bridgeDir" -ForegroundColor Red
    exit 1
}

# Create a virtual environment and install dependencies
Write-Host "Setting up Python bridge..." -ForegroundColor Cyan
$venvPath = "$tempDir\python"
python -m venv $venvPath
& "$venvPath\Scripts\pip" install -r "$bridgeDir\requirements.txt"

# Copy bridge files
$bridgeFiles = @(
    "$bridgeDir\__main__.py",
    "$bridgeDir\requirements.txt",
    "$bridgeDir\README.md"
)

foreach ($file in $bridgeFiles) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $binDir\
    }
}

# Create a batch file to run the bridge
$bridgeLauncher = "$binDir\fastsearch-mcp-bridge.bat"
@"
@echo off
"%~dp0\python\Scripts\python.exe" "%~dp0\__main__.py" %*
"@ | Out-File -FilePath $bridgeLauncher -Encoding ascii

# Create a configuration file
$configContent = @"
{
    "mcpServers": {
        "fastsearch": {
            "command": "fastsearch-mcp-bridge.bat",
            "args": ["--service-pipe", "\\\\\\.\\pipe\\fastsearch-service"],
            "timeout": 30,
            "autoStart": true
        }
    }
}
"@

$configContent | Out-File -FilePath "$configDir\fastsearch-mcp-config.json" -Encoding utf8

# Create WiX installer
Write-Host "Creating installer..." -ForegroundColor Cyan

# Create a unique upgrade code based on the version
$upgradeGuid = [guid]::NewGuid().ToString().ToUpper()

# Create the WiX config file
$wxsContent = @"
<?xml version='1.0' encoding='windows-1252'?>
<Wix xmlns='http://schemas.microsoft.com/wix/2006/wi'>
  <Product Name='FastSearch MCP' 
           Version='$Version' 
           Manufacturer='FastSearch' 
           UpgradeCode='$upgradeGuid'
           Language='1033'>
    
    <Package Compressed='yes' 
             InstallerVersion='200' 
             Compressed='yes' 
             InstallPrivileges='elevated' 
             InstallScope='perMachine'
             Platform='x64' />
    
    <MajorUpgrade 
      DowngradeErrorMessage='A newer version of [ProductName] is already installed.' />
    
    <MediaTemplate EmbedCab='yes' />
    
    <Feature Id='ProductFeature' Title='FastSearch MCP' Level='1'>
      <ComponentGroupRef Id='ProductComponents' />
    </Feature>
    
    <UIRef Id="WixUI_Minimal" />
    <UIRef Id="WixUI_ErrorProgressText" />
    
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER" />
    
  </Product>
  
  <Fragment>
    <Directory Id='TARGETDIR' Name='SourceDir'>
      <Directory Id='ProgramFiles64Folder'>
        <Directory Id='INSTALLFOLDER' Name='FastSearch MCP'>
          <Directory Id='BINDIR' Name='bin' />
          <Directory Id='CONFIGDIR' Name='config' />
        </Directory>
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="FastSearch MCP"/>
      </Directory>
    </Directory>
  </Fragment>
  
  <Fragment>
    <ComponentGroup Id='ProductComponents' Directory='INSTALLFOLDER'>
      <Component Id='MainExecutable' Guid='*'>
        <File Id='FastSearchService' 
              Name='fastsearch-service.exe' 
              Source='$binDir\fastsearch-service.exe' 
              KeyPath='yes' 
              Checksum='yes' />
      </Component>
      
      <Component Id='PythonBridge' Guid='*'>
        <File Id='BridgeMain' 
              Name='__main__.py' 
              Source='$binDir\__main__.py' 
              KeyPath='yes' />
        <File Id='BridgeRequirements' 
              Name='requirements.txt' 
              Source='$binDir\requirements.txt' />
        <File Id='BridgeReadme' 
              Name='README.md' 
              Source='$binDir\README.md' />
        <File Id='BridgeLauncher' 
              Name='fastsearch-mcp-bridge.bat' 
              Source='$bridgeLauncher' />
      </Component>
      
      <Component Id='ConfigFiles' Guid='*'>
        <File Id='ConfigFile' 
              Name='fastsearch-mcp-config.json' 
              Source='$configDir\fastsearch-mcp-config.json' 
              KeyPath='yes' />
      </Component>
      
      <Component Id='PythonEnvironment' Guid='*'>
        <CreateFolder />
        <util:RemoveFolderEx On='uninstall' Property='PYTHONENV' />
      </Component>
    </ComponentGroup>
  </Fragment>
  
  <Fragment>
    <DirectoryRef Id="ApplicationProgramsFolder">
      <Component Id="ApplicationShortcut" Guid="*">
        <Shortcut Id="ApplicationStartMenuShortcut" 
                  Name="FastSearch MCP Bridge" 
                  Description="Start FastSearch MCP Bridge" 
                  Target="[BINDIR]fastsearch-mcp-bridge.bat"
                  WorkingDirectory="BINDIR"/>
        <RemoveFolder Id="RemoveApplicationProgramsFolder" On="uninstall"/>
        <RegistryValue Root="HKCU" Key="Software\FastSearchMCP" Name="installed" Type="integer" Value="1" KeyPath="yes"/>
      </Component>
    </DirectoryRef>
  </Fragment>
  
</Wix>
"@

$wxsPath = "$tempDir\FastSearchMCP.wxs"
$wxsContent | Out-File -FilePath $wxsPath -Encoding utf8

# Create the installer
$msiPath = "$OutputDir\FastSearchMCP-$Version.msi"
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Write-Host "Compiling installer..." -ForegroundColor Cyan
candle.exe -nologo -out "$tempDir\" "$wxsPath"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to compile WiX source files" -ForegroundColor Red
    exit 1
}

Write-Host "Linking installer..." -ForegroundColor Cyan
light.exe -nologo -out "$msiPath" -ext WixUIExtension "$tempDir\FastSearchMCP.wixobj"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create MSI package" -ForegroundColor Red
    exit 1
}

Write-Host "`nInstaller created successfully at: $msiPath" -ForegroundColor Green
Write-Host "`nTo install, run: msiexec /i `"$msiPath`" /qb" -ForegroundColor Cyan

# Clean up
# Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

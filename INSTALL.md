# FastSearch MCP - Installation Guide

## Prerequisites

- Windows 10/11 (64-bit)
- [Rust](https://www.rust-lang.org/tools/install) (latest stable version)
- [Python 3.8+](https://www.python.org/downloads/)
- [WiX Toolset v3.11+](https://wixtoolset.org/releases/) (for creating the installer)
- Administrator privileges (for installation)

## Building from Source

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/fastsearch-mcp.git
cd fastsearch-mcp
```

### 2. Build the Service

Run the build script to compile the Rust service:

```powershell
.\build.ps1
```

### 3. Create Installer

Create a Windows Installer (MSI) package:

```powershell
.\create-installer.ps1 -Version 1.0.0
```

The installer will be created in the `dist` directory.

## Installation

### Using the Installer

1. Double-click the `FastSearchMCP-1.0.0.msi` file
2. Follow the on-screen instructions
3. The installer will:
   - Install the FastSearch service
   - Set up the Python bridge
   - Create Start Menu shortcuts
   - Add the service to Windows Services

### Manual Installation

If you prefer to install manually:

1. Copy the contents of the `service\target\release` directory to your desired installation location
2. Install Python dependencies:
   ```
   pip install -r bridge/requirements.txt
   ```
3. Run the service manually:
   ```
   fastsearch-service.exe run
   ```

## Configuration

After installation, you can configure the service by editing the configuration file at:

```
%PROGRAMFILES%\FastSearch MCP\config\fastsearch-mcp-config.json
```

### Web API

The service includes a web API that runs on port 8080 by default. You can change this by:

1. Edit the configuration file
2. Or run the service with a custom port:
   ```
   fastsearch-service.exe run --port 9000
   ```

## Uninstallation

### Using Windows Add/Remove Programs

1. Open Windows Settings
2. Go to Apps > Apps & features
3. Find "FastSearch MCP" and click Uninstall

### Using Command Line

```powershell
msiexec /x "C:\Path\To\FastSearchMCP-1.0.0.msi" /qb
```

## Troubleshooting

### Service Won't Start

1. Check the service logs at `C:\ProgramData\FastSearch\service.log`
2. Ensure no other service is using the same port (default: 8080)
3. Run the service in console mode for detailed error output:
   ```
   fastsearch-service.exe run
   ```

### Build Issues

1. Ensure all prerequisites are installed
2. Run PowerShell as Administrator
3. Check that the Rust toolchain is properly installed:
   ```
   rustc --version
   cargo --version
   ```

## Support

For issues and feature requests, please open an issue on our [GitHub repository](https://github.com/yourusername/fastsearch-mcp).

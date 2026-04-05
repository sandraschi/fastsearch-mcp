# FastSearch MCP Installer

This directory contains the WiX Toolset source files for creating a professional Windows installer for the FastSearch MCP service and Python MCP bridge.

## Architecture

FastSearch MCP uses a **dual-process architecture**:
- **C++ Windows Service**: High-privilege NTFS MFT access with UAC elevation
- **Python MCP Bridge**: Claude Desktop integration without UAC requirements
- **Named Pipe Communication**: Secure IPC between processes

## Prerequisites

1. **WiX Toolset v3.11 or later**
   - Download from: <https://wixtoolset.org/releases/>
   - Add WiX to your PATH during installation

2. **Python 3.8+ Runtime**
   - The installer will automatically download and install this if needed
   - Manual download: <https://www.python.org/downloads/>

3. **Visual C++ Redistributable**
   - Required for the C++ service executable
   - Automatically installed by the installer

## Building the Installer

1. Build the C++ service in Release mode:

   ```powershell
   cd service\build
   cmake --build . --config Release
   ```

2. Verify all required files exist:
   - `service\build\bin\Release\FastSearchServiceNew.exe` (C++ service)
   - `src\fastsearch_mcp\server.py` (Python MCP bridge)
   - `install-service.ps1` (PowerShell management)
   - `service-control.bat` (Service control script)

3. Run the build script to create the installer:

   ```powershell
   .\build-installer.ps1
   ```

   This will create two files in the `installer` directory:
   - `FastSearchMCP.msi` - The main MSI installer
   - `FastSearchMCP.exe` - The bootstrapper with dependencies

## Installer Features

### MSI Package (`FastSearchMCP.msi`)
- **C++ Service Binary**: `FastSearchServiceNew.exe` with LocalSystem privileges
- **Python MCP Bridge**: Complete Python MCP server implementation
- **PowerShell Scripts**: Service management and diagnostic tools
- **Service Installation**: Automatic Windows service registration
- **Documentation**: README, CHANGELOG, and development status

### Bundle Package (`FastSearchMCP.exe`)
- **Python 3.8+ Detection**: Automatic Python runtime detection
- **Python Installation**: Downloads and installs Python if needed
- **Visual C++ Redistributable**: Required for C++ service
- **MSI Integration**: Embeds the main MSI package
- **Professional UI**: Custom branding and error handling

## Service Configuration

The installer configures the service with:
- **Service Name**: `FastSearchMCP`
- **Display Name**: `FastSearch MCP Service`
- **Account**: `LocalSystem` (for UAC privileges)
- **Start Type**: `Automatic` (starts with Windows)
- **Dependencies**: TCP/IP service

## Installation Process

1. **Dependency Check**: Verifies Python 3.8+ and Visual C++ Redistributable
2. **Dependency Installation**: Downloads and installs missing components
3. **MSI Installation**: Installs FastSearch MCP files and service
4. **Service Registration**: Registers and starts the Windows service
5. **Post-Install**: Optional service control launcher

## Post-Installation

After installation, users can:
- **Service Control**: Use `service-control.bat` for management
- **PowerShell Management**: Use `install-service.ps1` for advanced control
- **Claude Desktop**: Configure MCP server connection
- **Diagnostics**: Use built-in diagnostic tools

## Uninstallation

The installer provides complete uninstallation:
- **Service Stop**: Gracefully stops the service
- **Service Removal**: Removes Windows service registration
- **File Cleanup**: Removes all installed files
- **Registry Cleanup**: Removes installation registry entries

## Development Notes

### File Structure
```
installer/
├── FastSearchMCP.msi          # Main installer package
├── FastSearchMCP.exe          # Bootstrapper with dependencies
└── FastSearchMCP.wixobj       # Compiled WiX objects
```

### WiX Source Files
- `Product.wxs` - Main MSI package definition
- `Bundle.wxs` - Bootstrapper with dependency management
- `license.rtf` - License agreement text
- `theme.xml` - Custom installer theme

### Build Process
1. **CMake Build**: Compiles C++ service executable
2. **File Verification**: Ensures all required files exist
3. **WiX Compilation**: Compiles WiX source files
4. **MSI Linking**: Creates the MSI package
5. **Bundle Linking**: Creates the bootstrapper EXE

## Troubleshooting

### Common Issues
- **WiX Not Found**: Install WiX Toolset and add to PATH
- **Missing Dependencies**: Ensure Visual Studio 2022 and CMake are installed
- **Build Failures**: Check that all source files exist and are accessible
- **Service Issues**: Use `install-service.ps1 diagnose` for troubleshooting

### Build Requirements
- Windows 10/11 with Visual Studio 2022
- WiX Toolset v3.11 or later
- CMake 3.20 or later
- PowerShell 5.1 or later

## Distribution

The installer is ready for distribution:
- **Single EXE**: `FastSearchMCP.exe` includes all dependencies
- **Professional Branding**: Custom installer UI and branding
- **Error Handling**: Comprehensive error handling and recovery
- **Silent Installation**: Supports silent installation for enterprise deployment

## Support

For installation issues:
1. Check the Windows Event Log for service errors
2. Use `install-service.ps1 diagnose` for automated diagnostics
3. Verify all prerequisites are installed
4. Check file permissions and UAC settings

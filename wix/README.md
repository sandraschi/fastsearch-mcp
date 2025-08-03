# FastSearch MCP Installer

This directory contains the WiX Toolset source files for creating a professional Windows installer for the FastSearch MCP service and bridge.

## Prerequisites

1. **WiX Toolset v3.11 or later**
   - Download from: <https://wixtoolset.org/releases/>
   - Add WiX to your PATH during installation

2. **.NET 6.0 Desktop Runtime**
   - The installer will automatically download and install this if needed
   - Manual download: <https://dotnet.microsoft.com/download/dotnet/6.0>

## Building the Installer

1. Build the Rust project in Release mode:

   ```
   cargo build --release
   ```

2. Run the build script to create the installer:

   ```
   .\build-installer.ps1
   ```

   This will create two files in the `installer` directory:
   - `FastSearchMCP.msi` - The main MSI installer
   - `FastSearchMCP-Setup.exe` - A single-file bootstrapper that can install prerequisites

## Installer Features

- **Single EXE Distribution**: The bootstrapper includes all required components
- **Automatic Prerequisite Installation**: Installs .NET 6.0 if needed
- **Professional UI**: Custom branded installation experience
- **Service Installation**: Automatically installs and starts the FastSearch service
- **Uninstallation**: Clean removal of all components

## Customization

### Branding

1. Replace `banner.bmp` (493x58 pixels) - Top banner image
2. Replace `dlgbmp.bmp` (493x49 pixels) - Dialog background
3. Update `theme.xml` for custom colors and layouts

### Version Information

Update the version in:

1. `Product.wxs` - Update the `Version` attribute
2. `Bundle.wxs` - Update the `Version` attribute

## Silent Installation

For silent installation (unattended):

```
FastSearchMCP-Setup.exe /quiet /norestart
```

## Troubleshooting

- If you get WiX errors, ensure the WiX Toolset is properly installed and in your PATH
- Check the build logs in the `installer` directory for detailed error information
- Ensure you have administrator privileges when running the installer

## License

See the main project README for license information.

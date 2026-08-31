# FastSearch MCP Packaging

This document explains how to package and distribute the FastSearch MCP.

## Prerequisites

- Windows 10/11
- Visual Studio 2022 Build Tools (for C++ service)
- `dxt` CLI tool installed
- PowerShell 5.1 or later

## Package Contents

The DXT package will include:

- `fastsearch-mcp-bridge.exe` - The main MCP bridge executable
- `dxt_manifest.json` - Package metadata and prompt templates
- `README.md` - Basic documentation
- `LICENSE` - MIT license
- `icons/` - Application icons (if available)

## Building the Package

1. Ensure the C++ service is built:

   ```powershell
   cd service
   cmake -S . -B build -G "Visual Studio 17 2022" -A x64
   cmake --build build --config Release
   cd ..
   ```

2. Run the packaging script:

   ```powershell
   .\package.ps1
   ```

3. The script will create two files in the `dist` directory:
   - `fastsearch-mcp-<version>.mcpb` - The DXT package
   - `fastsearch-mcp-<version>.zip` - A zip archive of the package

## Installing the Package

To install the package locally:

```powershell
npx @anthropic-ai/mcpb pack .\dist\fastsearch-mcp-<version>.mcpb
```

## Verifying the Installation

After installation, you can verify the package is available:

```powershell
dxt list | findstr fastsearch-mcp
```

## Distribution

To distribute the package:

1. Share the `.mcpb` file with users
2. They can install it using the `npx @anthropic-ai/mcpb pack` command
3. Or use the zip archive for manual installation

## Versioning

Update the version in:

1. `dxt_manifest.json`
2. `service/CMakeLists.txt`
3. `package.ps1`

## Troubleshooting

- If the build fails, ensure all dependencies are installed
- Check that the `dxt` CLI is in your PATH
- Verify the output directory is writable

## License

MIT - See [LICENSE](LICENSE) for more information.


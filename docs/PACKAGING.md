# FastSearch MCP Packaging

This document explains how to package and distribute the FastSearch MCP.

## Prerequisites

- Windows 10/11
- Rust toolchain (latest stable)
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

1. Ensure all dependencies are installed:
   ```powershell
   cargo build --release
   ```

2. Run the packaging script:
   ```powershell
   .\package.ps1
   ```

3. The script will create two files in the `dist` directory:
   - `fastsearch-mcp-<version>.dxt` - The DXT package
   - `fastsearch-mcp-<version>.zip` - A zip archive of the package

## Installing the Package

To install the package locally:

```powershell
dxt install .\dist\fastsearch-mcp-<version>.dxt
```

## Verifying the Installation

After installation, you can verify the package is available:

```powershell
dxt list | findstr fastsearch-mcp
```

## Distribution

To distribute the package:

1. Share the `.dxt` file with users
2. They can install it using the `dxt install` command
3. Or use the zip archive for manual installation

## Versioning

Update the version in:

1. `dxt_manifest.json`
2. `Cargo.toml`
3. `package.ps1`

## Troubleshooting

- If the build fails, ensure all dependencies are installed
- Check that the `dxt` CLI is in your PATH
- Verify the output directory is writable

## License

MIT - See [LICENSE](LICENSE) for more information.

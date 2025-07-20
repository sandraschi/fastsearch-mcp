# FastSearch MCP Release Process

This document outlines the process for creating new releases of FastSearch MCP.

## Prerequisites

- Git
- Rust toolchain (stable)
- WiX Toolset v3.11+ (Windows)
- GitHub CLI (`gh`) - Recommended for managing releases

## Release Checklist

### Before Creating a Release

1. **Update Version**
   - Update version in `Cargo.toml`
   - Update version in `wix/Product.wxs` and `wix/Bundle.wxs`
   - Update `CHANGELOG.md` with release notes

2. **Test Locally**
   ```powershell
   # Run the test script
   .\test-release.ps1
   ```

   This will:
   - Clean previous builds
   - Build all release targets
   - Create the Windows installer
   - Verify all artifacts are present

### Creating a Release

1. **Commit Changes**
   ```bash
   git add .
   git commit -m "Prepare release vX.Y.Z"
   git push
   ```

2. **Create and Push Tag**
   ```bash
   # Create an annotated tag
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   
   # Push the tag to trigger the GitHub Actions workflow
   git push origin vX.Y.Z
   ```

3. **Monitor GitHub Actions**
   - Go to the "Actions" tab in GitHub
   - Monitor the build and release workflow
   - Verify all platforms build successfully

4. **Verify Release**
   - Go to "Releases" in GitHub
   - Verify all artifacts are attached
   - Review the automatically generated release notes
   - Add any additional information if needed

## Post-Release Tasks

1. **Update Version for Development**
   - Update version in `Cargo.toml` to the next development version (e.g., `0.2.0-dev`)
   - Commit and push the change

## Troubleshooting

### Build Failures
- Check the GitHub Actions logs for specific errors
- Common issues:
  - Missing dependencies
  - Version conflicts
  - Path issues in build scripts

### Missing Artifacts
- Verify the workflow completed successfully
- Check the "Upload artifacts" step in the workflow
- Ensure no files were excluded by `.gitignore`

## Manual Release Process (Fallback)

If the automated process fails, you can create a release manually:

1. Build the project locally:
   ```powershell
   cargo build --release --all-targets
   .\build-installer.ps1
   ```

2. Create a new release in GitHub
3. Upload the following artifacts:
   - `installer/FastSearchMCP-Setup.exe`
   - `target/release/fastsearch-mcp-bridge` (and `.exe` on Windows)
   - `target/release/fastsearch` (and `.exe` on Windows)

## Versioning

FastSearch MCP follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for added functionality in a backward-compatible manner
- **PATCH** version for backward-compatible bug fixes

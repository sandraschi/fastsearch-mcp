# FastSearch MCP Release Process

This document outlines the process for creating new releases of FastSearch MCP.

## Prerequisites

- Git
- Python 3.8+
- Rust toolchain (stable, for service compilation)
- WiX Toolset v3.11+ (Windows, for installer)
- GitHub CLI (`gh`) - Recommended for managing releases
- DXT CLI (`dxt`) - For DXT package creation

## Release Checklist

### Before Creating a Release

1. **Update Version**
   - Update version in `fastsearch_mcp/__init__.py`
   - Update version in `pyproject.toml`
   - Update version in `wix/Product.wxs` and `wix/Bundle.wxs` (Windows)
   - Update `CHANGELOG.md` with release notes
   - Update any version references in documentation

2. **Test Locally**

   ```powershell
   # Run the test script
   .\test-release.ps1
   ```

   This will:
   - Clean previous builds
   - Run all tests (Python and Rust)
   - Build the Python package
   - Build the Rust service
   - Create the Windows installer
   - Generate DXT package
   - Verify all artifacts are present

### Creating a Release

1. **Verify Dependencies**
   ```bash
   # Install/update build dependencies
   pip install --upgrade pip setuptools wheel twine
   pip install -e .[dev]
   ```

2. **Run Pre-release Checks**
   ```bash
   # Run linters and type checking
   pre-commit run --all-files
   
   # Run tests
   pytest --cov=fastsearch_mcp tests/
   ```

3. **Build Python Package**
   ```bash
   # Build source distribution and wheel
   python -m build
   
   # Verify package can be installed
   pip install --force-reinstall dist/*.whl
   ```

4. **Build Rust Service (Windows)**
   ```bash
   cd service
   cargo build --release
   ```

5. **Generate DXT Package**
   ```bash
   # Ensure DXT manifest is valid
   dxt validate
   
   # Create DXT package
   dxt pack
   ```

6. **Commit Changes**
   ```bash
   git add .
   git commit -m "Prepare release vX.Y.Z"
   git push
   ```

7. **Create and Push Tag**
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

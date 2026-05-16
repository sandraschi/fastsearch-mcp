# First Release Guide - FastSearch MCP

This guide explains how to create the first release, which requires building both the C++ Windows Service (MSI) and the MCPB package.

## Overview

FastSearch MCP requires **two separate packages** for a complete release:

1. **MSI Installer** (`fastsearch-mcp-setup.msi`) - Windows Service (C++ CMake build)
2. **MCPB Package** (`fastsearch-mcp.mcpb`) - Claude Desktop Extension (Python)

## Current CI/CD Status

### ✅ What Works

- **CI Workflow** (`.github/workflows/ci.yml`):
  - Python tests and linting
  - MCPB manifest validation
  - Runs on every push/PR

### ❌ What Needs Fixing

- **Release Workflow** (`.github/workflows/build-release.yml`):
  - Currently configured for **Rust/Cargo** (wrong!)
  - Service is actually **C++ with CMake**
  - Missing CMake build steps
  - Missing MSI creation script integration
  - Missing MCPB bash script (workflow references non-existent `create_mcpb_package.sh`)

- **Release Workflow** (`.github/workflows/release.yml`):
  - Outdated, still references DXT
  - Should be removed or updated

## Release Process (Manual - First Release)

Since CI/CD needs fixes, here's how to create the first release manually:

### Prerequisites

1. **Windows 10/11** (required for MSI build)
2. **Visual Studio 2022** (or Build Tools) with C++ workload
3. **CMake 3.20+**
4. **WiX Toolset v3.11+** (for MSI creation)
5. **Node.js 16+** (for MCPB CLI)
6. **Python 3.8+** with pip
7. **Git** with repository access

### Step 1: Build C++ Service (MSI)

```powershell
# 1. Build the service
cd service
cmake -S . -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release

# 2. Verify binary exists
Test-Path "build\bin\Release\FastSearchServiceNew.exe"

# 3. Create MSI installer
cd ..
.\scripts\create_msi_package.ps1 `
    -Version "0.5.0" `
    -Platform "windows-x64" `
    -OutputDir "dist" `
    -ProjectDir "." `
    -WixBinDir "C:\Program Files (x86)\WiX Toolset v3.11\bin"

# 4. Verify MSI
Test-Path "dist\fastsearch-mcp-setup-0.5.0.msi"
```

### Step 2: Build MCPB Package

```powershell
# 1. Install MCPB CLI (if not already installed)
npm install -g @anthropic-ai/mcpb

# 2. Build MCPB package
.\mcpb\scripts\build-mcpb-package.ps1

# 3. Verify MCPB
Test-Path "dist\fastsearch-mcp-0.5.0.mcpb"
```

### Step 3: Create GitHub Release

```powershell
# 1. Tag the release
git tag -a v0.5.0 -m "Release v0.5.0: First release with MCPB packaging"
git push origin v0.5.0

# 2. Create release on GitHub (manual via web UI or CLI)
# Upload both files:
#   - dist\fastsearch-mcp-setup-0.5.0.msi
#   - dist\fastsearch-mcp-0.5.0.mcpb
```

## Fixing CI/CD for Future Releases

### Required Changes to `.github/workflows/build-release.yml`

1. **Replace Rust setup with CMake**:
   ```yaml
   - name: Setup CMake
     uses: microsoft/setup-msbuild@v1
   
   - name: Setup Visual Studio
     uses: microsoft/setup-msbuild@v1
   ```

2. **Build C++ service with CMake**:
   ```yaml
   - name: Build C++ Service
     shell: pwsh
     run: |
       cd service
       cmake -S . -B build -G "Visual Studio 17 2022" -A x64
       cmake --build build --config Release
   ```

3. **Fix MCPB package creation**:
   - Either create `scripts/create_mcpb_package.sh` (bash)
   - Or change workflow to use PowerShell: `mcpb/scripts/build-mcpb-package.ps1`

4. **Fix MSI creation**:
   - Ensure `scripts/create_msi_package.ps1` works in CI
   - Install WiX Toolset in CI (already done, but verify)

### Required Changes to `.github/workflows/release.yml`

- **Delete or completely rewrite** - it's outdated and references DXT

## Release Checklist

Before creating the first release:

- [ ] All tests pass (`pytest tests/`)
- [ ] Ruff linting passes (`ruff check src/ tests/`)
- [ ] Ruff formatting passes (`ruff format --check src/ tests/`)
- [ ] MCPB manifest validates (`mcpb validate`)
- [ ] Service builds successfully (CMake)
- [ ] MSI installer creates successfully
- [ ] MCPB package creates successfully
- [ ] Both packages tested locally
- [ ] Version numbers updated in:
  - [ ] `pyproject.toml`
  - [ ] `mcpb/mcpb.json`
  - [ ] `manifest.json`
  - [ ] `package.json`
  - [ ] `service/CMakeLists.txt`
- [ ] CHANGELOG.md updated
- [ ] Release notes prepared

## Version Numbering

Use [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., `0.5.0`)
- First release: `0.5.0` (or `1.0.0` if you consider it stable)

## Next Steps After First Release

1. Fix CI/CD workflows (see above)
2. Test automated release process
3. Document release process in `docs/RELEASING.md`
4. Set up automated version bumping
5. Consider PyPI publishing (optional, for `pip install fastsearch-mcp`)

## Troubleshooting

### MSI Build Fails

- **WiX not found**: Install WiX Toolset v3.11+
- **Service binary missing**: Verify CMake build succeeded
- **Permissions**: Run PowerShell as Administrator

### MCPB Build Fails

- **MCPB CLI not found**: `npm install -g @anthropic-ai/mcpb`
- **Manifest validation fails**: Check `manifest.json` format
- **Missing prompts**: Ensure `prompts/` directory exists

### CI/CD Issues

- **CMake not found**: Add CMake setup step
- **Visual Studio not found**: Use `microsoft/setup-msbuild@v1`
- **WiX not found**: Install WiX in CI (already done, verify path)

## Related Documentation

- [Release Packaging](RELEASE_PACKAGING.md)
- [Installation Methods](INSTALLATION_METHODS.md)
- [MCPB Building Guide](mcpb-packaging/MCPB_BUILDING_GUIDE.md)
- [Service Development](SERVICE_DEVELOPMENT_STATUS.md)


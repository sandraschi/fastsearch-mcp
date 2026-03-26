# Development Guide

This guide describes how to set up a development environment and contribute to FastSearch MCP.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Workflow](#workflow)
- [Testing](#testing)
- [Debugging](#debugging)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Releasing](#releasing)

## Prerequisites

- Python 3.10+
- Visual Studio 2022 Build Tools (Desktop development with C++)
- CMake 3.20+
- Git
- [pre-commit](https://pre-commit.com/)

## Environment Setup

1. **Clone the repository**

   ```powershell
   git clone https://github.com/yourusername/fastsearch-mcp.git
   cd fastsearch-mcp
   ```

2. **Create a virtual environment**

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   pip install -e .
   ```

3. **Install pre-commit hooks**

   ```powershell
   pre-commit install
   ```

4. **Build the C++ service (Debug configuration recommended during development)**

   ```powershell
   cd service
   cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Debug
   cmake --build build --config Debug
   cd ..
   ```

## Project Structure

```
fastsearch-mcp/
├── docs/                      # Documentation
├── scripts/                   # Helper scripts (PowerShell + bash)
├── service/                   # C++ Windows service
│   ├── src/                   # Service sources
│   └── build/                 # CMake build output
├── src/fastsearch_mcp/        # Python MCP bridge package
│   ├── tools/                 # FastMCP tool implementations
│   └── utils/                 # Shared helpers
├── tests/                     # Python test suite
├── install-service.ps1        # Service management script
├── package.ps1                # DXT packaging helper
├── pyproject.toml             # Python project configuration
└── README.md
```

## Workflow

1. **Create a feature branch**
   ```powershell
   git checkout -b feature/your-feature
   ```

2. **Make changes**
   - Update Python code under `src/fastsearch_mcp`
   - Modify the C++ service under `service/src`
   - Keep documentation consistent with architectural constraints

3. **Run checks**
   ```powershell
   pre-commit run --all-files
   pytest
   cmake --build service/build --config Debug
   ```

4. **Commit and push**
   ```powershell
   git add .
   git commit -m "feat: describe your change"
   git push -u origin feature/your-feature
   ```

5. **Open a pull request**
   - Provide context and testing notes
   - Highlight any changes that affect service installation or architecture rules

## Testing

Run the Python test suite from the repository root:

```powershell
pytest
pytest --cov=fastsearch_mcp --cov-report=term-missing
```

Service-specific smoke tests can be run using the helper scripts:

```powershell
.\test-service-comprehensive.ps1 all
.\debug-service-startup.ps1
```

## MCP Client Development Tips

### Cursor IDE vs Claude Desktop

**Cursor IDE** provides better MCP server lifecycle management:
- ✅ **Hot reload**: Disable/enable MCP server to see tool changes immediately
- ✅ **No restart required**: Faster iteration during development
- ✅ **Hover tooltips**: Hovering over tool names shows docstrings (great for quick reference!)
- ✅ **Better DX**: Use Cursor IDE for tool development

**Claude Desktop** requires full restart:
- ❌ **Full restart needed**: Must restart Claude Desktop to see tool changes
- ❌ **Slower iteration**: Restart takes time, interrupts workflow
- ⚠️ **Use for final testing**: Use Claude Desktop for production testing

**Recommendation**: Develop and test tool changes in Cursor IDE, then verify in Claude Desktop before release.

## Debugging

### Python bridge
- Use `pdb` or VS Code's debugger (`scripts/start_server.py` is the usual entry point).
- Enable verbose logging via `FASTSEARCH_LOG_LEVEL=debug`.

### C++ service
- Use `.\scripts\install-visualstudio-community.ps1` (elevated) to install Visual Studio Community with the required workload, then follow `docs/Visual_Studio_Debugger_Setup.md` for attach instructions.
- Alternatively, load the workspace in Cursor/VS Code and pick the `Attach to FastSearch Service` configuration from `.vscode\launch.json` (requires the Microsoft `C/C++` extension and an elevated session).
- Build the service in `Debug` configuration and launch it under the Visual Studio debugger.
- Alternatively, run the binary from an elevated console with `--install`, `--start`, etc., or attach to the Windows service after launch.
- Review Event Viewer entries under `Applications and Services Logs → FastSearchMCP` for startup failures.

## Code Style

### Python
- Follow PEP 8.
- Use type hints and descriptive docstrings.
- Prefer `anyio`/`asyncio`-friendly patterns when integrating with FastMCP.

### C++
- Design for determinism and minimal allocations.
- Use RAII for HANDLE/RESOURCE management.
- Keep logging concise and actionable (all critical paths should log to the Windows Event Log).
- Never introduce caches or background indexing in the service.

## Documentation

Keep the documentation aligned with the architecture guardrails. When behaviour changes:
- Update `README.md`, `docs/TECHNICAL_ARCHITECTURE.md`, and any relevant troubleshooting guides.
- Ensure warnings about forbidden patterns (indexing, caching, background scans) remain prominent.

## Releasing

Follow `docs/RELEASING.md` for the full release checklist. At a minimum:
- Run the automated test suite and service diagnostics.
- Build the C++ service in `Release` mode.
- Regenerate any packages (PyPI wheel, DXT, MSI if applicable).
- Tag the release following semantic versioning.

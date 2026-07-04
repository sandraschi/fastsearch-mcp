set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
import 'scripts/just/fleet.just'

# ---- Dashboard -----------------------------------------------------------

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ---- Quality -------------------------------------------------------------

# Execute Ruff SOTA linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check src/ tests/
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome ci .

# Execute Ruff fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome check --write .

# ----------------------------------------

# Build the C++ Windows service
build-service:
    Set-Location '{{justfile_directory()}}\service\build'
    cmake --build . --config Release

# Install/start the C++ service (requires admin)
install-service:
    sc start FastSearchMCP 2>$null; if ($LASTEXITCODE -ne 0) { & '{{justfile_directory()}}\service\build\bin\Release\FastSearchServiceNew.exe' install; Start-Service FastSearchMCP }

# Stop the C++ service (requires admin)
stop-service:
    Stop-Service FastSearchMCP -Force

# ----------------------------------------

# Run MCP server in STDIO mode (default)
run:
    Set-Location '{{justfile_directory()}}'
    uv run python -m fastsearch_mcp

# Run MCP server with CodeMode agentic discovery
run-agentic:
    Set-Location '{{justfile_directory()}}'
    uv run python -m fastsearch_mcp --agentic

# Run MCP server in HTTP mode (port 10845)
run-http:
    Set-Location '{{justfile_directory()}}'
    uv run python -m fastsearch_mcp --http --port 10845

# Run web dashboard (port 10844)
run-web:
    Set-Location '{{justfile_directory()}}\web_sota'
    npm start

# Run API server only (FastAPI + MCP HTTP, port 10845)
run-api:
    Set-Location '{{justfile_directory()}}'
    uv run uvicorn fastsearch_mcp.server:app --host 127.0.0.1 --port 10845

# ----------------------------------------

# Run Python test suite
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -v

# Run live integration tests (requires service)
test-live:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/test_live_pipe.py -v

# ----------------------------------------

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety scan

# ----------------------------------------

# Tag and push a new release
release VERSION:
    Set-Location '{{justfile_directory()}}'
    git tag v{{VERSION}}
    git push origin v{{VERSION}}
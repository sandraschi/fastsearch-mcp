set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Display the SOTA Industrial Dashboard
default:
    @$lines = Get-Content '{{justfile()}}'; \
    Write-Host ' [SOTA] FastSearch MCP v0.5.0' -ForegroundColor White -BackgroundColor Cyan; \
    Write-Host '' ; \
    $currentCategory = ''; \
    foreach ($line in $lines) { \
        if ($line -match '^# ── ([^─]+) ─') { \
            $currentCategory = $matches[1].Trim(); \
            Write-Host "`n  $currentCategory" -ForegroundColor Cyan; \
            Write-Host ('  ' + ('─' * 45)) -ForegroundColor Gray; \
        } elseif ($line -match '^# ([^─].+)') { \
            $desc = $matches[1].Trim(); \
            $idx = [array]::IndexOf($lines, $line); \
            if ($idx -lt $lines.Count - 1) { \
                $nextLine = $lines[$idx + 1]; \
                if ($nextLine -match '^([a-z0-9-]+):') { \
                    $recipe = $matches[1]; \
                    $pad = ' ' * [math]::Max(2, (18 - $recipe.Length)); \
                    Write-Host "    $recipe" -ForegroundColor White -NoNewline; \
                    Write-Host "$pad$desc" -ForegroundColor Gray; \
                } \
            } \
        } \
    } \
    Write-Host "`n  [System State: PROD/HARDENED]" -ForegroundColor DarkGray; \
    Write-Host ''

# ── Quality ───────────────────────────────────────────────────────────────────

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

# ── Build ─────────────────────────────────────────────────────────────────────

# Build the C++ Windows service
build-service:
    Set-Location '{{justfile_directory()}}\service\build'
    cmake --build . --config Release

# Install/start the C++ service (requires admin)
install-service:
    sc start FastSearchMCP 2>$null
    if ($LASTEXITCODE -ne 0) {
        & '{{justfile_directory()}}\service\build\bin\Release\FastSearchServiceNew.exe' install
        Start-Service FastSearchMCP
    }

# Stop the C++ service (requires admin)
stop-service:
    Stop-Service FastSearchMCP -Force

# ── Run ───────────────────────────────────────────────────────────────────────

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

# ── Test ──────────────────────────────────────────────────────────────────────

# Run Python test suite
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -v

# Run live integration tests (requires service)
test-live:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/test_live_pipe.py -v

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety scan

# ── Release ───────────────────────────────────────────────────────────────────

# Tag and push a new release
release VERSION:
    Set-Location '{{justfile_directory()}}'
    git tag v{{VERSION}}
    git push origin v{{VERSION}}

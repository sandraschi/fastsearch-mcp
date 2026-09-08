# Per-repo fleet start config for fastsearch-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'fastsearch-mcp'
    BackendPort  = 10845
    FrontendPort = 10844
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\fastsearch-mcp\web_sota'
    # Explicit even though it matches Name -- this repo also has an
    # unrelated native Windows service called 'FastSearchMCP' (the C++
    # NTFS-MFT-access engine, install-service.ps1, its own service).
    # NssmService here is the separate Python REST bridge (this config),
    # installed 2026-09-08. Do not conflate the two.
    NssmService  = 'fastsearch-mcp'
    Backend = @{
        # 'nssm', not 'uvicorn'. Previously this backend was just a bare,
        # unmanaged `uv run uvicorn ...` process someone started by hand --
        # nothing restarted it if it crashed or the machine rebooted, and it
        # wasn't a Windows service at all, so Resolve-FleetPortConflict's
        # generic path treated it as an ordinary port squatter rather than
        # a persistent backend. Wrapped it in its own NSSM service
        # ('fastsearch-mcp', distinct from the native 'FastSearchMCP'
        # NTFS service) so it behaves like the rest of the fleet: survives
        # reboot, auto-restarts, and reuses cleanly via Start-FleetNssmWebapp
        # instead of needing -ReuseIfRunning. See email-mcp/discord-mcp/
        # tvtropes-mcp for the sibling Kind-mismatch fix; this one didn't
        # have a service to mismatch against at all, so the fix was
        # installing one, not just flipping Kind.
        Kind          = 'nssm'
        UvicornTarget = 'fastsearch_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10845' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}

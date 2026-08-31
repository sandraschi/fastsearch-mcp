# Per-repo fleet start config for fastsearch-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'fastsearch-mcp'
    BackendPort  = 10845
    FrontendPort = 10844
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\fastsearch-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
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

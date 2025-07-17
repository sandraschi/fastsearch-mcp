use fastsearch_mcp_bridge::{McpBridge, IpcClient, BridgeError};
use tracing::{info, error};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize logging to stderr (stdout is for MCP communication)
    tracing_subscriber::fmt()
        .with_writer(std::io::stderr)
        .init();
    
    info!("FastSearch MCP Bridge v1.0.0 starting...");
    
    // Try to connect to admin service
    let ipc_client = match IpcClient::new("\\\\.\\pipe\\fastsearch-engine").await {
        Ok(client) => {
            info!("✅ Connected to FastSearch service");
            client
        }
        Err(e) => {
            info!("⚠️ Service not available: {} (will show installation help)", e);
            IpcClient::disconnected()
        }
    };
    
    // Create and run MCP bridge
    let mut bridge = McpBridge::new(ipc_client);
    
    info!("🚀 MCP Bridge ready for requests");
    
    // Run the bridge (blocks until stdin closes)
    if let Err(e) = bridge.run().await {
        error!("❌ Bridge error: {}", e);
        std::process::exit(1);
    }
    
    info!("🔚 MCP Bridge shutting down");
    Ok(())
}

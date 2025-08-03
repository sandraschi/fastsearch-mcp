use std::error::Error;
use std::io::{self, BufRead};
use serde_json::json;
use fastsearch_shared::types::{SearchRequest, SearchResponse};

mod mcp_compat;
use mcp_compat::{McpServer, McpError};

/// Handle search requests from the MCP client
fn handle_search(params: serde_json::Value) -> Result<serde_json::Value, McpError> {
    // Parse the search request
    let request: SearchRequest = serde_json::from_value(params)
        .map_err(|e| McpError::InvalidParams(e.to_string()))?;
    
    // In a real implementation, this would call the actual search logic
    // For now, we'll return a mock response
    let response = SearchResponse {
        results: vec![],
        total_matches: 0,
        search_time_ms: 0,
    };
    
    Ok(serde_json::to_value(response).unwrap())
}

/// Handle service status requests
fn handle_status(_params: serde_json::Value) -> Result<serde_json::Value, McpError> {
    // In a real implementation, this would check the service status
    Ok(json!({
        "status": "running",
        "version": env!("CARGO_PKG_VERSION"),
        "service_available": false
    }))
}

fn main() -> Result<(), Box<dyn Error>> {
    // Initialize logging
    env_logger::init();
    log::info!("🚀 FastSearch MCP Bridge v{} starting...", env!("CARGO_PKG_VERSION"));

    // Create the MCP server
    let server = McpServer::new(
        "fastsearch-mcp",
        env!("CARGO_PKG_VERSION"),
        "FastSearch MCP - Lightning-fast file search using NTFS MFT"
    )
    .add_tool(
        "fast_search",
        "Search for files using the FastSearch engine",
        handle_search
    )
    .add_tool(
        "service_status",
        "Get the status of the FastSearch service",
        handle_status
    );

    log::info!("🔧 MCP Server initialized with FastMCP compatibility layer");
    log::info!("📡 Listening for MCP requests...");

    // Run the server (this blocks until stdin is closed)
    server.run_stdio();
    
    log::info!("🔚 MCP Server shutting down");
    Ok(())
}

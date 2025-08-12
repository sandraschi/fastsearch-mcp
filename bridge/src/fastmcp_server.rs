use log::{debug, error, info};
use mcp_core::{
    ServerBuilder,
    Tool, ToolCall, ToolCallResult, ToolAnnotations,
};
use serde_json::json;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::instrument;

use crate::ipc_client::IpcClient;
use fastsearch_shared::SearchRequest as SharedSearchRequest;
use crate::{
    SearchResponse, SearchStats, SearchResult,
    ServiceStatus,
};

/// Custom error type for the MCP bridge
#[derive(Debug, thiserror::Error)]
pub enum Error {
    /// I/O error
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    
    /// IPC communication error
    #[error("IPC error: {0}")]
    Ipc(#[from] crate::ipc_client::IpcError),
    
    /// Serialization/deserialization error
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    /// Invalid parameters
    #[error("Invalid parameters: {0}")]
    InvalidParams(String),
    
    /// Service error
    #[error("Service error: {0}")]
    Service(String),
}

/// The main MCP bridge server that handles search requests and communicates with the IPC client.
#[derive(Clone)]

/// FastMCP 2.10 server implementation for FastSearch
pub struct McpBridge {
    /// The IPC client for communicating with the FastSearch service
    ipc_client: Arc<Mutex<IpcClient>>,
}

impl McpBridge {
    /// Create a new MCP bridge instance
    pub fn new(ipc_client: IpcClient) -> Self {
        Self {
            ipc_client: Arc::new(Mutex::new(ipc_client)),
        }
    }
    
    /// Get the list of tools provided by this MCP bridge
    pub fn get_tools() -> Vec<Tool> {
        // Create search schema (simplified for now, will need to update with actual schema)
        let search_schema = serde_json::json!({});
        
        // Create tools with explicit field initialization
        vec![
            // Search tool
            Tool {
                name: "search".to_string(),
                description: Some("Search for files matching a query".to_string()),
                input_schema: search_schema,
                annotations: None, // Use None instead of empty HashMap
            },
            // Search stats tool
            Tool {
                name: "search_stats".to_string(),
                description: Some("Get search statistics".to_string()),
                input_schema: serde_json::json!({}),
                annotations: None,
            },
            // Service status tool
            Tool {
                name: "service_status".to_string(),
                description: Some("Get the status of the FastSearch service".to_string()),
                input_schema: serde_json::json!({}),
                annotations: None,
            },
        ]
    }

    /// Create the search tool definition
    fn create_search_tool(&self) -> Tool {
        // Create a simple search tool with basic parameters
        Tool {
            name: "search".to_string(),
            description: "Search for files and directories".to_string(),
            parameters: Some(serde_json::json!({
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (supports glob patterns, regex, or literal text)"
                    },
                    "path": {
                        "type": "string",
                        "description": "Base directory to search in (default: all drives)"
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Whether the search is case-sensitive (default: false)",
                        "default": false
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 100)",
                        "minimum": 1,
                        "maximum": 1000,
                        "default": 100
                    }
                },
                "required": ["query"]
            })),
        }
    }

    /// Create the search stats tool definition
    fn create_search_stats_tool(&self) -> Tool {
        Tool {
            name: "search_stats".to_string(),
            description: "Get statistics about the search index".to_string(),
            parameters: Some(serde_json::json!({})), // No parameters needed for stats
        }
    }

    /// Create the service status tool definition
    fn create_service_status_tool(&self) -> Tool {
        Tool {
            name: "service_status".to_string(),
            description: "Get the status of the FastSearch service".to_string(),
            parameters: Some(serde_json::json!({})), // No parameters needed for status
        }
    }

    /// Handle a search request
    #[instrument(skip(self, call))]
    async fn handle_search(
        &self,
        call: ToolCall,
    ) -> Result<ToolCallResult, Error> {
        use serde_json::Value;

        // Extract search parameters
        let pattern = call
            .parameters
            .as_ref()
            .and_then(|p| p.get("query"))
            .and_then(Value::as_str)
            .ok_or_else(|| Error::InvalidParams("Missing required field: query".to_string()))?
            .to_string();

        let max_results = call
            .parameters
            .as_ref()
            .and_then(|p| p.get("max_results"))
            .and_then(Value::as_u64)
            .unwrap_or(50) as u32;

        let case_sensitive = call
            .parameters
            .as_ref()
            .and_then(|p| p.get("case_sensitive"))
            .and_then(Value::as_bool)
            .unwrap_or(false);

        // Create search request with the correct fields
        let request = fastsearch_shared::SearchRequest {
            pattern,
            search_type: if case_sensitive { "exact" } else { "fuzzy" }.to_string(),
            max_results,
            filters: None, // No filters by default
        };

        // Send request to IPC client
        let response = self.ipc_client.lock().await.send_request(request).await?;

        // Format results into a vector of JSON objects
        let results: Vec<serde_json::Value> = response
            .results
            .into_iter()
            .map(|result| {
                // Create a JSON object with the available fields
                let mut json_result = json!({ 
                    "path": result.path,
                    "name": result.name,
                    "size": result.size,
                    "size_human": result.size_human,
                    "modified": result.modified,
                });

                // Add file extension if available
                if let Some(extension) = std::path::Path::new(&result.name)
                    .extension()
                    .and_then(|ext| ext.to_str()) {
                    json_result["extension"] = json!(extension.to_lowercase());
                }
                
                json_result
            })
            .collect();
        
        // Return the results as a successful tool call result
        Ok(ToolCallResult {
            call_id: call.call_id,
            content: Some(json!({ "results": results })),
            is_error: false,
        })
    }

    /// Handle a search stats request
    #[instrument(skip(self, call))]
    async fn handle_search_stats(
        &self,
        call: ToolCall,
    ) -> Result<ToolCallResult, Error> {
        debug!("Handling search stats request");

        let stats = self.ipc_client.lock().await.get_stats().await?;
        
        // Create a JSON object with all available fields
            "last_updated": stats.last_updated,
            "index_size_mb": stats.index_size_mb,
        });
        
        // Return success with stats
        Ok(ToolCallResult {
            call_id: call.call_id,
            content: Some(stats_value),
            is_error: false,
        })
    }

    /// Handle a service status request
    #[instrument(skip(self, call))]
    async fn handle_service_status(
        &self,
        call: ToolCall,
    ) -> Result<ToolCallResult, Error> {
        // Check if the service is running
        let status = self.ipc_client.lock().await.check_service_status().await;
        
        // Format the status as a JSON object
        let status_value = json!({ 
            "status": if status.is_ok() { "running" } else { "stopped" },
            "version": env!("CARGO_PKG_VERSION"),
        });
        
        // Return success with status
        Ok(ToolCallResult {
            call_id: call.call_id,
            content: Some(status_value),
            is_error: false,
        })
    }

    /// Run the MCP server
    #[instrument(skip(self))]
    pub async fn run(self) -> Result<(), Error> {
        use std::sync::Arc;
        use tokio::sync::Mutex;
        use mcp_core::ServerBuilder;

        // Create a new MCP server builder
        let server_builder = ServerBuilder::new()
            .with_name("fastsearch-mcp")
            .with_version(env!("CARGO_PKG_VERSION").to_string())
            .with_description("FastSearch MCP Server - Lightning-fast file search using NTFS MFT");

        // Get the list of tools
        let tools = self.get_tools();
        
        // Register tool handlers
        let server = server_builder
            .with_tools(tools)
            .with_tool_handler("search", {
                let this = self.clone();
                move |call| {
                    let this = this.clone();
                    async move { this.handle_search(call).await }
                }
            })
            .with_tool_handler("search_stats", {
                let this = self.clone();
                move |call| {
                    let this = this.clone();
                    async move { this.handle_search_stats(call).await }
                }
            })
            .with_tool_handler("service_status", {
                let this = self.clone();
                move |call| {
                    let this = this.clone();
                    async move { this.handle_service_status(call).await }
                }
            });

        // Set up signal handling for graceful shutdown
        let (shutdown_tx, mut shutdown_rx) = tokio::sync::mpsc::channel(1);
        let ctrl_c = tokio::spawn(async move {
            tokio::signal::ctrl_c().await.ok();
            info!("Received Ctrl+C, shutting down...");
            let _ = shutdown_tx.send(()).await;
        });

        // Start the server
        info!("Starting FastSearch MCP server");
        
        // Run the server until shutdown signal is received
        let server_handle = server.start().await?;
        
        // Wait for either server completion or shutdown signal
        tokio::select! {
            result = server_handle => {
                if let Err(e) = result {
                    error!("Server error: {}", e);
                    return Err(Error::Service(format!("Server error: {}", e)));
                }
                info!("Server task completed");
            }
            _ = shutdown_rx.recv() => {
                info!("Shutdown signal received");
            }
        }

        // Clean up
        ctrl_c.abort();
        info!("FastSearch MCP server stopped");
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;
    use tokio::sync::Mutex;

    #[tokio::test]
    async fn test_handle_search() {
        // Test setup would go here
    }

    // More tests would go here
}

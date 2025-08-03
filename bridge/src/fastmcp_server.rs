use log::{debug, error, info};
use mcp_core::{
    server::ServerBuilder,
    types::{
        Tool, ToolCall, ToolCallResult, ToolAnnotations,
    },
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
    fn create_search_tool() -> Tool {
        let mut schema = JsonSchema::new(JsonSchemaType::Object);
        schema.properties.insert(
            "pattern".to_string(),
            JsonSchema::new(JsonSchemaType::String)
                .with_description("The search pattern (supports glob format)")
                .with_required(true),
        );
        schema.properties.insert(
            "search_type".to_string(),
            JsonSchema::new(JsonSchemaType::String)
                .with_enum_values(&["smart", "exact", "glob", "regex", "fuzzy"])
                .with_default(json!("smart"))
                .with_description("The type of search to perform"),
        );
        schema.properties.insert(
            "max_results".to_string(),
            JsonSchema::new(JsonSchemaType::Integer)
                .with_minimum(1)
                .with_default(json!(100))
                .with_description("Maximum number of results to return"),
        );

        Tool {
            name: "search".to_string(),
            description: Some("Search for files matching the given pattern".to_owned()),
            input_schema: schema,
            ..Default::default()
        }
    }

    /// Create the search stats tool definition
    fn create_search_stats_tool() -> Tool {
        Tool {
            name: "search_stats".to_string(),
            description: Some("Get search statistics".to_owned()),
            input_schema: JsonSchema::new(JsonSchemaType::Object),
            ..Default::default()
        }
    }

    /// Create the service status tool definition
    fn create_service_status_tool() -> Tool {
        Tool {
            name: "service_status".to_string(),
            description: Some("Get the status of the FastSearch service".to_owned()),
            input_schema: JsonSchema::new(JsonSchemaType::Object),
            ..Default::default()
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
            .params
            .get("query")
            .and_then(Value::as_str)
            .ok_or_else(|| Error::InvalidParams("Missing required field: query".to_string()))?
            .to_string();

        let limit = call
            .params
            .get("limit")
            .and_then(Value::as_u64)
            .unwrap_or(50) as u32;

        // Create search request with correct fields
        let request = fastsearch_shared::SearchRequest {
            pattern,
            search_type: "fuzzy".to_string(), // Default to fuzzy search
            max_results: limit,
            filters: None, // No filters by default
        };

        // Send request to IPC client
        let response = self.ipc_client.lock().await.send_request(request).await?;

        // Format results
        let results = response
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
            .collect::<Vec<_>>();
        
        // Return success with results
        Ok(ToolCallResult::Success {
            content: serde_json::to_value(json!({ "results": results }))?,
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
        let result = json!({ 
            "files_indexed": stats.files_indexed,
            "total_size": stats.total_size,
            "last_updated": stats.last_updated,
            "directories_indexed": stats.directories_indexed,
            "avg_search_time_ms": stats.avg_search_time_ms,
            "total_searches": stats.total_searches,
            "cache_hit_rate": stats.cache_hit_rate,
            "memory_usage_mb": stats.memory_usage_mb,
            "uptime_seconds": stats.uptime_seconds,
            "service_running": stats.service_running,
            "ntfs_mode": stats.ntfs_mode,
        });
        
        // Return success with stats
        Ok(ToolCallResult::Success {
            content: serde_json::to_value(result)?,
            is_error: false,
        })
    }

    /// Handle a service status request
    #[instrument(skip(self, call))]
    async fn handle_service_status(
        &self,
        call: ToolCall,
    ) -> Result<ToolCallResult, Error> {
        debug!("Handling service status request");

        let is_running = self.ipc_client.lock().await.check_service_status().await?;
        
        // Create response
        let result = json!({
            "status": if is_running { "running" } else { "stopped" },
            "timestamp": chrono::Utc::now().to_rfc3339(),
        });
        
        // Return success with status
        Ok(ToolCallResult::Success {
            content: serde_json::to_value(result)?,
            is_error: false,
        })
    }

    /// Run the MCP server
    #[instrument(skip(self))]
    pub async fn run(self) -> Result<(), Error> {
        use mcp_core::server::ServerBuilder;
        use std::sync::Arc;

        // Create a new MCP server builder
        let server_builder = ServerBuilder::new()
            .with_name("fastsearch-mcp")
            .with_version(env!("CARGO_PKG_VERSION").to_string())
            .with_description(Some("FastSearch MCP Server - Lightning-fast file search using NTFS MFT".to_string()));

        // Register tools
        let server = server_builder.with_tools(Self::get_tools());

        // Set up signal handling for graceful shutdown
        let (shutdown_tx, shutdown_rx) = tokio::sync::oneshot::channel();
        let ctrl_c = tokio::spawn(async move {
            tokio::signal::ctrl_c().await.ok();
            info!("Received Ctrl+C, shutting down...");
            let _ = shutdown_tx.send(());
        });

        // Start the server
        info!("Starting FastSearch MCP server");
        
        // Run the server until shutdown signal is received
        let server_handle = server.start().await?;
        
        tokio::select! {
            result = server_handle => {
                if let Err(e) = result {
                    error!("Server error: {}", e);
                    return Err(Error::Service(format!("Server error: {}", e)));
                }
                info!("Server task completed");
            }
            _ = shutdown_rx => {
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

pub mod mcp_bridge;
pub mod ipc_client;
pub mod validation;

// Re-export shared types
pub use fastsearch_shared::*;
pub use mcp_bridge::McpBridge;
pub use ipc_client::{IpcClient, IpcError};

#[derive(thiserror::Error, Debug)]
pub enum BridgeError {
    #[error("IPC communication failed: {0}")]
    Ipc(#[from] IpcError),
    
    #[error("JSON parsing failed: {0}")]
    Json(#[from] serde_json::Error),
    
    #[error("IO operation failed: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Request validation failed: {0}")]
    Validation(String),
    
    #[error("Service unavailable: {0}")]
    ServiceUnavailable(String),
}

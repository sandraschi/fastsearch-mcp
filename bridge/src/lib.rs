//! FastSearch MCP Bridge
//! 
//! This crate provides a FastMCP 2.10 compliant bridge for the FastSearch service,
//! enabling fast file search capabilities through the Model Context Protocol.

#![warn(missing_docs)]
#![warn(rustdoc::missing_crate_level_docs)]

pub mod mcp_bridge;

pub mod fastmcp_server;
pub mod ipc_client;
pub mod types;
pub mod validation;

// Re-export commonly used types
pub use fastmcp_server::McpBridge;
pub use ipc_client::IpcClient;
pub use types::*;
pub use validation::validate_search_args;

/// Custom result type for the FastSearch MCP bridge
pub type Result<T> = std::result::Result<T, BridgeError>;

/// Error type for the FastSearch MCP bridge
#[derive(thiserror::Error, Debug)]
pub enum BridgeError {
    /// I/O operation failed
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    
    /// IPC communication error
    #[error("IPC error: {0}")]
    Ipc(#[from] ipc_client::IpcError),
    
    /// Serialization/deserialization error
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    /// Input validation error
    #[error("Validation error: {0}")]
    Validation(String),
    
    /// Invalid arguments provided
    #[error("Invalid arguments: {0}")]
    InvalidArgs(String),
    
    /// Service-related error
    #[error("Service error: {0}")]
    Service(String),
    
    /// FastMCP protocol error
    #[error("MCP error: {0}")]
    Mcp(#[from] fastmcp::McpError),
}

impl From<BridgeError> for std::io::Error {
    fn from(err: BridgeError) -> Self {
        match err {
            BridgeError::Io(e) => e,
            _ => std::io::Error::new(std::io::ErrorKind::Other, err.to_string()),
        }
    }
}

//! FastSearch MCP Service - Core functionality

pub mod file_types;
pub mod mcp_server;
pub mod ntfs_reader;
pub mod search_engine;
pub mod web_api;

// Re-export shared types (be specific to avoid conflicts)
pub use fastsearch_shared::{
    SearchFilters, SearchRequest, SearchResponse, SearchStats, SearchInfo, FileInfo
};

// Re-export main modules
pub use mcp_server::McpServer;
pub use ntfs_reader::*;
pub use search_engine::*;
pub use web_api::{
    WebApiServer, SearchRequest as WebSearchRequest, SearchResponse as WebSearchResponse
};

// Re-export commonly used types
pub use anyhow::{Result, Context};
pub use log::{info, debug, error};

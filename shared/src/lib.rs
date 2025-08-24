// FastSearch Shared Types
// Used by both the bridge (user-mode MCP server) and service (elevated NTFS engine)

//! Shared types and utilities for the FastSearch MCP bridge and service

#![warn(missing_docs)]

pub mod types;

// Re-export all types for easier importing
pub use types::{
    SearchRequest, SearchResult, SearchResponse, SearchMetadata, IndexStats,
    TextHighlight, ServiceStatus, ServiceHealth
};

pub use types::*;

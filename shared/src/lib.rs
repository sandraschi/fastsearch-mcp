//! # FastSearch Shared Types
//!
//! This module contains types and utilities shared between the bridge (user-mode MCP server)
//! and service (elevated NTFS engine) components of FastSearch.

#![warn(missing_docs)]

pub mod types;

// Re-export all types for easier importing
pub use types::{
    SearchRequest, SearchResult, SearchResponse, SearchMetadata, IndexStats,
    TextHighlight, ServiceStatus, ServiceHealth
};

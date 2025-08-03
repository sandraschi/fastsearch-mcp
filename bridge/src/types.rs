//! Type definitions for the FastSearch MCP bridge

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Search request parameters
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchRequest {
    /// The search query string
    pub query: String,
    
    /// The base path to search within
    pub path: Option<PathBuf>,
    
    /// Maximum number of results to return
    #[serde(default = "default_max_results")]
    pub max_results: usize,
    
    /// Whether the search is case-sensitive
    #[serde(default)]
    pub case_sensitive: bool,
    
    /// File extensions to include (empty for all)
    #[serde(default)]
    pub extensions: Vec<String>,
}

fn default_max_results() -> usize {
    50
}

impl SearchRequest {
    /// Create a new search request from a JSON value
    pub fn from_json(value: &serde_json::Value) -> Result<Self, String> {
        serde_json::from_value(value.clone()).map_err(|e| e.to_string())
    }
    
    /// Convert to JSON value
    pub fn to_json(&self) -> serde_json::Value {
        serde_json::to_value(self).unwrap_or_default()
    }
}

/// Search result entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    /// Full path to the file
    pub path: PathBuf,
    
    /// File name
    pub name: String,
    
    /// File size in bytes
    pub size: u64,
    
    /// Last modification time as Unix timestamp
    pub modified: i64,
    
    /// File attributes
    pub attributes: u32,
}

/// Search statistics
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SearchStats {
    /// Number of files indexed
    pub files_indexed: u64,
    
    /// Total size of indexed files in bytes
    pub total_size: u64,
    
    /// Last index update timestamp
    pub last_updated: i64,
    
    /// Number of directories indexed
    pub directories_indexed: u64,
}

/// Service status information
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ServiceStatus {
    /// Service is running normally
    Running,
    
    /// Service is not running
    Stopped,
    
    /// Service is running but not responding
    Unresponsive,
    
    /// Service is in an error state
    Error(String),
}

impl Default for ServiceStatus {
    fn default() -> Self {
        Self::Stopped
    }
}

/// Search response containing results and metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResponse {
    /// The search results
    pub results: Vec<SearchResult>,
    
    /// Total number of results available
    pub total_results: usize,
    
    /// Time taken for the search in milliseconds
    pub search_time_ms: u64,
    
    /// Any warnings generated during the search
    #[serde(default)]
    pub warnings: Vec<String>,
}

impl Default for SearchResponse {
    fn default() -> Self {
        Self {
            results: Vec::new(),
            total_results: 0,
            search_time_ms: 0,
            warnings: Vec::new(),
        }
    }
}

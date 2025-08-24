use serde::{Serialize, Deserialize};
use std::time::{SystemTime, UNIX_EPOCH};
use chrono::{DateTime, Utc};

/// Search request following FastMCP 2.11.3 standards
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct SearchRequest {
    /// The search query string
    pub query: String,
    
    /// Maximum number of results to return (1-1000)
    #[serde(default = "default_max_results")]
    pub max_results: usize,
    
    /// Whether the search should be case sensitive
    #[serde(default)]
    pub case_sensitive: bool,
    
    /// Optional path to limit the search scope
    pub path: Option<String>,
    
    /// Optional file type filters (extensions without leading .)
    pub file_types: Option<Vec<String>>,
    
    /// Minimum file size in bytes
    pub min_size: Option<u64>,
    
    /// Maximum file size in bytes
    pub max_size: Option<u64>,
    
    /// Only include files modified after this timestamp (UNIX epoch seconds)
    pub modified_after: Option<i64>,
    
    /// Whether to include hidden files and directories
    #[serde(default)]
    pub include_hidden: bool,
    
    /// Whether to only return directories
    #[serde(default)]
    pub directories_only: bool,
}

/// Default maximum number of results
fn default_max_results() -> usize { 50 }

/// Search result item with file/directory information
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct SearchResult {
    /// Full path to the file/directory
    pub path: String,
    
    /// File/directory name
    pub name: String,
    
    /// Size in bytes
    pub size: u64,
    
    /// Last modification time (UNIX timestamp)
    pub modified: i64,
    
    /// Whether this is a directory
    pub is_dir: bool,
    
    /// Whether this is a hidden file/directory
    pub is_hidden: bool,
    
    /// File extension (without leading .), if any
    pub extension: Option<String>,
    
    /// Relevance score (0.0 to 1.0)
    pub score: f64,
    
    /// Text highlights showing where the query matched
    pub highlights: Option<Vec<TextHighlight>>,
    
    /// Additional metadata
    #[serde(flatten)]
    pub metadata: serde_json::Value,
}

/// Text highlight information for search results
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextHighlight {
    /// Start position of the highlight
    pub start: usize,
    
    /// End position of the highlight
    pub end: usize,
    
    /// Snippet of text around the highlight
    pub snippet: String,
}

/// Search response following FastMCP 2.11.3 standards
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct SearchResponse {
    /// Search results
    pub results: Vec<SearchResult>,
    
    /// Search metadata
    pub metadata: SearchMetadata,
}

/// Metadata about the search operation
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct SearchMetadata {
    /// The original search query
    pub query: String,
    
    /// Number of results returned
    pub result_count: usize,
    
    /// Total number of matches (may be larger than result_count if results are limited)
    pub total_matches: usize,
    
    /// Time taken to perform the search in milliseconds
    pub search_time_ms: u64,
    
    /// Server version
    pub server_version: String,
    
    /// Protocol version
    pub protocol_version: String,
    
    /// Index statistics (if available)
    pub index_stats: Option<IndexStats>,
}

/// Index statistics
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct IndexStats {
    /// Total number of files indexed
    pub file_count: u64,
    
    /// Total size of indexed files in bytes
    pub total_size: u64,
    
    /// When the index was last updated (UNIX timestamp)
    pub last_updated: i64,
    
    /// Whether the index is currently being updated
    pub is_indexing: bool,
}

/// Service status information
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct ServiceStatus {
    /// Service status (running, starting, stopping, etc.)
    pub status: String,
    
    /// Service version
    pub version: String,
    
    /// Uptime in seconds
    pub uptime_seconds: u64,
    
    /// Service capabilities
    pub capabilities: Vec<String>,
    
    /// Service health information
    pub health: ServiceHealth,
}

/// Service health information
#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub struct ServiceHealth {
    /// Whether the service is healthy
    pub is_healthy: bool,
    
    /// Optional health check message
    pub message: Option<String>,
    
    /// Timestamp of the last health check
    pub last_checked: i64,
    
    /// Additional health metrics
    pub metrics: serde_json::Value,
}
    #[serde(skip_serializing_if = "Option::is_none")]
    pub avg_search_time_ms: Option<u32>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub total_searches: Option<u64>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cache_hit_rate: Option<f32>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub memory_usage_mb: Option<u32>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub uptime_seconds: Option<u64>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub service_running: Option<bool>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ntfs_mode: Option<bool>,
}

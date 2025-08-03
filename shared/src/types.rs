use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct SearchRequest {
    pub pattern: String,
    pub search_type: String,
    pub max_results: u32,
    pub filters: Option<SearchFilters>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SearchFilters {
    pub min_size: Option<String>,
    pub max_size: Option<String>,
    pub file_types: Option<Vec<String>>,
    pub modified_after: Option<String>,
    pub include_hidden: Option<bool>,
    pub directories_only: Option<bool>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SearchResponse {
    pub results: Vec<FileInfo>,
    pub search_info: SearchInfo,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct FileInfo {
    pub path: String,
    pub name: String,
    pub size: u64,
    pub size_human: String,
    pub modified: String,
    pub created: String,
    pub extension: String,
    pub is_directory: bool,
    pub is_hidden: bool,
    pub match_score: f32,
    pub match_type: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SearchInfo {
    pub pattern: String,
    pub search_type: String,
    pub search_time_ms: u32,
    pub match_type: String,
    pub index_size: u64,
    pub ntfs_mode: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SearchStats {
    pub files_indexed: u64,
    pub total_size: u64,
    pub last_updated: i64,  // Unix timestamp in seconds
    pub directories_indexed: u64,
    
    // Additional fields that might be used elsewhere
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

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
    pub avg_search_time_ms: u32,
    pub total_searches: u64,
    pub cache_hit_rate: f32,
    pub index_size: u64,
    pub memory_usage_mb: u32,
    pub uptime_seconds: u64,
    pub service_running: bool,
    pub ntfs_mode: bool,
}

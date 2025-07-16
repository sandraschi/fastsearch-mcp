// FastSearch MCP Server - Full implementation with NTFS MFT reading

use serde_json::{json, Value};
use anyhow::Result;
use log::{info, debug, warn};
use std::fs;
use std::path::Path;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Instant;

// Re-export FileEntry from ntfs_reader module
pub use crate::ntfs_reader::FileEntry;

pub struct McpServer {
    // File index cache - will be populated from NTFS MFT
    file_index: Arc<Mutex<FileIndex>>,
}

struct FileIndex {
    files: Vec<FileEntry>,
    name_index: HashMap<String, Vec<usize>>, // filename -> file indices
    path_index: HashMap<String, Vec<usize>>, // path -> file indices
    indexed_drives: Vec<String>,
    last_updated: std::time::SystemTime,
}

impl McpServer {
    pub fn new() -> Result<Self> {
        info!("Initializing FastSearch MCP Server");
        let file_index = Arc::new(Mutex::new(FileIndex::new()));
        
        // Start background indexing of C: drive
        let index_clone = file_index.clone();
        std::thread::spawn(move || {
            if let Err(e) = Self::index_drive(index_clone, "C") {
                warn!("Failed to index C: drive: {}", e);
            }
        });
        
        Ok(McpServer { file_index })
    }
    
    fn index_drive(index: Arc<Mutex<FileIndex>>, drive: &str) -> Result<()> {
        info!("Starting NTFS MFT indexing for drive {}", drive);
        let start_time = Instant::now();
        
        // Try to use ntfs-reader crate for fast MFT access
        #[cfg(windows)]
        {
            // Use ntfs-reader for Windows
            match crate::ntfs_reader::read_mft_files(drive) {
                Ok(files) => {
                    let mut index_lock = index.lock().unwrap();
                    index_lock.files = files;
                    index_lock.rebuild_indexes();
                    index_lock.indexed_drives.push(drive.to_string());
                    index_lock.last_updated = std::time::SystemTime::now();
                    
                    let elapsed = start_time.elapsed();
                    info!("NTFS MFT indexing completed: {} files in {:?}", 
                          index_lock.files.len(), elapsed);
                    return Ok(());
                }
                Err(e) => {
                    warn!("NTFS MFT reader failed: {}, falling back to filesystem walk", e);
                }
            }
        }
        
        // Fallback to traditional filesystem walk
        let files = Self::index_with_filesystem_walk(drive)?;
        let mut index_lock = index.lock().unwrap();
        index_lock.files = files;
        index_lock.rebuild_indexes();
        index_lock.indexed_drives.push(drive.to_string());
        index_lock.last_updated = std::time::SystemTime::now();
        
        let elapsed = start_time.elapsed();
        info!("Filesystem walk indexing completed: {} files in {:?}", 
              index_lock.files.len(), elapsed);
        
        Ok(())
    }
    
    fn index_with_filesystem_walk(drive: &str) -> Result<Vec<FileEntry>> {
        let mut files = Vec::new();
        let root_path = format!("{}:\\", drive);
        
        fn visit_dir(dir: &Path, files: &mut Vec<FileEntry>) -> Result<()> {
            if dir.is_dir() {
                for entry in fs::read_dir(dir)? {
                    let entry = entry?;
                    let path = entry.path();
                    let metadata = entry.metadata()?;
                    
                    let file_entry = FileEntry {
                        name: entry.file_name().to_string_lossy().to_string(),
                        path: path.parent().unwrap_or(Path::new("")).to_string_lossy().to_string(),
                        full_path: path.to_string_lossy().to_string(),
                        size: metadata.len(),
                        is_directory: metadata.is_dir(),
                        created: metadata.created().unwrap_or(std::time::SystemTime::UNIX_EPOCH)
                            .duration_since(std::time::SystemTime::UNIX_EPOCH)
                            .unwrap_or_default().as_secs(),
                        modified: metadata.modified().unwrap_or(std::time::SystemTime::UNIX_EPOCH)
                            .duration_since(std::time::SystemTime::UNIX_EPOCH)
                            .unwrap_or_default().as_secs(),
                        accessed: metadata.accessed().unwrap_or(std::time::SystemTime::UNIX_EPOCH)
                            .duration_since(std::time::SystemTime::UNIX_EPOCH)
                            .unwrap_or_default().as_secs(),
                    };
                    
                    files.push(file_entry);
                    
                    if metadata.is_dir() {
                        // Recursively visit subdirectories
                        if let Err(e) = visit_dir(&path, files) {
                            // Skip directories we can't access
                            debug!("Skipping directory {}: {}", path.display(), e);
                        }
                    }
                }
            }
            Ok(())
        }
        
        visit_dir(Path::new(&root_path), &mut files)?;
        Ok(files)
    }
    
    pub fn handle_request(&self, request: Value) -> Result<Value> {
        debug!("Handling MCP request: {}", request);
        
        let method = request["method"].as_str().unwrap_or("");
        
        match method {
            "initialize" => self.handle_initialize(request),
            "tools/list" => self.handle_tools_list(),
            "tools/call" => self.handle_tool_call(request),
            _ => Ok(json!({
                "error": {
                    "code": -32601,
                    "message": "Method not found"
                }
            }))
        }
    }
    
    fn handle_initialize(&self, _request: Value) -> Result<Value> {
        Ok(json!({
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "fastsearch-mcp",
                    "version": "0.1.0"
                }
            }
        }))
    }
    
    fn handle_tools_list(&self) -> Result<Value> {
        Ok(json!({
            "result": {
                "tools": [
                    {
                        "name": "fast_search",
                        "description": "Lightning-fast file search using NTFS Master File Table",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "pattern": {
                                    "type": "string",
                                    "description": "File pattern to search for (*.js, README*, etc.)"
                                },
                                "path": {
                                    "type": "string", 
                                    "description": "Root path to search in"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return",
                                    "default": 1000
                                },
                                "filters": {
                                    "type": "object",
                                    "properties": {
                                        "exclude_dirs": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "Directories to exclude from search"
                                        },
                                        "min_size": {
                                            "type": "string",
                                            "description": "Minimum file size (e.g., '1MB')"
                                        },
                                        "max_size": {
                                            "type": "string", 
                                            "description": "Maximum file size (e.g., '100MB')"
                                        },
                                        "modified_after": {
                                            "type": "string",
                                            "description": "Only files modified after this date"
                                        },
                                        "file_types": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "description": "File extensions to include (e.g., ['.js', '.ts'])"
                                        }
                                    }
                                }
                            },
                            "required": ["pattern"]
                        }
                    },
                    {
                        "name": "find_duplicates",
                        "description": "Find duplicate files by content hash",
                        "inputSchema": {
                            "type": "object", 
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Path to search for duplicates"
                                },
                                "file_types": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "File types to check (e.g., ['.jpg', '.png'])"
                                },
                                "min_size": {
                                    "type": "string",
                                    "description": "Minimum file size to check"
                                }
                            },
                            "required": ["path"]
                        }
                    },
                    {
                        "name": "index_status",
                        "description": "Get status of file indexing",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "name": "reindex_drive",
                        "description": "Reindex a drive",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "drive": {
                                    "type": "string",
                                    "description": "Drive letter to reindex (e.g., 'C')"
                                }
                            },
                            "required": ["drive"]
                        }
                    }
                ]
            }
        }))
    }
    
    fn handle_tool_call(&self, request: Value) -> Result<Value> {
        let tool_name = request["params"]["name"].as_str().unwrap_or("");
        let arguments = &request["params"]["arguments"];
        
        match tool_name {
            "fast_search" => self.fast_search(arguments),
            "find_duplicates" => self.find_duplicates(arguments),
            "index_status" => self.index_status(arguments),
            "reindex_drive" => self.reindex_drive(arguments),
            _ => Ok(json!({
                "error": {
                    "code": -32602,
                    "message": "Unknown tool"
                }
            }))
        }
    }
    
    fn fast_search(&self, args: &Value) -> Result<Value> {
        let pattern = args["pattern"].as_str().unwrap_or("*");
        let path = args["path"].as_str().unwrap_or("");
        let max_results = args["max_results"].as_u64().unwrap_or(1000) as usize;
        
        info!("FastSearch: pattern='{}', path='{}', max_results={}", pattern, path, max_results);
        
        let search_start = Instant::now();
        let index = self.file_index.lock().unwrap();
        
        if index.files.is_empty() {
            return Ok(json!({
                "result": {
                    "content": [{
                        "type": "text",
                        "text": "File index is empty. Please wait for indexing to complete or use 'reindex_drive' tool."
                    }]
                }
            }));
        }
        
        let results = index.search(pattern, path, max_results);
        let search_duration = search_start.elapsed();
        
        let results_text = if results.is_empty() {
            format!("No files found matching pattern '{}' in path '{}'", pattern, path)
        } else {
            let mut text = format!("Found {} files matching '{}' in {:.2}ms\n\n", 
                                   results.len(), pattern, search_duration.as_millis());
            
            for (i, file) in results.iter().enumerate().take(max_results) {
                text.push_str(&format!("{}. {} ({})\n", 
                                       i + 1, 
                                       file.full_path,
                                       if file.is_directory { "DIR" } else { &format!("{} bytes", file.size) }));
            }
            
            if results.len() > max_results {
                text.push_str(&format!("\n... and {} more results (use max_results parameter to see more)", 
                                       results.len() - max_results));
            }
            
            text
        };
        
        Ok(json!({
            "result": {
                "content": [{
                    "type": "text",
                    "text": results_text
                }]
            }
        }))
    }
    
    fn find_duplicates(&self, args: &Value) -> Result<Value> {
        let path = args["path"].as_str().unwrap_or("C:");
        
        info!("Finding duplicates in: {}", path);
        
        // TODO: Implement actual duplicate detection using content hashing
        Ok(json!({
            "result": {
                "content": [{
                    "type": "text", 
                    "text": format!("Duplicate detection in: {}\n\nThis feature is not yet implemented.\nWill use content hashing to identify duplicate files.", path)
                }]
            }
        }))
    }
    
    fn index_status(&self, _args: &Value) -> Result<Value> {
        let index = self.file_index.lock().unwrap();
        
        let status_text = format!(
            "FastSearch Index Status\n\n\
            Indexed Files: {}\n\
            Indexed Drives: {}\n\
            Last Updated: {:?}\n\
            Name Index Entries: {}\n\
            Path Index Entries: {}",
            index.files.len(),
            index.indexed_drives.join(", "),
            index.last_updated,
            index.name_index.len(),
            index.path_index.len()
        );
        
        Ok(json!({
            "result": {
                "content": [{
                    "type": "text",
                    "text": status_text
                }]
            }
        }))
    }
    
    fn reindex_drive(&self, args: &Value) -> Result<Value> {
        let drive = args["drive"].as_str().unwrap_or("C");
        
        info!("Reindexing drive: {}", drive);
        
        // Clear existing index for this drive
        {
            let mut index = self.file_index.lock().unwrap();
            index.files.clear();
            index.name_index.clear();
            index.path_index.clear();
            index.indexed_drives.clear();
        }
        
        // Start reindexing in background
        let index_clone = self.file_index.clone();
        let drive_clone = drive.to_string();
        std::thread::spawn(move || {
            if let Err(e) = Self::index_drive(index_clone, &drive_clone) {
                warn!("Failed to reindex drive {}: {}", drive_clone, e);
            }
        });
        
        Ok(json!({
            "result": {
                "content": [{
                    "type": "text",
                    "text": format!("Started reindexing drive: {}\nThis will run in the background. Use 'index_status' to check progress.", drive)
                }]
            }
        }))
    }
}

impl FileIndex {
    fn new() -> Self {
        FileIndex {
            files: Vec::new(),
            name_index: HashMap::new(),
            path_index: HashMap::new(),
            indexed_drives: Vec::new(),
            last_updated: std::time::SystemTime::UNIX_EPOCH,
        }
    }
    
    fn rebuild_indexes(&mut self) {
        self.name_index.clear();
        self.path_index.clear();
        
        for (i, file) in self.files.iter().enumerate() {
            // Build name index
            let name_lower = file.name.to_lowercase();
            self.name_index.entry(name_lower).or_insert_with(Vec::new).push(i);
            
            // Build path index
            let path_lower = file.path.to_lowercase();
            self.path_index.entry(path_lower).or_insert_with(Vec::new).push(i);
        }
    }
    
    fn search(&self, pattern: &str, path_filter: &str, max_results: usize) -> Vec<&FileEntry> {
        let mut results = Vec::new();
        let pattern_lower = pattern.to_lowercase();
        let path_filter_lower = path_filter.to_lowercase();
        
        // Simple pattern matching - can be enhanced with regex later
        for file in &self.files {
            if results.len() >= max_results {
                break;
            }
            
            // Apply path filter if specified
            if !path_filter.is_empty() && !file.path.to_lowercase().contains(&path_filter_lower) {
                continue;
            }
            
            // Check if file matches pattern
            if Self::matches_pattern(&file.name.to_lowercase(), &pattern_lower) {
                results.push(file);
            }
        }
        
        results
    }
    
    fn matches_pattern(name: &str, pattern: &str) -> bool {
        if pattern == "*" {
            return true;
        }
        
        // Simple wildcard matching
        if pattern.contains('*') {
            let parts: Vec<&str> = pattern.split('*').collect();
            if parts.len() == 2 {
                let (prefix, suffix) = (parts[0], parts[1]);
                if prefix.is_empty() {
                    return name.ends_with(suffix);
                } else if suffix.is_empty() {
                    return name.starts_with(prefix);
                } else {
                    return name.starts_with(prefix) && name.ends_with(suffix);
                }
            }
        }
        
        // Exact match or contains
        name.contains(pattern)
    }
}

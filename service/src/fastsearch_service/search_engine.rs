// FastSearch MCP Server - CACHED MFT SEARCH IMPLEMENTATION

use serde_json::{json, Value};
use anyhow::{Result, Context};
use log::{info, debug, error};
use std::time::Instant;
use std::collections::{HashSet, HashMap};
use std::sync::Arc;
use parking_lot::RwLock;

// Import file_types with relative path
use crate::file_types::{get_extensions, DocumentType, parse_document_type};
use super::mft_cache::{MftCache, FileEntry};

/// SearchEngine handles all search-related functionality
pub struct SearchEngine {
    // MFT cache for fast file searches
    mft_cache: Arc<RwLock<HashMap<char, MftCache>>>,
    
    // Cache for document type extensions
    doc_type_extensions: HashMap<DocumentType, HashSet<String>>,
}

impl SearchEngine {
    /// Create a new SearchEngine instance with MFT cache
    pub fn new() -> Result<Self> {
        info!("Initializing FastSearch Search Engine (MFT CACHE MODE)");
        
        // Initialize document type extensions
        let doc_type_extensions = get_extensions()
            .into_iter()
            .collect();
            
        Ok(SearchEngine {
            mft_cache: Arc::new(RwLock::new(HashMap::new())),
            doc_type_extensions,
        })
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
    
    pub(crate) fn handle_tools_list(&self) -> Result<Value> {
        Ok(json!({
            "result": {
                "tools": [
                    {
                        "name": "list_ntfs_drives",
                        "description": "List all available NTFS drives on the system",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "fast_search",
                        "description": "Lightning-fast DIRECT file search using NTFS Master File Table (no indexing)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "pattern": {
                                    "type": "string",
                                    "description": "File pattern to search for (*.js, README*, config.*, etc.)"
                                },
                                "path": {
                                    "type": "string",
                                    "description": "Optional path to search within (e.g., \"src/\" or \"C:\\Windows\")"
                                },
                                "drive": {
                                    "type": "string",
                                    "description": "Drive letter to search (e.g., 'C'). Use '*' to search all NTFS drives.",
                                    "default": "C"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return (default: 1000)",
                                    "default": 1000
                                },
                                "type": {
                                    "type": "string",
                                    "description": "Type filter: 'file', 'directory', or 'any' (default)",
                                    "enum": ["file", "directory", "any"],
                                    "default": "any"
                                },
                                "doc_type": {
                                    "type": "string",
                                    "description": "Document type filter (e.g., 'text', 'code', 'image', 'pdf')",
                                    "default": ""
                                },
                                "extensions": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    },
                                    "description": "File extensions to include (without leading .), overrides doc_type if both are specified"
                                },
                            },
                            "required": ["pattern"]
                        }
                    },
                    {
                        "name": "find_large_files",
                        "description": "Find large files by direct MFT scan",
                        "inputSchema": {
                            "type": "object", 
                            "properties": {
                                "min_size_mb": {
                                    "type": "integer",
                                    "description": "Minimum file size in MB",
                                    "default": 100
                                },
                                "drive": {
                                    "type": "string",
                                    "description": "Drive letter to search",
                                    "default": "C"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results",
                                    "default": 50
                                }
                            }
                        }
                    },
                    {
                        "name": "benchmark_search",
                        "description": "Benchmark direct search performance",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "drive": {
                                    "type": "string",
                                    "description": "Drive letter to benchmark",
                                    "default": "C"
                                }
                            }
                        }
                    }
                ]
            }
        }))
    }
    
    /// List all supported document types and their extensions
    fn list_document_types(&self) -> Result<Value> {
        use strum::IntoEnumIterator;
        use std::collections::HashMap;
        
        let mut doc_types = HashMap::new();
        
        for doc_type in DocumentType::iter() {
            let name = match doc_type {
                DocumentType::Text => "text",
                DocumentType::Code => "code",
                DocumentType::Image => "image",
                DocumentType::Spreadsheet => "spreadsheet",
                DocumentType::Presentation => "presentation",
                DocumentType::Archive => "archive",
                DocumentType::Audio => "audio",
                DocumentType::Video => "video",
                DocumentType::Pdf => "pdf",
            };
            
            doc_types.insert(name.to_string(), get_extensions(doc_type));
        }
        
        Ok(json!({
            "result": {
                "content": [{
                    "type": "text",
                    "text": format!("Supported document types: {}", 
                        doc_types.keys().map(|s| s.as_str()).collect::<Vec<_>>().join(", "))
                }],
                "document_types": doc_types
            }
        }))
    }
    
    /// List all available NTFS drives on the system
    fn list_ntfs_drives(&self) -> Result<Value> {
        let drives = crate::ntfs_reader::get_ntfs_drives()?;
        
        Ok(json!({
            "result": {
                "content": [{
                    "type": "text",
                    "text": format!("Available NTFS drives: {}", 
                        drives.join(", "))
                }],
                "drives": drives
            }
        }))
    }
    
    fn handle_tool_call(&self, request: Value) -> Result<Value> {
        let tool_name = request["params"]["name"].as_str().unwrap_or("");
        let arguments = &request["params"]["arguments"];
        
        match tool_name {
            "fast_search" => self.fast_search(arguments),
            "find_large_files" => self.find_large_files(arguments),
            "benchmark_search" => self.benchmark_search(arguments),
            "list_ntfs_drives" => self.list_ntfs_drives(),
            "list_document_types" => self.list_document_types(),
            _ => Ok(json!({
                "error": {
                    "code": -32602,
                    "message": "Unknown tool"
                }
            }))
        }
    }
    
    /// FAST SEARCH USING MFT CACHE
    /// 
    /// Args:
    /// - pattern: File pattern to search for (e.g., "*.txt", "*.rs")
    /// - path_filter: Filter by path (optional)
    /// - drive: Drive letter (e.g., "C") or "*" for all NTFS drives
    /// - max_results: Maximum number of results to return
    pub fn fast_search(&self, args: &Value) -> Result<Value> {
        let pattern = args["pattern"].as_str().unwrap_or("*");
        let path_filter = args["path"].as_str().unwrap_or("").to_lowercase();
        let drive = args["drive"].as_str().unwrap_or("C").to_uppercase();
        let max_results = args["max_results"].as_u64().unwrap_or(1000) as usize;
        
        // Parse document type filter
        let doc_type = args["doc_type"]
            .as_str()
            .and_then(|s| parse_document_type(s));
            
        // Parse explicit extensions if provided
        let extensions: Option<HashSet<String>> = args["extensions"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str())
                    .map(|s| s.trim_start_matches('.').to_lowercase())
                    .collect()
            });
            
        info!("Search filters - doc_type: {:?}, extensions: {:?}", doc_type, extensions);
        info!("FAST SEARCH: pattern='{}', path='{}', drive='{}', max_results={}", 
              pattern, path_filter, drive, max_results);
        
        let search_start = Instant::now();
        
        // Get or create MFT cache for the drive
        let drive_char = drive.chars().next().unwrap_or('C');
        let mft_cache = self.get_or_create_cache(drive_char)?;
        
        // Get read locks on the cache
        let files = mft_cache.get_files();
        let path_index = mft_cache.get_path_index();
        
        // Convert pattern to regex
        let pattern_regex = self.pattern_to_regex(pattern)?;
        
        // Filter files based on criteria
        let mut results = Vec::new();
        let mut result_count = 0;
        
        for (_, file) in files.iter() {
            // Apply path filter
            if !path_filter.is_empty() && !file.path.to_lowercase().contains(&path_filter) {
                continue;
            }
            
            // Apply pattern filter
            if !pattern_regex.is_match(&file.name) {
                continue;
            }
            
            // Apply extension filter if specified
            if let Some(exts) = &extensions {
                if let Some(ext) = &file.extension {
                    if !exts.contains(ext) {
                        continue;
                    }
                } else if !exts.is_empty() {
                    continue; // No extension but extensions were specified
                }
            }
            
            // Apply document type filter
            if let Some(doc_type) = doc_type {
                if let Some(ext) = &file.extension {
                    if !self.doc_type_extensions.get(&doc_type)
                        .map_or(false, |exts| exts.contains(ext)) {
                        continue;
                    }
                } else {
                    continue; // No extension but document type requires one
                }
            }
            
            // Add to results
            results.push(file.clone());
            result_count += 1;
            
            // Early exit if we've reached max results
            if result_count >= max_results {
                break;
            }
        }
        
        let search_duration = search_start.elapsed();
        
        // Format results
        let results_text = if results.is_empty() {
            format!("No files found matching pattern '{}' in drive {} (searched in {:.2}ms)", 
                    pattern, drive, search_duration.as_millis())
        } else {
            let mut text = format!("🚀 FAST SEARCH: Found {} files matching '{}' in {:.2}ms\n\n", 
                                 results.len(), pattern, search_duration.as_millis());
            
            for (i, file) in results.iter().enumerate() {
                let size_info = if file.is_directory { 
                    "DIR".to_string() 
                } else { 
                    format!("{} bytes", file.size) 
                };
                text.push_str(&format!("{}. {} ({})\n", 
                                     i + 1, 
                                     file.path,
                                     size_info));
            }
            
            if results.len() >= max_results {
                text.push_str(&format!("\n⚡ Stopped at {} results (use max_results to get more)", max_results));
            }
            
            text.push_str(&format!("\n💡 Search completed in {:.2}ms - USING MFT CACHE", search_duration.as_millis()));
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
    
    /// Find large files by direct scan
    fn find_large_files(&self, args: &Value) -> Result<Value> {
        let min_size_mb = args["min_size_mb"].as_u64().unwrap_or(100);
        let drive = args["drive"].as_str().unwrap_or("C");
        let max_results = args["max_results"].as_u64().unwrap_or(50) as usize;
        
        info!("Finding large files: min_size={}MB, drive={}", min_size_mb, drive);
        
        let search_start = Instant::now();
        
        // Search for all files and filter by size
        let all_files = crate::ntfs_reader::search_files_direct(drive, "*", "", max_results * 10)?;
        
        let min_size_bytes = min_size_mb * 1024 * 1024;
        let mut large_files: Vec<_> = all_files
            .into_iter()
            .filter(|f| !f.is_directory && f.size >= min_size_bytes)
            .collect();
        
        // Sort by size (largest first)
        large_files.sort_by(|a, b| b.size.cmp(&a.size));
        large_files.truncate(max_results);
        
        let search_duration = search_start.elapsed();
        
        let results_text = if large_files.is_empty() {
            format!("No files larger than {}MB found in drive {} (searched in {:.2}ms)", 
                    min_size_mb, drive, search_duration.as_millis())
        } else {
            let mut text = format!("📁 Found {} files larger than {}MB (searched in {:.2}ms):\n\n", 
                                   large_files.len(), min_size_mb, search_duration.as_millis());
            
            for (i, file) in large_files.iter().enumerate() {
                let size_mb = file.size as f64 / (1024.0 * 1024.0);
                text.push_str(&format!("{}. {} ({:.1} MB)\n", 
                                       i + 1, 
                                       file.full_path,
                                       size_mb));
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
    
    /// Helper to get or create MFT cache for a drive
    fn get_or_create_cache(&self, drive: char) -> Result<Arc<MftCache>> {
        // Check if we already have a cache for this drive
        let cache_map = self.mft_cache.read().map_err(|e| anyhow::anyhow!("Failed to acquire read lock: {}", e))?;
        if let Some(cache) = cache_map.get(&drive) {
            return Ok(Arc::clone(cache));
        }
        
        // Release read lock before acquiring write lock
        drop(cache_map);
        
        // Create new cache for this drive
        let mut cache_map = self.mft_cache.write().map_err(|e| anyhow::anyhow!("Failed to acquire write lock: {}", e))?;
        
        // Double check in case another thread created it while we were waiting for the write lock
        if let Some(cache) = cache_map.get(&drive) {
            return Ok(Arc::clone(cache));
        }
        
        info!("Creating new MFT cache for drive {}:", drive);
        let mft_cache = match MftCache::new(drive) {
            Ok(cache) => Arc::new(cache),
            Err(e) => return Err(anyhow::anyhow!("Failed to create MFT cache: {}", e)),
        };
        
        // Insert into our cache map
        cache_map.insert(drive, Arc::clone(&mft_cache));
        
        Ok(mft_cache)
    }
    
    /// Convert a file pattern to a regex
    fn pattern_to_regex(&self, pattern: &str) -> Result<regex::Regex> {
        // Handle special cases
        if pattern == "*" || pattern == "*.*" {
            return Ok(regex::Regex::new(".*").unwrap());
        }
        
        // Escape special regex characters
        let mut regex_str = regex::escape(pattern);
        
        // Convert wildcards to regex patterns
        regex_str = regex_str.replace(".", "\\.."); // Escape literal dots
        regex_str = regex_str.replace("*", ".*");     // Convert * to .*
        regex_str = regex_str.replace("?", ".");      // Convert ? to .
        
        // Make case-insensitive and ensure we match the whole string
        regex_str = format!(r"^(?i){}$", regex_str);
        
        regex::Regex::new(&regex_str)
            .with_context(|| format!("Invalid search pattern: {}", pattern))
    }
    
    /// Benchmark direct search performance
    pub fn benchmark_search(&self, args: &Value) -> Result<Value> {
        let drive = args["drive"].as_str().unwrap_or("C");
        
        info!("Running direct search benchmark for drive: {}", drive);
        
        #[cfg(windows)]
        {
            match crate::ntfs_reader::benchmark_mft_performance(drive) {
                Ok(_) => {
                    Ok(json!({
                        "result": {
                            "content": [{
                                "type": "text",
                                "text": format!("Benchmark completed for drive {}. Check console output for detailed results.", drive)
                            }]
                        }
                    }))
                }
                Err(e) => {
                    Ok(json!({
                        "result": {
                            "content": [{
                                "type": "text",
                                "text": format!("Benchmark failed: {}", e)
                            }]
                        }
                    }))
                }
            }
        }
        
        #[cfg(not(windows))]
        {
            Ok(json!({
                "result": {
                    "content": [{
                        "type": "text",
                        "text": "Benchmark is only available on Windows (NTFS required)".to_string()
                    }]
                }
            }))
        }
    }
}

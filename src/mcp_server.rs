// FastSearch MCP Server - DIRECT SEARCH IMPLEMENTATION (NO INDEXING!)

use serde_json::{json, Value};
use anyhow::Result;
use log::{info, debug};
use std::time::Instant;

pub struct McpServer {
    // NO MORE FILE INDEX! We do direct searches now
}

impl McpServer {
    pub fn new() -> Result<Self> {
        info!("Initializing FastSearch MCP Server (DIRECT SEARCH MODE)");
        Ok(McpServer {})
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
                                    "description": "Path filter (searches files whose path contains this string)"
                                },
                                "drive": {
                                    "type": "string",
                                    "description": "Drive letter to search (default: C)",
                                    "default": "C"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return",
                                    "default": 1000
                                }
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
    
    fn handle_tool_call(&self, request: Value) -> Result<Value> {
        let tool_name = request["params"]["name"].as_str().unwrap_or("");
        let arguments = &request["params"]["arguments"];
        
        match tool_name {
            "fast_search" => self.fast_search(arguments),
            "find_large_files" => self.find_large_files(arguments),
            "benchmark_search" => self.benchmark_search(arguments),
            _ => Ok(json!({
                "error": {
                    "code": -32602,
                    "message": "Unknown tool"
                }
            }))
        }
    }
    
    /// DIRECT SEARCH - NO INDEXING!
    pub fn fast_search(&self, args: &Value) -> Result<Value> {
        let pattern = args["pattern"].as_str().unwrap_or("*");
        let path_filter = args["path"].as_str().unwrap_or("");
        let drive = args["drive"].as_str().unwrap_or("C");
        let max_results = args["max_results"].as_u64().unwrap_or(1000) as usize;
        
        info!("DIRECT FastSearch: pattern='{}', path='{}', drive='{}', max_results={}", 
              pattern, path_filter, drive, max_results);
        
        let search_start = Instant::now();
        
        // DIRECT MFT SEARCH - NO CACHING!
        let results = crate::ntfs_reader::search_files_direct(drive, pattern, path_filter, max_results)
            .map_err(|e| {
                if e.to_string().contains("Access is denied") {
                    anyhow::anyhow!("Administrator privileges required for NTFS access. Please run Claude Desktop as Administrator.\nError: {}", e)
                } else {
                    e
                }
            })?;
        
        let search_duration = search_start.elapsed();
        
        let results_text = if results.is_empty() {
            format!("No files found matching pattern '{}' in drive {} (searched in {:.2}ms)", 
                    pattern, drive, search_duration.as_millis())
        } else {
            let mut text = format!("🚀 DIRECT SEARCH: Found {} files matching '{}' in {:.2}ms\n\n", 
                                   results.len(), pattern, search_duration.as_millis());
            
            for (i, file) in results.iter().enumerate() {
                let size_info = if file.is_directory { 
                    "DIR".to_string() 
                } else { 
                    format!("{} bytes", file.size) 
                };
                text.push_str(&format!("{}. {} ({})\n", 
                                       i + 1, 
                                       file.full_path,
                                       size_info));
            }
            
            if results.len() >= max_results {
                text.push_str(&format!("\n⚡ Stopped at {} results (use max_results to get more)", max_results));
            }
            
            text.push_str(&format!("\n💡 Search completed in {:.2}ms - NO INDEXING!", search_duration.as_millis()));
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

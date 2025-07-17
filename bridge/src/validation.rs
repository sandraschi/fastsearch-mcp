use serde_json::Value;
use regex::Regex;

pub fn validate_search_args(args: &Value) -> Result<(), String> {
    // Validate pattern
    let pattern = args.get("pattern")
        .and_then(|p| p.as_str())
        .ok_or("Pattern is required")?;
        
    if pattern.is_empty() {
        return Err("Pattern cannot be empty".to_string());
    }
    
    if pattern.len() > 1000 {
        return Err("Pattern too long (max 1000 characters)".to_string());
    }
    
    // Security: Prevent path traversal
    if pattern.contains("..") || pattern.contains("\\..\\") || pattern.contains("/../") {
        return Err("Path traversal patterns not allowed".to_string());
    }
    
    // Validate search_type if provided
    if let Some(search_type) = args.get("search_type").and_then(|s| s.as_str()) {
        match search_type {
            "smart" | "exact" | "glob" | "regex" | "fuzzy" => {}
            _ => return Err("Invalid search_type. Must be: smart, exact, glob, regex, or fuzzy".to_string()),
        }
    }
    
    // Validate max_results if provided
    if let Some(max_results) = args.get("max_results").and_then(|m| m.as_u64()) {
        if max_results == 0 {
            return Err("max_results must be at least 1".to_string());
        }
        if max_results > 10000 {
            return Err("max_results cannot exceed 10000".to_string());
        }
    }
    
    // Validate filters if present
    if let Some(filters) = args.get("filters") {
        validate_filters(filters)?;
    }
    
    Ok(())
}

fn validate_filters(filters: &Value) -> Result<(), String> {
    // Validate size filters
    for size_field in ["min_size", "max_size"] {
        if let Some(size) = filters.get(size_field).and_then(|s| s.as_str()) {
            validate_size_format(size)?;
        }
    }
    
    // Validate file_types
    if let Some(types) = filters.get("file_types") {
        if let Some(array) = types.as_array() {
            for ext in array {
                if let Some(ext_str) = ext.as_str() {
                    if !ext_str.starts_with('.') {
                        return Err("File extensions must start with '.' (e.g., '.js', '.txt')".to_string());
                    }
                    if ext_str.len() > 10 {
                        return Err("File extension too long".to_string());
                    }
                }
            }
        }
    }
    
    // Validate date filters
    if let Some(date) = filters.get("modified_after").and_then(|d| d.as_str()) {
        validate_date_format(date)?;
    }
    
    Ok(())
}

fn validate_size_format(size: &str) -> Result<(), String> {
    let size_regex = Regex::new(r"^\d+[BKMGT]?B?$").unwrap();
    if !size_regex.is_match(size) {
        return Err("Invalid size format. Use: 1KB, 10MB, 1GB, etc.".to_string());
    }
    Ok(())
}

fn validate_date_format(date: &str) -> Result<(), String> {
    let date_regex = Regex::new(r"^\d{4}-\d{2}-\d{2}$").unwrap();
    if !date_regex.is_match(date) {
        return Err("Invalid date format. Use YYYY-MM-DD (e.g., 2025-07-17)".to_string());
    }
    Ok(())
}

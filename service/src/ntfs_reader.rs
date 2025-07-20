// NTFS MFT Reader - DIRECT QUERY IMPLEMENTATION (NO INDEXING!)

use anyhow::{Result, Context};
use log::{info, debug, warn};
use std::time::Instant;
use std::fs::File;
use std::io::{Read, Seek};
use ntfs::Ntfs;
use regex::Regex;
use std::path::Path;
use winapi::um::fileapi::{GetDriveTypeW, GetLogicalDriveStringsW};
use widestring::WideCString;
use std::ffi::OsString;
use std::os::windows::ffi::OsStringExt;

#[derive(Debug, Clone)]
pub struct FileEntry {
    pub name: String,
    pub path: String,
    pub full_path: String,
    pub size: u64,
    pub is_directory: bool,
    pub created: u64,
    pub modified: u64,
    pub accessed: u64,
}

/// DIRECT MFT SEARCH - NO CACHING, NO INDEXING!
#[cfg(windows)]
pub fn search_files_direct(drive: &str, pattern: &str, path_filter: &str, max_results: usize) -> Result<Vec<FileEntry>> {
    let volume_path = format!("\\\\.\\{}:", drive.trim_end_matches(':'));
    info!("Direct MFT search: pattern='{}', path='{}', drive='{}'", pattern, path_filter, drive);
    
    let start_time = Instant::now();
    
    // Open the raw volume (requires admin privileges)
    let mut file = File::open(&volume_path)
        .map_err(|e| anyhow::anyhow!("Failed to open volume {} (needs admin privileges): {}", volume_path, e))?;
    
    let ntfs = Ntfs::new(&mut file)
        .map_err(|e| anyhow::anyhow!("Failed to initialize NTFS: {}", e))?;
    
    let mut results = Vec::new();
    
    // Convert pattern to regex for matching
    let pattern_regex = glob_to_regex(pattern)?;
    let path_filter_lower = path_filter.to_lowercase();
    
    // Get the root directory and search
    let root = ntfs.root_directory(&mut file)
        .map_err(|e| anyhow::anyhow!("Failed to get root directory: {}", e))?;
    
    // DIRECT SEARCH - only traverse what we need
    search_directory_direct(
        &mut file,
        &ntfs,
        &root,
        "",
        &pattern_regex,
        &path_filter_lower,
        &mut results,
        max_results,
        &start_time
    )?;
    
    let elapsed = start_time.elapsed();
    info!("Direct MFT search completed: {} results in {:?}", results.len(), elapsed);
    
    Ok(results)
}

/// RECURSIVE SEARCH WITH EARLY TERMINATION
#[cfg(windows)]
fn search_directory_direct<T: Read + Seek>(
    fs: &mut T,
    ntfs: &Ntfs,
    directory: &ntfs::NtfsFile,
    current_path: &str,
    pattern_regex: &Regex,
    path_filter: &str,
    results: &mut Vec<FileEntry>,
    max_results: usize,
    start_time: &Instant,
) -> Result<()> {
    // EARLY EXIT if we have enough results
    if results.len() >= max_results {
        return Ok(());
    }
    
    // Skip if this path doesn't match our filter
    if !path_filter.is_empty() && !current_path.to_lowercase().contains(path_filter) {
        // Check if any subdirectory could match
        if !path_could_contain_filter(current_path, path_filter) {
            return Ok(());
        }
    }
    
    let index = match directory.directory_index(fs) {
        Ok(index) => index,
        Err(_) => return Ok(()), // Skip inaccessible directories
    };
    
    let mut iter = index.entries();
    
    while let Some(entry) = iter.next(fs) {
        // EARLY EXIT if we have enough results
        if results.len() >= max_results {
            break;
        }
        
        let entry = match entry {
            Ok(entry) => entry,
            Err(_) => continue, // Skip corrupted entries
        };
        
        let file_name = match entry.key() {
            Some(Ok(key)) => key.name().to_string_lossy().to_string(),
            _ => continue,
        };
        
        // Skip system entries
        if file_name == "." || file_name == ".." {
            continue;
        }
        
        let full_path = if current_path.is_empty() {
            file_name.clone()
        } else {
            format!("{}\\{}", current_path, file_name)
        };
        
        let file_reference = entry.file_reference();
        let ntfs_file = match ntfs.file(fs, file_reference.file_record_number()) {
            Ok(file) => file,
            Err(_) => continue,
        };
        
        let is_directory = ntfs_file.directory_index(fs).is_ok();
        
        // CHECK IF THIS FILE MATCHES OUR PATTERN
        if pattern_regex.is_match(&file_name) {
            // Apply path filter
            if path_filter.is_empty() || current_path.to_lowercase().contains(path_filter) {
                
                let size = if is_directory { 
                    0 
                } else { 
                    // Simple size estimation - just use 0 for now to avoid NTFS API complexity
                    0
                };
                
                // Get timestamps - simplified to avoid API issues
                let (created, modified, accessed) = (0, 0, 0);
                
                let file_entry = FileEntry {
                    name: file_name.clone(),
                    path: current_path.to_string(),
                    full_path: full_path.clone(),
                    size,
                    is_directory,
                    created,
                    modified,
                    accessed,
                };
                
                results.push(file_entry);
                
                // Log progress for user feedback
                if results.len() % 1000 == 0 {
                    debug!("Found {} matches in {:?}", results.len(), start_time.elapsed());
                }
            }
        }
        
        // RECURSIVELY SEARCH SUBDIRECTORIES (but with early exit)
        if is_directory && results.len() < max_results {
            if let Err(e) = search_directory_direct(
                fs, ntfs, &ntfs_file, &full_path, 
                pattern_regex, path_filter, results, max_results, start_time
            ) {
                debug!("Failed to search directory {}: {}", full_path, e);
            }
        }
    }
    
    Ok(())
}

/// Convert glob pattern to regex
fn glob_to_regex(pattern: &str) -> Result<Regex> {
    let mut regex_pattern = String::new();
    regex_pattern.push('^');
    
    for ch in pattern.chars() {
        match ch {
            '*' => regex_pattern.push_str(".*"),
            '?' => regex_pattern.push('.'),
            '.' => regex_pattern.push_str("\\."),
            '^' | '$' | '(' | ')' | '[' | ']' | '{' | '}' | '|' | '+' | '\\' => {
                regex_pattern.push('\\');
                regex_pattern.push(ch);
            }
            _ => regex_pattern.push(ch),
        }
    }
    
    regex_pattern.push('$');
    
    Regex::new(&regex_pattern)
        .map_err(|e| anyhow::anyhow!("Invalid pattern '{}': {}", pattern, e))
}

/// Check if a path could contain our filter (for early pruning)
fn path_could_contain_filter(current_path: &str, filter: &str) -> bool {
    if filter.is_empty() {
        return true;
    }
    
    // If filter contains path separators, do more sophisticated checking
    if filter.contains('\\') || filter.contains('/') {
        filter.to_lowercase().starts_with(&current_path.to_lowercase())
    } else {
        true // Conservative: assume subdirectories might match
    }
}

/// Convert NTFS time to Unix timestamp
#[cfg(windows)]
fn ntfs_time_to_unix(ntfs_time: ntfs::NtfsTime) -> u64 {
    let nt_timestamp = ntfs_time.nt_timestamp();
    const NT_UNIX_DIFF: u64 = 116_444_736_000_000_000;
    if nt_timestamp > NT_UNIX_DIFF {
        (nt_timestamp - NT_UNIX_DIFF) / 10_000_000
    } else {
        0
    }
}

/// NON-WINDOWS FALLBACK - DIRECT FILESYSTEM SEARCH
#[cfg(not(windows))]
pub fn search_files_direct(_drive: &str, pattern: &str, path_filter: &str, max_results: usize) -> Result<Vec<FileEntry>> {
    use std::path::Path;
    use std::fs;
    
    let start_time = Instant::now();
    let mut results = Vec::new();
    let pattern_regex = glob_to_regex(pattern)?;
    
    let root_path = format!("{}:/", _drive.trim_end_matches(':'));
    search_filesystem_direct(Path::new(&root_path), &pattern_regex, path_filter, &mut results, max_results)?;
    
    let elapsed = start_time.elapsed();
    info!("Direct filesystem search completed: {} results in {:?}", results.len(), elapsed);
    
    Ok(results)
}

#[cfg(not(windows))]
fn search_filesystem_direct(
    dir: &std::path::Path,
    pattern_regex: &Regex,
    path_filter: &str,
    results: &mut Vec<FileEntry>,
    max_results: usize,
) -> Result<()> {
    if results.len() >= max_results {
        return Ok(());
    }
    
    let entries = match std::fs::read_dir(dir) {
        Ok(entries) => entries,
        Err(_) => return Ok(()), // Skip inaccessible directories
    };
    
    for entry in entries {
        if results.len() >= max_results {
            break;
        }
        
        let entry = match entry {
            Ok(entry) => entry,
            Err(_) => continue,
        };
        
        let file_name = entry.file_name().to_string_lossy().to_string();
        let path = entry.path();
        let metadata = match entry.metadata() {
            Ok(metadata) => metadata,
            Err(_) => continue,
        };
        
        // Check pattern match
        if pattern_regex.is_match(&file_name) {
            let current_path = path.parent().unwrap_or(std::path::Path::new("")).to_string_lossy().to_string();
            
            // Apply path filter
            if path_filter.is_empty() || current_path.to_lowercase().contains(&path_filter.to_lowercase()) {
                let file_entry = FileEntry {
                    name: file_name,
                    path: current_path,
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
                
                results.push(file_entry);
            }
        }
        
        // Recursively search subdirectories
        if metadata.is_dir() && results.len() < max_results {
            let _ = search_filesystem_direct(&path, pattern_regex, path_filter, results, max_results);
        }
    }
    
    Ok(())
}

/// Get a list of all available NTFS drives on the system
#[cfg(windows)]
pub fn get_ntfs_drives() -> Result<Vec<String>> {
    use std::os::windows::ffi::OsStrExt;
    use std::ffi::OsStr;
    
    const DRIVE_FIXED: u32 = 3; // DRIVE_FIXED from winapi
    const MAX_PATH: usize = 260;
    
    // Get all drive letters
    let mut buffer = [0u16; MAX_PATH * 4]; // Should be enough for all drives
    let len = unsafe {
        GetLogicalDriveStringsW(
            buffer.len() as u32,
            buffer.as_mut_ptr()
        )
    };
    
    if len == 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    
    let buffer = &buffer[..len as usize];
    let mut drives = Vec::new();
    
    // Split the null-terminated wide strings
    for drive in buffer.split(|&c| c == 0) {
        if drive.is_empty() {
            continue;
        }
        
        // Convert wide string to Rust string
        let drive_str = OsString::from_wide(drive)
            .to_string_lossy()
            .to_string();
            
        // Check if it's a fixed drive (not removable, network, etc.)
        let drive_type = unsafe { 
            GetDriveTypeW(
                WideCString::from_str(&drive_str)
                    .map_err(|_| anyhow::anyhow!("Invalid drive string"))?
                    .as_ptr()
            )
        };
        
        if drive_type == DRIVE_FIXED {
            // Remove the trailing backslash
            if let Some(drive_letter) = drive_str.trim_end_matches('\\').chars().next() {
                drives.push(drive_letter.to_uppercase().to_string());
            }
        }
    }
    
    Ok(drives)
}

/// Search multiple NTFS drives
#[cfg(windows)]
pub fn search_multiple_drives(drives: &[String], pattern: &str, path_filter: &str, max_results: usize) -> Result<Vec<FileEntry>> {
    let mut all_results = Vec::new();
    let mut remaining_results = max_results;
    
    for drive in drives {
        if remaining_results == 0 {
            break;
        }
        
        match search_files_direct(drive, pattern, path_filter, remaining_results) {
            Ok(mut results) => {
                let len = results.len();
                all_results.append(&mut results);
                
                if len >= remaining_results {
                    break;
                }
                remaining_results -= len;
            }
            Err(e) => {
                warn!("Failed to search drive {}: {}", drive, e);
                // Continue with next drive
            }
        }
    }
    
    Ok(all_results)
}

// LEGACY FUNCTIONS - DEPRECATED (but kept for compatibility)
#[cfg(windows)]
pub fn read_mft_files(drive: &str) -> Result<Vec<FileEntry>> {
    warn!("read_mft_files is deprecated - use search_files_direct instead");
    search_files_direct(drive, "*", "", 100000) // Return max 100k files
}

#[cfg(not(windows))]
pub fn read_mft_files(_drive: &str) -> Result<Vec<FileEntry>> {
    warn!("read_mft_files is deprecated - use search_files_direct instead");
    Err(anyhow::anyhow!("NTFS MFT reading is only supported on Windows"))
}

/// Benchmark function
#[cfg(windows)]
pub fn benchmark_mft_performance(drive: &str) -> Result<()> {
    info!("Starting DIRECT MFT search benchmark for drive {}", drive);
    
    let patterns = vec!["*.txt", "*.exe", "*.dll", "*.js", "*.log"];
    
    for pattern in patterns {
        let start = Instant::now();
        let results = search_files_direct(drive, pattern, "", 1000)?;
        let duration = start.elapsed();
        
        println!("Pattern '{}': {} files in {:?} ({:.2} files/ms)", 
                 pattern, results.len(), duration, 
                 results.len() as f64 / duration.as_millis() as f64);
    }
    
    Ok(())
}

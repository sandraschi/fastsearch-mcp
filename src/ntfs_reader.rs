// NTFS MFT Reader implementation using ntfs-reader crate

use anyhow::Result;
use log::{info, debug, warn};
use std::time::Instant;

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

#[cfg(windows)]
pub fn read_mft_files(drive: &str) -> Result<Vec<FileEntry>> {
    use ntfs_reader::{Volume, Mft, FileInfo};
    
    let volume_path = format!("\\\\.\\{}:", drive.trim_end_matches(':'));
    info!("Opening NTFS volume: {}", volume_path);
    
    let volume = Volume::new(&volume_path)
        .map_err(|e| anyhow::anyhow!("Failed to open volume {}: {}", volume_path, e))?;
    
    let mft = Mft::new(volume)
        .map_err(|e| anyhow::anyhow!("Failed to read MFT: {}", e))?;
    
    let mut files = Vec::new();
    let start_time = Instant::now();
    let mut file_count = 0;
    
    info!("Starting MFT iteration...");
    
    // Iterate through all files in the MFT
    mft.iterate_files(|file| {
        file_count += 1;
        
        // Log progress every 100,000 files
        if file_count % 100000 == 0 {
            debug!("Processed {} files in {:?}", file_count, start_time.elapsed());
        }
        
        // Use FileInfo to get file details
        match FileInfo::new(&mft, file) {
            Ok(info) => {
                // Extract file information
                let name = info.name().unwrap_or_default();
                let path = info.path().unwrap_or_default();
                let full_path = if path.is_empty() {
                    name.clone()
                } else {
                    format!("{}\\{}", path, name)
                };
                
                let file_entry = FileEntry {
                    name,
                    path,
                    full_path,
                    size: info.size().unwrap_or(0),
                    is_directory: info.is_directory().unwrap_or(false),
                    created: info.created().unwrap_or(0),
                    modified: info.modified().unwrap_or(0),
                    accessed: info.accessed().unwrap_or(0),
                };
                
                files.push(file_entry);
            }
            Err(e) => {
                debug!("Failed to get file info: {}", e);
            }
        }
    }).map_err(|e| anyhow::anyhow!("MFT iteration failed: {}", e))?;
    
    let elapsed = start_time.elapsed();
    info!("MFT reading completed: {} files in {:?} ({:.2} files/sec)", 
          files.len(), elapsed, files.len() as f64 / elapsed.as_secs_f64());
    
    Ok(files)
}

#[cfg(not(windows))]
pub fn read_mft_files(_drive: &str) -> Result<Vec<FileEntry>> {
    Err(anyhow::anyhow!("NTFS MFT reading is only supported on Windows"))
}

// Benchmark function for testing performance
#[cfg(windows)]
pub fn benchmark_mft_performance(drive: &str) -> Result<()> {
    use std::collections::HashMap;
    
    info!("Starting MFT performance benchmark for drive {}", drive);
    
    // Test different caching strategies
    let mut results = HashMap::new();
    
    // Test 1: No cache
    let start = Instant::now();
    let files_no_cache = read_mft_files(drive)?;
    let no_cache_time = start.elapsed();
    results.insert("no_cache", (files_no_cache.len(), no_cache_time));
    
    // Test 2: With optimizations (if available)
    // This would test different FileInfo caching strategies
    
    // Print results
    println!("\n=== MFT Performance Benchmark ===");
    println!("Drive: {}", drive);
    
    for (test_name, (file_count, duration)) in results {
        println!("{}: {} files in {:?} ({:.2} files/sec)", 
                 test_name, file_count, duration, 
                 file_count as f64 / duration.as_secs_f64());
    }
    
    Ok(())
}

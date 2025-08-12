//! MFT cache persistence implementation for saving/loading cache to/from disk

use std::fs::{self, File};
use std::io::{self, BufReader, BufWriter};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{Context, Result};
use bincode::{deserialize_from, serialize_into};
use log::{debug, error, info};
use serde::{Deserialize, Serialize};

use crate::fastsearch_service::mft_cache::{FileEntry, MftCache};

/// Cache metadata for versioning and validation
#[derive(Debug, Serialize, Deserialize)]
struct CacheMetadata {
    version: u32,
    created: u64,
    volume_serial: String,
    file_count: usize,
    total_size: u64,
}

/// Save the MFT cache to disk
pub fn save_cache(cache: &MftCache, cache_dir: &Path) -> Result<()> {
    let start_time = std::time::Instant::now();
    
    // Ensure cache directory exists
    fs::create_dir_all(cache_dir).context("Failed to create cache directory")?;
    
    // Generate cache filename with timestamp
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs();
    
    let cache_file = cache_dir.join(format!("mft_cache_{}.bin", timestamp));
    let meta_file = cache_dir.join(format!("mft_cache_{}.meta", timestamp));
    
    // Create temporary files for atomic writes
    let temp_cache = cache_dir.join(format!(".mft_cache_{}.tmp", timestamp));
    let temp_meta = cache_dir.join(format!(".mft_cache_{}.meta.tmp", timestamp));
    
    // Serialize and save the cache data
    {
        let file = File::create(&temp_cache).context("Failed to create cache file")?;
        let mut writer = BufWriter::new(file);
        
        // Get a read lock on the cache data
        let files = cache.files.read();
        let extension_index = cache.extension_index.read();
        let name_index = cache.name_index.read();
        let path_index = cache.path_index.read();
        
        // Calculate total size
        let total_size = files.values().map(|f| f.size).sum();
        
        // Save metadata
        let metadata = CacheMetadata {
            version: 1,
            created: timestamp,
            volume_serial: cache.drive_letter.to_string(),
            file_count: files.len(),
            total_size,
        };
        
        // Write metadata
        let meta_file = File::create(&temp_meta).context("Failed to create metadata file")?;
        let meta_writer = BufWriter::new(meta_file);
        serialize_into(meta_writer, &metadata).context("Failed to serialize metadata")?;
        
        // Write cache data
        for (id, entry) in files.iter() {
            // Write file ID
            bincode::serialize_into(&mut writer, id).context("Failed to serialize file ID")?;
            // Write entry
            bincode::serialize_into(&mut writer, entry).context("Failed to serialize file entry")?;
        }
        
        // Flush to ensure all data is written
        writer.flush().context("Failed to flush cache data")?;
    }
    
    // Atomically rename temp files to final names
    fs::rename(&temp_cache, &cache_file).context("Failed to rename cache file")?;
    fs::rename(&temp_meta, &meta_file).context("Failed to rename metadata file")?;
    
    // Clean up old cache files (keep last 3)
    cleanup_old_caches(cache_dir, 3)?;
    
    info!(
        "Saved MFT cache with {} files ({} MB) in {:.2?}",
        files.len(),
        total_size / 1024 / 1024,
        start_time.elapsed()
    );
    
    Ok(())
}

/// Load the MFT cache from disk
pub fn load_cache(cache_dir: &Path, drive_letter: char) -> Result<Option<MftCache>> {
    // Find the most recent cache file for this drive
    let cache_files = find_cache_files(cache_dir, drive_letter)?;
    
    if cache_files.is_empty() {
        debug!("No cache files found for drive {}", drive_letter);
        return Ok(None);
    }
    
    let (cache_file, meta_file) = &cache_files[0];
    let start_time = std::time::Instant::now();
    
    // Load metadata
    let meta_reader = BufReader::new(File::open(meta_file).context("Failed to open metadata file")?);
    let metadata: CacheMetadata = deserialize_from(meta_reader).context("Failed to deserialize metadata")?;
    
    // Create a new cache with the same configuration
    let cache = MftCache::with_config(
        drive_letter,
        MftCacheConfig::default(), // Will be updated with saved config
    )?;
    
    // Load cache data
    {
        let mut files = cache.files.write();
        let mut extension_index = cache.extension_index.write();
        let mut name_index = cache.name_index.write();
        let mut path_index = cache.path_index.write();
        
        let reader = BufReader::new(File::open(cache_file).context("Failed to open cache file")?);
        let mut reader = io::BufReader::new(reader);
        
        // Read entries until EOF
        while let Ok(id) = bincode::deserialize_from::<_, u64>(&mut reader) {
            let entry: FileEntry = bincode::deserialize_from(&mut reader)
                .context("Failed to deserialize file entry")?;
                
            // Add to indexes
            files.insert(id, entry);
            
            // Index by extension (if any)
            if let Some(ext) = Path::new(&entry.name).extension() {
                let ext = ext.to_string_lossy().to_lowercase();
                if !ext.is_empty() {
                    extension_index.entry(ext).or_default().push(id);
                }
            }
            
            // Index by name (case-insensitive)
            let name_lower = entry.name.to_lowercase();
            name_index.entry(name_lower).or_default().push(id);
            
            // Index by path
            path_index.insert(entry.path.clone(), id);
        }
    }
    
    info!(
        "Loaded MFT cache with {} files ({} MB) in {:.2?}",
        metadata.file_count,
        metadata.total_size / 1024 / 1024,
        start_time.elapsed()
    );
    
    Ok(Some(cache))
}

/// Find cache files for a specific drive, sorted by creation time (newest first)
fn find_cache_files(cache_dir: &Path, drive_letter: char) -> Result<Vec<(PathBuf, PathBuf)>> {
    let mut cache_files = Vec::new();
    
    for entry in fs::read_dir(cache_dir).context("Failed to read cache directory")? {
        let entry = entry.context("Failed to read cache directory entry")?;
        let path = entry.path();
        
        if let Some(ext) = path.extension() {
            if ext == "meta" {
                if let Some(stem) = path.file_stem() {
                    let cache_path = path.with_extension("");
                    if cache_path.exists() {
                        // Extract timestamp from filename
                        if let Some(timestamp) = stem.to_string_lossy()
                            .strip_prefix("mft_cache_")
                            .and_then(|s| s.strip_suffix(".meta"))
                            .and_then(|s| s.parse::<u64>().ok())
                        {
                            cache_files.push((cache_path, path, timestamp));
                        }
                    }
                }
            }
        }
    }
    
    // Sort by timestamp (newest first)
    cache_files.sort_by_key(|&(_, _, ts)| std::cmp::Reverse(ts));
    
    // Filter by drive letter and convert to (cache_path, meta_path)
    let result = cache_files
        .into_iter()
        .filter_map(|(cache_path, meta_path, _)| {
            // TODO: Verify drive letter matches
            Some((cache_path, meta_path))
        })
        .collect();
    
    Ok(result)
}

/// Clean up old cache files, keeping only the N most recent
fn cleanup_old_caches(cache_dir: &Path, keep: usize) -> Result<()> {
    // Find all cache files
    let mut cache_files = Vec::new();
    
    for entry in fs::read_dir(cache_dir).context("Failed to read cache directory")? {
        let entry = entry.context("Failed to read cache directory entry")?;
        let path = entry.path();
        
        if let Some(ext) = path.extension() {
            if ext == "meta" {
                if let Some(stem) = path.file_stem() {
                    let cache_path = path.with_extension("");
                    if cache_path.exists() {
                        // Extract timestamp from filename
                        if let Some(timestamp) = stem.to_string_lossy()
                            .strip_prefix("mft_cache_")
                            .and_then(|s| s.strip_suffix(".meta"))
                            .and_then(|s| s.parse::<u64>().ok())
                        {
                            cache_files.push((cache_path, path, timestamp));
                        }
                    }
                }
            }
        }
    }
    
    // Sort by timestamp (oldest first)
    cache_files.sort_by_key(|&(_, _, ts)| ts);
    
    // Calculate how many files to remove
    let num_to_remove = cache_files.len().saturating_sub(keep);
    
    // Take only the files we want to remove
    let files_to_remove: Vec<_> = cache_files.into_iter().take(num_to_remove).collect();
    
    // Remove the old cache files
    for (cache_path, meta_path, _) in files_to_remove {
        if let Err(e) = fs::remove_file(&cache_path) {
            error!("Failed to remove old cache file {}: {}", cache_path.display(), e);
        }
        if let Err(e) = fs::remove_file(&meta_path) {
            error!("Failed to remove old metadata file {}: {}", meta_path.display(), e);
        }
    }
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    
    #[test]
    fn test_cache_persistence() {
        // Create a temporary directory for testing
        let temp_dir = tempdir().unwrap();
        let cache_dir = temp_dir.path();
        
        // Create a test cache
        let mut cache = MftCache::new('C').unwrap();
        
        // Add some test data
        // ...
        
        // Save the cache
        save_cache(&cache, cache_dir).unwrap();
        
        // Load the cache
        let loaded_cache = load_cache(cache_dir, 'C').unwrap().unwrap();
        
        // Verify the loaded cache matches the original
        // ...
    }
}

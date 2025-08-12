//! Unit and integration tests for the MFT cache

use super::mft_cache::{FileEntry, MftCache, MftCacheConfig};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::{Duration, SystemTime};
use tempfile::tempdir;

#[test]
fn test_file_entry_size() {
    // Test that FileEntry size is reasonable
    use std::mem::size_of;
    
    // This is a sanity check to catch unexpected size increases
    // Adjust these values if the struct changes intentionally
    const EXPECTED_SIZE: usize = 120; // Approximate expected size in bytes
    const TOLERANCE: usize = 32; // Allow some variance for different platforms
    
    let actual_size = size_of::<FileEntry>();
    assert!(
        actual_size <= EXPECTED_SIZE + TOLERANCE,
        "FileEntry size ({}) is larger than expected (expected ~{} ± {} bytes)",
        actual_size,
        EXPECTED_SIZE,
        TOLERANCE
    );
}

#[test]
fn test_cache_config_defaults() {
    let config = MftCacheConfig::default();
    
    // Verify default values
    assert!(config.parallel_processing);
    assert!(config.persistence_enabled);
    assert!(config.max_memory_usage > 0.0);
    assert!(config.max_memory_usage <= 1.0);
    assert!(config.num_threads > 0);
    assert!(config.save_interval_secs > 0);
    assert!(config.max_cache_versions > 0);
}

#[test]
fn test_cache_creation() {
    // Test creating a cache with default config
    let cache = MftCache::with_config('C', MftCacheConfig::default());
    assert!(cache.is_ok());
    
    let cache = cache.unwrap();
    assert_eq!(cache.drive_letter(), 'C');
    assert!(cache.is_empty());
    assert_eq!(cache.len(), 0);
    assert_eq!(cache.size_in_bytes(), 0);
    
    // Test stats
    let stats = cache.stats();
    assert_eq!(stats.file_count, 0);
    assert_eq!(stats.files_processed, 0);
    assert_eq!(stats.memory_usage_bytes, 0);
    assert_eq!(stats.drive_letter, 'C');
}

#[test]
fn test_cache_clear() {
    let cache = MftCache::with_config('C', MftCacheConfig::default())
        .expect("Failed to create cache");
    
    // Add some dummy data
    {
        let mut files = cache.files.write();
        files.insert(1, FileEntry {
            id: 1,
            name: "test.txt".to_string(),
            path: "C:\\test.txt".to_string(),
            size: 1024,
            created: SystemTime::now(),
            modified: SystemTime::now(),
            is_directory: false,
            attributes: 0,
        });
    }
    
    assert!(!cache.is_empty());
    
    // Clear the cache
    cache.clear().expect("Failed to clear cache");
    
    // Verify it's empty
    assert!(cache.is_empty());
    assert_eq!(cache.len(), 0);
    assert_eq!(cache.size_in_bytes(), 0);
}

#[test]
fn test_cache_persistence() {
    // Create a temporary directory for testing
    let temp_dir = tempdir().expect("Failed to create temp dir");
    
    // Configure cache with persistence to temp dir
    let mut config = MftCacheConfig::default()
        .with_cache_dir(temp_dir.path())
        .with_save_interval(1); // 1 second for testing
    
    // Create and populate a cache
    let cache = MftCache::with_config('C', config.clone())
        .expect("Failed to create cache");
    
    // Add some test data
    {
        let mut files = cache.files.write();
        files.insert(1, FileEntry {
            id: 1,
            name: "test.txt".to_string(),
            path: "C:\\test.txt".to_string(),
            size: 1024,
            created: SystemTime::now(),
            modified: SystemTime::now(),
            is_directory: false,
            attributes: 0,
        });
    }
    
    // Save to disk
    cache.save_to_disk().expect("Failed to save cache");
    
    // Create a new cache that should load from disk
    let loaded_cache = MftCache::with_config('C', config)
        .expect("Failed to create cache with loading from disk");
    
    // Verify the data was loaded
    assert!(!loaded_cache.is_empty());
    assert_eq!(loaded_cache.len(), 1);
    
    // Clean up
    drop(temp_dir);
}

#[test]
fn test_cache_rebuild() {
    // Create a cache with a very low memory limit to test memory checking
    let config = MftCacheConfig::default()
        .with_memory_usage(0.0001) // Very low memory limit
        .unwrap();
    
    let cache = MftCache::with_config('C', config)
        .expect("Failed to create cache");
    
    // Rebuild should handle memory limits gracefully
    let result = cache.rebuild();
    
    // Rebuild might fail due to memory constraints, but shouldn't panic
    if let Err(e) = result {
        assert!(e.to_string().contains("memory"));
    }
}

#[test]
fn test_cache_thread_safety() {
    // Test that the cache can be safely accessed from multiple threads
    use std::sync::mpsc;
    use std::thread;
    
    let cache = Arc::new(
        MftCache::with_config('C', MftCacheConfig::default())
            .expect("Failed to create cache")
    );
    
    let (tx, rx) = mpsc::channel();
    let num_threads = 4;
    
    // Spawn multiple threads that access the cache
    for i in 0..num_threads {
        let cache = cache.clone();
        let tx = tx.clone();
        
        thread::spawn(move || {
            // Each thread adds a file
            let file_id = i as u64 + 1;
            let file_name = format!("test{}.txt", i);
            let file_path = format!("C:\\{}", file_name);
            
            {
                let mut files = cache.files.write();
                files.insert(file_id, FileEntry {
                    id: file_id,
                    name: file_name,
                    path: file_path,
                    size: 1024,
                    created: SystemTime::now(),
                    modified: SystemTime::now(),
                    is_directory: false,
                    attributes: 0,
                });
            }
            
            // Signal completion
            tx.send(()).unwrap();
        });
    }
    
    // Wait for all threads to complete
    for _ in 0..num_threads {
        rx.recv_timeout(Duration::from_secs(5))
            .expect("Thread did not complete in time");
    }
    
    // Verify all files were added
    assert_eq!(cache.len() as usize, num_threads);
}

#[test]
fn test_cache_stats() {
    let cache = MftCache::with_config('C', MftCacheConfig::default())
        .expect("Failed to create cache");
    
    // Add some test data
    {
        let mut files = cache.files.write();
        
        // Add a file
        files.insert(1, FileEntry {
            id: 1,
            name: "test1.txt".to_string(),
            path: "C:\\test1.txt".to_string(),
            size: 1024,
            created: SystemTime::now(),
            modified: SystemTime::now(),
            is_directory: false,
            attributes: 0,
        });
        
        // Add a directory
        files.insert(2, FileEntry {
            id: 2,
            name: "test_dir".to_string(),
            path: "C:\\test_dir".to_string(),
            size: 0,
            created: SystemTime::now(),
            modified: SystemTime::now(),
            is_directory: true,
            attributes: 0x10, // DIRECTORY attribute
        });
    }
    
    // Update files_processed counter
    cache.files_processed.store(2, std::sync::atomic::Ordering::Relaxed);
    
    // Get stats
    let stats = cache.stats();
    
    // Verify stats
    assert_eq!(stats.file_count, 2);
    assert_eq!(stats.files_processed, 2);
    assert!(stats.memory_usage_bytes > 0);
    assert_eq!(stats.drive_letter, 'C');
    
    // Test Display implementation
    let stats_str = format!("{}", stats);
    assert!(stats_str.contains("MFT Cache Statistics"));
    assert!(stats_str.contains("Files:           2"));
    assert!(stats_str.contains("Files Processed: 2"));
    assert!(stats_str.contains("Memory Usage:"));
    assert!(stats_str.contains("Last Updated:"));
}

// Note: Benchmarks are only compiled when the "bench" feature is enabled
#[cfg(feature = "bench")]
mod benches {
    use super::*;
    use test::Bencher;
    
    #[bench]
    fn bench_cache_insert(b: &mut Bencher) {
        let cache = Arc::new(
            MftCache::with_config('C', MftCacheConfig::default())
                .expect("Failed to create cache")
        );
        
        let mut id = 0;
        
        b.iter(|| {
            id += 1;
            let file_id = id as u64;
            let file_name = format!("test{}.txt", id);
            let file_path = format!("C:\\{}", file_name);
            
            cache.files.write().insert(file_id, FileEntry {
                id: file_id,
                name: file_name,
                path: file_path,
                size: 1024,
                created: SystemTime::now(),
                modified: SystemTime::now(),
                is_directory: false,
                attributes: 0,
            });
        });
    }
    
    #[bench]
    fn bench_cache_lookup(b: &mut Bencher) {
        let cache = Arc::new(
            MftCache::with_config('C', MftCacheConfig::default())
                .expect("Failed to create cache")
        );
        
        // Pre-populate the cache
        const NUM_FILES: u64 = 10_000;
        
        for i in 0..NUM_FILES {
            let file_name = format!("test{}.txt", i);
            let file_path = format!("C:\\{}", file_name);
            
            cache.files.write().insert(i, FileEntry {
                id: i,
                name: file_name,
                path: file_path,
                size: 1024,
                created: SystemTime::now(),
                modified: SystemTime::now(),
                is_directory: false,
                attributes: 0,
            });
        }
        
        // Benchmark lookups
        let mut i = 0;
        b.iter(|| {
            i = (i + 1) % NUM_FILES;
            let files = cache.files.read();
            test::black_box(files.get(&i).is_some());
        });
    }
}

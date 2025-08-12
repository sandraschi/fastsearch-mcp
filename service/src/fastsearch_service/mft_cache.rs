//! High-performance MFT cache with parallel processing and memory management

use std::collections::{HashMap, HashSet};
use std::path::{Path, PathBuf};
#[cfg(windows)]
use std::os::windows::ffi::OsStrExt;
use std::sync::atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime};
use std::thread;
use std::sync::atomic::AtomicBool as StdAtomicBool;
use std::sync::atomic::AtomicI64;

use anyhow::{anyhow, Context, Result};
use log::{debug, error, info, warn};
use ntfs::Ntfs;
use parking_lot::RwLock;
use rayon::prelude::*;
use systemstat::{Platform, System};
use winapi::um::fileapi::CreateFileW;
use winapi::um::winbase::{FILE_FLAG_NO_BUFFERING, FILE_FLAG_RANDOM_ACCESS};
use winapi::um::winnt::{FILE_SHARE_READ, FILE_SHARE_WRITE, GENERIC_READ, INVALID_HANDLE_VALUE};

/// Default maximum number of files to process before checking memory usage
const DEFAULT_MAX_FILES_BEFORE_MEMCHECK: usize = 100_000;
/// Target memory usage percentage (0.8 = 80%)
const TARGET_MEMORY_USAGE: f32 = 0.8;

/// Configuration for MFT cache
#[derive(Debug, Clone)]
pub struct MftCacheConfig {
    // Memory and processing settings
    /// Maximum number of files to process before checking memory
    pub max_files_before_memcheck: usize,
    /// Maximum percentage of system memory to use (0.0 to 1.0)
    pub max_memory_usage: f32,
    /// Whether to use parallel processing
    pub parallel_processing: bool,
    /// Number of threads to use for parallel processing (0 = auto)
    pub num_threads: usize,
    
    // Persistence settings
    /// Whether to enable cache persistence
    pub persistence_enabled: bool,
    /// Directory to store cache files
    pub cache_dir: PathBuf,
    /// How often to save the cache (in seconds, 0 = disable auto-save)
    pub save_interval_secs: u64,
    /// Maximum number of cache versions to keep
    pub max_cache_versions: usize,
}

impl MftCacheConfig {
    /// Create a new configuration with default values
    pub fn new() -> Self {
        Self::default()
    }
    
    /// Create a configuration with auto-detected system resources
    pub fn auto() -> Result<Self> {
        let mut config = Self::default();
        
        // Auto-detect number of threads (leaving one core free for the system)
        let num_cores = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(1);
        config.num_threads = num_cores.saturating_sub(1).max(1);
        
        // Auto-detect available memory and set limits
        if let Ok(mem) = System::new().memory() {
            let total_mem = mem.total.as_u64() as f64;
            let target_mem = (total_mem * config.max_memory_usage as f64) as u64;
            
            // Estimate memory usage per file (adjust based on your needs)
            const BYTES_PER_FILE: u64 = 1024; // Conservative estimate
            let max_files = target_mem / BYTES_PER_FILE;
            
            config.max_files_before_memcheck = max_files.min(usize::MAX as u64) as usize;
        }
        
        Ok(config)
    }
    
    /// Set the maximum memory usage percentage (0.0 to 1.0)
    pub fn with_memory_usage(mut self, usage: f32) -> Result<Self> {
        if !(0.0..=1.0).contains(&usage) {
            return Err(anyhow!("Memory usage must be between 0.0 and 1.0"));
        }
        self.max_memory_usage = usage;
        Ok(self)
    }
    
    /// Set the number of threads to use for parallel processing (0 = auto)
    pub fn with_threads(mut self, num_threads: usize) -> Self {
        self.num_threads = num_threads;
        self
    }
    
    /// Enable or disable parallel processing
    pub fn with_parallel_processing(mut self, enabled: bool) -> Self {
        self.parallel_processing = enabled;
        self
    }
    
    /// Set the directory for cache persistence
    pub fn with_cache_dir<P: AsRef<Path>>(mut self, dir: P) -> Self {
        self.cache_dir = dir.as_ref().to_path_buf();
        self
    }
    
    /// Enable or disable cache persistence
    pub fn with_persistence(mut self, enabled: bool) -> Self {
        self.persistence_enabled = enabled;
        self
    }
    
    /// Set the interval for auto-saving the cache (in seconds, 0 = disable)
    pub fn with_save_interval(mut self, seconds: u64) -> Self {
        self.save_interval_secs = seconds;
        self
    }
    
    /// Set the maximum number of cache versions to keep
    pub fn with_max_versions(mut self, max_versions: usize) -> Self {
        self.max_cache_versions = max_versions;
        self
    }
}

impl Default for MftCacheConfig {
    fn default() -> Self {
        let num_threads = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(1);
            
        // Default cache directory: %LOCALAPPDATA%\FastSearchMCP\cache
        let cache_dir = dirs::cache_dir()
            .unwrap_or_else(|| std::env::temp_dir().join("FastSearchMCP"))
            .join("cache");
            
        Self {
            // Memory and processing settings
            max_files_before_memcheck: DEFAULT_MAX_FILES_BEFORE_MEMCHECK,
            max_memory_usage: TARGET_MEMORY_USAGE,
            parallel_processing: true,
            num_threads,
            
            // Persistence settings
            persistence_enabled: true,
            cache_dir,
            save_interval_secs: 300, // 5 minutes
            max_cache_versions: 3,
        }
    }
}

/// In-memory MFT cache for fast file searches
#[derive(Debug)]
pub struct MftCache {
    // Core data structures
    files: RwLock<HashMap<u64, FileEntry>>,
    extension_index: RwLock<HashMap<String, Vec<u64>>>,
    name_index: RwLock<HashMap<String, Vec<u64>>>,
    path_index: RwLock<HashMap<String, u64>>,
    
    // Metadata
    last_update: RwLock<SystemTime>,
    drive_letter: char,
    config: MftCacheConfig,
    
    // Statistics and tracking
    memory_usage: AtomicU64,
    files_processed: AtomicUsize,
    
    // Persistence
    save_thread_handle: parking_lot::Mutex<Option<std::thread::JoinHandle<()>>>,
    shutdown_flag: Arc<StdAtomicBool>,
    
    // USN Journal monitoring
    usn_monitor: parking_lot::Mutex<Option<crate::fastsearch_service::usn_journal::UsnJournalMonitor>>,
    volume_handle: parking_lot::Mutex<Option<winapi::um::winnt::HANDLE>>,
}

/// Statistics about the MFT cache
#[derive(Debug, Clone)]
pub struct CacheStats {
    /// Number of files in the cache
    pub file_count: usize,
    /// Total number of files processed (may be different from file_count if some files were filtered)
    pub files_processed: usize,
    /// Total memory usage in bytes
    pub memory_usage_bytes: u64,
    /// When the cache was last updated
    pub last_update: SystemTime,
    /// The drive letter this cache is for
    pub drive_letter: char,
    /// The last USN (Update Sequence Number) processed
    pub last_processed_usn: i64,
}

impl std::fmt::Display for CacheStats {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let memory_mb = self.memory_usage_bytes as f64 / (1024.0 * 1024.0);
        let last_update = humantime::format_rfc3339_seconds(self.last_update);
        
        write!(
            f,
            "MFT Cache Statistics ({}:)\
            \n  Files:           {}\
            \n  Files Processed: {}\
            \n  Memory Usage:    {:.2} MB\
            \n  Last Updated:    {}",
            self.drive_letter,
            self.file_count,
            self.files_processed,
            memory_mb,
            last_update
        )
    }
}

/// Represents a file entry in the MFT cache
#[derive(Debug, Clone)]
pub struct FileEntry {
    pub id: u64,
    pub name: String,
    pub path: String,
    pub size: u64,
    pub is_directory: bool,
    pub extension: Option<String>,
}

impl MftCache {
    /// Create a new MFT cache for the specified drive with default config
    pub fn new(drive_letter: char) -> Result<Self> {
        Self::with_config(drive_letter, MftCacheConfig::default())
    }
    
    /// Create a new MFT cache with custom configuration
    pub fn with_config(drive_letter: char, config: MftCacheConfig) -> Result<Self> {
        // Ensure cache directory exists if persistence is enabled
        if config.persistence_enabled {
            if let Err(e) = std::fs::create_dir_all(&config.cache_dir) {
                error!("Failed to create cache directory: {}", e);
                // Continue without persistence
            }
        }
        
        let shutdown_flag = Arc::new(StdAtomicBool::new(false));
        
        let mut cache = Self {
            // Core data structures
            files: Default::default(),
            extension_index: Default::default(),
            name_index: Default::default(),
            path_index: Default::default(),
            
            // Metadata
            last_update: RwLock::new(SystemTime::now()),
            drive_letter: drive_letter.to_ascii_uppercase(),
            config,
            
            // Statistics and tracking
            memory_usage: AtomicU64::new(0),
            files_processed: AtomicUsize::new(0),
            
            // Persistence
            save_thread_handle: parking_lot::Mutex::new(None),
            shutdown_flag: shutdown_flag.clone(),
            
            // USN Journal monitoring
            usn_monitor: parking_lot::Mutex::new(None),
            volume_handle: parking_lot::Mutex::new(None),
        };
        
        // Initialize Rayon thread pool if parallel processing is enabled
        if cache.config.parallel_processing && cache.config.num_threads > 0 {
            rayon::ThreadPoolBuilder::new()
                .num_threads(cache.config.num_threads)
                .build_global()
                .context("Failed to initialize Rayon thread pool")?;
        }
        
        // Try to load from cache if persistence is enabled
        let mut loaded_from_cache = false;
        if cache.config.persistence_enabled {
            if let Some(loaded_cache) = cache.load_from_disk()? {
                // Use the loaded cache instead of rebuilding
                *cache = loaded_cache;
                loaded_from_cache = true;
                info!("Successfully loaded MFT cache from disk");
            }
        }
        
        // Rebuild if not loaded from cache
        if !loaded_from_cache {
            cache.rebuild()?;
        }
        
        // Start auto-save thread if enabled
        if cache.config.persistence_enabled && cache.config.save_interval_secs > 0 {
            cache.start_auto_save()?;
        }
        
        Ok(cache)
    }
    
    /// Load the cache from disk if available
    fn load_from_disk(&self) -> Result<Option<Self>> {
        use crate::fastsearch_service::cache_persistence::load_cache;
        
        match load_cache(&self.config.cache_dir, self.drive_letter) {
            Ok(Some(mut cache)) => {
                // Update the configuration to match the current one
                cache.config = self.config.clone();
                
                // Update timestamps
                *cache.last_update.write() = SystemTime::now();
                
                // Reinitialize persistence
                cache.shutdown_flag = Arc::new(StdAtomicBool::new(false));
                
                // Start auto-save if needed
                if cache.config.persistence_enabled && cache.config.save_interval_secs > 0 {
                    cache.start_auto_save()?;
                }
                
                Ok(Some(cache))
            }
            Ok(None) => Ok(None),
            Err(e) => {
                error!("Failed to load cache from disk: {}", e);
                Ok(None)
            }
        }
    }
    
    /// Start the auto-save thread
    fn start_auto_save(&self) -> Result<()> {
        if self.config.save_interval_secs == 0 {
            return Ok(());
        }
        
        let cache_dir = self.config.cache_dir.clone();
        let save_interval = Duration::from_secs(self.config.save_interval_secs);
        let shutdown_flag = self.shutdown_flag.clone();
        
        // Create a new Arc<Self> for the thread
        let cache_arc = Arc::new(self.clone());
        
        let handle = std::thread::spawn(move || {
            while !shutdown_flag.load(Ordering::SeqCst) {
                std::thread::sleep(save_interval);
                
                if let Err(e) = cache_arc.save_to_disk() {
                    error!("Error in auto-save thread: {}", e);
                }
            }
        });
        
        // Store the thread handle
        *self.save_thread_handle.lock() = Some(handle);
        
        Ok(())
    }
    
    /// Save the cache to disk
    pub fn save_to_disk(&self) -> Result<()> {
        use crate::fastsearch_service::cache_persistence::save_cache;
        
        if !self.config.persistence_enabled {
            return Ok(());
        }
        
        save_cache(self, &self.config.cache_dir)
            .context("Failed to save cache to disk")
    }
    
    /// Clear the cache and rebuild it from scratch
    pub fn rebuild(&self) -> Result<()> {
        info!("Rebuilding MFT cache for drive {}:", self.drive_letter);
        
        // Clear existing data
        self.clear()?;
        
        // Rebuild the cache
        self.rebuild_internal()?;
        
        // Update the last update time
        *self.last_update.write() = SystemTime::now();
        
        // Save to disk if persistence is enabled
        if self.config.persistence_enabled {
            self.save_to_disk()?;
        }
        
        Ok(())
    }
    
    /// Internal method to rebuild the cache from the MFT
    fn rebuild_internal(&self) -> Result<()> {
        let volume_path = format!(r"\\.\{}:", self.drive_letter);
        info!("Rebuilding MFT cache from volume: {}", volume_path);
        
        // Open the volume with direct access to the MFT
        let volume_handle = unsafe {
            CreateFileW(
                wide_string(&volume_path).as_ptr(),
                winapi::um::winnt::GENERIC_READ,
                winapi::um::winnt::FILE_SHARE_READ | winapi::um::winnt::FILE_SHARE_WRITE,
                std::ptr::null_mut(),
                winapi::um::fileapi::OPEN_EXISTING,
                winapi::um::winbase::FILE_FLAG_BACKUP_SEMANTICS,
                std::ptr::null_mut(),
            )
        };
        
        if volume_handle == winapi::um::handleapi::INVALID_HANDLE_VALUE {
            return Err(std::io::Error::last_os_error())
                .with_context(|| format!("Failed to open volume {} (admin rights required)", volume_path));
        }
        
        // Read MFT into memory
        let mft_data = self.read_mft(volume_handle)?;
        
        // Parse MFT and build indexes
        let mft_data_slice = &mft_data[..];
        let mut cursor = std::io::Cursor::new(mft_data_slice);
        let ntfs = Ntfs::new(&mut cursor).context("Failed to parse NTFS")?;
        let root = ntfs.root_directory(&mut cursor).context("Failed to get root directory")?;
        
        // Use parallel or sequential processing based on config
        if self.config.parallel_processing {
            self.rebuild_parallel(&ntfs, &root)?;
        } else {
            self.rebuild_sequential(&ntfs, &root)?;
        }
        
        info!(
            "MFT cache rebuilt with {} files in {:.2?}",
            self.files.read().len(),
            self.last_update.read().elapsed()?
        );
        
        Ok(())
    }
    
    /// Clear all data from the cache
    pub fn clear(&self) -> Result<()> {
        info!("Clearing MFT cache for drive {}", self.drive_letter);
        
        // Clear all data structures
        self.files.write().clear();
        self.extension_index.write().clear();
        self.name_index.write().clear();
        self.path_index.write().clear();
        
        // Reset statistics
        self.memory_usage.store(0, Ordering::Relaxed);
        self.files_processed.store(0, Ordering::Relaxed);
        
        // Update the last update time
        *self.last_update.write() = SystemTime::now();
        
        Ok(())
    }
    
    /// Get cache statistics
    pub fn stats(&self) -> CacheStats {
        let files = self.files.read();
        let last_update = *self.last_update.read();
        let files_processed = self.files_processed.load(Ordering::Relaxed);
        let memory_usage = self.memory_usage.load(Ordering::Relaxed);
        
        CacheStats {
            file_count: files.len(),
            files_processed,
            memory_usage_bytes: memory_usage,
            last_update,
            drive_letter: self.drive_letter,
            last_processed_usn: 0, // TODO: Track last processed USN
        }
    }
    
    /// Get the last time the cache was updated
    pub fn last_update(&self) -> SystemTime {
        *self.last_update.read()
    }
    
    /// Get the drive letter this cache is for
    pub fn drive_letter(&self) -> char {
        self.drive_letter
    }
    
    /// Get a reference to the cache configuration
    pub fn config(&self) -> &MftCacheConfig {
        &self.config
    }
    
    /// Get a read lock on the files map
    pub fn get_files(&self) -> RwLockReadGuard<'_, HashMap<u64, FileEntry>> {
        self.files.read()
    }
    
    /// Get a read lock on the path index
    pub fn get_path_index(&self) -> RwLockReadGuard<'_, HashMap<String, u64>> {
        self.path_index.read()
    }
    
    /// Start monitoring the filesystem for changes using USN Journal
    pub fn start_monitoring(&self) -> Result<()> {
        use winapi::um::fileapi::CreateFileW;
        use winapi::um::winnt::GENERIC_READ;
        use winapi::um::winnt::FILE_SHARE_READ;
        use winapi::um::winnt::FILE_SHARE_WRITE;
        use winapi::um::winnt::OPEN_EXISTING;
        use winapi::um::winnt::FILE_FLAG_BACKUP_SEMANTICS;
        use std::os::windows::prelude::*;
        
        // Check if already monitoring
        if self.usn_monitor.lock().is_some() {
            return Ok(());
        }
        
        // Open the volume handle if not already open
        let volume_path = format!(r"\\.\{}:", self.drive_letter);
        let volume_wide: Vec<u16> = volume_path.encode_utf16().chain(std::iter::once(0)).collect();
        
        let handle = unsafe {
            CreateFileW(
                volume_wide.as_ptr(),
                GENERIC_READ,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                std::ptr::null_mut(),
                OPEN_EXISTING,
                FILE_FLAG_BACKUP_SEMANTICS,
                std::ptr::null_mut(),
            )
        };
        
        if handle.is_null() {
            return Err(std::io::Error::last_os_error())
                .context("Failed to open volume handle for USN Journal monitoring");
        }
        
        // Store the volume handle
        *self.volume_handle.lock() = Some(handle);
        
        // Create and start the USN Journal monitor
        let mut usn_monitor = crate::fastsearch_service::usn_journal::UsnJournalMonitor::new(
            self.drive_letter,
            handle,
        )?;
        
        // Clone self for the callback
        let cache = self.clone();
        
        // Start monitoring with a callback to update the cache
        usn_monitor.start(move || {
            if let Err(e) = cache.handle_filesystem_changes() {
                error!("Error handling filesystem changes: {}", e);
            }
        })?;
        
        *self.usn_monitor.lock() = Some(usn_monitor);
        info!("Started USN Journal monitoring for drive {}", self.drive_letter);
        
        Ok(())
    }
    
    /// Stop monitoring the filesystem for changes
    pub fn stop_monitoring(&self) -> Result<()> {
        // Stop the USN Journal monitor if running
        if let Some(mut monitor) = self.usn_monitor.lock().take() {
            monitor.stop()?;
            info!("Stopped USN Journal monitoring for drive {}", self.drive_letter);
        }
        
        // Close the volume handle if open
        if let Some(handle) = self.volume_handle.lock().take() {
            if !handle.is_null() {
                unsafe { winapi::um::handleapi::CloseHandle(handle); }
            }
        }
        
        Ok(())
    }
    
    /// Handle filesystem changes detected by the USN Journal
    fn handle_filesystem_changes(&self) -> Result<()> {
        info!("Handling filesystem changes for drive {}", self.drive_letter);
        
        // For now, we'll just rebuild the entire cache when changes are detected
        // In a production system, you'd want to be more granular and only update what changed
        self.rebuild()?;
        
        Ok(())
    }
    
    /// Read the MFT (Master File Table) from the specified volume handle
    fn read_mft(&self, volume_handle: winapi::um::winnt::HANDLE) -> Result<Vec<u8>> {
        use std::os::windows::io::AsRawHandle;
        use winapi::um::fileapi::ReadFile;
        use winapi::um::winbase::DeviceIoControl;
        use winapi::um::winioctl::FSCTL_GET_NTFS_VOLUME_DATA;
        use winapi::um::winioctl::NTFS_VOLUME_DATA_BUFFER;
        use winapi::um::winnt::LARGE_INTEGER;
        use winapi::um::minwinbase::OVERLAPPED;
        
        // Get volume data to determine MFT size and location
        let mut volume_data: NTFS_VOLUME_DATA_BUFFER = unsafe { std::mem::zeroed() };
        let mut bytes_returned = 0;
        
        let result = unsafe {
            DeviceIoControl(
                volume_handle,
                FSCTL_GET_NTFS_VOLUME_DATA,
                std::ptr::null_mut(),
                0,
                &mut volume_data as *mut _ as *mut _,
                std::mem::size_of::<NTFS_VOLUME_DATA_BUFFER>() as u32,
                &mut bytes_returned,
                std::ptr::null_mut(),
            )
        };
        
        if result == 0 {
            return Err(std::io::Error::last_os_error())
                .context("Failed to get NTFS volume data");
        }
        
        // Calculate MFT size in bytes
        let mft_size = unsafe {
            let clusters = volume_data.MftValidDataLength.QuadPart as u64;
            let bytes_per_cluster = volume_data.BytesPerCluster as u64;
            clusters * bytes_per_cluster
        };
        
        // Allocate buffer for MFT
        let mut buffer = vec![0u8; mft_size as usize];
        
        // Read the MFT
        let mut bytes_read = 0;
        let result = unsafe {
            ReadFile(
                volume_handle,
                buffer.as_mut_ptr() as *mut _,
                buffer.len() as u32,
                &mut bytes_read,
                std::ptr::null_mut(),
            )
        };
        
        if result == 0 {
            return Err(std::io::Error::last_os_error())
                .context("Failed to read MFT data");
        }
        
        info!("Successfully read {} bytes of MFT data", bytes_read);
        Ok(buffer)
    }
    
    /// Check if we've exceeded memory limits
    fn check_memory_limits(&self) -> Result<()> {
        // Only check memory every N files to avoid overhead
        let files_processed = self.files_processed.fetch_add(1, Ordering::Relaxed);
        if files_processed % self.config.max_files_before_memcheck != 0 {
            return Ok(());
        }
        
        // Get system memory information
        let sys = System::new_all();
        
        // Get memory usage using the global memory info
        let memory = sys.global_memory_info();
        
        // Calculate memory usage using the underlying u64 values
        let total_memory = memory.total();
        let free_memory = memory.free();
        let used_memory = total_memory - free_memory;
        
        // Calculate memory usage percentage
        let memory_usage_percent = used_memory as f64 / total_memory as f64 * 100.0;
        
        // Check if we're approaching memory limits
        if memory_usage_percent > (self.config.max_memory_usage * 100.0) as f64 {
            warn!(
                "Memory usage high: {:.1}% ({} MB used of {} MB total)",
                memory_usage_percent,
                used_memory / 1024 / 1024,
                total_memory / 1024 / 1024,
            );
                
            // If we're over the limit, clear some memory
            if memory_usage_percent > (self.config.max_memory_usage * 1.1 * 100.0) as f64 {
                warn!("Memory usage over limit, clearing cache");
                self.clear()?;
            }
        }
        
        Ok(())
    }
    
    /// Rebuild the entire cache from the MFT
    pub fn rebuild(&self) -> Result<()> {
        let start_time = Instant::now();
        let volume_path = format!(r"\\.\{}:", self.drive_letter);
        info!(
            "Rebuilding MFT cache for volume: {} (parallel: {}, threads: {})",
            volume_path, self.config.parallel_processing, self.config.num_threads
        );
        
        // Reset counters
        self.memory_usage.store(0, Ordering::Relaxed);
        self.files_processed.store(0, Ordering::Relaxed);
        
        // Open the volume with direct access to the MFT
        let mft_handle = unsafe {
            CreateFileW(
                Self::wide_string(&volume_path).as_ptr(),
                GENERIC_READ,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                std::ptr::null_mut(),
                winapi::um::fileapi::OPEN_EXISTING,
                FILE_FLAG_NO_BUFFERING | FILE_FLAG_RANDOM_ACCESS,
                std::ptr::null_mut(),
            )
        };
        
        if mft_handle == INVALID_HANDLE_VALUE {
            return Err(std::io::Error::last_os_error())
                .with_context(|| format!("Failed to open volume {} (admin rights required)", volume_path));
        }
        
        // Read MFT into memory
        let mft_data = self.read_mft(mft_handle)?;
        
        // Parse MFT and build indexes
        let mft_data_slice = &mft_data[..];
        let mut cursor = std::io::Cursor::new(mft_data_slice);
        let ntfs = Ntfs::new(&mut cursor).context("Failed to parse NTFS")?;
        let root = ntfs.root_directory(&mut cursor).context("Failed to get root directory")?;
        
        // Use parallel or sequential processing based on config
        if self.config.parallel_processing {
            self.rebuild_parallel(&ntfs, &root)?;
        } else {
            self.rebuild_sequential(&ntfs, &root)?;
        }
        
        info!(
            "MFT cache rebuilt with {} files in {:.2?} (memory: {:.2} MB)",
            self.files.read().len(),
            start_time.elapsed(),
            self.memory_usage.load(Ordering::Relaxed) as f64 / 1024.0 / 1024.0
        );
        
        Ok(())
    }
    
    /// Rebuild cache using parallel processing
    fn rebuild_parallel(&self, ntfs: &Ntfs, root: &ntfs::NtfsFile) -> Result<()> {
        use rayon::prelude::*;
        
        let (tx, rx) = std::sync::mpsc::channel();
        
        // Process directories in parallel
        let mut fs = ntfs.fs();
        let root_dir = match root.directory_index(&mut fs) {
            Ok(index) => index,
            Err(e) => return Err(e).context("Failed to get root directory index"),
        };
        
        // Process top-level directories in parallel
        
    // Check if we're approaching memory limits
    if memory_usage_percent > (self.config.max_memory_usage * 100.0) as f64 {
        warn!(
            "Memory usage high: {:.1}% ({} MB used of {} MB total)",
            memory_usage_percent,
            used_memory / 1024 / 1024,
            total_memory / 1024 / 1024,
        );
            
        // If we're over the limit, clear some memory
        if memory_usage_percent > (self.config.max_memory_usage * 1.1 * 100.0) as f64 {
            warn!("Memory usage over limit, clearing cache");
            self.clear()?;
        }
    }
        
    Ok(())
}
        
/// Rebuild the entire cache from the MFT
pub fn rebuild(&self) -> Result<()> {
    let start_time = Instant::now();
    let volume_path = format!(r"\\.\{}:", self.drive_letter);
    info!(
        "Rebuilding MFT cache for volume: {} (parallel: {}, threads: {})",
        volume_path, self.config.parallel_processing, self.config.num_threads
    );
        
    // Reset counters
    self.memory_usage.store(0, Ordering::Relaxed);
    self.files_processed.store(0, Ordering::Relaxed);
        
    // Open the volume with direct access to the MFT
    let mft_handle = unsafe {
        CreateFileW(
            Self::wide_string(&volume_path).as_ptr(),
            GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            std::ptr::null_mut(),
            winapi::um::fileapi::OPEN_EXISTING,
            FILE_FLAG_NO_BUFFERING | FILE_FLAG_RANDOM_ACCESS,
            std::ptr::null_mut(),
        )
    };
        
    if mft_handle == INVALID_HANDLE_VALUE {
        return Err(std::io::Error::last_os_error())
            .with_context(|| format!("Failed to open volume {} (admin rights required)", volume_path));
    }
        
    // Read MFT into memory
    let mft_data = self.read_mft(mft_handle)?;
        
    // Parse MFT and build indexes
    let mft_data_slice = &mft_data[..];
    let mut cursor = std::io::Cursor::new(mft_data_slice);
    let ntfs = Ntfs::new(&mut cursor).context("Failed to parse NTFS")?;
    let root = ntfs.root_directory(&mut cursor).context("Failed to get root directory")?;
        
    // Use parallel or sequential processing based on config
    if self.config.parallel_processing {
        self.rebuild_parallel(&ntfs, &root)?;
    } else {
        self.rebuild_sequential(&ntfs, &root)?;
    }
        
    info!(
        "MFT cache rebuilt with {} files in {:.2?} (memory: {:.2} MB)",
        self.files.read().len(),
        start_time.elapsed(),
        self.memory_usage.load(Ordering::Relaxed) as f64 / 1024.0 / 1024.0
    );
        
    Ok(())
}
        
/// Rebuild cache using parallel processing
fn rebuild_parallel(&self, ntfs: &Ntfs, root: &ntfs::NtfsFile) -> Result<()> {
    use rayon::prelude::*;
        
    let (tx, rx) = std::sync::mpsc::channel();
        
    // Process directories in parallel
    let mut fs = ntfs.fs();
    let root_dir = match root.directory_index(&mut fs) {
        Ok(index) => index,
        Err(e) => return Err(e).context("Failed to get root directory index"),
    };
        
    // Process top-level directories in parallel
    let mut top_level_dirs = Vec::new();
    let entries = root_dir.entries();
    for entry_result in entries {
        match entry_result {
            Ok(entry) => {
                // Only include directories that aren't special entries
                if entry.file_name().name() != "." && 
                   entry.file_name().name() != ".." &&
                   entry.file_name().is_directory() {
                    top_level_dirs.push(entry);
                }
            }
            Err(e) => {
                warn!("Error reading directory entry: {}", e);
                continue;
            }
        }
    }
        
    // Process directories in parallel
    top_level_dirs.par_iter()
        .try_for_each_with(tx, |sender, entry| {
            let ntfs = ntfs.clone();
            let path = Path::new(""); // Root path for top-level directories
            
            if let Ok(file) = entry.to_file(&ntfs) {
                // Process the directory and its contents
                if let Err(e) = self.process_directory(&ntfs, &file, path, sender) {
                    warn!("Error processing directory: {}", e);
                }
                    if let Err(e) = self.process_directory(
                        &ntfs,
                        &file,
                        &mut fs,
                        &name,
                        &mut files,
                        &mut extension_index,
                        &mut name_index,
                        &mut path_index
                    ) {
                        error!("Error processing directory {}: {}", name, e);
                        return Err(e);
                    }
                    
                    // Send results back to main thread
                    if let Err(e) = sender.send((files, extension_index, name_index, path_index)) {
                        error!("Failed to send directory results: {}", e);
                        return Err(e.into());
                    }
                }
                Ok(())
            })?;
        
        // Merge results from all directories
        let mut all_files = HashMap::new();
        let mut all_extension_index: HashMap<String, Vec<u64>> = HashMap::new();
        let mut all_name_index: HashMap<String, Vec<u64>> = HashMap::new();
        let mut all_path_index: HashMap<String, u64> = HashMap::new();
        
        for (files, ext_idx, name_idx, path_idx) in rx {
            all_files.extend(files);
            
            for (ext, ids) in ext_idx {
                all_extension_index.entry(ext).or_default().extend(ids);
            }
            
            for (name, ids) in name_idx {
                all_name_index.entry(name).or_default().extend(ids);
            }
            
            all_path_index.extend(path_idx);
        }
        
        // Update cache atomically
        *self.files.write() = all_files;
        *self.extension_index.write() = all_extension_index;
        *self.name_index.write() = all_name_index;
        *self.path_index.write() = all_path_index;
        *self.last_update.write() = SystemTime::now();
        
        Ok(())
    }
    
    /// Rebuild cache using sequential processing
    fn rebuild_sequential(&self, ntfs: &Ntfs, root: &ntfs::NtfsFile) -> Result<()> {
        let mut files = HashMap::new();
        let mut extension_index = HashMap::new();
        let mut name_index = HashMap::new();
        let mut path_index = HashMap::new();
        
        self.process_directory(
            ntfs,
            root,
            &mut ntfs.fs(),
            "",
            &mut files,
            &mut extension_index,
            &mut name_index,
            &mut path_index,
        )?;
        
        // Update cache atomically
        *self.files.write() = files;
        *self.extension_index.write() = extension_index;
        *self.name_index.write() = name_index;
        *self.path_index.write() = path_index;
        *self.last_update.write() = SystemTime::now();
        
        Ok(())
    }
    
    /// Read the MFT into memory
    fn read_mft(&self, handle: winapi::shared::ntdef::HANDLE) -> Result<Vec<u8>> {
        use std::os::windows::io::FromRawHandle;
        use std::io::{Read, Seek, SeekFrom};
        
        let mut file = unsafe { std::fs::File::from_raw_handle(handle as *mut _) };
        
        // Get file size
        let size = file.seek(SeekFrom::End(0))?;
        file.seek(SeekFrom::Start(0))?;
        
        // Read the entire MFT into memory
        let mut buffer = Vec::with_capacity(size as usize);
        file.take(size).read_to_end(&mut buffer)?;
        
        Ok(buffer)
    }
/// Represents a file entry in the MFT cache
#[derive(Debug, Clone)]
pub struct FileEntry {
    /// Unique file ID (MFT record number)
    pub id: u64,
    /// File name
    pub name: String,
    /// Full file path
    pub path: String,
    /// File size in bytes
    pub size: u64,
    /// File creation time
    pub created: SystemTime,
    /// File last modified time
    pub modified: SystemTime,
    /// Whether the entry is a directory
    pub is_directory: bool,
}

impl MftCache {
    /// Process a directory and its contents
    fn process_directory(
        &self,
        ntfs: &Ntfs,
        dir_entry: &ntfs::NtfsFile,
        path: &Path,
        sender: &mpsc::Sender<FileEntry>,
    ) -> Result<()> {
        let mut fs = ntfs.fs();
        let parent_path = path.to_string_lossy().to_string();
        let dir_index = match dir_entry.directory_index(&mut fs) {
            Ok(index) => index,
            Err(e) => {
                warn!("Failed to get directory index: {}", e);
                return Ok(()); // Skip inaccessible directories
            }
        };
        // Process each entry in the directory
        for entry_result in dir_index.entries() {
            // Check memory limits periodically
            self.files_processed.fetch_add(1, Ordering::Relaxed);
            if self.files_processed.load(Ordering::Relaxed) % self.config.max_files_before_memcheck == 0 {
                if let Err(e) = self.check_memory_limits() {
                    warn!("Memory check failed: {}", e);
                }
            }
            
            let entry = match entry_result {
                Ok(e) => e,
                Err(e) => {
                    warn!("Error reading directory entry: {}", e);
                    continue; // Skip invalid entries
                }
            };
            
            // Skip system files and directories
            let name = match entry.file_name() {
                Some(name) => name.to_string_lossy().to_string(),
                None => continue,
            };
            
            if name == "." || name == ".." || name.starts_with('$') {
                continue;
            }
            
            // Get the file record
            let file_record = match entry.to_file(ntfs) {
                Ok(f) => f,
                Err(e) => {
                    warn!("Failed to get file record for {}: {}", name, e);
                    continue;
                }
            };
            
            let file_id = file_record.reference().entry() as u64;
            let is_directory = file_record.is_directory();
            
            // Build the full path
            let full_path = if parent_path.is_empty() {
                name.clone()
            } else {
                format!("{}\\{}", parent_path, name)
            };
            
            // Get file size and timestamps
            let size = file_record.data_size(&mut fs).unwrap_or(0);
            let created = file_record.created(&mut fs).unwrap_or_else(|_| SystemTime::now());
            let modified = file_record.modified(&mut fs).unwrap_or_else(|_| SystemTime::now());
            
            // Create the file entry
            let file_entry = FileEntry {
                id: file_id,
                name: name.clone(),
                path: full_path.clone(),
                size,
                created,
                modified,
                is_directory,
            };
            
            // Send the file entry through the channel
            if let Err(e) = sender.send(file_entry) {
                error!("Failed to send file entry: {}", e);
                return Err(anyhow::anyhow!("Failed to send file entry: {}", e));
            }
            
            // Process subdirectories recursively
            if is_directory {
                if let Err(e) = self.process_directory(ntfs, &file_record, Path::new(&full_path), sender) {
                    warn!("Error processing subdirectory '{}': {}", full_path, e);
                    // Continue with next directory
                }
            }
            
            // Log progress periodically
            let processed = self.files_processed.load(Ordering::Relaxed);
            if processed > 0 && processed % 100_000 == 0 {
                info!(
                    "Processed {} files (memory: {:.2} MB)",
                    processed,
                    self.memory_usage.load(Ordering::Relaxed) as f64 / 1024.0 / 1024.0
                );
            }
        }
        
        Ok(())
    }
} // End of impl MftCache

    /// Helper function to convert string to Windows wide string
    fn wide_string(s: &str) -> Vec<u16> {
        use std::os::windows::ffi::OsStrExt;
        std::ffi::OsStr::new(s)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect()
    }
} // End of impl MftCache

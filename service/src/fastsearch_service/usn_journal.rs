//! USN Journal monitoring for cache invalidation and updates

use std::path::Path;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use anyhow::{Context, Result};
use log::{debug, error, info, trace};
use ntfs::NtfsFile;
use winapi::um::winioctl::FSCTL_READ_USN_JOURNAL;
use winapi::um::winioctl::FSCTL_QUERY_USN_JOURNAL;
use winapi::um::winioctl::USN_JOURNAL_DATA;
use winapi::um::winnt::HANDLE;

use crate::fastsearch_service::mft_cache::MftCache;

/// Monitors USN Journal for changes and updates the cache accordingly
#[derive(Debug)]
pub struct UsnJournalMonitor {
    drive_letter: char,
    volume_handle: HANDLE,
    running: Arc<AtomicBool>,
    thread_handle: Option<thread::JoinHandle<()>>,
}

impl UsnJournalMonitor {
    /// Create a new USN Journal monitor for the specified volume
    pub fn new(drive_letter: char, volume_handle: HANDLE) -> Result<Self> {
        Ok(Self {
            drive_letter: drive_letter.to_ascii_uppercase(),
            volume_handle,
            running: Arc::new(AtomicBool::new(false)),
            thread_handle: None,
        })
    }
    
    /// Start monitoring the USN Journal for changes
    pub fn start<F>(&mut self, callback: F) -> Result<()>
    where
        F: Fn() + Send + 'static + Sync,
    {
        if self.running.load(Ordering::Relaxed) {
            return Ok(());
        }
        
        self.running.store(true, Ordering::Relaxed);
        
        let running = self.running.clone();
        let volume_handle = self.volume_handle;
        let drive_letter = self.drive_letter;
        
        let handle = thread::spawn(move || {
            let mut last_usn = 0;
            
            while running.load(Ordering::Relaxed) {
                match Self::query_journal(volume_handle) {
                    Ok(journal_data) => {
                        if journal_data.NextUsn > last_usn {
                            if last_usn > 0 {
                                // There are new changes
                                debug!(
                                    "Detected filesystem changes on drive {}: {} new changes",
                                    drive_letter,
                                    journal_data.NextUsn - last_usn
                                );
                                
                                // Notify the cache to update
                                callback();
                            }
                            last_usn = journal_data.NextUsn;
                        }
                    }
                    Err(e) => {
                        error!("Error querying USN Journal for drive {}: {}", drive_letter, e);
                    }
                }
                
                // Sleep for a short duration before checking again
                thread::sleep(Duration::from_secs(1));
            }
        });
        
        self.thread_handle = Some(handle);
        info!("Started USN Journal monitoring for drive {}", drive_letter);
        
        Ok(())
    }
    
    /// Stop monitoring the USN Journal
    pub fn stop(&mut self) -> Result<()> {
        if !self.running.load(Ordering::Relaxed) {
            return Ok(());
        }
        
        self.running.store(false, Ordering::Relaxed);
        
        if let Some(handle) = self.thread_handle.take() {
            if let Err(e) = handle.join() {
                error!("Error joining USN Journal monitor thread: {:?}", e);
            }
        }
        
        info!("Stopped USN Journal monitoring for drive {}", self.drive_letter);
        Ok(())
    }
    
    /// Query the USN Journal data for the volume
    fn query_journal(volume_handle: HANDLE) -> Result<USN_JOURNAL_DATA> {
        use std::mem;
        use std::ptr;
        
        let mut bytes_returned = 0;
        let mut journal_data: USN_JOURNAL_DATA = unsafe { mem::zeroed() };
        
        let result = unsafe {
            winapi::um::ioapiset::DeviceIoControl(
                volume_handle,
                FSCTL_QUERY_USN_JOURNAL,
                ptr::null_mut(),
                0,
                &mut journal_data as *mut _ as *mut _,
                mem::size_of::<USN_JOURNAL_DATA>() as u32,
                &mut bytes_returned,
                ptr::null_mut(),
            )
        };
        
        if result == 0 {
            let error = std::io::Error::last_os_error();
            return Err(error).context("Failed to query USN Journal");
        }
        
        Ok(journal_data)
    }
    
    /// Read changes from the USN Journal
    fn read_journal_changes(
        &self,
        start_usn: i64,
        buffer: &mut [u8],
    ) -> Result<usize> {
        use std::mem;
        use std::ptr;
        
        let mut bytes_returned = 0;
        
        let result = unsafe {
            winapi::um::ioapiset::DeviceIoControl(
                self.volume_handle,
                FSCTL_READ_USN_JOURNAL,
                &start_usn as *const _ as *mut _,
                mem::size_of::<i64>() as u32,
                buffer.as_mut_ptr() as *mut _,
                buffer.len() as u32,
                &mut bytes_returned,
                ptr::null_mut(),
            )
        };
        
        if result == 0 {
            let error = std::io::Error::last_os_error();
            return Err(error).context("Failed to read USN Journal");
        }
        
        Ok(bytes_returned as usize)
    }
}

impl Drop for UsnJournalMonitor {
    fn drop(&mut self) {
        if let Err(e) = self.stop() {
            error!("Error stopping USN Journal monitor: {}", e);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use tempfile::tempdir;
    
    #[test]
    fn test_usn_journal_monitor() {
        // This is a simple smoke test that just verifies we can create and drop the monitor
        // Real testing would require actual filesystem operations
        let temp_dir = tempdir().unwrap();
        let test_file = temp_dir.path().join("test.txt");
        File::create(&test_file).unwrap();
        
        // Note: In a real test, we would need a valid volume handle
        // This is just for compilation testing
        let monitor = UsnJournalMonitor::new('C', std::ptr::null_mut());
        assert!(monitor.is_ok());
    }
}

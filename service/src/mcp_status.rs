use anyhow::Result;
use serde::{Serialize, Deserialize};
use windows_service::{
    service::{ServiceAccess, ServiceState, ServiceStatus},
    service_manager::{ServiceManager, ServiceManagerAccess}
};
use std::time::SystemTime;
use winapi::um::{
    fileapi::CreateFileW,
    handleapi::{CloseHandle, INVALID_HANDLE_VALUE},
    winbase::GENERIC_READ,
    fileapi::OPEN_EXISTING,
    winnt::FILE_SHARE_READ,
};
use std::ffi::OsStr;
use std::os::windows::ffi::OsStrExt;
use std::ptr::null_mut;

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ServiceStatusResponse {
    pub service_name: String,
    pub display_name: String,
    pub is_installed: bool,
    pub is_running: bool,
    pub pipe_accessible: bool,
    pub state: Option<String>,
    pub pid: Option<u32>,
    pub start_type: Option<String>,
    pub binary_path: Option<String>,
    pub last_check: String,
}

pub fn get_service_status(service_name: &str, display_name: &str) -> Result<ServiceStatusResponse> {
    let manager = ServiceManager::local_computer(
        None::<&str>,
        ServiceManagerAccess::CONNECT
    )?;

    let service = manager.open_service(
        service_name,
        ServiceAccess::QUERY_STATUS | ServiceAccess::QUERY_CONFIG
    );

    let mut response = ServiceStatusResponse {
        service_name: service_name.to_string(),
        display_name: display_name.to_string(),
        is_installed: false,
        is_running: false,
        pipe_accessible: false,
        state: None,
        pid: None,
        start_type: None,
        binary_path: None,
        last_check: chrono::Local::now().to_rfc3339(),
    };

    if let Ok(service) = service {
        response.is_installed = true;
        
        if let Ok(status) = service.query_status() {
            response.state = Some(format!("{:?}", status.current_state));
            response.is_running = status.current_state == ServiceState::Running;
            response.pid = status.process_id;
            
            if let Ok(config) = service.query_config() {
                response.start_type = Some(format!("{:?}", config.start_type));
                response.binary_path = Some(config.executable_path.display().to_string());
            }
        }
    }

    // Check if the named pipe is accessible
    response.pipe_accessible = is_pipe_accessible("fastsearch-service");
    
    Ok(response)
}

fn is_pipe_accessible(pipe_name: &str) -> bool {
    let pipe_path = format!(r"\\.\pipe\{}", pipe_name);
    let wide: Vec<u16> = OsStr::new(&pipe_path).encode_wide().chain(Some(0)).collect();
    
    let handle = unsafe {
        CreateFileW(
            wide.as_ptr(),
            GENERIC_READ,
            FILE_SHARE_READ,
            null_mut(),
            OPEN_EXISTING,
            0,
            null_mut()
        )
    };
    
    if handle != INVALID_HANDLE_VALUE {
        unsafe { CloseHandle(handle); }
        true
    } else {
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_pipe_accessible() {
        // This is a basic test that just verifies the function doesn't panic
        let _ = is_pipe_accessible("nonexistent-pipe");
    }
}

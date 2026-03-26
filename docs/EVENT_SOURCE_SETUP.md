# Event Source and DebugView Setup

## Event Source Registration

The FastSearch service event source has been registered in the Windows Registry to enable Event Log writing.

### Registry Location
```
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\EventLog\Application\FastSearchMCP
```

### Registry Values
- **EventMessageFile**: Path to service executable
- **TypesSupported**: 7 (Error, Warning, Information)
- **CategoryCount**: 0

### Registration Script
Run `scripts\register_event_source.ps1` as Administrator to register the event source.

## DebugView Setup

DebugView has been installed and configured to capture `OutputDebugStringW` messages from the FastSearch service.

### Installation Location
```
C:\Users\<username>\AppData\Local\DebugView\Dbgview.exe
```

### Usage

#### Automatic Start
Run `scripts\setup_debugview.ps1` to automatically download, install, and start DebugView.

#### Manual Usage
1. Run: `C:\Users\<username>\AppData\Local\DebugView\Dbgview.exe`
2. Enable: **Capture -> Capture Win32**
3. Enable: **Capture -> Capture Global Win32** (for services)
4. Filter: Enter `[FastSearch]` in the filter box to see only FastSearch messages

### What DebugView Captures

DebugView will show all `OutputDebugStringW` messages, including:
- Service startup messages
- Error messages when Event Log is unavailable
- Fallback logging when `LogServiceEvent` can't write to Event Log
- Messages prefixed with `[FastSearch]`

## Service Start with Logging

Use `scripts\start_service_with_logging.ps1` to:
1. Start the service
2. Monitor service status
3. Read Application Event Log entries
4. Display crash information if service fails

### Usage
```powershell
# Run as Administrator
.\scripts\start_service_with_logging.ps1
```

## Log Reading

### Application Event Log
```powershell
Get-EventLog -LogName Application -Source "FastSearchMCP" -Newest 10
```

### System Event Log (Service Control Manager)
```powershell
Get-EventLog -LogName System -Source "Service Control Manager" | 
    Where-Object { $_.Message -like "*FastSearch*" }
```

### Python Log Reader
```powershell
python tests/read_service_logs.py
```

## Troubleshooting

### No Logs in Event Viewer
1. Verify event source is registered: Check registry key exists
2. Check DebugView: Service may be logging to DebugView instead
3. Verify service has permissions: Service must run with appropriate privileges

### Service Crashes Before Logging
1. Check DebugView: Early crashes log to `OutputDebugStringW`
2. Check System Event Log: Windows logs service crashes automatically
3. Use Visual Studio Debugger: Attach to service process to catch crash

### DebugView Not Showing Messages
1. Verify "Capture Win32" is enabled
2. Verify "Capture Global Win32" is enabled (required for services)
3. Check filter: Make sure `[FastSearch]` filter is correct
4. Verify service is running: Messages only appear when service is active

## Next Steps

1. **Start the service** using `scripts\start_service_with_logging.ps1`
2. **Monitor DebugView** for `[FastSearch]` messages
3. **Check Event Logs** for service events
4. **Debug crashes** using Visual Studio debugger if needed

---

**Status**: Event source registered ✅ | DebugView installed ✅ | Ready for testing ✅


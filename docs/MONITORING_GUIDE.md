# Service Log Monitoring Guide

## Real-Time Log Monitoring

### Start Monitor Script
```powershell
.\scripts\monitor_service_logs.ps1
```

This script:
- Shows recent log entries on startup
- Continuously monitors for new log entries
- Displays logs in real-time with color coding
- Monitors service status changes
- Shows System Event Log entries for crashes
- Runs until you press Ctrl+C

### Color Coding
- **Green**: Information messages
- **Yellow**: Warnings
- **Red**: Errors
- **Gray**: Timestamps and metadata
- **Magenta**: System Event Log entries

## Alternative Monitoring Methods

### 1. DebugView (Recommended for Early Startup)
```powershell
.\scripts\setup_debugview.ps1
```

DebugView shows `OutputDebugStringW` messages, which appear even before Event Log is available.

### 2. Event Viewer (GUI)
1. Open Event Viewer (`eventvwr.msn`)
2. Navigate to: **Windows Logs -> Application**
3. Filter by Source: **FastSearchMCP**

### 3. PowerShell One-Liner
```powershell
Get-EventLog -LogName Application -Source "FastSearchMCP" -Newest 10 | Format-Table TimeGenerated, EntryType, Message -AutoSize
```

### 4. Continuous PowerShell Monitor
```powershell
while ($true) { 
    Get-EventLog -LogName Application -Source "FastSearchMCP" -Newest 1 | Format-List
    Start-Sleep -Seconds 2 
}
```

## What to Look For

### Successful Startup Sequence
1. `ServiceMain called - service starting`
2. `Service control handler registered successfully`
3. `Stop event created successfully`
4. `Event source registered successfully`
5. `Worker thread created successfully`
6. `Service worker thread started`
7. `Service is now running`

### Error Indicators
- **Service crashes**: Check System Event Log for "terminated unexpectedly"
- **Pipe errors**: Look for "CreateNamedPipe failed" or "ConnectNamedPipe failed"
- **Thread errors**: Look for "CreateThread failed"
- **Event source errors**: Look for "RegisterEventSource failed"

### Common Log Messages

#### Information
- Service lifecycle events
- Thread creation/startup
- Client connections/disconnections
- Successful operations

#### Warnings
- Pipe connection failures (non-fatal)
- Invalid commands received
- Message read/write failures

#### Errors
- Service initialization failures
- Thread creation failures
- Exception messages
- Critical operation failures

## Troubleshooting

### No Logs Appearing
1. **Check event source registration**: Run `.\scripts\register_event_source.ps1`
2. **Check DebugView**: Early logs may only appear in DebugView
3. **Check service status**: Service must be running to log
4. **Check permissions**: Service needs appropriate privileges

### Logs Stop Appearing
1. **Service may have crashed**: Check System Event Log
2. **Service may have stopped**: Check service status
3. **Event log may be full**: Clear old logs if needed

### Too Many Logs
- Filter by EntryType: `Where-Object { $_.EntryType -eq "Error" }`
- Filter by time: `Where-Object { $_.TimeGenerated -gt (Get-Date).AddHours(-1) }`
- Use DebugView filter: Enter `[FastSearch]` in filter box

## Best Practices

1. **Start monitoring before starting service** to catch all logs
2. **Use DebugView for early startup debugging** (before Event Log is available)
3. **Monitor both Application and System logs** for complete picture
4. **Save logs periodically** for later analysis
5. **Filter logs** to focus on errors/warnings when needed

---

**Quick Start**: Run `.\scripts\monitor_service_logs.ps1` and keep it running while testing the service.


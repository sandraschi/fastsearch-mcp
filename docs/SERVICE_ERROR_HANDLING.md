# Service Error Handling and Logging Improvements

## Overview

Comprehensive error handling and logging has been added to the FastSearch C++ service to ensure **no crash occurs without logging**. Every critical operation is now wrapped in try-catch blocks with detailed error logging.

## Key Improvements

### 1. **ServiceMain - Complete Exception Handling**

- ✅ Wrapped entire `ServiceMain` in try-catch blocks
- ✅ Logs entry: "ServiceMain called - service starting"
- ✅ Logs each initialization step:
  - Service control handler registration
  - Stop event creation
  - Event source registration
  - Worker thread creation
  - Service running state
  - Shutdown sequence
- ✅ All error paths log before returning
- ✅ Catches both `std::exception` and unknown exceptions
- ✅ Reports proper exit codes to Windows

### 2. **ServiceWorkerThread - Thread-Safe Error Handling**

- ✅ Entire thread function wrapped in try-catch
- ✅ Logs thread start and exit
- ✅ All pipe operations have error handling
- ✅ Client connection/disconnection logged
- ✅ Command processing errors logged
- ✅ Returns error code on exception

### 3. **LogServiceEvent - Safe Logging with Fallback**

- ✅ Wrapped in try-catch to prevent logging failures from crashing
- ✅ Falls back to `OutputDebugStringW` if event log unavailable
- ✅ Handles `RegisterEventSourceW` failures gracefully
- ✅ Handles `ReportEventW` failures gracefully
- ✅ Never throws exceptions

### 4. **ReportServiceStatus - Safe Status Reporting**

- ✅ Checks for null status handle
- ✅ Wrapped in try-catch
- ✅ Logs if `SetServiceStatus` fails
- ✅ Never crashes on status update failures

### 5. **ServiceCtrlHandler - Stop Request Logging**

- ✅ Logs when stop is requested
- ✅ Logs if `SetEvent` fails
- ✅ Checks for null stop event handle
- ✅ Wrapped in try-catch

### 6. **Pipe Operations - Comprehensive Error Handling**

#### ReadPipeMessage
- ✅ Validates pipe handle
- ✅ Logs invalid message lengths
- ✅ Wrapped in try-catch
- ✅ Returns false on any error (doesn't crash)

#### WritePipeMessage
- ✅ Validates pipe handle
- ✅ Logs `FlushFileBuffers` failures (except broken pipe)
- ✅ Wrapped in try-catch
- ✅ Returns false on any error (doesn't crash)

### 7. **Command Handlers - Exception Safety**

All command handlers (`HandlePing`, `HandleGetServiceInfo`, `HandleSearchRequest`) now:
- ✅ Wrapped in try-catch blocks
- ✅ Log exceptions with details
- ✅ Return error JSON on exception (never throw)
- ✅ Handle both `std::exception` and unknown exceptions

### 8. **Client Message Loop - Per-Message Error Handling**

- ✅ Each message processing wrapped in try-catch
- ✅ Command parsing errors logged
- ✅ Unknown commands logged with command name
- ✅ Invalid requests logged
- ✅ Exceptions in command handlers caught and logged
- ✅ Client disconnected on error (graceful degradation)

### 9. **wmain - Entry Point Logging**

- ✅ Logs `StartServiceCtrlDispatcherW` failures to:
  - Console (if available)
  - Debug output
  - Event log (if possible)
- ✅ Returns proper error codes

## Logging Strategy

### Log Levels

- **EVENTLOG_INFORMATION_TYPE**: Normal operations, state changes
- **EVENTLOG_WARNING_TYPE**: Recoverable errors, unusual conditions
- **EVENTLOG_ERROR_TYPE**: Critical errors, exceptions

### Log Messages Include

1. **Context**: What operation was being performed
2. **Error Code**: Windows error code (when available)
3. **Exception Details**: Exception message (when available)
4. **State Information**: Current service state

### Fallback Logging

If event log is unavailable:
- Uses `OutputDebugStringW` (visible in debugger)
- Never crashes due to logging failures

## Error Recovery

### Service Startup Failures

- ✅ All initialization steps log before failing
- ✅ Proper cleanup on failure
- ✅ Service reports STOPPED state with error code
- ✅ Windows Event Log contains full error details

### Runtime Errors

- ✅ Worker thread continues on pipe errors
- ✅ Client disconnections handled gracefully
- ✅ Invalid commands logged but don't crash service
- ✅ Exceptions in command handlers return error JSON

### Shutdown Errors

- ✅ Worker thread timeout logged
- ✅ Cleanup failures logged
- ✅ Service always reports final state

## Testing

To verify error handling:

1. **Check Event Logs**: All errors should appear in Windows Event Log
2. **Service Startup**: Even if service fails to start, logs should explain why
3. **Runtime Errors**: Service should continue running after non-fatal errors
4. **Shutdown**: Service should log shutdown sequence

## Example Log Messages

### Successful Startup
```
[INFO] ServiceMain called - service starting
[INFO] Service control handler registered successfully
[INFO] Stop event created successfully
[INFO] Event source registered successfully
[INFO] Worker thread created successfully
[INFO] Service is now running
[INFO] Service worker thread started
```

### Error During Startup
```
[INFO] ServiceMain called - service starting
[INFO] Service control handler registered successfully
[ERROR] CreateEvent failed with error 8
```

### Runtime Error
```
[INFO] Client connected to named pipe
[WARNING] ReadPipeMessage failed with error 109
[INFO] Client disconnected from named pipe
```

### Exception
```
[ERROR] Exception in ServiceWorkerThread: std::bad_alloc
```

## Benefits

1. **No Silent Failures**: Every error is logged
2. **Easier Debugging**: Detailed error messages with context
3. **Service Stability**: Exceptions don't crash the service
4. **Production Ready**: Comprehensive error handling for production use
5. **Diagnostic Information**: Full error trail in Windows Event Log

---

**Result**: The service will **never crash without logging**. All errors, exceptions, and failures are captured and logged to the Windows Event Log with detailed context.


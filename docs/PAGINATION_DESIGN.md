# Pagination Design - Switchable Modes

## Overview

FastSearch MCP supports **three pagination modes** for handling large result sets:

1. **`none`** (default) - Return all results in single response (current behavior)
2. **`offset`** - Offset-based pagination (page + page_size)
3. **`streaming`** - Progressive chunked results (chunk_size, request more)

## Use Cases

### Mode: `none` (Default)
- **When**: Small result sets (< 1000 files)
- **Behavior**: Returns all results immediately
- **Pros**: Simple, fast for small searches
- **Cons**: Memory/network intensive for large results

### Mode: `offset` 
- **When**: Random access needed, jumping to specific pages
- **Behavior**: Client requests page N, service scans from start but only returns that page
- **Pros**: Simple, no server state, supports random access
- **Cons**: Re-scans for each page (but MFT access is fast)
- **Example**: "Show me page 5 of 1000 results"

### Mode: `streaming`
- **When**: Processing large result sets progressively
- **Behavior**: Service sends chunks as found, client can request more or stop early
- **Pros**: Efficient, progressive results, early termination
- **Cons**: Requires protocol changes (chunked responses)
- **Example**: "Stream results in chunks of 1000, I'll process as they arrive"

## API Design

### Request Parameters

```json
{
  "command": "search_files",
  "pattern": "*.py",
  "directory": "C:\\",
  "max_results": 0,  // 0 = unlimited (capped at 10M)
  
  // Pagination parameters
  "pagination_mode": "offset",  // "none" | "offset" | "streaming"
  
  // For offset mode:
  "page": 1,           // 1-indexed page number
  "page_size": 1000,    // Results per page
  
  // For streaming mode:
  "chunk_size": 1000,   // Results per chunk
  "chunk_id": null      // null for first chunk, then use returned chunk_id for next
}
```

### Response Format

#### Mode: `none` (Default)
```json
{
  "success": true,
  "results": [...],
  "count": 5000,
  "pagination": null
}
```

#### Mode: `offset`
```json
{
  "success": true,
  "results": [...],  // Only page_size results
  "count": 1000,     // Results in this page
  "pagination": {
    "mode": "offset",
    "page": 1,
    "page_size": 1000,
    "total_pages": 5,      // Estimated (may be approximate)
    "total_results": 5000, // Estimated (may be approximate)
    "has_next": true,
    "has_previous": false
  }
}
```

#### Mode: `streaming`
```json
{
  "success": true,
  "results": [...],  // chunk_size results
  "count": 1000,     // Results in this chunk
  "pagination": {
    "mode": "streaming",
    "chunk_id": "abc123...",  // Use this to request next chunk
    "chunk_size": 1000,
    "chunk_number": 1,
    "has_more": true,         // More chunks available
    "total_found_so_far": 1000 // Running total
  }
}
```

## Implementation Strategy

### Phase 1: Offset Pagination (Simpler)
1. Add `pagination_mode`, `page`, `page_size` to request parsing
2. Modify result collection to skip results before `(page - 1) * page_size`
3. Stop after collecting `page_size` results
4. Return pagination metadata

### Phase 2: Streaming Pagination (More Complex)
1. Add `chunk_size` parameter
2. Modify pipe protocol to support chunked responses
3. Generate unique `chunk_id` for each search session
4. Store minimal state (MFT position) per chunk_id (violates no-state? Need to think...)
5. Actually, for streaming: send chunks as found, no state needed!

### Streaming Without State
- Service sends chunk 1 immediately when found
- Client can request "next chunk" with same search params
- Service continues from where it stopped (but this requires state...)

**Better approach**: Streaming sends chunks as they're found in real-time
- Service doesn't wait for client requests
- Service sends multiple chunk messages as results are found
- Client processes chunks as they arrive
- Client can send "stop" message to terminate early

## Architecture Considerations

### No-State Principle
- **Offset mode**: ✅ No state - re-scans each time (acceptable, MFT is fast)
- **Streaming mode**: ⚠️ Requires connection state (but only during active search)
  - State is ephemeral (only during pipe connection)
  - No persistent state across connections
  - Acceptable deviation for streaming benefits

### Memory Efficiency
- **Offset mode**: Only loads one page into memory ✅
- **Streaming mode**: Only loads one chunk into memory ✅
- Both much better than loading 10M results ✅

## Example Usage

### Offset Pagination
```python
# Get page 1
results1 = await search_files_via_pipe(
    pattern="*.py",
    directory="C:\\",
    max_results=0,
    pagination_mode="offset",
    page=1,
    page_size=1000
)

# Get page 2
results2 = await search_files_via_pipe(
    pattern="*.py",
    directory="C:\\",
    max_results=0,
    pagination_mode="offset",
    page=2,
    page_size=1000
)
```

### Streaming Pagination
```python
# Start streaming search
async for chunk in stream_search_files_via_pipe(
    pattern="*.py",
    directory="C:\\",
    max_results=0,
    chunk_size=1000
):
    # Process chunk as it arrives
    process_chunk(chunk)
    if enough_results():
        break  # Stop early
```

## Benefits

1. **Memory efficient** - Only load one page/chunk at a time
2. **Network efficient** - Smaller JSON responses
3. **User experience** - Progressive results, show progress
4. **Early termination** - Stop when enough results found
5. **Flexibility** - Choose mode based on use case

## Migration Path

1. **Phase 1**: Implement offset pagination (simpler, no protocol changes)
2. **Phase 2**: Add streaming support (requires protocol changes)
3. **Backward compatibility**: Default to `none` mode (current behavior)


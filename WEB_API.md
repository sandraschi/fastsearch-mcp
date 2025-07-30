# FastSearch Web API Documentation

## Overview

The FastSearch service provides a RESTful HTTP API that allows you to perform fast file searches across NTFS volumes. This API is built on top of the same core search engine used by the MCP server, providing web-friendly access to the powerful search capabilities.

## Getting Started

### Starting the Web API Server

```bash
# Build the service (if not already built)
cargo build --release

# Start the web API server
./target/release/fastsearch --web-api

# By default, the server runs on http://localhost:3000
# You can customize the host and port using environment variables:
# FASTSEARCH_WEB_HOST=0.0.0.0 FASTSEARCH_WEB_PORT=8080 ./target/release/fastsearch --web-api
```

## API Endpoints

### Search for Files

`POST /api/search`

Search for files matching a pattern.

**Request Body:**
```json
{
  "pattern": "*.rs",
  "path": "C:\\Dev",
  "max_results": 100,
  "doc_type": "code"
}
```

**Parameters:**
- `pattern` (string, required): Search pattern (supports glob format)
- `path` (string, optional): Base directory to search in (default: root of all NTFS volumes)
- `max_results` (number, optional): Maximum number of results to return (default: 1000)
- `doc_type` (string, optional): Filter by document type (e.g., "code", "image", "audio", "video")

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "name": "main.rs",
      "path": "C:\\Dev\\fastsearch\\src",
      "full_path": "C:\\Dev\\fastsearch\\src\\main.rs",
      "size": 12345,
      "is_directory": false,
      "size_formatted": "12.1 KB"
    }
  ],
  "count": 1,
  "search_time_ms": 0.45,
  "message": "Search completed"
}
```

### Get Service Status

`GET /api/status`

Get the current status of the FastSearch service.

**Response:**
```json
{
  "success": true,
  "status": "ready",
  "message": "FastSearch service is running",
  "version": "0.1.0",
  "indexed_volumes": ["C:", "D:"],
  "uptime_seconds": 1234
}
```

### Run Benchmark

`GET /api/benchmark?pattern=*.rs&path=C:\\Dev`

Run a performance benchmark with the given search parameters.

**Query Parameters:**
- `pattern` (required): Search pattern
- `path` (optional): Base directory to search in

**Response:**
```json
{
  "success": true,
  "pattern": "*.rs",
  "path": "C:\\Dev",
  "matches": 42,
  "duration_ms": 12.34,
  "searches_per_second": 3456.78
}
```

### Health Check

`GET /health`

Simple health check endpoint for monitoring.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-07-20T01:30:00Z"
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes and JSON error responses:

```json
{
  "success": false,
  "error": {
    "code": "invalid_request",
    "message": "Missing required parameter: pattern"
  }
}
```

## Authentication

The API currently doesn't implement authentication, so it's recommended to:
1. Only expose the API on localhost (default)
2. Use a reverse proxy with authentication for remote access
3. Configure appropriate firewall rules

## Rate Limiting

No built-in rate limiting is currently implemented. For production use, consider:
1. Running behind a reverse proxy with rate limiting (e.g., nginx, Cloudflare)
2. Implementing request throttling in your application

## CORS

CORS is enabled by default with the following settings:
- Allowed Origins: `*`
- Allowed Methods: `GET, POST, OPTIONS`
- Allowed Headers: `Content-Type, Authorization`

## Configuration

You can configure the web server using environment variables:

- `FASTSEARCH_WEB_HOST`: Host to bind to (default: `127.0.0.1`)
- `FASTSEARCH_WEB_PORT`: Port to listen on (default: `3000`)
- `FASTSEARCH_WORKERS`: Number of worker threads (default: number of CPU cores)

Example:
```bash
FASTSEARCH_WEB_HOST=0.0.0.0 FASTSEARCH_WEB_PORT=8080 ./target/release/fastsearch --web-api
```

## Client Libraries

### JavaScript/TypeScript

```typescript
interface SearchOptions {
  pattern: string;
  path?: string;
  max_results?: number;
  doc_type?: string;
}

async function searchFiles(options: SearchOptions) {
  const response = await fetch('http://localhost:3000/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(options)
  });
  return await response.json();
}

// Example usage
const results = await searchFiles({
  pattern: '*.rs',
  path: 'C:\\Dev',
  max_results: 10,
  doc_type: 'code'
});
```

### Python

```python
import requests

def search_files(pattern, path=None, max_results=100, doc_type=None):
    response = requests.post(
        'http://localhost:3000/api/search',
        json={
            'pattern': pattern,
            'path': path,
            'max_results': max_results,
            'doc_type': doc_type
        }
    )
    return response.json()

# Example usage
results = search_files(
    pattern='*.py',
    path='/home/user/projects',
    max_results=5,
    doc_type='code'
)
```

## Troubleshooting

### Common Issues

1. **Service not starting**
   - Ensure no other application is using port 3000
   - Check if you have permission to access the specified directories

2. **No results returned**
   - Verify the search pattern is correct
   - Check if the path exists and is accessible
   - Try running with elevated privileges if searching system directories

3. **Performance issues**
   - First search might be slower as the MFT is being read
   - Subsequent searches should be much faster
   - Consider increasing `FASTSEARCH_WORKERS` for better performance

## Security Considerations

- The web API has no built-in authentication
- By default, it only listens on localhost (127.0.0.1)
- Exposing the API to the network could allow unauthorized file system access
- Always run behind a reverse proxy with proper security measures in production

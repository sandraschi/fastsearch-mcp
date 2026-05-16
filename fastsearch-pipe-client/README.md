# fastsearch-pipe-client

Thin async/sync Python client for the [FastSearch](https://github.com/sandraschi/fastsearch-mcp) Windows service — search files via direct NTFS MFT access without any dependency on FastSearch MCP itself.

```python
from fastsearch_pipe_client import FastSearchClient

client = FastSearchClient()
results = client.search_sync("*.txt", "C:\\", max_results=10)
for f in results:
    print(f["name"], f["size"])
```

## Requirements

- Windows 10+ with the FastSearch Windows service running
- Python 3.10+
- `pywin32` (installed automatically)

## Install

```bash
pip install fastsearch-pipe-client
```

## Usage

### One-shot (sync)

```python
from fastsearch_pipe_client import search_files

results = search_files("*.py", "C:\\Projects", max_results=50)
```

### Async context manager

```python
from fastsearch_pipe_client import FastSearchClient

async with FastSearchClient() as client:
    info = await client.service_info()
    ok = await client.ping()
    files = await client.search("*.log", "C:\\Windows", max_results=20)
```

### Check service

```python
from fastsearch_pipe_client import test_connection, get_service_info

if test_connection():
    info = get_service_info()
    print(info)
```

## Return format

Each result dict contains:

| Key | Type | Description |
|-----|------|-------------|
| `path` | str | Bare file name |
| `name` | str | File name |
| `size` | int | File size in bytes |
| `created` | int | NTFS 100-ns timestamp |
| `modified` | int | NTFS 100-ns timestamp |
| `accessed` | int | NTFS 100-ns timestamp |
| `is_directory` | bool | True if directory |
| `is_hidden` | bool | True if hidden |
| `parent_dir` | int | MFT parent record reference |

## Custom pipe name

Set `FASTSEARCH_PIPE_NAME` env var to use a non-default pipe path:

```powershell
$env:FASTSEARCH_PIPE_NAME = "\\.\pipe\MyCustomPipe"
```

Or pass it to the constructor:

```python
client = FastSearchClient(pipe_name=r"\\.\pipe\MyCustomPipe")
```

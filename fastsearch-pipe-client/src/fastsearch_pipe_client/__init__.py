"""
fastsearch-pipe-client — Talk to the FastSearch C++ service over the named pipe.

```python
from fastsearch_pipe_client import FastSearchClient

client = FastSearchClient()
results = client.search_files("*.txt", "C:\\", max_results=10)
for f in results:
    print(f["name"], f["size"])
```
"""

from .client import FastSearchClient, get_service_info, search_files, test_connection

__all__ = ["FastSearchClient", "get_service_info", "search_files", "test_connection"]

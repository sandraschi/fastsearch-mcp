#!/bin/bash

# Get the platform from the first argument
PLATFORM=$1
VERSION=$2
BRIDGE_BINARY=$3

# Determine the platform value for the manifest
case "$PLATFORM" in
  "windows-x64")
    PLATFORM_VALUE="win32"
    ;;
  "linux-x64")
    PLATFORM_VALUE="linux"
    ;;
  *)
    PLATFORM_VALUE="darwin"
    ;;
esac

# Create the manifest JSON
cat > dxt-build/manifest.json << EOF
{
  "dxt_version": "0.1",
  "name": "fastsearch-mcp",
  "version": "$VERSION",
  "description": "Lightning-fast semantic search across all your files using NTFS MFT indexing",
  "author": {
    "name": "Sandra Schimanski",
    "email": "sandra@sandraschi.dev",
    "url": "https://github.com/sandraschi"
  },
  "homepage": "https://github.com/sandraschi/fastsearch-mcp",
  "license": "MIT",
  "keywords": ["search", "semantic", "files", "ntfs", "mft", "indexing"],
  
  "server": {
    "type": "binary",
    "entry_point": "server/$BRIDGE_BINARY",
    "mcp_config": {
      "command": "server/$BRIDGE_BINARY",
      "args": [],
      "env": {
        "FASTSEARCH_PIPE_NAME": "fastsearch-mcp",
        "RUST_LOG": "info"
      }
    }
  },
  
  "compatibility": {
    "claude_desktop": ">=0.10.0",
    "platforms": ["$PLATFORM_VALUE"]
  },
  
  "capabilities": {
    "tools": true,
    "resources": false,
    "prompts": false
  },
  
  "tools": [
    {
      "name": "semantic_search",
      "description": "Search across all indexed files using natural language queries. Supports semantic similarity, exact matches, and complex queries.",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Natural language search query (e.g., 'documents about machine learning', 'emails from last week')",
            "minLength": 1
          },
          "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "default": 10,
            "minimum": 1,
            "maximum": 100
          },
          "file_types": {
            "type": "array",
            "description": "Filter by file extensions (e.g., ['txt', 'md', 'pdf'])",
            "items": {
              "type": "string"
            },
            "default": []
          },
          "modified_after": {
            "type": "string",
            "description": "ISO date string - only return files modified after this date",
            "format": "date-time"
          }
        },
        "required": ["query"]
      }
    },
    {
      "name": "index_status",
      "description": "Get current indexing status, statistics, and performance metrics",
      "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": false
      }
    },
    {
      "name": "reindex_directory",
      "description": "Force reindexing of a specific directory or drive",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Directory path to reindex (e.g., 'C:\\\\Users\\\\Sandra\\\\Documents')"
          },
          "recursive": {
            "type": "boolean",
            "description": "Include subdirectories",
            "default": true
          }
        },
        "required": ["path"]
      }
    },
    {
      "name": "search_statistics",
      "description": "Get detailed search statistics and index health metrics",
      "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": false
      }
    }
  ],
  
  "permissions": {
    "filesystem": {
      "read": true,
      "write": false
    },
    "network": {
      "allowed": false
    }
  }
}
EOF

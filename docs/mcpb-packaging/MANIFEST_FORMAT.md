# MCPB Manifest.json Format Reference

**Last Updated**: 2025-01-15  
**MCPB CLI Version**: 1.1.1  
**Manifest Version**: 0.2

## ✅ Correct Format

```json
{
  "manifest_version": "0.2",
  "name": "your-extension-name",
  "version": "1.0.0",
  "description": "Brief description of your extension",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "license": "MIT",
  "homepage": "https://github.com/yourusername/your-extension",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourusername/your-extension.git"
  },
  "keywords": ["mcp", "search", "filesystem"],
  "server": {
    "type": "python",
    "entry_point": "src/your_package/__main__.py",
    "mcp_config": {
      "command": "python",
      "args": ["-m", "your_package"],
      "env": {
        "PYTHONPATH": "${PWD}",
        "PYTHONUNBUFFERED": "1"
      }
    }
  },
  "prompts": [
    {
      "name": "system",
      "description": "System prompt defining capabilities",
      "text": "prompts/system.md"
    },
    {
      "name": "user",
      "description": "User guide",
      "text": "prompts/user.md"
    }
  ]
}
```

## ❌ Common Mistakes

### 1. Wrong Version Field
```json
// ❌ WRONG
"mcpb_version": "0.1"

// ✅ CORRECT
"manifest_version": "0.2"
```

### 2. Author as String
```json
// ❌ WRONG
"author": "Your Name <email@example.com>"

// ✅ CORRECT
"author": {
  "name": "Your Name",
  "email": "email@example.com"
}
```

### 3. Including Tools Array
```json
// ❌ WRONG - Tools are auto-discovered from server
"tools": [
  {
    "name": "my_tool",
    "parameters": { ... }
  }
]

// ✅ CORRECT - Omit tools entirely
// Tools are automatically discovered from your FastMCP server
```

### 4. Including Unrecognized Keys
```json
// ❌ WRONG - These keys are NOT part of the standard
{
  "capabilities": { ... },
  "categories": [ ... ],
  "mcp": { ... },
  "requirements": { ... },
  "permissions": [ ... ],
  "configuration": { ... }
}

// ✅ CORRECT - Omit these keys
// Only include standard fields shown in the correct format above
```

### 5. Wrong Prompts Format
```json
// ❌ WRONG
"prompts": {
  "system": "prompts/system.md",
  "user": "prompts/user.md"
}

// ✅ CORRECT
"prompts": [
  {
    "name": "system",
    "description": "System prompt",
    "text": "prompts/system.md"
  },
  {
    "name": "user",
    "description": "User guide",
    "text": "prompts/user.md"
  }
]
```

## 📋 Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manifest_version` | string | ✅ Yes | Must be `"0.2"` |
| `name` | string | ✅ Yes | Extension name (kebab-case) |
| `version` | string | ✅ Yes | Semantic version (e.g., `"1.0.0"`) |
| `description` | string | ✅ Yes | Brief description |
| `author` | object | ✅ Yes | `{"name": "...", "email": "..."}` |
| `license` | string | ✅ Yes | License identifier (e.g., `"MIT"`) |
| `server` | object | ✅ Yes | Server configuration |

## 📋 Optional Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `homepage` | string | ❌ No | Project homepage URL |
| `repository` | object | ❌ No | Git repository info |
| `keywords` | array | ❌ No | Search keywords |
| `prompts` | array | ❌ No | Prompt templates |

## 🔧 Build Command

```bash
# Syntax: mcpb pack [directory] [output]
mcpb pack ./mcpb-build ./dist/package-name-version.mcpb

# ❌ WRONG - No --output flag
mcpb pack --output ./dist/package.mcpb
```

## ✅ Validation

Always validate before building:

```bash
mcpb validate manifest.json
```

This will catch format errors before packaging.

## 📚 Reference

- MCPB CLI: `npm install -g @anthropic-ai/mcpb`
- Manifest Version: 0.2
- Tools: Auto-discovered from FastMCP server (do NOT list in manifest)
- Dependencies: Listed in `requirements.txt` (installed by Claude Desktop)


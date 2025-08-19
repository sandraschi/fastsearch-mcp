# FastSearch MCP Dual Package Architecture

**Document Version**: 1.0  
**Date**: 2025-08-13  
**Author**: Sandra Schimanski  
**Status**: Implementation Guide for Windsurf AI  

## 🎯 **CRITICAL ARCHITECTURE UNDERSTANDING**

FastSearch MCP is **NOT** a standard MCP server. It requires a **unique dual-component architecture** that cannot function without both parts:

### **Component 1: Windows Service (Elevated)**
- **Binary**: `fastsearch-service.exe` 
- **Privileges**: **MUST run elevated** (Administrator rights)
- **Purpose**: Direct NTFS MFT reading, in-memory database building
- **Communication**: Named pipe server `\\.\pipe\fastsearch-mcp`
- **Lifecycle**: Windows service (auto-start, crash recovery)

### **Component 2: MCP Bridge (User-level)**
- **Binary**: `fastsearch-mcp-bridge.exe`
- **Privileges**: Normal user context (no elevation)
- **Purpose**: stdio MCP protocol interface to Claude Desktop
- **Communication**: Named pipe client to service + stdio to Claude
- **Lifecycle**: Launched by Claude Desktop per MCP session

**🚨 CRITICAL**: Bridge without service = completely useless. Service without bridge = inaccessible to Claude. **BOTH REQUIRED**.

## 📦 **DUAL PACKAGE RELEASE STRATEGY**

### **Package 1: MSI Installer** 
**File**: `fastsearch-mcp-setup.msi`  
**Purpose**: Professional Windows service deployment with UAC elevation  
**Target**: System-level installation with elevated privileges  

**Contents**:
```
MSI Package Contents:
├── fastsearch-service.exe       # Windows service binary
├── config.toml                  # Service configuration template  
├── service-install.ps1          # Service registration script
├── service-uninstall.ps1        # Service removal script
└── [MSI metadata/registry]      # Windows Installer database
```

**MSI Responsibilities**:
- ✅ Request UAC elevation (one-time only)
- ✅ Install service binary to `Program Files\FastSearchMCP\`
- ✅ Register Windows service with auto-start
- ✅ Configure named pipe permissions
- ✅ Start service immediately after install
- ✅ Add proper uninstall entries to Control Panel
- ✅ Handle service upgrades and downgrades

### **Package 2: DXT Extension**
**File**: `fastsearch-mcp.dxt`  
**Purpose**: Claude Desktop extension with rich tool integration  
**Target**: User-level Claude Desktop extensions  

**Contents**:
```
fastsearch-mcp.dxt (ZIP archive):
├── manifest.json                # DXT specification with tool declarations
├── server/
│   └── fastsearch-mcp-bridge.exe   # MCP bridge binary
├── icon.png                     # Extension icon (64x64 PNG)
├── README.md                    # Extension documentation
└── LICENSE                      # MIT license
```

**DXT Responsibilities**:
- ✅ Self-documenting tools with parameter schemas
- ✅ Professional extension metadata 
- ✅ Enable/disable tool controls in Claude Desktop
- ✅ Bridge connects to service via named pipe
- ✅ Rich error handling and user feedback
- ✅ Automatic updates via Claude Desktop

## 🔧 **DETAILED IMPLEMENTATION SPECIFICATIONS**

### **MSI Installer Requirements**

**WiX Toolset Configuration** (FREE - no licensing fees, only phone support costs $500/month via FireGiant):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="FastSearch MCP" Language="1033" Version="1.0.0" 
           Manufacturer="Sandra Schimanski" UpgradeCode="[GUID]">
    
    <!-- Require elevated privileges -->
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" />
    <Condition Message="Administrator rights required for service installation.">
      Privileged
    </Condition>
    
    <!-- Service installation -->
    <Component Id="ServiceComponent" Guid="[GUID]">
      <File Id="ServiceExe" Source="fastsearch-service.exe" 
            KeyPath="yes" Checksum="yes" />
      <ServiceInstall Id="FastSearchService" 
                      Name="FastSearchMCP"
                      DisplayName="FastSearch MCP Service"
                      Description="Fast semantic search service for Claude Desktop"
                      Type="ownProcess" 
                      Start="auto" 
                      Account="LocalSystem" 
                      ErrorControl="normal" />
      <ServiceControl Id="StartService" Name="FastSearchMCP" 
                      Start="install" Stop="both" Remove="uninstall" />
    </Component>
  </Product>
</Wix>
```

**MSI Build Process**:
1. Compile `fastsearch-service.exe` for Windows x64
2. Generate WiX source files with proper GUIDs
3. Use WiX toolset to create MSI package
4. Sign MSI with code signing certificate (optional but recommended)
5. Test MSI installation in clean Windows VM

### **DXT Extension Requirements**

**Manifest.json Specification**:
```json
{
  "dxt_version": "0.1",
  "name": "fastsearch-mcp",
  "version": "1.0.0",
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
    "entry_point": "server/fastsearch-mcp-bridge.exe",
    "mcp_config": {
      "command": "server/fastsearch-mcp-bridge.exe",
      "args": [],
      "env": {
        "FASTSEARCH_PIPE_NAME": "fastsearch-mcp",
        "RUST_LOG": "info"
      }
    }
  },
  
  "compatibility": {
    "claude_desktop": ">=0.10.0",
    "platforms": ["win32"]
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
            "description": "Directory path to reindex (e.g., 'C:\\Users\\Sandra\\Documents')"
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
  },
  
  "config": {
    "service_check_timeout": {
      "type": "integer",
      "description": "Timeout in seconds for service connectivity check",
      "default": 5
    }
  }
}
```

**DXT Build Process**:
1. Compile `fastsearch-mcp-bridge.exe` for Windows x64
2. Create DXT directory structure
3. Generate manifest.json with proper tool schemas
4. Add icon.png (64x64 FastSearch logo)
5. Create ZIP archive with .dxt extension
6. Validate DXT package with `dxt validate`

## 🏗️ **CI/CD GITHUB ACTIONS STRATEGY**

### **Build Matrix Configuration**:
```yaml
name: Build FastSearch MCP Dual Packages

on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build-packages:
    runs-on: windows-latest
    strategy:
      matrix:
        include:
          # MSI Package
          - package_type: msi
            target: x86_64-pc-windows-msvc
            binary_service: fastsearch-service.exe
            binary_bridge: fastsearch-mcp-bridge.exe
            output: fastsearch-mcp-setup.msi
            
          # DXT Package  
          - package_type: dxt
            target: x86_64-pc-windows-msvc
            binary_service: null
            binary_bridge: fastsearch-mcp-bridge.exe
            output: fastsearch-mcp.dxt
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}
          
      - name: Cache Rust dependencies
        uses: Swatinem/rust-cache@v2
        
      - name: Build Rust binaries
        run: |
          cargo build --release --target ${{ matrix.target }}
          
      - name: Setup WiX Toolset (MSI only)
        if: matrix.package_type == 'msi'
        run: |
          # Install WiX toolset (FREE - no licensing required)
          dotnet tool install --global wix
          
      - name: Setup DXT CLI (DXT only) 
        if: matrix.package_type == 'dxt'
        run: |
          npm install -g @anthropic-ai/dxt
          
      - name: Build MSI Package
        if: matrix.package_type == 'msi'
        run: |
          # Copy binaries to MSI build directory
          mkdir msi-build
          copy target\${{ matrix.target }}\release\${{ matrix.binary_service }} msi-build\
          copy target\${{ matrix.target }}\release\${{ matrix.binary_bridge }} msi-build\
          copy packaging\msi\config.toml msi-build\
          
          # Build MSI with WiX (FREE toolset - professional output)
          wix build packaging\msi\fastsearch-mcp.wxs -o ${{ matrix.output }}
          
      - name: Build DXT Package
        if: matrix.package_type == 'dxt'
        run: |
          # Create DXT structure
          mkdir dxt-build\server
          copy target\${{ matrix.target }}\release\${{ matrix.binary_bridge }} dxt-build\server\
          copy packaging\dxt\manifest.json dxt-build\
          copy packaging\dxt\icon.png dxt-build\
          copy README.md dxt-build\
          copy LICENSE dxt-build\
          
          # Create DXT package
          cd dxt-build
          dxt pack --output ..\${{ matrix.output }}
          
      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.package_type }}-package
          path: ${{ matrix.output }}
          
  create-release:
    needs: build-packages
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    
    steps:
      - name: Download All Artifacts
        uses: actions/download-artifact@v4
        
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            msi-package/fastsearch-mcp-setup.msi
            dxt-package/fastsearch-mcp.dxt
          body: |
            ## FastSearch MCP Release ${{ github.ref_name }}
            
            **INSTALLATION REQUIRES BOTH PACKAGES:**
            
            1. **First**: Install `fastsearch-mcp-setup.msi` (requires UAC elevation)
            2. **Second**: Install `fastsearch-mcp.dxt` via Claude Desktop Extensions
            
            ### Changes
            - See CHANGELOG.md for detailed changes
            
            ### Requirements
            - Windows 10/11 (x64)
            - Claude Desktop 0.10.0+
            - Administrator privileges for service installation
          draft: false
          prerelease: false
```

## 🧪 **LOCAL TESTING STRATEGY**

### **Phase 1: Local Development Testing**
```powershell
# Build both binaries locally
cargo build --release

# Test MSI creation (requires WiX)
cd packaging\msi
wix build fastsearch-mcp.wxs -o ..\..\fastsearch-mcp-setup.msi

# Test DXT creation  
cd ..\dxt
dxt init
dxt pack --output ..\..\fastsearch-mcp.dxt

# Test complete installation flow
# 1. Install MSI (UAC prompt)
# 2. Verify service is running: sc query FastSearchMCP
# 3. Install DXT in Claude Desktop
# 4. Test MCP tools in Claude
```

### **Phase 2: Clean VM Testing**
- Fresh Windows 11 VM
- Install MSI first, verify service
- Install DXT second, verify Claude integration
- Test all MCP tools work correctly
- Test uninstall procedures

### **Phase 3: GitHub Actions Testing**
- Push to test branch with workflow
- Verify both packages build correctly
- Download artifacts and test locally
- Only then tag for release

## 💰 **WiX LICENSING CLARIFICATION**

**IMPORTANT**: The WiX Toolset is **completely FREE** for all commercial and non-commercial usage. The "$500/month Open Source Maintenance Fee" mentioned in WiX documentation is **ONLY** for FireGiant's phone support services, not for using the toolset itself.

**What's FREE**:
- ✅ WiX Toolset (complete installer framework)
- ✅ Command-line tools (`wix build`, `heat`, etc.)
- ✅ GitHub Actions integration (`dotnet tool install --global wix`)
- ✅ Professional MSI output with Windows service support
- ✅ All documentation and online resources

**What Costs $500/month**:
- 📞 FireGiant phone support (who needs phone support for XML configuration?!)
- 📞 Priority issue responses
- 📞 Direct developer consultation

**For FastSearch MCP**: We use the **free WiX toolset** with zero licensing costs. Professional MSI deployment without the insane support fees.

## ⚠️ **CRITICAL IMPLEMENTATION NOTES**

### **Security Considerations**:
- Service runs as LocalSystem (required for NTFS MFT access)
- Named pipe permissions must allow user access to service
- Bridge validates all service responses before sending to Claude
- No network access required (fully local)

### **Error Handling Requirements**:
- Bridge must gracefully handle service unavailable
- Service must handle bridge disconnections
- Clear error messages for missing components
- Proper logging for debugging

### **Performance Requirements**:
- Service startup: < 10 seconds
- Bridge startup: < 2 seconds  
- Search response: < 500ms for typical queries
- Memory usage: < 500MB for service under normal load

### **Compatibility Requirements**:
- Windows 10 1903+ (required for modern named pipe features)
- x64 architecture only
- Claude Desktop 0.10.0+ (DXT support)
- .NET runtime NOT required (pure Rust binaries)

## 🚀 **WINDSURF IMPLEMENTATION TASKS**

### **Task 1: MSI Package Creation**
1. **Setup WiX project structure** in `packaging/msi/`
2. **Create fastsearch-mcp.wxs** with service installation logic
3. **Add proper GUIDs** for all components
4. **Configure service permissions** for named pipe access
5. **Test MSI creation** locally with WiX toolset

### **Task 2: DXT Package Creation** 
1. **Create DXT manifest** in `packaging/dxt/manifest.json`
2. **Add tool schemas** with proper parameter validation
3. **Create extension icon** (64x64 PNG)
4. **Test DXT creation** with `dxt pack` command
5. **Validate DXT** with `dxt validate` command

### **Task 3: CI/CD Integration**
1. **Add WiX toolset** to GitHub Actions
2. **Add DXT CLI** to GitHub Actions  
3. **Update build matrix** for dual packages
4. **Test workflow** on test branch first
5. **Create release workflow** with proper artifact handling

### **Task 4: Documentation**
1. **Update README.md** with dual installation instructions
2. **Create INSTALLATION.md** with detailed steps
3. **Add troubleshooting guide** for common issues
4. **Document service architecture** for developers

**⚡ PRIORITY ORDER**: DXT first (easier), then MSI with WiX (straightforward with free toolset), then CI/CD integration, then comprehensive testing.

**WiX Advantage**: Professional MSI output with Windows service registration, UAC elevation, and Control Panel integration - all using the free WiX toolset without licensing concerns.

---

**END OF SPECIFICATION**

This document serves as the complete implementation guide for the unique dual-package architecture required by FastSearch MCP. Both packages are mandatory for functionality - neither can work alone.

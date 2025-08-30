#!/bin/bash

# Get parameters
PLATFORM=$1
VERSION=$2
BINARY_BRIDGE=$3
TARGET=$4
OUTPUT=$5

# Create DXT structure
mkdir -p dxt-build/server

# Copy bridge binary to DXT server directory
cp "target/$TARGET/release/$BINARY_BRIDGE" "dxt-build/server/"

# Generate manifest using the script
chmod +x scripts/generate_manifest.sh
./scripts/generate_manifest.sh "$PLATFORM" "$VERSION" "$BINARY_BRIDGE"

# Create extension icon (placeholder - 64x64 PNG)
# Note: This creates a simple colored square as placeholder
convert -size 64x64 xc:#FF6B35 dxt-build/icon.png 2>/dev/null || {
  # Fallback if ImageMagick not available
  echo "Warning: Could not create icon.png (ImageMagick not available)"
}

# Create README for extension
cat > dxt-build/README.md << 'EOF2'
# FastSearch MCP Extension

Lightning-fast semantic search across all your files using NTFS MFT indexing.

## Requirements

- **Windows**: FastSearch MCP Service must be installed first via MSI installer
- **Linux/macOS**: Bridge-only functionality (limited compared to Windows)

## Installation

1. Install this extension via Claude Desktop Extensions panel
2. The extension will automatically connect to the FastSearch service

## Tools

- **semantic_search**: Natural language file search
- **index_status**: Check indexing progress and statistics  
- **reindex_directory**: Force reindexing of specific paths
- **search_statistics**: Detailed performance metrics

## Support

GitHub: https://github.com/sandraschi/fastsearch-mcp
EOF2

# Copy LICENSE
cp LICENSE dxt-build/ 2>/dev/null || echo "# MIT License" > dxt-build/LICENSE

# Create DXT package (ZIP archive with .dxt extension)
cd dxt-build
dxt pack --output "../$OUTPUT" || {
  # Fallback to manual ZIP creation if dxt pack fails
  echo "DXT CLI failed, creating ZIP manually..."
  zip -r "../$OUTPUT" .
}
cd ..

# Verify DXT was created
if [[ -f "$OUTPUT" ]]; then
  echo "✅ DXT package created: $OUTPUT"
  ls -la "$OUTPUT"
else
  echo "❌ DXT package not found: $OUTPUT"
  exit 1
fi

# Support

Thank you for using FastSearch MCP! This document provides information on how to get help and support for the project.

## Table of Contents

- [Getting Help](#getting-help)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
- [Troubleshooting](#troubleshooting)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [Community Support](#community-support)
- [Professional Support](#professional-support)

## Getting Help

### Documentation

- [README](README.md) - Quick start and overview
- [DEVELOPMENT](DEVELOPMENT.md) - Development setup and workflow
- [API Reference](docs/API.md) - Detailed API documentation
- [CHANGELOG](CHANGELOG.md) - Release notes and changes

### Community Help

- [GitHub Discussions](https://github.com/yourusername/fastsearch-mcp/discussions) - Ask questions and share ideas
- [GitHub Issues](https://github.com/yourusername/fastsearch-mcp/issues) - Report bugs and request features
- [Gitter](https://gitter.im/fastsearch-mcp/community) - Real-time chat with the community

## Frequently Asked Questions (FAQ)

### General

**Q: What is FastSearch MCP?**  
A: FastSearch MCP is a high-performance file search tool that integrates with Claude Desktop, providing lightning-fast file search capabilities.

**Q: How is this different from other search tools?**  
A: FastSearch MCP uses direct NTFS MFT access for faster searches and runs as a privileged service for better performance and security.

### Installation

**Q: What are the system requirements?**  
A: FastSearch MCP requires:
- Windows 10/11 (64-bit)
- Python 3.8 or later
- Rust toolchain (for service compilation)

**Q: How do I install the latest version?**  
```bash
pip install --upgrade fastsearch-mcp
```

### Usage

**Q: How do I search for files?**  
```python
from fastsearch_mcp import FastSearch

search = FastSearch()
results = search.find("*.py")
```

**Q: How do I search within file contents?**  
A: Content search is planned for a future release. Follow our [ROADMAP](ROADMAP.md) for updates.

## Troubleshooting

### Common Issues

**Search not returning results**
- Verify the service is running
- Check if the paths you're searching are accessible
- Ensure you have proper permissions

**Installation fails**
- Make sure you have the required build tools installed
- Check that your Python version is compatible
- Review the installation logs for specific error messages

### Getting Logs

Service logs are available in the following location:
- Windows: `%LOCALAPPDATA%\FastSearch\logs\`
- Linux/macOS: `~/.local/share/fastsearch/logs/`

Enable debug logging:
```bash
export FASTSEARCH_LOG_LEVEL=debug
fastsearch-mcp
```

## Reporting Issues

Before reporting an issue, please:

1. Check the [existing issues](https://github.com/yourusername/fastsearch-mcp/issues) to see if it's already reported
2. Update to the latest version
3. Check the documentation and FAQ

When reporting an issue, please include:

- Steps to reproduce the issue
- Expected and actual behavior
- Version of FastSearch MCP
- Operating system and version
- Any error messages or logs

## Feature Requests

We welcome feature requests! Please:

1. Check the [ROADMAP](ROADMAP.md) to see if it's already planned
2. Search [existing issues](https://github.com/yourusername/fastsearch-mcp/issues) to avoid duplicates
3. Open a new issue with a clear description of the feature and its benefits

## Community Support

Join our community for help and discussions:

- [GitHub Discussions](https://github.com/yourusername/fastsearch-mcp/discussions)
- [Gitter](https://gitter.im/fastsearch-mcp/community)
- [Twitter](https://twitter.com/fastsearchmcp)

## Professional Support

For professional support, enterprise features, or custom development, please contact us at [support@example.com](mailto:support@example.com).

### Support Plans

| Plan | Features | Price |
|------|----------|-------|
| Community | Community support, GitHub issues | Free |
| Basic | Email support, 3 business day response | $99/month |
| Professional | Priority support, 1 business day response | $299/month |
| Enterprise | 24/7 support, dedicated engineer | Custom |

## Security Issues

Please report security issues to [security@example.com](mailto:security@example.com) instead of the public issue tracker. See our [Security Policy](SECURITY.md) for more information.

## Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for more information on how to get involved.

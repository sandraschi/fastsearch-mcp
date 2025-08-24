# Development Guide

This guide provides detailed instructions for setting up a development environment and working with the FastSearch MCP codebase.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Debugging](#debugging)
- [Code Style](#code-style)
- [Documentation](#documentation)
- [Releasing](#releasing)

## Prerequisites

- Python 3.8+
- Rust toolchain (for service development)
- Git
- [Poetry](https://python-poetry.org/) (Python dependency management)
- [pre-commit](https://pre-commit.com/)

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/fastsearch-mcp.git
   cd fastsearch-mcp
   ```

2. **Set up Python environment**
   ```bash
   # Install Poetry if you haven't already
   pip install poetry
   
   # Install project dependencies
   poetry install
   
   # Activate the virtual environment
   poetry shell
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Set up Rust toolchain (for service development)**
   ```bash
   # Install Rust if you haven't already
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Add required Rust components
   rustup component add rustfmt clippy
   ```

## Project Structure

```
fastsearch-mcp/
├── .github/              # GitHub workflows and templates
├── fastsearch_mcp/       # Python package source
│   ├── __init__.py       # Package metadata and version
│   ├── server.py         # MCP server implementation
│   ├── service.py        # Service client implementation
│   └── utils/            # Utility modules
├── service/              # Rust service code
│   ├── src/              # Source files
│   └── Cargo.toml        # Rust project configuration
├── tests/                # Test suite
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml        # Python project configuration
└── README.md
```

## Development Workflow

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the code style guidelines
   - Write tests for new functionality
   - Update documentation as needed

3. **Run tests and checks**
   ```bash
   # Run Python tests
   pytest
   
   # Run Rust tests
   cd service && cargo test && cd ..
   
   # Run linters
   pre-commit run --all-files
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push your changes**
   ```bash
   git push -u origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Follow the PR template
   - Request reviews from maintainers
   - Address any feedback

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=fastsearch_mcp --cov-report=term-missing

# Run a specific test file
pytest tests/test_server.py

# Run a specific test method
pytest tests/test_server.py::TestServer::test_search
```

### Writing Tests

- Place test files in the `tests/` directory
- Follow the naming convention `test_*.py` for test files
- Use descriptive test method names
- Include docstrings explaining what each test verifies

## Debugging

### Python Debugging

Use the built-in `pdb` debugger:

```python
import pdb; pdb.set_trace()  # Add this where you want to start debugging
```

Or use VS Code's debugger with the following launch configuration:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastSearch MCP",
            "type": "python",
            "request": "launch",
            "module": "fastsearch_mcp.server",
            "justMyCode": true
        }
    ]
}
```

### Rust Debugging

Use `rust-lldb` or VS Code with the Rust Analyzer extension:

```bash
# Build with debug symbols
cargo build

# Debug with lldb
lldb target/debug/fastsearch-service
```

## Code Style

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for all function signatures
- Keep lines under 100 characters
- Use docstrings for all public functions and classes
- Run `black .` to format code

### Rust

- Follow the [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Run `cargo fmt` to format code
- Run `cargo clippy` for additional lints

## Documentation

- Update `CHANGELOG.md` for all user-facing changes
- Add docstrings to all public functions and classes
- Update README.md for major changes
- Add inline comments for complex logic

## Releasing

See [RELEASING.md](RELEASING.md) for detailed release instructions.

# Contributing to FastSearch MCP

Thank you for your interest in contributing to FastSearch MCP! We welcome contributions from the community to help improve this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
   ```bash
   git clone https://github.com/yourusername/fastsearch-mcp.git
   cd fastsearch-mcp
   ```
3. Set up the development environment:
   ```bash
   # Install Python dependencies
   pip install -e .[dev]
   
   # Install pre-commit hooks
   pre-commit install
   ```

## Development Workflow

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the code style guidelines

3. Run tests to ensure nothing is broken
   ```bash
   pytest
   ```

4. Commit your changes with a descriptive message:
   ```bash
   git commit -m "Add feature: your feature description"
   ```

5. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Open a Pull Request against the `main` branch

## Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting
- **Flake8** for linting
- **Mypy** for static type checking

These are enforced via pre-commit hooks. To run them manually:

```bash
pre-commit run --all-files
```

## Testing

We use `pytest` for testing. To run the test suite:

```bash
pytest
```

For more detailed output:

```bash
pytest -v
```

To run tests with coverage:

```bash
pytest --cov=fastsearch_mcp tests/
```

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build
2. Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations, and container parameters
3. Increase the version number in `fastsearch_mcp/__init__.py` and the CHANGELOG.md to the new version that this Pull Request would represent
4. The PR must pass all CI checks before it can be merged
5. You may merge the PR once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the reviewer to merge it for you

## Reporting Issues

When reporting issues, please include:

1. The version of FastSearch MCP you're using
2. Your operating system and version
3. Steps to reproduce the issue
4. Any relevant error messages or logs

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

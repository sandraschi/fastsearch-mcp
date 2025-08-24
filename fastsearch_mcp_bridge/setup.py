from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fastsearch-mcp",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="FastSearch MCP 2.11.3 compliant server implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fastsearch-mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=1.8.0,<2.0.0",
        "aiofiles>=0.7.0",
        "typing-extensions>=3.10.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.15.0",
            "black>=21.7b0",
            "mypy>=0.910",
            "flake8>=3.9.0",
            "pytest-cov>=2.12.0",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=0.5.2",
            "sphinx-autodoc-typehints>=1.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "fastsearch-mcp=fastsearch_mcp.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

#!/usr/bin/env python3
"""Generate llms-full.txt — aggregated project docs for LLM context."""

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent

CORE_DOCS = [
    ("README.md", "README"),
    ("docs/STATUS_REPORT.md", "Status Report"),
    ("docs/TECHNICAL_ARCHITECTURE.md", "Technical Architecture"),
    ("docs/INSTALL.md", "Installation Guide"),
    ("docs/PRODUCT_REQUIREMENTS.md", "Product Requirements"),
    ("docs/ROADMAP.md", "Roadmap"),
    ("docs/SECURITY.md", "Security"),
    ("docs/CONTRIBUTING.md", "Contributing"),
]

IGNORE_PATTERNS = [
    "node_modules", ".git", "__pycache__", ".venv", "build",
    ".windsurf", ".cursor", ".trash",
]

IGNORE_FILES = {
    "package-lock.json", "uv.lock", ".mcpbignore",
}


def should_include(path: Path) -> bool:
    for pat in IGNORE_PATTERNS:
        if pat in path.parts:
            return False
    if path.name in IGNORE_FILES:
        return False
    if path.suffix not in (".md", ".py", ".toml", ".json", ".yml", ".yaml", ".txt", ".ps1", ".bat", ".cfg", ".ini", ".cff"):
        return False
    return True


def main():
    lines = [f"# FastSearch MCP v0.5.0 — Full Documentation", f"Generated: {datetime.now().isoformat()}", ""]

    # Core docs
    for rel_path, label in CORE_DOCS:
        path = ROOT / rel_path
        if path.exists():
            lines.append(f"## {label}")
            lines.append(f"Source: {rel_path}")
            lines.append("```")
            lines.append(path.read_text(encoding="utf-8").rstrip())
            lines.append("```")
            lines.append("")

    # Key source files
    lines.append("## Key Source Files")
    src_files = [
        "src/fastsearch_mcp/__init__.py",
        "src/fastsearch_mcp/mcp_instance.py",
        "src/fastsearch_mcp/server.py",
        "src/fastsearch_mcp/transport.py",
        "src/fastsearch_mcp/prompts.py",
        "src/fastsearch_mcp/skills.py",
        "src/fastsearch_mcp/pipe_client.py",
        "pyproject.toml",
    ]
    for rel_path in src_files:
        path = ROOT / rel_path
        if path.exists():
            lines.append(f"### {rel_path}")
            lines.append("```")
            lines.append(path.read_text(encoding="utf-8").rstrip())
            lines.append("```")
            lines.append("")

    output = ROOT / "llms-full.txt"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {output} ({len(lines)} lines, {output.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

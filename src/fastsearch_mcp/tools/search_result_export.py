"""
Search result export tool for FastSearch MCP.

Exports search results to various formats (CSV, JSON, Markdown, TSV) for
external analysis, sharing, or documentation purposes. Also supports advanced
formats (PDF, Word, HTML, EPUB) via Pandoc when available.
"""

import asyncio
import csv
import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastsearch_mcp.mcp_instance import mcp

logger = logging.getLogger(__name__)

# Formats that require Pandoc
PANDOC_FORMATS = ["pdf", "docx", "html", "epub", "odt", "rtf", "latex"]

# Formats that work without Pandoc
STANDARD_FORMATS = ["csv", "json", "markdown", "tsv"]


def _format_timestamp(timestamp: Any) -> str:
    """Format timestamp to ISO string."""
    if timestamp is None:
        return ""
    try:
        if isinstance(timestamp, str):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(float(timestamp))
            return dt.isoformat()
        else:
            return str(timestamp)
    except Exception:
        return str(timestamp)


def _format_size(size: Any) -> str:
    """Format size to human-readable string."""
    if size is None:
        return ""
    try:
        size_int = int(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_int < 1024.0:
                return f"{size_int:.2f} {unit}"
            size_int /= 1024.0
        return f"{size_int:.2f} PB"
    except Exception:
        return str(size)


def _check_pandoc_available() -> bool:
    """Check if Pandoc is available on the system."""
    try:
        result = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


async def _convert_with_pandoc(markdown_content: str, output_format: str, output_path: str) -> dict[str, Any]:
    """Convert markdown content to another format using Pandoc."""
    try:
        # Create temporary markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as temp_md:
            temp_md.write(markdown_content)
            temp_md_path = temp_md.name

        try:
            # Run pandoc conversion
            cmd = [
                "pandoc",
                temp_md_path,
                "-o",
                output_path,
                "-f",
                "markdown",
                "-t",
                output_format,
            ]

            # Add PDF-specific options
            if output_format == "pdf":
                cmd.extend(["--pdf-engine=pdflatex"])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            _stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore")
                return {
                    "success": False,
                    "error": f"Pandoc conversion failed: {error_msg}",
                }

            return {"success": True}

        finally:
            # Clean up temporary file
            try:
                Path(temp_md_path).unlink()
            except Exception:
                pass

    except TimeoutError:
        return {
            "success": False,
            "error": "Pandoc conversion timed out (60 seconds)",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Pandoc conversion error: {e!s}",
        }


@mcp.tool
async def search_result_export(
    results: list[dict[str, Any]],
    export_format: str = "csv",
    output_path: str | None = None,
    include_columns: list[str] | None = None,
    exclude_columns: list[str] | None = None,
    include_metadata: bool = True,
    search_query: str | None = None,
) -> dict[str, Any]:
    """Export search results to various formats for external analysis.

    Exports search results to CSV, JSON, Markdown, or TSV formats. Useful for
    sharing results, creating reports, or feeding data into other tools. This
    tool operates on search results (post-processing) and does not perform
    additional searches.

    Prerequisites:
        - Search results from fastsearch_search or fastsearch_search_advanced
        - Each result dictionary must contain at minimum a 'path' key
        - For file output: write permissions to output_path directory

    Parameters:
        results: List of search result dictionaries from fastsearch_search or
            fastsearch_search_advanced. Each result should contain at minimum a
            'path' key. Optional keys: 'size', 'modified', 'created', 'attributes'.
            Required: List of dictionaries with file metadata.

        export_format: Export format (default: 'csv'). Standard formats (no dependencies):
            'csv', 'json', 'markdown', 'tsv'. Pandoc formats (requires Pandoc installed):
            'pdf', 'docx', 'html', 'epub', 'odt', 'rtf', 'latex'. Case-insensitive.
            Pandoc formats require output_path and will fail if Pandoc is not available.

        output_path: Path where exported file should be saved. If None, returns
            content as string in response (default: None). Examples:
            'C:\\temp\\results.csv', 'D:\\exports\\data.json'. Parent directory
            will be created if it doesn't exist.

        include_columns: List of column names to include. If None, includes all
            available columns: path, size, modified, created, attributes
            (default: None). Examples: ['path', 'size'], ['path', 'modified'].
            Columns not present in results are silently ignored.

        exclude_columns: List of column names to exclude from export
            (default: None). Examples: ['attributes'], ['created', 'modified'].
            Applied after include_columns filtering.

        include_metadata: Include search metadata (query, timestamp, result count)
            in exported file (default: True). Adds header section with search
            query, export date, and result count.

        search_query: Original search query for metadata (default: None).
            Used in metadata header if include_metadata is True. Examples:
            '*.log', 'test*.txt', 'C:\\Windows\\*.dll'.

    Returns:
        Dictionary containing:
            success: Boolean indicating operation success. True if export completed
                successfully, False if an error occurred.

            format: Export format used (lowercase string). Standard formats: "csv", "json",
                "markdown", "tsv". Pandoc formats: "pdf", "docx", "html", "epub", "odt",
                "rtf", "latex". Same as export_format parameter (normalized).

            pandoc_used: Boolean indicating if Pandoc was used for conversion (only present
                for Pandoc formats). True if Pandoc was used, not present for standard formats.

            output_path: Path where file was saved (only if output_path provided).
                Absolute path to the exported file. Example: "C:\\temp\\logs.csv".

            content: Exported content as string (only if output_path not provided and
                format is not a Pandoc format). The full exported content ready to use
                or save. For JSON, this is formatted JSON string. For CSV/TSV/Markdown,
                this is the formatted text. Pandoc formats always require output_path
                and do not return content.

            row_count: Number of rows exported (integer). Total number of result rows
                included in the export.

            columns: List of columns included in export. Contains column names that
                were actually exported. May include formatted columns like "size_formatted"
                or "modified_formatted" if those base columns were included.

            error: Error message if success is False. Describes what went wrong and
                may include suggestions for resolution.

    Usage:
        This tool is used when you need to export search results for external
        analysis, sharing, or documentation. It works by processing the results
        list, formatting columns (size and dates get formatted versions),
        and generating format-specific output. Best practices include:
        - Use CSV for spreadsheet analysis (Excel-compatible)
        - Use JSON for programmatic processing
        - Use Markdown for documentation (or as intermediate format)
        - Use TSV for tab-delimited compatibility
        - Use PDF/Word/HTML for professional reports (requires Pandoc)
        - Use EPUB for e-book format (requires Pandoc)

        Common scenarios:
        - Export search results to Excel-compatible CSV
        - Generate JSON for API integration
        - Create Markdown reports for documentation
        - Generate PDF reports for sharing (requires Pandoc)
        - Export to Word format for editing (requires Pandoc)
        - Create HTML reports for web viewing (requires Pandoc)
        - Filter columns before export for focused analysis

        Pandoc formats (PDF, Word, HTML, EPUB, etc.) require:
        - Pandoc installed on the system (https://pandoc.org/installing.html)
        - output_path parameter (cannot return content string)
        - For PDF: LaTeX distribution (e.g., MiKTeX, TeX Live) may be required

    Examples:
        Export to CSV file:
            results = await fastsearch_search("*.log", path="C:\\Windows")
            export = await search_result_export(
                results["results"],
                export_format="csv",
                output_path="C:\\temp\\logs.csv",
                search_query="*.log"
            )
            # Returns: {'success': True, 'output_path': 'C:\\temp\\logs.csv',
            #          'format': 'csv', 'row_count': 150, 'columns': [...]}

        Export to JSON (return content):
            export = await search_result_export(
                results["results"],
                export_format="json",
                include_columns=["path", "size"]
            )
            # Returns: {'success': True, 'content': '{"metadata": {...},
            #          "results": [...]}', 'format': 'json', ...}

        Export Markdown with selected columns:
            export = await search_result_export(
                results["results"],
                export_format="markdown",
                include_columns=["path", "size", "modified"],
                exclude_columns=["attributes"],
                include_metadata=True
            )
            # Returns: {'success': True, 'content': '# Search Results...', ...}

        Export to PDF (requires Pandoc):
            export = await search_result_export(
                results["results"],
                export_format="pdf",
                output_path="C:\\temp\\report.pdf",
                search_query="*.log"
            )
            # Returns: {'success': True, 'output_path': 'C:\\temp\\report.pdf',
            #          'format': 'pdf', 'pandoc_used': True, ...}

        Export to Word document (requires Pandoc):
            export = await search_result_export(
                results["results"],
                export_format="docx",
                output_path="C:\\temp\\report.docx"
            )
            # Returns: {'success': True, 'output_path': 'C:\\temp\\report.docx',
            #          'format': 'docx', 'pandoc_used': True, ...}

    Errors:
        Common errors and solutions:
        - No results to export: Ensure results list is not empty before calling
        - Unsupported format: Use one of the supported formats (standard or Pandoc)
        - Pandoc not available: Install Pandoc from https://pandoc.org/installing.html
          for PDF, Word, HTML, EPUB, and other Pandoc formats
        - Pandoc format without output_path: Pandoc formats require output_path parameter
        - Pandoc conversion failed: Check Pandoc installation and LaTeX (for PDF)
        - Failed to write export file: Check write permissions and disk space
        - Invalid output_path: Ensure parent directory exists or is writable
        - Pandoc timeout: Conversion exceeded 60 seconds (try smaller result sets)

    See Also:
        - fastsearch_search: Generate search results to export
        - fastsearch_search_advanced: Advanced search with filters
        - search_result_filter: Filter results before export
        - search_result_analyze: Analyze results before export
    """
    try:
        if not results:
            return {
                "success": False,
                "error": "No results to export",
                "row_count": 0,
            }

        format_lower = export_format.lower()
        all_supported_formats = STANDARD_FORMATS + PANDOC_FORMATS

        if format_lower not in all_supported_formats:
            standard_list = ", ".join(STANDARD_FORMATS)
            pandoc_list = ", ".join(PANDOC_FORMATS)
            return {
                "success": False,
                "error": (
                    f"Unsupported format: {export_format}. "
                    f"Standard formats: {standard_list}. "
                    f"Pandoc formats (requires Pandoc): {pandoc_list}"
                ),
            }

        # Check if Pandoc is needed and available
        requires_pandoc = format_lower in PANDOC_FORMATS
        if requires_pandoc:
            pandoc_available = _check_pandoc_available()
            if not pandoc_available:
                return {
                    "success": False,
                    "error": (
                        f"Format '{format_lower}' requires Pandoc, but Pandoc is not available. "
                        "Please install Pandoc from https://pandoc.org/installing.html. "
                        f"Standard formats available without Pandoc: {', '.join(STANDARD_FORMATS)}"
                    ),
                    "pandoc_required": True,
                }

        # Determine columns to include
        all_columns = set()
        for result in results:
            all_columns.update(result.keys())

        # Default columns if not specified
        default_columns = ["path", "size", "modified", "created", "attributes"]
        available_columns = [col for col in default_columns if col in all_columns]
        available_columns.extend([col for col in all_columns if col not in default_columns])

        if include_columns:
            columns = [col for col in include_columns if col in all_columns]
        else:
            columns = available_columns.copy()

        if exclude_columns:
            columns = [col for col in columns if col not in exclude_columns]

        if not columns:
            columns = ["path"]  # At minimum, include path

        # Prepare data rows
        rows = []
        for result in results:
            row = {}
            for col in columns:
                value = result.get(col, "")
                # Format specific columns
                if col == "size" and value:
                    row[col] = value
                    row[f"{col}_formatted"] = _format_size(value)
                elif col in ["modified", "created"] and value:
                    row[col] = value
                    row[f"{col}_formatted"] = _format_timestamp(value)
                else:
                    row[col] = value
            rows.append(row)

        # Add formatted columns to column list if they exist
        export_columns = columns.copy()
        if "size" in columns:
            export_columns.append("size_formatted")
        if "modified" in columns:
            export_columns.append("modified_formatted")
        if "created" in columns:
            export_columns.append("created_formatted")

        # Generate export content
        content_lines = []

        # Add metadata header if requested
        if include_metadata:
            if format_lower in ["markdown", *PANDOC_FORMATS]:
                content_lines.append("# Search Results Export")
                content_lines.append("")
                if search_query:
                    content_lines.append(f"**Search Query:** {search_query}")
                content_lines.append(f"**Export Date:** {datetime.now().isoformat()}")
                content_lines.append(f"**Result Count:** {len(results)}")
                content_lines.append("")
            elif format_lower in ["csv", "tsv"]:
                content_lines.append("# Search Results Export")
                content_lines.append(f"# Search Query: {search_query or 'N/A'}")
                content_lines.append(f"# Export Date: {datetime.now().isoformat()}")
                content_lines.append(f"# Result Count: {len(results)}")
                content_lines.append("")

        # Generate format-specific content
        if format_lower == "csv":
            import io

            meta = "\n".join(content_lines) + "\n" if content_lines else ""
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=export_columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            content = meta + output.getvalue()
            output.close()

        elif format_lower == "tsv":
            import io

            meta = "\n".join(content_lines) + "\n" if content_lines else ""
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=export_columns, delimiter="\t", extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            content = meta + output.getvalue()
            output.close()

        elif format_lower == "json":
            export_data = {
                "metadata": {
                    "search_query": search_query,
                    "export_date": datetime.now().isoformat(),
                    "result_count": len(results),
                },
                "results": rows,
            }
            content = json.dumps(export_data, indent=2, ensure_ascii=False)

        elif format_lower == "markdown" or format_lower in PANDOC_FORMATS:
            # Markdown table (used for markdown output or as intermediate for Pandoc)
            content_lines.append("| " + " | ".join(export_columns) + " |")
            content_lines.append("| " + " | ".join(["---"] * len(export_columns)) + " |")
            for row in rows:
                row_values = []
                for col in export_columns:
                    value = row.get(col, "")
                    # Escape pipe characters in markdown
                    value_str = str(value).replace("|", "\\|")
                    row_values.append(value_str)
                content_lines.append("| " + " | ".join(row_values) + " |")
            content = "\n".join(content_lines)

        # Handle Pandoc formats (require output_path)
        if requires_pandoc:
            if not output_path:
                return {
                    "success": False,
                    "error": (
                        f"Format '{format_lower}' requires output_path. Pandoc formats must be written to a file."
                    ),
                }

            # Use the markdown content we just generated
            markdown_content = content

            # Convert using Pandoc
            try:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)

                conversion_result = await _convert_with_pandoc(
                    markdown_content, format_lower, str(output_file.absolute())
                )

                if not conversion_result.get("success"):
                    return {
                        "success": False,
                        "error": conversion_result.get("error", "Pandoc conversion failed"),
                        "format": format_lower,
                        "row_count": len(results),
                    }

                logger.info(f"Exported {len(results)} results to {output_path} using Pandoc")
                return {
                    "success": True,
                    "format": format_lower,
                    "output_path": str(output_file.absolute()),
                    "row_count": len(results),
                    "columns": export_columns,
                    "pandoc_used": True,
                }

            except Exception as e:
                logger.error(f"Error converting with Pandoc: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Failed to convert with Pandoc: {e!s}",
                    "format": format_lower,
                    "row_count": len(results),
                }

        # Write to file if output_path provided
        if output_path:
            try:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Exported {len(results)} results to {output_path}")
                return {
                    "success": True,
                    "format": format_lower,
                    "output_path": str(output_file.absolute()),
                    "row_count": len(results),
                    "columns": export_columns,
                }
            except Exception as e:
                logger.error(f"Error writing export file: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Failed to write export file: {e!s}",
                    "format": format_lower,
                    "row_count": len(results),
                }
        else:
            # Return content in response
            return {
                "success": True,
                "format": format_lower,
                "content": content,
                "row_count": len(results),
                "columns": export_columns,
            }

    except Exception as e:
        logger.error(f"Error exporting search results: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to export search results: {e!s}",
            "format": export_format,
            "row_count": 0,
        }

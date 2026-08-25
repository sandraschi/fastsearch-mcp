"""
REST API bridge for the web_sota frontend.
Exposes GET /health, GET /tools, POST /tools/:name, GET /file, and LLM endpoints for chat and analysis.
"""

import base64
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query, Response

from fastsearch_mcp.mcp_instance import mcp

logger = logging.getLogger(__name__)

router = APIRouter()

# Max size for file preview: 10 MB binary/media, 2 MB text
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TEXT_BYTES = 2 * 1024 * 1024

TEXT_EXTENSIONS = frozenset(
    ".txt .log .md .json .xml .py .js .ts .tsx .html .htm .css .csv .ini .cfg .yml .yaml .rst .sh .ps1 .bat .cmd .env .gitignore".split()
)
IMAGE_EXTENSIONS = frozenset(".jpg .jpeg .png .gif .webp .bmp .svg .ico".split())
VIDEO_EXTENSIONS = frozenset(".mp4 .webm .mov .avi .mkv .m4v".split())
AUDIO_EXTENSIONS = frozenset(".mp3 .wav .ogg .m4a .flac .aac".split())


def _resolve_and_validate_path(path_str: str) -> Path:
    """Resolve to absolute path and ensure it is under an allowed root (Windows drive)."""
    if not path_str or not path_str.strip():
        raise HTTPException(status_code=400, detail="path is required")
    p = Path(path_str.strip()).resolve()
    try:
        p = p.resolve()
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"invalid path: {e}") from e
    if not p.is_absolute():
        raise HTTPException(status_code=400, detail="path must be absolute")
    # Allow only local drives (e.g. C:\, D:\); reject UNC and relative
    parts = p.parts
    if not parts:
        raise HTTPException(status_code=400, detail="invalid path")
    root = parts[0]
    if not (len(root) >= 2 and root[0].isalpha() and root[1] == ":"):
        raise HTTPException(status_code=403, detail="only local drive paths are allowed")
    return p


def _detect_type(path: Path, raw: bytes) -> tuple[str, str]:
    """Return (type, mime). type is text, image, video, audio, or binary."""
    ext = path.suffix.lower() if path.suffix else ""
    if ext in IMAGE_EXTENSIONS:
        mime = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "bmp": "image/bmp",
            "svg": "image/svg+xml",
            "ico": "image/x-icon",
        }.get(ext, "application/octet-stream")
        return "image", mime
    if ext in VIDEO_EXTENSIONS:
        mime = {
            "mp4": "video/mp4",
            "webm": "video/webm",
            "mov": "video/quicktime",
            "avi": "video/x-msvideo",
            "mkv": "video/x-matroska",
            "m4v": "video/mp4",
        }.get(ext, "video/mp4")
        return "video", mime
    if ext in AUDIO_EXTENSIONS:
        mime = (
            "audio/mpeg"
            if ext == "mp3"
            else "audio/wav"
            if ext == "wav"
            else "audio/ogg"
            if ext == "ogg"
            else "audio/mp4"
            if ext in (".m4a", ".aac")
            else "audio/flac"
            if ext == "flac"
            else "application/octet-stream"
        )
        return "audio", mime
    if ext in TEXT_EXTENSIONS or not ext:
        try:
            raw.decode("utf-8")
            return "text", "text/plain; charset=utf-8"
        except UnicodeDecodeError:
            pass
    return "binary", "application/octet-stream"


def _tool_to_dict(tool: Any) -> dict:
    """Serialize a FastMCP Tool for JSON (skip non-serializable fields)."""
    out = {
        "name": getattr(tool, "name", None),
        "description": getattr(tool, "description", None) or "",
        "parameters": getattr(tool, "parameters", None) or {},
    }
    if getattr(tool, "title", None):
        out["title"] = tool.title
    return out


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "fastsearch-mcp"}


@router.get("/tools")
async def list_tools() -> list[dict]:
    """List registered MCP tools for the web UI."""
    try:
        tools = await mcp.list_tools()
        return [_tool_to_dict(t) for t in tools]
    except Exception:
        logger.exception("list_tools failed")
        return []


@router.post("/tools/{name}")
async def call_tool(name: str, body: dict) -> dict:
    """Call an MCP tool by name. Body: { \"arguments\": { ... } }."""
    args = body.get("arguments") if isinstance(body.get("arguments"), dict) else {}
    try:
        result = await mcp.call_tool(name, arguments=args or None)
        if hasattr(result, "structured_content") and result.structured_content is not None:
            return result.structured_content
        if hasattr(result, "content") and result.content:
            first = result.content[0]
            text = getattr(first, "text", None)
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {"text": text}
        return result.model_dump() if hasattr(result, "model_dump") else {"result": str(result)}
    except Exception as e:
        logger.warning("call_tool %s failed: %s", name, e)
        err_msg = str(e)
        is_down = "service is not running" in err_msg.lower() or "not connected" in err_msg.lower()
        return {
            "success": False,
            "error": err_msg,
            "service_down": is_down,
        }


@router.post("/search")
async def api_search(body: dict) -> dict:
    """Direct search endpoint for web UI dedicated Search page.
    Body: { pattern: str, directory?: str, max_results?: int, pagination_mode?: str, page?: int, page_size?: int }
    """
    pattern = body.get("pattern", "*")
    directory = body.get("directory", "C:\\")
    max_results = int(body.get("max_results", 100))
    pagination_mode = body.get("pagination_mode")
    page = int(body.get("page", 1))
    page_size = int(body.get("page_size", 1000))

    try:
        from fastsearch_mcp.service_client import is_service_running, search_files
        from fastsearch_mcp.service_ensure import ensure_service_available

        if not is_service_running():
            from fastsearch_mcp.service_ensure import ensure_service_available

            ensured = await ensure_service_available(start_if_needed=True)
            if not ensured.get("success") and not is_service_running():
                return {
                    "success": False,
                    "service_down": True,
                    "error": "FastSearch C++ Windows Service is disconnected. Direct NTFS MFT disk access requires the elevated background service. Run 'sc start FastSearchMCP' or 'just install-service' in an elevated Administrator prompt.",
                    "results": [],
                    "count": 0,
                }

        res = await search_files(
            pattern=pattern,
            directory=directory,
            max_results=max_results,
            pagination_mode=pagination_mode,
            page=page,
            page_size=page_size,
        )
        return {"success": True, "service_down": False, **res}
    except Exception as e:
        logger.warning("api_search failed: %s", e)
        return {
            "success": False,
            "service_down": "not running" in str(e).lower(),
            "error": str(e),
            "results": [],
            "count": 0,
        }


@router.get("/service/status")
async def api_service_status() -> dict:
    """Get service status directly without MCP overhead."""
    try:
        from fastsearch_mcp.service_client import get_service_status
        from fastsearch_mcp.service_ensure import ensure_service_available

        status = await get_service_status()
        if not status.get("running"):
            ensured = await ensure_service_available(start_if_needed=True)
            if ensured.get("success"):
                status = await get_service_status()
        return {"success": True, **status}
    except Exception as e:
        return {"success": False, "running": False, "error": str(e)}


@router.post("/service/start")
async def api_service_start() -> dict:
    """Start FastSearch service."""
    try:
        from fastsearch_mcp.service_client import start_service

        ok = await start_service()
        return {"success": ok, "message": "Service start command sent" if ok else "Failed to start service"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/service/stop")
async def api_service_stop() -> dict:
    """Stop FastSearch service."""
    try:
        from fastsearch_mcp.service_client import stop_service

        ok = await stop_service()
        return {"success": ok, "message": "Service stop command sent" if ok else "Failed to stop service"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/service/restart")
async def api_service_restart() -> dict:
    """Restart FastSearch service."""
    try:
        import asyncio

        from fastsearch_mcp.service_client import start_service, stop_service

        await stop_service()
        await asyncio.sleep(1.0)
        ok = await start_service()
        return {"success": ok, "message": "Service restarted" if ok else "Failed to restart service"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/file")
async def get_file(path: str = Query(..., description="Absolute path to file")) -> dict:
    """Return file content for preview: text as string, binary/image/video/audio as base64."""
    p = _resolve_and_validate_path(path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="file not found")
    if not p.is_file():
        raise HTTPException(status_code=400, detail="not a file")
    try:
        raw = p.read_bytes()
    except OSError as e:
        logger.warning("read_file failed path=%s err=%s", p, e)
        raise HTTPException(status_code=403, detail="cannot read file") from e
    size = len(raw)
    max_bytes = MAX_FILE_BYTES
    kind, mime = _detect_type(p, raw)
    if kind == "text":
        max_bytes = min(max_bytes, MAX_TEXT_BYTES)
    if size > max_bytes:
        raw = raw[:max_bytes]
        # Trim incomplete trailing multi-byte UTF-8 character
        while raw and (raw[-1] & 0xC0) == 0x80:
            raw = raw[:-1]
        if raw and raw[-1] & 0x80:
            # Check if last byte is a multi-byte start without all continuation bytes
            b = raw[-1]
            if (b & 0xE0) == 0xC0 and len(raw) < max_bytes:
                raw = raw[:-1]  # 2-byte char start, cut
            elif (b & 0xF0) == 0xE0 and len(raw) < max_bytes - 1:
                raw = raw[:-1]  # 3-byte char start, cut
            elif (b & 0xF8) == 0xF0 and len(raw) < max_bytes - 2:
                raw = raw[:-1]  # 4-byte char start, cut
    if kind == "text":
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            content = raw.decode("utf-8", errors="replace")
    else:
        content = base64.b64encode(raw).decode("ascii")
    return {"path": str(p), "type": kind, "mime": mime, "content": content, "size": size, "truncated": size > max_bytes}


# ---------------------------------------------------------------------------
# Local LLM stack: discovery, chat, and search-result analysis
# ---------------------------------------------------------------------------

DEFAULT_OLLAMA_BASE = "http://localhost:11434"
DEFAULT_LMSTUDIO_BASE = "http://localhost:1234"


@router.get("/llm/models")
async def llm_models(
    provider: str = Query("ollama", description="ollama or lm_studio"),
    base_url: str | None = Query(None, description="Override base URL"),
) -> dict:
    """Discover models from Ollama or LM Studio (OpenAI-compatible)."""
    base = base_url or (DEFAULT_OLLAMA_BASE if provider == "ollama" else DEFAULT_LMSTUDIO_BASE)
    models: list[str] = []
    error: str | None = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "ollama":
                r = await client.get(f"{base.rstrip('/')}/api/tags")
                if r.status_code == 200:
                    data = r.json()
                    models = [m["name"] for m in data.get("models", [])]
                else:
                    error = f"Ollama returned {r.status_code}"
            else:
                r = await client.get(f"{base.rstrip('/')}/v1/models")
                if r.status_code == 200:
                    data = r.json()
                    models = [m.get("id", "") for m in data.get("data", [])]
                else:
                    error = f"LM Studio returned {r.status_code}"
    except Exception as e:
        logger.warning("llm models discovery failed: %s", e)
        error = str(e)
    return {"provider": provider, "base_url": base, "models": models, "error": error}


@router.post("/llm/chat")
async def llm_chat(body: dict) -> dict:
    """Send messages to local LLM. Body: { messages: [{role, content}], model?, provider?, base_url? }."""
    messages = body.get("messages") or []
    model = body.get("model") or ""
    provider = body.get("provider") or "ollama"
    base_url = body.get("base_url") or (DEFAULT_OLLAMA_BASE if provider == "ollama" else DEFAULT_LMSTUDIO_BASE)
    base = base_url.rstrip("/")
    if not messages:
        raise HTTPException(status_code=400, detail="messages required")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            if provider == "ollama":
                r = await client.post(
                    f"{base}/api/chat",
                    json={"model": model or "llama3.2", "stream": False, "messages": messages},
                )
                if r.status_code != 200:
                    raise HTTPException(status_code=r.status_code, detail=r.text[:500])
                data = r.json()
                content = (data.get("message") or {}).get("content") or ""
                return {"content": content}
            else:
                r = await client.post(
                    f"{base}/v1/chat/completions",
                    json={"model": model or "local", "stream": False, "messages": messages},
                )
                if r.status_code != 200:
                    raise HTTPException(status_code=r.status_code, detail=r.text[:500])
                data = r.json()
                choice = (data.get("choices") or [None])[0]
                content = (choice.get("message") or {}).get("content") or "" if choice else ""
                return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("llm chat failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/llm/analyze")
async def llm_analyze(body: dict) -> dict:
    """Run advanced analysis on search results using the configured LLM. Body: { search_results, prompt?, model?, provider?, base_url? }."""
    search_results = body.get("search_results")
    user_prompt = body.get("prompt") or "Summarize and highlight the most useful insights and any recommended actions."
    model = body.get("model") or ""
    provider = body.get("provider") or "ollama"
    base_url = body.get("base_url") or (DEFAULT_OLLAMA_BASE if provider == "ollama" else DEFAULT_LMSTUDIO_BASE)
    base = base_url.rstrip("/")
    system_prompt = (
        "You are a file system search analyst. The user has run a search and received a list of results (paths, sizes, metadata). "
        "Analyze the JSON search results provided and respond with: 1) a short summary of what was found; 2) patterns or notable findings; "
        "3) practical recommendations (e.g. cleanup, archiving, security). Be concise and actionable. Output plain text, no code blocks unless listing paths."
    )
    import json as _json

    results_str = _json.dumps(search_results, indent=2) if search_results is not None else "{}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Search results (JSON):\n{results_str}\n\nUser request: {user_prompt}"},
    ]
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            if provider == "ollama":
                r = await client.post(
                    f"{base}/api/chat",
                    json={"model": model or "llama3.2", "stream": False, "messages": messages},
                )
                if r.status_code != 200:
                    raise HTTPException(status_code=r.status_code, detail=r.text[:500])
                data = r.json()
                content = (data.get("message") or {}).get("content") or ""
                return {"content": content}
            else:
                r = await client.post(
                    f"{base}/v1/chat/completions",
                    json={"model": model or "local", "stream": False, "messages": messages},
                )
                if r.status_code != 200:
                    raise HTTPException(status_code=r.status_code, detail=r.text[:500])
                data = r.json()
                choice = (data.get("choices") or [None])[0]
                content = (choice.get("message") or {}).get("content") or "" if choice else ""
                return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("llm analyze failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


FORENSIC_SYSTEM_PROMPT = (
    "You are a digital triage assistant. You receive a list of file search results (paths, names, sizes, dates, metadata). "
    "Your role is to flag items that might warrant further human review from a forensic or compliance perspective. "
    "Consider: hidden or suspicious naming, unusual locations, timestamps that suggest exfil or cover-up, high volume of documents in odd places, "
    "or path patterns that suggest sensitive or restricted data. If the result set includes many documents (e.g. markdown, text), "
    "note that file content would need to be read separately to look for concerning language or evidence. "
    "Do not accuse or conclude; only highlight possible red flags for human review. Be concise. Output plain text."
)


@router.post("/llm/analyze-forensic")
async def llm_analyze_forensic(body: dict) -> dict:
    """Triage search results for potential forensic/compliance red flags. Body: { search_results, model?, provider?, base_url? }."""
    search_results = body.get("search_results")
    model = body.get("model") or ""
    provider = body.get("provider") or "ollama"
    base_url = body.get("base_url") or (DEFAULT_OLLAMA_BASE if provider == "ollama" else DEFAULT_LMSTUDIO_BASE)
    base = base_url.rstrip("/")
    import json as _json

    results_str = _json.dumps(search_results, indent=2) if search_results is not None else "{}"
    user_content = (
        "Review this list of file search results (paths, names, sizes, dates). "
        "Flag any that might suggest criminal activity or warrant forensic/compliance review. "
        "If there are many markdown or text files, note that their content would need to be read separately to look for concerning language."
    )
    messages = [
        {"role": "system", "content": FORENSIC_SYSTEM_PROMPT},
        {"role": "user", "content": f"Search results (JSON):\n{results_str}\n\n{user_content}"},
    ]
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            if provider == "ollama":
                r = await client.post(
                    f"{base}/api/chat",
                    json={"model": model or "llama3.2", "stream": False, "messages": messages},
                )
                if r.status_code != 200:
                    raise HTTPException(status_code=r.status_code, detail=r.text[:500])
                data = r.json()
                content = (data.get("message") or {}).get("content") or ""
                return {"content": content}
            else:
                r = await client.post(
                    f"{base}/v1/chat/completions",
                    json={"model": model or "local", "stream": False, "messages": messages},
                )
                if r.status_code != 200:
                    raise HTTPException(status_code=r.status_code, detail=r.text[:500])
                data = r.json()
                choice = (data.get("choices") or [None])[0]
                content = (choice.get("message") or {}).get("content") or "" if choice else ""
                return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("llm analyze-forensic failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Live tests (pipe + real search) for webapp Tests page
# ---------------------------------------------------------------------------


@router.post("/tests/run")
async def run_tests(body: dict | None = None) -> dict:
    """Run live integration tests: pipe connect, service info, real search via pipe.

    Body (optional): { "pattern": "*.txt", "directory": "C:\\\\", "max_results": 5 }
    """
    from fastsearch_mcp.live_tests import run_live_tests

    args = body or {}
    pattern = args.get("pattern", "*.txt")
    directory = args.get("directory", "C:\\")
    max_results = int(args.get("max_results", 5))
    try:
        results = await run_live_tests(
            search_pattern=pattern,
            search_directory=directory,
            search_max_results=max_results,
        )
        passed = sum(1 for r in results if r.get("passed"))
        return {"passed": passed, "total": len(results), "results": results}
    except Exception as e:
        logger.exception("run_tests failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Logging Endpoints for webapp Logs page
# ---------------------------------------------------------------------------

LOG_ENTRIES: list[dict] = [
    {
        "id": "1",
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "INFO",
        "kind": "server",
        "detail": "FastSearch REST API Bridge initialized on port 10845.",
        "meta": {},
    },
    {
        "id": "2",
        "timestamp": datetime.now(UTC).isoformat(),
        "level": "INFO",
        "kind": "server",
        "detail": "Named pipe \\\\.\\pipe\\FastSearchMCP listener configured.",
        "meta": {},
    },
]


def log_event(level: str, kind: str, detail: str, meta: dict | None = None) -> None:
    """Record a log entry into the in-memory ring buffer."""
    new_id = str(len(LOG_ENTRIES) + 1)
    LOG_ENTRIES.append(
        {
            "id": new_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "kind": kind,
            "detail": detail,
            "meta": meta or {},
        }
    )
    if len(LOG_ENTRIES) > 1000:
        LOG_ENTRIES.pop(0)


@router.get("/logs")
async def get_logs(
    limit: int = 50,
    offset: int = 0,
    sort: str = "desc",
    level: str | None = None,
    kind: str | None = None,
    search: str | None = None,
    after_id: str | None = None,
) -> dict:
    """Fetch logs with filtering and pagination."""
    filtered = LOG_ENTRIES[:]

    if level:
        filtered = [e for e in filtered if e.get("level", "").upper() == level.upper()]
    if kind:
        filtered = [e for e in filtered if e.get("kind", "").lower() == kind.lower()]
    if search:
        s = search.lower()
        filtered = [e for e in filtered if s in e.get("detail", "").lower()]
    if after_id:
        try:
            aid = int(after_id)
            filtered = [e for e in filtered if int(e.get("id", "0")) > aid]
        except ValueError:
            pass

    if sort == "desc":
        filtered = list(reversed(filtered))

    total = len(filtered)
    paged = filtered[offset : offset + limit]

    return {
        "entries": paged,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.delete("/logs")
async def clear_logs() -> dict:
    """Clear all log entries."""
    global LOG_ENTRIES
    LOG_ENTRIES = []
    return {"success": True, "message": "Logs cleared"}


@router.get("/logs/export")
async def export_logs(
    format: str = "json",
    level: str | None = None,
    kind: str | None = None,
    search: str | None = None,
) -> Response:
    """Export log entries as JSON or CSV file download."""
    filtered = LOG_ENTRIES[:]
    if level:
        filtered = [e for e in filtered if e.get("level", "").upper() == level.upper()]
    if kind:
        filtered = [e for e in filtered if e.get("kind", "").lower() == kind.lower()]
    if search:
        s = search.lower()
        filtered = [e for e in filtered if s in e.get("detail", "").lower()]

    if format.lower() == "csv":
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "timestamp", "level", "kind", "detail"])
        for e in filtered:
            writer.writerow([e.get("id"), e.get("timestamp"), e.get("level"), e.get("kind"), e.get("detail")])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=logs.csv"},
        )
    else:
        content = json.dumps(filtered, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=logs.json"},
        )

import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    Search,
    FileSearch,
    Database,
    Activity,
    HardDrive,
    FileText,
    Download,
    Loader2,
    AlertCircle,
    CheckCircle2,
    File,
    X,
} from "lucide-react";
import { mcpClient } from "@/common/mcp-client";
import { getLlmConfig } from "@/common/llm-config";

type ResultView = "list" | "json";

function getResultItems(value: unknown): unknown[] {
    if (value == null) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === "object" && "results" in value && Array.isArray((value as { results: unknown }).results)) {
        return (value as { results: unknown[] }).results;
    }
    if (typeof value === "object" && "files" in value && Array.isArray((value as { files: unknown }).files)) {
        return (value as { files: unknown[] }).files;
    }
    if (typeof value === "object" && "entries" in value && Array.isArray((value as { entries: unknown }).entries)) {
        return (value as { entries: unknown[] }).entries;
    }
    return [];
}

function getItemPath(item: unknown): string {
    if (item == null) return "";
    if (typeof item === "string") return item;
    if (typeof item === "object") {
        const o = item as Record<string, unknown>;
        const path = (o.path ?? o.file_path ?? o.full_path ?? o.name ?? o.file) as string | undefined;
        if (typeof path === "string") return path;
    }
    return String(item);
}

function getItemSize(item: unknown): string | null {
    if (item == null || typeof item !== "object") return null;
    const o = item as Record<string, unknown>;
    const size = o.size ?? o.size_bytes ?? o.length;
    if (typeof size === "number") return size < 1024 ? `${size} B` : size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} KB` : `${(size / (1024 * 1024)).toFixed(1)} MB`;
    if (typeof size === "string") return size;
    return null;
}

type FileViewerState = {
    path: string;
    type: string;
    mime: string;
    content: string;
    size: number;
    truncated?: boolean;
};

const HEX_VIEWER_MAX_BYTES = 65536;

function hexViewer(base64Content: string): string {
    try {
        const binary = atob(base64Content);
        const len = Math.min(binary.length, HEX_VIEWER_MAX_BYTES);
        const lines: string[] = [];
        for (let i = 0; i < len; i += 16) {
            const chunk = binary.slice(i, Math.min(i + 16, len));
            const offset = i.toString(16).toUpperCase().padStart(8, "0");
            const hex = Array.from(chunk)
                .map((c) => c.charCodeAt(0).toString(16).toUpperCase().padStart(2, "0"))
                .join(" ");
            const ascii = Array.from(chunk)
                .map((c) => (c.charCodeAt(0) >= 32 && c.charCodeAt(0) < 127 ? c : "."))
                .join("");
            lines.push(`${offset}  ${hex.padEnd(48, " ")}  |${ascii}|`);
        }
        if (binary.length > HEX_VIEWER_MAX_BYTES) {
            lines.push(`... (${binary.length - HEX_VIEWER_MAX_BYTES} more bytes)`);
        }
        return lines.join("\n");
    } catch {
        return "(invalid base64)";
    }
}

function dataUrl(mime: string, base64: string): string {
    return `data:${mime};base64,${base64}`;
}

export function Tools() {
    const [loading, setLoading] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [status, setStatus] = useState<string | null>(null);
    const [serviceRunning, setServiceRunning] = useState<boolean | null>(null);
    const [lastResult, setLastResult] = useState<unknown>(null);
    const [filenamePattern, setFilenamePattern] = useState("*.txt");
    const [filenamePath, setFilenamePath] = useState("C:\\");
    const [contentSearch, setContentSearch] = useState("TODO");
    const [contentPath, setContentPath] = useState("C:\\");
    const [resultView, setResultView] = useState<ResultView>("list");
    const [fileViewer, setFileViewer] = useState<FileViewerState | null>(null);
    const [fileViewerError, setFileViewerError] = useState<string | null>(null);
    const [fileViewerLoading, setFileViewerLoading] = useState(false);
    const [llmAnalysis, setLlmAnalysis] = useState<string | null>(null);
    const [llmAnalysisLoading, setLlmAnalysisLoading] = useState(false);
    const [llmAnalysisError, setLlmAnalysisError] = useState<string | null>(null);
    const [llmAnalysisPrompt, setLlmAnalysisPrompt] = useState("");

    const fetchServiceStatus = async () => {
        try {
            const res = await mcpClient.callTool("service_status", { level: "basic" });
            setServiceRunning(Boolean((res as { running?: boolean })?.running));
        } catch {
            setServiceRunning(false);
        }
    };

    useEffect(() => {
        fetchServiceStatus();
    }, []);

    const runLlmAnalysis = async () => {
        if (lastResult == null) {
            setError("Run a search first, then use Advanced analysis (LLM).");
            return;
        }
        const cfg = getLlmConfig();
        setLlmAnalysis(null);
        setLlmAnalysisError(null);
        setLlmAnalysisLoading(true);
        try {
            const res = await mcpClient.llmAnalyze({
                search_results: lastResult,
                prompt: llmAnalysisPrompt.trim() || undefined,
                model: cfg.model || undefined,
                provider: cfg.provider,
                base_url: cfg.baseUrl || undefined,
            });
            setLlmAnalysis(res.content);
        } catch (e: unknown) {
            setLlmAnalysisError(e instanceof Error ? e.message : String(e));
        } finally {
            setLlmAnalysisLoading(false);
        }
    };

    const runLlmForensic = async () => {
        if (lastResult == null) {
            setError("Run a search first, then use Forensic analysis.");
            return;
        }
        const cfg = getLlmConfig();
        setLlmAnalysis(null);
        setLlmAnalysisError(null);
        setLlmAnalysisLoading(true);
        try {
            const res = await mcpClient.llmAnalyzeForensic({
                search_results: lastResult,
                model: cfg.model || undefined,
                provider: cfg.provider,
                base_url: cfg.baseUrl || undefined,
            });
            setLlmAnalysis(res.content);
        } catch (e: unknown) {
            setLlmAnalysisError(e instanceof Error ? e.message : String(e));
        } finally {
            setLlmAnalysisLoading(false);
        }
    };

    const openFile = async (path: string) => {
        if (!path.trim()) return;
        setFileViewer(null);
        setFileViewerError(null);
        setFileViewerLoading(true);
        try {
            const data = await mcpClient.fetchFile(path);
            setFileViewer({
                path: data.path,
                type: data.type,
                mime: data.mime,
                content: data.content,
                size: data.size,
                truncated: data.truncated,
            });
        } catch (err: unknown) {
            setFileViewerError(err instanceof Error ? err.message : String(err));
        } finally {
            setFileViewerLoading(false);
        }
    };

    const runTool = async (
        key: string,
        toolName: string,
        args: Record<string, unknown>,
        successMessage: string
    ) => {
        setLoading(key);
        setError(null);
        setStatus(null);
        setLastResult(null);
        try {
            const response = await mcpClient.callTool(toolName, args);
            setLastResult(response);
            setResultView("list");
            setStatus(successMessage);
            if (key === "restart" || key === "stop") {
                await fetchServiceStatus();
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            setError(msg);
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Search Utilities</h2>
                <p className="text-slate-400">High-speed file system indexing and diagnostic tools</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <Search className="h-5 w-5 text-blue-400" />
                            Core Search
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                            Fast filename and content search
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-xs font-medium text-slate-400">
                                Filename search (glob pattern)
                            </label>
                            <input
                                type="text"
                                value={filenamePattern}
                                onChange={(e) => setFilenamePattern(e.target.value)}
                                placeholder="e.g. *.txt or *.pdf"
                                className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            <input
                                type="text"
                                value={filenamePath}
                                onChange={(e) => setFilenamePath(e.target.value)}
                                placeholder="Path (e.g. C:\\)"
                                className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            <Button
                                className="w-full bg-blue-600 hover:bg-blue-700"
                                disabled={!!loading}
                                onClick={() =>
                                    runTool(
                                        "filename",
                                        "fastsearch_search",
                                        {
                                            pattern: filenamePattern || "*.txt",
                                            path: filenamePath || "C:\\",
                                            max_results: 50,
                                        },
                                        "Filename search completed. See result below."
                                    )
                                }
                            >
                                {loading === "filename" ? (
                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                ) : null}
                                Filename Search
                            </Button>
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-medium text-slate-400">
                                Content search (text to find)
                            </label>
                            <input
                                type="text"
                                value={contentSearch}
                                onChange={(e) => setContentSearch(e.target.value)}
                                placeholder="e.g. TODO or keyword"
                                className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            <input
                                type="text"
                                value={contentPath}
                                onChange={(e) => setContentPath(e.target.value)}
                                placeholder="Path (e.g. C:\\)"
                                className="w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                            <Button
                                variant="outline"
                                className="w-full border-slate-800"
                                disabled={!!loading}
                                onClick={() =>
                                    runTool(
                                        "content",
                                        "file_content_search",
                                        {
                                            search_pattern: contentSearch || "TODO",
                                            search_dir: contentPath || "C:\\",
                                            max_results: 30,
                                        },
                                        "Content search completed. See result below."
                                    )
                                }
                            >
                                {loading === "content" ? (
                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                ) : null}
                                Content Search
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <Activity className="h-5 w-5 text-emerald-400" />
                            Service Control
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                            Manage FastSearch indexer service
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                        <div className="flex justify-between text-xs text-slate-400 mb-2">
                            <span>Status:</span>
                            <span
                                className={
                                    serviceRunning === null
                                        ? "text-slate-500"
                                        : serviceRunning
                                          ? "text-emerald-400"
                                          : "text-amber-400"
                                }
                            >
                                {serviceRunning === null
                                    ? "Checking..."
                                    : serviceRunning
                                      ? "Running"
                                      : "Stopped"}
                            </span>
                        </div>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                className="flex-1 border-slate-800"
                                disabled={!!loading}
                                onClick={() =>
                                    runTool(
                                        "restart",
                                        "service_restart_fastsearch",
                                        {},
                                        "Service restart requested."
                                    )
                                }
                            >
                                {loading === "restart" ? (
                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                ) : null}
                                Restart
                            </Button>
                            <Button
                                variant="outline"
                                className="flex-1 border-slate-800 text-red-400 hover:text-red-300"
                                disabled={!!loading}
                                onClick={() =>
                                    runTool(
                                        "stop",
                                        "service_stop_fastsearch",
                                        {},
                                        "Service stop requested."
                                    )
                                }
                            >
                                {loading === "stop" ? (
                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                ) : null}
                                Stop
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <HardDrive className="h-5 w-5 text-purple-400" />
                            Disk Analysis
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                            Analyze growth and NTFS metadata
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                        <Button
                            variant="outline"
                            className="w-full border-slate-800"
                            disabled={!!loading}
                            onClick={() =>
                                runTool(
                                    "disk",
                                    "analyze_disk_usage",
                                    { path: "C:\\", max_depth: 2, large_file_limit: 20 },
                                    "Disk usage analysis completed."
                                )
                            }
                        >
                            {loading === "disk" ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            Analyze Disk Usage
                        </Button>
                        <Button
                            variant="outline"
                            className="w-full border-slate-800"
                            disabled={!!loading}
                            onClick={() =>
                                runTool(
                                    "ntfs",
                                    "ntfs_volume_info",
                                    { volume_path: "C:" },
                                    "NTFS volume info retrieved."
                                )
                            }
                        >
                            {loading === "ntfs" ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            NTFS Volume Info
                        </Button>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Result Enhancement</CardTitle>
                        <CardDescription className="text-slate-400">
                            Process and filter search results (use after running a search)
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        <Button
                            variant="ghost"
                            className="flex flex-col gap-2 h-auto py-4"
                            disabled={!!loading}
                            onClick={() =>
                                runTool(
                                    "analyze",
                                    "search_result_analyze",
                                    { results: [] },
                                    "Result analyze tool runs on results from a prior search."
                                )
                            }
                        >
                            {loading === "analyze" ? (
                                <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
                            ) : (
                                <FileText className="h-5 w-5 text-blue-400" />
                            )}
                            Analyze
                        </Button>
                        <Button
                            variant="ghost"
                            className="flex flex-col gap-2 h-auto py-4"
                            disabled={!!loading}
                            onClick={() =>
                                runTool(
                                    "export",
                                    "search_result_export",
                                    { results: [], export_format: "json" },
                                    "Result export runs on results from a prior search."
                                )
                            }
                        >
                            {loading === "export" ? (
                                <Loader2 className="h-5 w-5 animate-spin text-emerald-400" />
                            ) : (
                                <Download className="h-5 w-5 text-emerald-400" />
                            )}
                            Export
                        </Button>
                        <Button
                            variant="ghost"
                            className="flex flex-col gap-2 h-auto py-4"
                            disabled={!!loading}
                            onClick={() =>
                                runTool(
                                    "filter",
                                    "search_result_filter",
                                    { results: [] },
                                    "Result filter runs on results from a prior search."
                                )
                            }
                        >
                            {loading === "filter" ? (
                                <Loader2 className="h-5 w-5 animate-spin text-orange-400" />
                            ) : (
                                <Database className="h-5 w-5 text-orange-400" />
                            )}
                            Filter
                        </Button>
                        <Button
                            variant="ghost"
                            className="flex flex-col gap-2 h-auto py-4 border border-purple-500/30"
                            disabled={!!loading || lastResult == null}
                            onClick={runLlmAnalysis}
                        >
                            {llmAnalysisLoading ? (
                                <Loader2 className="h-5 w-5 animate-spin text-purple-400" />
                            ) : (
                                <FileText className="h-5 w-5 text-purple-400" />
                            )}
                            Advanced (LLM)
                        </Button>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Maintenance & Integrity</CardTitle>
                        <CardDescription className="text-slate-400">
                            Duplicates and file hashing
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="flex gap-4">
                        <Button
                            variant="outline"
                            className="flex-1 border-slate-800"
                            disabled={!!loading}
                            onClick={() =>
                                runTool(
                                    "duplicates",
                                    "find_duplicate_files",
                                    { search_dir: "C:\\", max_results: 15, min_size: 1024 },
                                    "Duplicate scan completed."
                                )
                            }
                        >
                            {loading === "duplicates" ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            Find Duplicates
                        </Button>
                        <Button
                            variant="outline"
                            className="flex-1 border-slate-800"
                            disabled={!!loading}
                            onClick={() =>
                                runTool(
                                    "hashes",
                                    "generate_file_hashes",
                                    {
                                        paths: ["C:\\Windows\\System32\\drivers\\etc\\hosts"],
                                        algorithm: "sha256",
                                    },
                                    "Hash generated."
                                )
                            }
                        >
                            {loading === "hashes" ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            Generate Hashes
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {(status || error || lastResult) && (
                <Card className="border-slate-800 bg-slate-900/30">
                    <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                            <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
                                {error ? (
                                    <AlertCircle className="h-4 w-4 text-red-400" />
                                ) : (
                                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                                )}
                                Result
                            </CardTitle>
                            {lastResult != null && (
                                <div className="flex rounded border border-slate-700 overflow-hidden">
                                    <button
                                        type="button"
                                        onClick={() => setResultView("list")}
                                        className={`px-3 py-1 text-xs ${resultView === "list" ? "bg-slate-700 text-white" : "bg-slate-800/50 text-slate-400 hover:text-slate-300"}`}
                                    >
                                        List
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setResultView("json")}
                                        className={`px-3 py-1 text-xs ${resultView === "json" ? "bg-slate-700 text-white" : "bg-slate-800/50 text-slate-400 hover:text-slate-300"}`}
                                    >
                                        JSON
                                    </button>
                                </div>
                            )}
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {status && <p className="text-xs text-slate-400">{status}</p>}
                        {error && (
                            <p className="text-xs text-red-400 bg-red-400/10 p-2 rounded border border-red-400/20">
                                {error}
                            </p>
                        )}
                        {lastResult != null && typeof lastResult === "object" && "error" in lastResult && (lastResult as { error?: string }).error && (
                            <p className="text-xs text-amber-400 bg-amber-400/10 p-2 rounded border border-amber-400/20">
                                {(lastResult as { error: string }).error}
                            </p>
                        )}
                        {lastResult != null && resultView === "list" && (() => {
                            const items = getResultItems(lastResult);
                            if (items.length === 0) {
                                return (
                                    <p className="text-xs text-slate-500 py-2">No list data in result. Use JSON view for raw output.</p>
                                );
                            }
                            return (
                                <ul className="rounded border border-slate-800 bg-slate-950 max-h-[320px] overflow-auto">
                                    {items.map((item, i) => {
                                        const path = getItemPath(item);
                                        const size = getItemSize(item);
                                        return (
                                            <li
                                                key={i}
                                                role="button"
                                                tabIndex={0}
                                                onClick={() => path && openFile(path)}
                                                onKeyDown={(e) => path && (e.key === "Enter" || e.key === " ") && openFile(path)}
                                                className="flex cursor-pointer items-center gap-3 border-b border-slate-800/80 px-3 py-2 last:border-b-0 hover:bg-slate-800/30 focus:bg-slate-800/50 focus:outline-none"
                                            >
                                                <File className="h-4 w-4 shrink-0 text-slate-500" />
                                                <span className="min-w-0 flex-1 truncate font-mono text-xs text-slate-300" title={path}>
                                                    {path || "(no path)"}
                                                </span>
                                                {size != null && (
                                                    <span className="shrink-0 text-xs text-slate-500">{size}</span>
                                                )}
                                            </li>
                                        );
                                    })}
                                </ul>
                            );
                        })()}
                        {lastResult != null && resultView === "json" && (
                            <pre className="text-[10px] font-mono p-3 rounded bg-slate-950 border border-slate-800 text-slate-300 max-h-[320px] overflow-auto">
                                {JSON.stringify(lastResult, null, 2)}
                            </pre>
                        )}
                    </CardContent>
                </Card>
            )}

            {lastResult != null && (
                <Card className="border-slate-800 bg-slate-900/30 border-purple-500/20">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-slate-300">Advanced result analysis (LLM)</CardTitle>
                        <CardDescription className="text-slate-400 text-xs">
                            Optional prompt + Run, or Forensic to triage for red flags (paths/names/dates only; file content not read). Uses Settings model.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <div className="flex flex-wrap gap-2">
                            <input
                                type="text"
                                value={llmAnalysisPrompt}
                                onChange={(e) => setLlmAnalysisPrompt(e.target.value)}
                                placeholder="e.g. Focus on large files and cleanup suggestions"
                                className="flex-1 min-w-[200px] rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500"
                            />
                            <Button
                                className="bg-purple-600 hover:bg-purple-700 shrink-0"
                                onClick={runLlmAnalysis}
                                disabled={llmAnalysisLoading}
                            >
                                {llmAnalysisLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Run"}
                            </Button>
                            <Button
                                variant="outline"
                                className="border-amber-500/50 text-amber-400 hover:bg-amber-500/10 shrink-0"
                                onClick={runLlmForensic}
                                disabled={llmAnalysisLoading}
                                title="Triage for red flags; content of files is not read"
                            >
                                {llmAnalysisLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Forensic"}
                            </Button>
                        </div>
                        {llmAnalysisError && (
                            <p className="text-xs text-amber-400 bg-amber-400/10 p-2 rounded border border-amber-400/20">{llmAnalysisError}</p>
                        )}
                        {llmAnalysis != null && (
                            <pre className="text-xs text-slate-300 whitespace-pre-wrap p-3 rounded bg-slate-950 border border-slate-800 max-h-[240px] overflow-auto">
                                {llmAnalysis}
                            </pre>
                        )}
                    </CardContent>
                </Card>
            )}

            {(fileViewerLoading || fileViewerError || fileViewer) && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
                    onClick={() => {
                        if (!fileViewerLoading) {
                            setFileViewer(null);
                            setFileViewerError(null);
                        }
                    }}
                >
                    <Card
                        className="w-full max-w-4xl max-h-[90vh] flex flex-col border-slate-700 bg-slate-900 shadow-xl"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b border-slate-800 pb-3">
                            <CardTitle className="text-sm font-medium text-slate-200 truncate pr-4" title={fileViewer?.path ?? ""}>
                                {fileViewerLoading ? "Loading..." : fileViewerError ? "Error" : fileViewer?.path ?? ""}
                            </CardTitle>
                            <Button
                                variant="ghost"
                                size="icon"
                                className="shrink-0 text-slate-400 hover:text-white"
                                onClick={() => {
                                    setFileViewer(null);
                                    setFileViewerError(null);
                                }}
                                disabled={fileViewerLoading}
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-auto p-4 min-h-0">
                            {fileViewerLoading && (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-8 w-8 animate-spin text-blue-400" />
                                </div>
                            )}
                            {fileViewerError && (
                                <p className="text-sm text-red-400 bg-red-400/10 p-3 rounded border border-red-400/20">
                                    {fileViewerError}
                                </p>
                            )}
                            {fileViewer && !fileViewerLoading && (
                                <>
                                    {fileViewer.type === "text" && (
                                        <pre className="whitespace-pre-wrap break-words font-mono text-xs text-slate-300 rounded bg-slate-950 p-4 max-h-[70vh] overflow-auto">
                                            {fileViewer.content}
                                        </pre>
                                    )}
                                    {fileViewer.type === "image" && (
                                        <div className="flex justify-center bg-slate-950 rounded p-4">
                                            <img
                                                src={dataUrl(fileViewer.mime, fileViewer.content)}
                                                alt={fileViewer.path}
                                                className="max-h-[70vh] max-w-full object-contain"
                                            />
                                        </div>
                                    )}
                                    {fileViewer.type === "video" && (
                                        <div className="flex justify-center bg-slate-950 rounded p-4">
                                            <video
                                                src={dataUrl(fileViewer.mime, fileViewer.content)}
                                                controls
                                                className="max-h-[70vh] max-w-full"
                                            />
                                        </div>
                                    )}
                                    {fileViewer.type === "audio" && (
                                        <div className="rounded bg-slate-950 p-4">
                                            <audio src={dataUrl(fileViewer.mime, fileViewer.content)} controls className="w-full" />
                                        </div>
                                    )}
                                    {fileViewer.type === "binary" && (
                                        <pre className="whitespace-pre font-mono text-[10px] text-slate-400 rounded bg-slate-950 p-4 max-h-[70vh] overflow-auto">
                                            {hexViewer(fileViewer.content)}
                                        </pre>
                                    )}
                                    {(fileViewer.truncated ?? false) && (
                                        <p className="text-xs text-amber-400 mt-2">Truncated (file too large).</p>
                                    )}
                                </>
                            )}
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}

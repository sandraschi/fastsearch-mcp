import {
  AlertTriangle,
  Archive,
  ArrowUpDown,
  Check,
  CheckCircle2,
  Clock,
  Columns3,
  Copy,
  Download,
  Eye,
  FileCode,
  FileImage,
  FileText,
  FileVideo,
  Filter,
  LayoutGrid,
  LayoutList,
  List,
  Loader2,
  Play,
  Search as SearchIcon,
  Server,
  SortAsc,
  SortDesc,
  Sparkles,
  X,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { mcpClient } from "@/common/mcp-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type FileItem = {
  name?: string;
  path?: string;
  file_path?: string;
  full_path?: string;
  size?: number;
  size_bytes?: number;
  length?: number;
  modified?: string | number;
  modified_time?: string | number;
  is_directory?: boolean;
  type?: string;
};

type FilePreview = {
  path: string;
  type: string;
  mime: string;
  content: string;
  size: number;
  truncated?: boolean;
};

const CATEGORY_EXTENSIONS: Record<string, string[]> = {
  Code: [
    "py",
    "ts",
    "tsx",
    "js",
    "jsx",
    "cpp",
    "c",
    "h",
    "cs",
    "java",
    "rs",
    "go",
    "json",
    "html",
    "css",
    "xml",
    "yml",
    "yaml",
    "sh",
    "ps1",
  ],
  Docs: ["pdf", "doc", "docx", "txt", "md", "csv", "xlsx", "pptx", "log"],
  Images: ["png", "jpg", "jpeg", "gif", "webp", "svg", "ico", "bmp"],
  Media: ["mp4", "webm", "mkv", "avi", "mp3", "wav", "flac", "ogg"],
  Archives: ["zip", "7z", "tar", "gz", "rar", "bz2"],
  Apps: ["exe", "dll", "msi", "bat", "cmd", "ps1"],
};

function formatBytes(bytes?: number): string {
  if (bytes == null || isNaN(bytes)) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function getItemPath(item: FileItem): string {
  return item.path || item.file_path || item.full_path || item.name || "";
}

function getItemName(item: FileItem): string {
  if (item.name) return item.name;
  const p = getItemPath(item);
  if (!p) return "Unknown";
  const parts = p.split(/[/\\]/);
  return parts[parts.length - 1] || p;
}

function getItemFolder(item: FileItem): string {
  const p = getItemPath(item);
  if (!p) return "";
  const parts = p.split(/[/\\]/);
  return parts.slice(0, -1).join("\\");
}

function getItemSize(item: FileItem): number {
  return item.size ?? item.size_bytes ?? item.length ?? 0;
}

function getFileIcon(filename: string) {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  if (CATEGORY_EXTENSIONS.Code.includes(ext))
    return <FileCode className="h-4 w-4 text-blue-400 shrink-0" />;
  if (CATEGORY_EXTENSIONS.Images.includes(ext))
    return <FileImage className="h-4 w-4 text-emerald-400 shrink-0" />;
  if (CATEGORY_EXTENSIONS.Media.includes(ext))
    return <FileVideo className="h-4 w-4 text-purple-400 shrink-0" />;
  if (CATEGORY_EXTENSIONS.Archives.includes(ext))
    return <Archive className="h-4 w-4 text-amber-400 shrink-0" />;
  if (CATEGORY_EXTENSIONS.Docs.includes(ext))
    return <FileText className="h-4 w-4 text-slate-300 shrink-0" />;
  return <FileText className="h-4 w-4 text-slate-400 shrink-0" />;
}

const LOCAL_STORAGE_HISTORY_KEY = "fastsearch_history_v1";

export function Search() {
  const [pattern, setPattern] = useState<string>("*.py");
  const [directory, setDirectory] = useState<string>("C:\\");
  const [maxResults, setMaxResults] = useState<number>(500);

  // Service state
  const [serviceRunning, setServiceRunning] = useState<boolean | null>(null);
  const [serviceLoading, setServiceLoading] = useState<boolean>(false);

  // Results state
  const [results, setResults] = useState<FileItem[]>([]);
  const [searching, setSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);

  // View & Filter state
  type ViewMode = "details" | "grid" | "list" | "tiles";
  const [viewMode, setViewMode] = useState<ViewMode>("details");
  const [filterQuery, setFilterQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [sizeFilter, setSizeFilter] = useState<
    "any" | "small" | "medium" | "large"
  >("any");
  const [sortBy, setSortBy] = useState<"name" | "path" | "size" | "ext">(
    "name",
  );
  const [sortAsc, setSortAsc] = useState<boolean>(true);
  const [pageSize, setPageSize] = useState<number>(50);
  const [currentPage, setCurrentPage] = useState<number>(1);

  // UI Drawer / Modal
  const [previewFile, setPreviewFile] = useState<FilePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [copiedPath, setCopiedPath] = useState<string | null>(null);

  // History
  const [history, setHistory] = useState<string[]>(() => {
    try {
      const raw = localStorage.getItem(LOCAL_STORAGE_HISTORY_KEY);
      return raw
        ? JSON.parse(raw)
        : ["*.py", "*.pdf", "*.log", "*.docx", "*config*"];
    } catch {
      return ["*.py", "*.pdf", "*.log", "*.docx", "*config*"];
    }
  });

  const checkServiceStatus = useCallback(async () => {
    setServiceLoading(true);
    try {
      const status = await mcpClient.getServiceStatusDirect();
      setServiceRunning(status.running === true);
    } catch {
      setServiceRunning(false);
    } finally {
      setServiceLoading(false);
    }
  }, []);

  useEffect(() => {
    checkServiceStatus();
  }, [checkServiceStatus]);

  const handleStartService = async () => {
    setServiceLoading(true);
    try {
      await mcpClient.startServiceDirect();
      await new Promise((r) => setTimeout(r, 1500));
      await checkServiceStatus();
    } catch (e: unknown) {
      setSearchError(
        e instanceof Error ? e.message : "Failed to start service",
      );
    } finally {
      setServiceLoading(false);
    }
  };

  const runSearch = async (overridePattern?: string, overrideDir?: string) => {
    const activePattern = overridePattern ?? pattern;
    const activeDir = overrideDir ?? directory;

    if (!activePattern.trim()) return;

    setSearching(true);
    setSearchError(null);
    setCurrentPage(1);

    // Update history
    setHistory((prev) => {
      const updated = [
        activePattern,
        ...prev.filter((p) => p !== activePattern),
      ].slice(0, 10);
      try {
        localStorage.setItem(
          LOCAL_STORAGE_HISTORY_KEY,
          JSON.stringify(updated),
        );
      } catch {}
      return updated;
    });

    const startTime = performance.now();
    try {
      const res = await mcpClient.searchDirect({
        pattern: activePattern,
        directory: activeDir,
        max_results: maxResults,
      });

      const endTime = performance.now();
      setDurationMs(Math.round(endTime - startTime));

      if (res.service_down) {
        setServiceRunning(false);
        setSearchError(
          res.error || "FastSearch Windows Service is not running.",
        );
        setResults([]);
      } else if (res.success === false) {
        setSearchError(res.error || "Search failed");
        setResults([]);
      } else {
        setServiceRunning(true);
        const items = res.results || [];
        setResults(items);
      }
    } catch (e: unknown) {
      setSearchError(
        e instanceof Error ? e.message : "Unexpected search error",
      );
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  // Filtered and Sorted Results
  const filteredResults = useMemo(() => {
    return results.filter((item) => {
      const name = getItemName(item).toLowerCase();
      const fullPath = getItemPath(item).toLowerCase();

      // Client side quick filter text
      if (
        filterQuery &&
        !name.includes(filterQuery.toLowerCase()) &&
        !fullPath.includes(filterQuery.toLowerCase())
      ) {
        return false;
      }

      // Category filter
      if (selectedCategory !== "All") {
        const ext = name.split(".").pop()?.toLowerCase() || "";
        const allowedExts = CATEGORY_EXTENSIONS[selectedCategory] || [];
        if (!allowedExts.includes(ext)) return false;
      }

      // Size range filter
      if (sizeFilter !== "any") {
        const size = getItemSize(item);
        if (sizeFilter === "small" && size >= 1024 * 1024) return false;
        if (
          sizeFilter === "medium" &&
          (size < 1024 * 1024 || size > 100 * 1024 * 1024)
        )
          return false;
        if (sizeFilter === "large" && size <= 100 * 1024 * 1024) return false;
      }

      return true;
    });
  }, [results, filterQuery, selectedCategory, sizeFilter]);

  const sortedResults = useMemo(() => {
    return [...filteredResults].sort((a, b) => {
      let valA: string | number = "";
      let valB: string | number = "";
      if (sortBy === "name") {
        valA = getItemName(a).toLowerCase();
        valB = getItemName(b).toLowerCase();
      } else if (sortBy === "path") {
        valA = getItemPath(a).toLowerCase();
        valB = getItemPath(b).toLowerCase();
      } else if (sortBy === "size") {
        valA = getItemSize(a);
        valB = getItemSize(b);
      } else if (sortBy === "ext") {
        valA = getItemName(a).split(".").pop()?.toLowerCase() || "";
        valB = getItemName(b).split(".").pop()?.toLowerCase() || "";
      }

      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [filteredResults, sortBy, sortAsc]);

  // Paginated
  const totalPages = Math.ceil(sortedResults.length / pageSize) || 1;
  const paginatedResults = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedResults.slice(start, start + pageSize);
  }, [sortedResults, currentPage, pageSize]);

  const handleCopyPath = (path: string) => {
    navigator.clipboard.writeText(path);
    setCopiedPath(path);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const handlePreview = async (path: string) => {
    setPreviewLoading(true);
    setPreviewFile(null);
    try {
      const data = await mcpClient.fetchFile(path);
      setPreviewFile(data);
    } catch (e: unknown) {
      setPreviewFile({
        path,
        type: "error",
        mime: "text/plain",
        content: e instanceof Error ? e.message : "Failed to load file preview",
        size: 0,
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  const exportResults = (format: "json" | "csv") => {
    if (!results.length) return;

    let content = "";
    let mime = "application/json";
    const filename = `fastsearch_results_${Date.now()}.${format}`;

    if (format === "json") {
      content = JSON.stringify(results, null, 2);
    } else {
      mime = "text/csv";
      const headers = ["Name", "Path", "SizeBytes"];
      const rows = results.map((item) => [
        `"${getItemName(item).replace(/"/g, '""')}"`,
        `"${getItemPath(item).replace(/"/g, '""')}"`,
        getItemSize(item),
      ]);
      content = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    }

    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <SearchIcon className="h-7 w-7 text-blue-500" />
            Dedicated FastSearch
          </h2>
          <p className="text-slate-400">
            High-performance NTFS Master File Table (MFT) direct file search.
          </p>
        </div>

        {/* Service Status Badge */}
        <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-800 rounded-lg p-2.5 px-4">
          <Server className="h-5 w-5 text-slate-400" />
          <div>
            <div className="text-xs text-slate-400">NTFS Service</div>
            <div className="flex items-center gap-1.5 text-xs font-semibold">
              {serviceLoading ? (
                <span className="text-slate-400 flex items-center gap-1">
                  <Loader2 className="h-3 w-3 animate-spin" /> Checking...
                </span>
              ) : serviceRunning ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Connected (MFT Ready)
                </span>
              ) : (
                <span className="text-amber-400 flex items-center gap-1">
                  <XCircle className="h-3.5 w-3.5" /> Service Disconnected
                </span>
              )}
            </div>
          </div>

          {!serviceRunning && !serviceLoading && (
            <Button
              size="sm"
              className="bg-emerald-600 hover:bg-emerald-700 text-white ml-2 h-8"
              onClick={handleStartService}
            >
              <Play className="h-3.5 w-3.5 mr-1" /> Start
            </Button>
          )}
        </div>
      </div>

      {!serviceRunning && !serviceLoading && (
        <div className="rounded-lg border border-amber-800/60 bg-amber-950/20 p-4 space-y-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 text-amber-300 font-semibold text-sm">
              <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
              FastSearch C++ Engine Disconnected
            </div>
            <Button
              size="sm"
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs h-8 px-3"
              onClick={handleStartService}
            >
              <Play className="h-3.5 w-3.5 mr-1" /> Auto-Connect / Start Engine
            </Button>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            FastSearch performs live, zero-index reads of the NTFS Master File
            Table (MFT). Direct volume access requires <b>Administrator</b> or{" "}
            <b>LocalSystem</b> privileges on Windows.
          </p>
          <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-[11px] text-slate-400">
            <span className="text-slate-500 font-sans font-medium">
              Elevated start commands:
            </span>
            <code className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-amber-200">
              sc start FastSearchMCP
            </code>
            <span className="text-slate-500">or</span>
            <code className="bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-amber-200">
              just install-service
            </code>
          </div>
        </div>
      )}

      {/* Search Input Card */}
      <Card className="border-slate-800 bg-slate-950/60 shadow-xl">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-400" />
            Search Options
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Pattern + Search Button */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <input
                type="text"
                className="w-full rounded-md border border-slate-700 bg-slate-900 py-2 pl-9 pr-4 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Search pattern (e.g. *.py, project_*, *.pdf)..."
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && runSearch()}
              />
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                className="w-32 sm:w-40 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                placeholder="Directory (C:\)"
                value={directory}
                onChange={(e) => setDirectory(e.target.value)}
              />

              <select
                value={maxResults}
                onChange={(e) => setMaxResults(Number(e.target.value))}
                className="rounded-md border border-slate-700 bg-slate-900 px-2.5 py-2 text-xs font-mono text-slate-200 focus:border-blue-500 focus:outline-none cursor-pointer"
                title="Maximum MFT search limit"
              >
                <option value={100}>Max: 100</option>
                <option value={250}>Max: 250</option>
                <option value={500}>Max: 500</option>
                <option value={1000}>Max: 1,000</option>
                <option value={2000}>Max: 2,000</option>
                <option value={5000}>Max: 5,000</option>
                <option value={10000}>Max: 10,000</option>
              </select>

              <Button
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 font-medium shrink-0"
                onClick={() => runSearch()}
                disabled={searching}
              >
                {searching ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Searching...
                  </>
                ) : (
                  <>
                    <SearchIcon className="h-4 w-4 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Directory Presets & History tags */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="text-slate-500 font-medium">Quick Drives:</span>
            {["C:\\", "D:\\", "d:\\Dev\\repos"].map((d) => (
              <button
                key={d}
                onClick={() => setDirectory(d)}
                className={`rounded bg-slate-900 border px-2 py-0.5 transition-colors ${
                  directory === d
                    ? "border-blue-500 text-blue-400 font-semibold"
                    : "border-slate-800 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                {d}
              </button>
            ))}

            <div className="h-4 w-px bg-slate-800 mx-1 hidden sm:block" />

            <span className="text-slate-500 font-medium">Recent Queries:</span>
            {history.slice(0, 5).map((h) => (
              <button
                key={h}
                onClick={() => {
                  setPattern(h);
                  runSearch(h);
                }}
                className="rounded bg-slate-900/60 border border-slate-800 px-2 py-0.5 text-slate-400 hover:text-blue-400 hover:border-blue-500/50 transition-colors"
              >
                {h}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {searchError && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-amber-300 flex items-start gap-3">
          <XCircle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1 text-sm">
            <p className="font-semibold">Search Notice</p>
            <p className="mt-1 text-xs opacity-90">{searchError}</p>
          </div>
        </div>
      )}

      {/* Results Section */}
      <Card className="border-slate-800 bg-slate-950/60 shadow-xl">
        <CardHeader className="pb-3 border-b border-slate-800/80">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <CardTitle className="text-lg text-white">Results</CardTitle>
              {results.length > 0 && (
                <span className="rounded-full bg-blue-500/10 border border-blue-500/20 px-3 py-0.5 text-xs font-semibold text-blue-400">
                  {filteredResults.length} matches
                </span>
              )}
              {durationMs !== null && (
                <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                  <Clock className="h-3.5 w-3.5 text-slate-500" />
                  {durationMs} ms
                </span>
              )}
            </div>

            {/* View Mode Switcher + Export Toolbar */}
            {results.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                {/* Windows Explorer Style View Mode Switcher */}
                <div className="flex items-center gap-0.5 bg-slate-900 border border-slate-800 rounded-lg p-0.5">
                  <button
                    onClick={() => setViewMode("details")}
                    title="Details View (Table)"
                    className={`p-1.5 rounded transition-colors ${
                      viewMode === "details"
                        ? "bg-blue-600 text-white font-semibold"
                        : "text-slate-400 hover:text-white hover:bg-slate-800"
                    }`}
                  >
                    <LayoutList className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setViewMode("grid")}
                    title="Grid / Icons View"
                    className={`p-1.5 rounded transition-colors ${
                      viewMode === "grid"
                        ? "bg-blue-600 text-white font-semibold"
                        : "text-slate-400 hover:text-white hover:bg-slate-800"
                    }`}
                  >
                    <LayoutGrid className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setViewMode("tiles")}
                    title="Tiles View"
                    className={`p-1.5 rounded transition-colors ${
                      viewMode === "tiles"
                        ? "bg-blue-600 text-white font-semibold"
                        : "text-slate-400 hover:text-white hover:bg-slate-800"
                    }`}
                  >
                    <Columns3 className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setViewMode("list")}
                    title="Compact List View"
                    className={`p-1.5 rounded transition-colors ${
                      viewMode === "list"
                        ? "bg-blue-600 text-white font-semibold"
                        : "text-slate-400 hover:text-white hover:bg-slate-800"
                    }`}
                  >
                    <List className="h-3.5 w-3.5" />
                  </button>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="border-slate-700 text-slate-300 hover:text-white h-8 text-xs"
                  onClick={() => exportResults("csv")}
                >
                  <Download className="h-3.5 w-3.5 mr-1" /> Export CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-slate-700 text-slate-300 hover:text-white h-8 text-xs"
                  onClick={() => exportResults("json")}
                >
                  <Download className="h-3.5 w-3.5 mr-1" /> Export JSON
                </Button>
              </div>
            )}
          </div>

          {/* Filter toolbar */}
          {results.length > 0 && (
            <div className="pt-3 flex flex-col sm:flex-row gap-3 justify-between items-center">
              {/* Filter input */}
              <div className="relative w-full sm:w-64">
                <Filter className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  className="w-full rounded-md border border-slate-800 bg-slate-900/90 py-1.5 pl-8 pr-3 text-xs text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                  placeholder="Filter results..."
                  value={filterQuery}
                  onChange={(e) => {
                    setFilterQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                />
              </div>

              {/* Category Filter Pills */}
              <div className="flex items-center gap-1 overflow-x-auto w-full sm:w-auto py-1">
                {[
                  "All",
                  "Code",
                  "Docs",
                  "Images",
                  "Media",
                  "Archives",
                  "Apps",
                ].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => {
                      setSelectedCategory(cat);
                      setCurrentPage(1);
                    }}
                    className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                      selectedCategory === cat
                        ? "bg-blue-600 text-white"
                        : "bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Sorting & Size Filters */}
              <div className="flex flex-wrap items-center gap-2">
                {/* Sort By Dropdown */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-xs text-slate-300 focus:border-blue-500 focus:outline-none cursor-pointer"
                >
                  <option value="name">Sort: Name</option>
                  <option value="path">Sort: Path</option>
                  <option value="size">Sort: Size</option>
                  <option value="ext">Sort: Type</option>
                </select>

                {/* Sort Asc/Desc Button */}
                <Button
                  variant="outline"
                  size="sm"
                  className="border-slate-800 bg-slate-900 h-7 px-2 text-xs text-slate-300 hover:text-white"
                  onClick={() => setSortAsc(!sortAsc)}
                  title={sortAsc ? "Ascending" : "Descending"}
                >
                  {sortAsc ? (
                    <SortAsc className="h-3.5 w-3.5 mr-1 text-blue-400" />
                  ) : (
                    <SortDesc className="h-3.5 w-3.5 mr-1 text-amber-400" />
                  )}
                  {sortAsc ? "Asc" : "Desc"}
                </Button>

                {/* Size Filter Dropdown */}
                <select
                  value={sizeFilter}
                  onChange={(e) => {
                    setSizeFilter(e.target.value as any);
                    setCurrentPage(1);
                  }}
                  className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-xs text-slate-300 focus:border-blue-500 focus:outline-none cursor-pointer"
                >
                  <option value="any">Size: Any</option>
                  <option value="small">Small (&lt; 1 MB)</option>
                  <option value="medium">Medium (1-100 MB)</option>
                  <option value="large">Large (&gt; 100 MB)</option>
                </select>
              </div>
            </div>
          )}
        </CardHeader>

        <CardContent className="p-0">
          {searching ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500 mb-2" />
              <p className="text-sm font-medium">
                Scanning Master File Table...
              </p>
            </div>
          ) : results.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-500">
              <SearchIcon className="h-10 w-10 text-slate-700 mb-3" />
              <p className="text-sm font-medium text-slate-400">
                No search results
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Enter a pattern (e.g. *.py) and click Search to query NTFS MFT.
              </p>
            </div>
          ) : paginatedResults.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-500">
              <p className="text-sm font-medium text-slate-400">
                No files match the active filters
              </p>
              <Button
                variant="link"
                className="text-xs text-blue-400"
                onClick={() => {
                  setFilterQuery("");
                  setSelectedCategory("All");
                  setSizeFilter("any");
                }}
              >
                Clear filters
              </Button>
            </div>
          ) : viewMode === "grid" ? (
            /* Explorer Grid / Medium Icons View */
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 p-4">
              {paginatedResults.map((item, idx) => {
                const name = getItemName(item);
                const fullPath = getItemPath(item);
                const folder = getItemFolder(item);
                const size = getItemSize(item);

                return (
                  <div
                    key={fullPath + idx}
                    className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-3.5 hover:border-blue-500/50 hover:bg-slate-900 transition-all flex flex-col justify-between group"
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 shrink-0">
                        {getFileIcon(name)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div
                          className="font-medium text-xs text-slate-200 truncate hover:text-blue-400 cursor-pointer"
                          onClick={() => handlePreview(fullPath)}
                          title={name}
                        >
                          {name}
                        </div>
                        <div
                          className="text-[11px] text-slate-500 truncate mt-0.5 font-mono"
                          title={fullPath}
                        >
                          {folder}
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                      <span className="font-mono text-slate-400">
                        {formatBytes(size)}
                      </span>
                      <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-slate-400 hover:text-white"
                          title="Copy path"
                          onClick={() => handleCopyPath(fullPath)}
                        >
                          {copiedPath === fullPath ? (
                            <Check className="h-3 w-3 text-emerald-400" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-slate-400 hover:text-blue-400"
                          title="Preview file"
                          onClick={() => handlePreview(fullPath)}
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : viewMode === "tiles" ? (
            /* Explorer Tiles View */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 p-4">
              {paginatedResults.map((item, idx) => {
                const name = getItemName(item);
                const fullPath = getItemPath(item);
                const folder = getItemFolder(item);
                const size = getItemSize(item);

                return (
                  <div
                    key={fullPath + idx}
                    className="rounded-lg border border-slate-800 bg-slate-900/80 p-3 flex items-center justify-between hover:border-slate-700 transition-colors group"
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1 pr-2">
                      <div className="p-2 rounded bg-slate-950 border border-slate-800 shrink-0">
                        {getFileIcon(name)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div
                          className="font-semibold text-xs text-white truncate cursor-pointer hover:text-blue-400"
                          onClick={() => handlePreview(fullPath)}
                          title={name}
                        >
                          {name}
                        </div>
                        <div
                          className="text-[11px] text-slate-400 truncate font-mono"
                          title={fullPath}
                        >
                          {folder}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          {formatBytes(size)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-slate-400 hover:text-white"
                        title="Copy path"
                        onClick={() => handleCopyPath(fullPath)}
                      >
                        {copiedPath === fullPath ? (
                          <Check className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="h-3.5 w-3.5" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0 text-slate-400 hover:text-blue-400"
                        title="Preview file"
                        onClick={() => handlePreview(fullPath)}
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : viewMode === "list" ? (
            /* Explorer Compact List View */
            <div className="divide-y divide-slate-800/60 font-mono text-slate-300">
              {paginatedResults.map((item, idx) => {
                const name = getItemName(item);
                const fullPath = getItemPath(item);
                const folder = getItemFolder(item);
                const size = getItemSize(item);

                return (
                  <div
                    key={fullPath + idx}
                    className="px-4 py-2 hover:bg-slate-900/60 flex items-center justify-between text-xs group"
                  >
                    <div className="flex items-center gap-2.5 min-w-0 flex-1 pr-4">
                      {getFileIcon(name)}
                      <span
                        className="font-medium text-slate-200 truncate cursor-pointer hover:text-blue-400 font-sans"
                        onClick={() => handlePreview(fullPath)}
                        title={name}
                      >
                        {name}
                      </span>
                      <span
                        className="text-slate-500 text-[11px] truncate hidden sm:inline"
                        title={fullPath}
                      >
                        {folder}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 shrink-0">
                      <span className="font-mono text-slate-400 text-[11px]">
                        {formatBytes(size)}
                      </span>
                      <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-slate-400 hover:text-white"
                          title="Copy path"
                          onClick={() => handleCopyPath(fullPath)}
                        >
                          {copiedPath === fullPath ? (
                            <Check className="h-3 w-3 text-emerald-400" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-slate-400 hover:text-blue-400"
                          title="Preview file"
                          onClick={() => handlePreview(fullPath)}
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Explorer Details View (Table) */
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-800 bg-slate-900/50 text-slate-400 font-medium">
                  <tr>
                    <th className="py-3 px-4 w-8">#</th>
                    <th
                      className="py-3 px-4 cursor-pointer hover:text-white"
                      onClick={() => {
                        if (sortBy === "name") setSortAsc(!sortAsc);
                        else {
                          setSortBy("name");
                          setSortAsc(true);
                        }
                      }}
                    >
                      <div className="flex items-center gap-1">
                        File Name
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="py-3 px-4 cursor-pointer hover:text-white hidden md:table-cell"
                      onClick={() => {
                        if (sortBy === "path") setSortAsc(!sortAsc);
                        else {
                          setSortBy("path");
                          setSortAsc(true);
                        }
                      }}
                    >
                      <div className="flex items-center gap-1">
                        Folder Path
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th
                      className="py-3 px-4 cursor-pointer hover:text-white text-right"
                      onClick={() => {
                        if (sortBy === "size") setSortAsc(!sortAsc);
                        else {
                          setSortBy("size");
                          setSortAsc(false);
                        }
                      }}
                    >
                      <div className="flex items-center justify-end gap-1">
                        Size
                        <ArrowUpDown className="h-3 w-3" />
                      </div>
                    </th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {paginatedResults.map((item, idx) => {
                    const name = getItemName(item);
                    const fullPath = getItemPath(item);
                    const folder = getItemFolder(item);
                    const size = getItemSize(item);
                    const globalIdx = (currentPage - 1) * pageSize + idx + 1;

                    return (
                      <tr
                        key={fullPath + idx}
                        className="hover:bg-slate-800/40 transition-colors group"
                      >
                        <td className="py-2.5 px-4 text-slate-500">
                          {globalIdx}
                        </td>
                        <td className="py-2.5 px-4 font-sans font-medium text-slate-200">
                          <div className="flex items-center gap-2 truncate max-w-xs sm:max-w-md">
                            {getFileIcon(name)}
                            <span
                              className="truncate hover:text-blue-400 cursor-pointer"
                              onClick={() => handlePreview(fullPath)}
                            >
                              {name}
                            </span>
                          </div>
                        </td>
                        <td className="py-2.5 px-4 text-slate-400 hidden md:table-cell truncate max-w-md">
                          {folder}
                        </td>
                        <td className="py-2.5 px-4 text-right text-slate-400 font-mono">
                          {formatBytes(size)}
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1 opacity-80 group-hover:opacity-100">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0 text-slate-400 hover:text-white"
                              title="Copy path"
                              onClick={() => handleCopyPath(fullPath)}
                            >
                              {copiedPath === fullPath ? (
                                <Check className="h-3.5 w-3.5 text-emerald-400" />
                              ) : (
                                <Copy className="h-3.5 w-3.5" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-7 w-7 p-0 text-slate-400 hover:text-blue-400"
                              title="Preview file"
                              onClick={() => handlePreview(fullPath)}
                            >
                              <Eye className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls */}
          {results.length > 0 && (
            <div className="border-t border-slate-800 p-3 px-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <span>
                  Showing{" "}
                  <span className="font-semibold text-white font-mono">
                    {sortedResults.length > 0
                      ? (currentPage - 1) * pageSize + 1
                      : 0}
                  </span>{" "}
                  –{" "}
                  <span className="font-semibold text-white font-mono">
                    {Math.min(currentPage * pageSize, sortedResults.length)}
                  </span>{" "}
                  of{" "}
                  <span className="font-semibold text-white font-mono">
                    {sortedResults.length}
                  </span>{" "}
                  results
                </span>
              </div>

              {/* Switchable Page Size Dropdown */}
              <div className="flex items-center gap-2">
                <span className="text-slate-500">Per page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-xs font-mono text-slate-200 focus:border-blue-500 focus:outline-none cursor-pointer"
                >
                  <option value={25}>25 / page</option>
                  <option value={50}>50 / page</option>
                  <option value={100}>100 / page</option>
                  <option value={250}>250 / page</option>
                  <option value={500}>500 / page</option>
                </select>
              </div>

              {/* Page Navigation Buttons */}
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-slate-800 h-7 text-xs text-slate-300 hover:text-white"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <span>
                  Page{" "}
                  <span className="font-semibold text-white font-mono">
                    {currentPage}
                  </span>{" "}
                  of{" "}
                  <span className="font-semibold text-white font-mono">
                    {totalPages}
                  </span>
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-slate-800 h-7 text-xs text-slate-300 hover:text-white"
                  disabled={currentPage >= totalPages}
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* File Preview Drawer */}
      {previewFile && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-2xl bg-slate-950 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            {/* Drawer Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2 truncate">
                <FileText className="h-5 w-5 text-blue-400 shrink-0" />
                <span className="font-semibold text-slate-200 truncate">
                  {previewFile.path}
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-slate-400 hover:text-white"
                onClick={() => setPreviewFile(null)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* File Details Bar */}
            <div className="bg-slate-900/60 px-4 py-2 text-xs text-slate-400 flex items-center gap-4 border-b border-slate-800">
              <span>Type: {previewFile.type}</span>
              <span>Size: {formatBytes(previewFile.size)}</span>
              {previewFile.truncated && (
                <span className="text-amber-400">(Truncated preview)</span>
              )}
            </div>

            {/* File Body Content */}
            <div className="flex-1 overflow-auto p-4 font-mono text-xs text-slate-300 bg-slate-900/30">
              {previewLoading ? (
                <div className="flex items-center justify-center h-48 text-slate-400 gap-2">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-500" />{" "}
                  Loading preview...
                </div>
              ) : previewFile?.type === "text" ? (
                <pre className="whitespace-pre-wrap font-mono leading-relaxed">
                  {previewFile.content}
                </pre>
              ) : previewFile?.type === "image" ? (
                <div className="flex items-center justify-center h-full">
                  <img
                    src={`data:${previewFile.mime};base64,${previewFile.content}`}
                    alt="Preview"
                    className="max-h-full max-w-full rounded border border-slate-800"
                  />
                </div>
              ) : (
                <pre className="whitespace-pre-wrap font-mono text-slate-400">
                  {previewFile?.content}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

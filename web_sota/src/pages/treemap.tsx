import {
  AlertTriangle,
  Clock,
  FileText,
  HardDrive,
  Loader2,
  Map as MapIcon,
  PieChart,
  RefreshCw,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { mcpClient } from "@/common/mcp-client";
import { CushionTreemap, type FileItem } from "@/components/CushionTreemap";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type FilePreview = {
  path: string;
  type: string;
  mime: string;
  content: string;
  size: number;
  truncated?: boolean;
};

function formatBytes(bytes?: number): string {
  if (bytes == null || Number.isNaN(bytes)) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function TreemapPage() {
  const [directory, setDirectory] = useState<string>("C:\\");
  const [pattern, setPattern] = useState<string>("*");
  const [maxResults, setMaxResults] = useState<number>(1000);

  const [results, setResults] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);

  // File Preview Modal
  const [previewFile, setPreviewFile] = useState<FilePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);

  const runTreemapScan = useCallback(
    async (overrideDir?: string) => {
      const activeDir = overrideDir ?? directory;
      setLoading(true);
      setErrorMsg(null);

      const startTime = performance.now();
      try {
        const res = await mcpClient.searchDirect({
          pattern: pattern,
          directory: activeDir,
          max_results: maxResults,
        });

        const endTime = performance.now();
        setDurationMs(Math.round(endTime - startTime));

        if (res.service_down) {
          setErrorMsg(
            res.error || "FastSearch C++ Windows Service is offline.",
          );
          setResults([]);
        } else if (res.success === false) {
          setErrorMsg(res.error || "MFT volume scan failed.");
          setResults([]);
        } else {
          setResults(res.results || []);
        }
      } catch (e: unknown) {
        setErrorMsg(e instanceof Error ? e.message : "Treemap scan error");
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [directory, pattern, maxResults],
  );

  useEffect(() => {
    runTreemapScan();
  }, [runTreemapScan]);

  const handlePreview = async (path: string) => {
    setPreviewLoading(true);
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

  const totalBytes = results.reduce((sum, item) => {
    const s = item.size ?? item.size_bytes ?? item.length ?? 0;
    return sum + s;
  }, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <PieChart className="h-6 w-6 text-blue-500" />
            WizTree 3D Cushion Treemap
          </h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Visual disk space analyzer with 3D cushion layout and interactive
            volume hierarchy
          </p>
        </div>

        <Button
          onClick={() => runTreemapScan()}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2 self-start sm:self-auto"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Rescan Volume
        </Button>
      </div>

      {/* Control Bar */}
      <Card className="border-slate-800 bg-slate-950/60 shadow-xl">
        <CardContent className="p-4 space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 flex gap-2">
              <input
                type="text"
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                placeholder="Volume Directory (e.g. C:\, D:\, d:\Dev\repos)..."
                value={directory}
                onChange={(e) => setDirectory(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && runTreemapScan()}
              />
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                className="w-28 sm:w-36 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none font-mono"
                placeholder="Pattern (*)"
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
              />

              <select
                value={maxResults}
                onChange={(e) => setMaxResults(Number(e.target.value))}
                className="rounded-md border border-slate-700 bg-slate-900 px-2.5 py-2 text-xs font-mono text-slate-200 focus:border-blue-500 focus:outline-none cursor-pointer"
                title="Max Items limit"
              >
                <option value={500}>Max: 500</option>
                <option value={1000}>Max: 1,000</option>
                <option value={2500}>Max: 2,500</option>
                <option value={5000}>Max: 5,000</option>
                <option value={10000}>Max: 10,000</option>
              </select>
            </div>
          </div>

          {/* Presets Bar */}
          <div className="flex flex-wrap items-center gap-2 text-xs pt-1">
            <span className="text-slate-500 font-medium flex items-center gap-1">
              <HardDrive className="h-3.5 w-3.5 text-blue-400" /> Drives:
            </span>
            {["C:\\", "D:\\", "d:\\Dev\\repos"].map((d) => (
              <button
                key={d}
                onClick={() => {
                  setDirectory(d);
                  runTreemapScan(d);
                }}
                className={`rounded bg-slate-900 border px-2.5 py-0.5 transition-colors font-mono ${
                  directory === d
                    ? "border-blue-500 text-blue-400 font-semibold"
                    : "border-slate-800 text-slate-400 hover:text-white hover:border-slate-700"
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {errorMsg && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-amber-300 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1 text-sm">
            <p className="font-semibold">Volume Scan Warning</p>
            <p className="mt-1 text-xs opacity-90">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-slate-800 bg-slate-950/50 p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Total Scanned Files
          </div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">
            {results.length}
          </div>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50 p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Total Volume Size
          </div>
          <div className="text-2xl font-bold text-blue-400 mt-1 font-mono">
            {formatBytes(totalBytes)}
          </div>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50 p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            MFT Scan Latency
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1 font-mono flex items-center gap-1.5">
            <Clock className="h-5 w-5 text-emerald-500" />
            {durationMs !== null ? `${durationMs} ms` : "—"}
          </div>
        </Card>
      </div>

      {/* Standalone Cushion Treemap Card */}
      <Card className="border-slate-800 bg-slate-950/60 shadow-xl">
        <CardHeader className="pb-3 border-b border-slate-800">
          <CardTitle className="text-base font-semibold text-white flex items-center gap-2">
            <MapIcon className="h-4 w-4 text-blue-400" />
            Volume Cushion Treemap Layout
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 text-slate-400">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500 mb-3" />
              <p className="text-sm font-medium">
                Computing Cushion Treemap Geometry...
              </p>
            </div>
          ) : (
            <CushionTreemap
              items={results}
              height={620}
              onSelectFile={handlePreview}
            />
          )}
        </CardContent>
      </Card>

      {/* File Preview Drawer */}
      {previewFile && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-2xl bg-slate-950 border-l border-slate-800 h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
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

            <div className="bg-slate-900/60 px-4 py-2 text-xs text-slate-400 flex items-center gap-4 border-b border-slate-800">
              <span>Type: {previewFile.type}</span>
              <span>Size: {formatBytes(previewFile.size)}</span>
            </div>

            <div className="flex-1 overflow-auto p-4 font-mono text-xs text-slate-300 bg-slate-900/30">
              {previewLoading ? (
                <div className="flex items-center justify-center h-48 text-slate-400 gap-2">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                  Loading preview...
                </div>
              ) : (
                <pre className="whitespace-pre-wrap font-mono leading-relaxed">
                  {previewFile.content}
                </pre>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

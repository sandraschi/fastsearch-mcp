import {
  ArrowRight,
  CheckCircle2,
  Cpu,
  HardDrive,
  Loader2,
  PieChart,
  Play,
  RefreshCw,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  Terminal,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { mcpClient } from "@/common/mcp-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ServiceStatus = {
  success?: boolean;
  running?: boolean;
  service_down?: boolean;
  pipe_connected?: boolean;
  pipe_name?: string;
  executable_exists?: boolean;
  status?: string;
  message?: string;
  error?: string;
};

export function Dashboard() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [startLogs, setStartLogs] = useState<string[]>([]);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const data = await mcpClient.getServiceStatusDirect();
      setStatus(data);
    } catch {
      setStatus({ running: false, error: "Failed to connect to REST API" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleStartService = async () => {
    setActionLoading(true);
    setActionError(null);
    setStartLogs([]);
    try {
      const res = await mcpClient.startServiceDirect();
      if (res.logs && res.logs.length > 0) {
        setStartLogs(res.logs);
      }
      if (!res.success) {
        setActionError(
          res.error || res.message || "Failed to start Windows Service",
        );
      }
      await fetchStatus();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : String(e));
      fetchStatus();
    } finally {
      setActionLoading(false);
    }
  };

  const isRunning = status?.running || status?.status === "running";

  return (
    <div className="space-y-6 select-none">
      {/* 🚀 SOTA Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-blue-500/20 bg-gradient-to-r from-blue-950/70 via-slate-950 to-indigo-950/70 p-6 md:p-8 shadow-2xl backdrop-blur-xl">
        <div className="absolute -top-24 -right-24 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-purple-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold text-blue-400">
              <Sparkles className="h-3.5 w-3.5" />
              SOTA NTFS Master File Table Engine
            </div>

            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white leading-tight">
              Instant Zero-Indexing <br />
              <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                High-Performance File Search
              </span>
            </h1>

            <p className="text-slate-300 text-sm md:text-base leading-relaxed">
              FastSearch MCP queries raw Windows NTFS volume structures
              (`\\.\C:`, `\\.\D:`) directly over Win32 named pipes with{" "}
              <strong>zero background indexing overhead</strong> and sub-second
              MFT search speeds.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <a href="/search">
                <Button className="bg-blue-600 hover:bg-blue-500 text-white font-semibold flex items-center gap-2 shadow-lg shadow-blue-600/20">
                  <Search className="h-4 w-4" />
                  Launch Dedicated Search
                </Button>
              </a>

              <a href="/treemap">
                <Button
                  variant="outline"
                  className="border-slate-700 bg-slate-900/80 text-slate-200 hover:text-white hover:bg-slate-800 flex items-center gap-2"
                >
                  <PieChart className="h-4 w-4 text-purple-400" />
                  3D Cushion Treemap
                </Button>
              </a>
            </div>
          </div>

          {/* Engine Status Badge Card */}
          <div className="shrink-0 rounded-xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl space-y-4 w-full md:w-80 backdrop-blur-md">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Service Engine
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchStatus}
                disabled={loading}
                className="h-7 w-7 p-0 text-slate-400 hover:text-white"
                title="Refresh Status"
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`}
                />
              </Button>
            </div>

            <div className="flex items-center gap-3">
              <div
                className={`p-2.5 rounded-lg shrink-0 ${isRunning ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}
              >
                <Server className="h-6 w-6" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-bold text-white text-sm flex items-center gap-1.5 truncate">
                  FastSearch C++
                </div>
                {isRunning ? (
                  <span className="text-xs text-emerald-400 font-medium flex items-center gap-1 mt-0.5">
                    <CheckCircle2 className="h-3 w-3" /> Online (MFT Mode)
                  </span>
                ) : (
                  <span className="text-xs text-rose-400 font-medium flex items-center gap-1 mt-0.5">
                    <Zap className="h-3 w-3" /> Service Stopped
                  </span>
                )}
              </div>
            </div>

            {!isRunning && (
              <Button
                onClick={handleStartService}
                disabled={actionLoading}
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center justify-center gap-2"
              >
                {actionLoading ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Play className="h-3.5 w-3.5" />
                )}
                Elevate & Start Service
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* 📊 High-Level Metrics & Architecture Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/60 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Architecture
            </CardTitle>
            <Cpu className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-white">Direct MFT</div>
            <p className="text-[11px] text-slate-400 mt-1">
              0% idle CPU, no indexing services
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/60 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              IPC Transport
            </CardTitle>
            <Server className="h-4 w-4 text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-white">Win32 Pipe</div>
            <p className="text-[11px] text-slate-400 font-mono mt-1 truncate">
              \\.\pipe\FastSearchMCP
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/60 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              C++ Binary
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-white">
              {status?.executable_exists !== false ? "Ready" : "Missing"}
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-1 truncate">
              FastSearchServiceNew.exe
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/60 shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Filesystem
            </CardTitle>
            <HardDrive className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-white">NTFS Master</div>
            <p className="text-[11px] text-slate-400 mt-1">
              Direct volume handle read
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 🚀 Quick Action Drive Shortcuts & Feature Showcase */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Drive Launchers */}
        <Card className="border-slate-800 bg-slate-950/60 shadow-xl">
          <CardHeader className="pb-3 border-b border-slate-800">
            <CardTitle className="text-base font-bold text-white flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-blue-400" />
              Quick Drive & Folder Scans
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            {[
              {
                path: "C:\\",
                label: "System Drive C:\\",
                desc: "MFT Root Volume",
              },
              {
                path: "D:\\",
                label: "Data Drive D:\\",
                desc: "MFT Root Volume",
              },
              {
                path: "d:\\Dev\\repos",
                label: "Dev Fleet Workspace",
                desc: "Codebase Folder",
              },
            ].map((drive) => (
              <a
                key={drive.path}
                href={`/search?directory=${encodeURIComponent(drive.path)}`}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-800/80 bg-slate-900/50 hover:bg-slate-800/80 hover:border-slate-700 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded bg-slate-950 border border-slate-800 text-blue-400 group-hover:text-blue-300">
                    <HardDrive className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="font-bold text-white text-xs group-hover:text-blue-300">
                      {drive.label}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono">
                      {drive.path} • {drive.desc}
                    </div>
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-white transition-transform group-hover:translate-x-1" />
              </a>
            ))}
          </CardContent>
        </Card>

        {/* Cushion Treemap Feature Spotlight */}
        <Card className="border-slate-800 bg-slate-950/60 shadow-xl flex flex-col justify-between">
          <CardHeader className="pb-3 border-b border-slate-800">
            <CardTitle className="text-base font-bold text-white flex items-center gap-2">
              <PieChart className="h-4 w-4 text-purple-400" />
              3D Disk Cushion Treemap Visualizer
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-3 flex-1 flex flex-col justify-between">
            <p className="text-xs text-slate-300 leading-relaxed">
              Explore your hard drives in a full 3D cushion layout with radial
              lighting, subfolder zoom navigation, file type color-coding, and
              high-res PNG / CSV export.
            </p>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2">
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 text-slate-300">
                🎨 3D Cushion Lighting
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 text-slate-300">
                🔍 Subfolder Zooming
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 text-slate-300">
                📸 4K Image Export
              </div>
              <div className="p-2 rounded bg-slate-900/60 border border-slate-800 text-slate-300">
                📊 CSV & JSON Export
              </div>
            </div>

            <a href="/treemap" className="pt-2 block">
              <Button className="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs flex items-center justify-center gap-2">
                <PieChart className="h-4 w-4" />
                Open Cushion Treemap Webpage
              </Button>
            </a>
          </CardContent>
        </Card>
      </div>

      {/* Service Action Diagnostics Log Container */}
      {actionError && (
        <Card className="border-rose-800/60 bg-rose-950/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-bold text-rose-400 flex items-center gap-2">
              <Terminal className="h-4 w-4" />
              Service Execution Diagnostic Output
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-2">
            <div className="text-xs text-rose-300 font-semibold">
              {actionError}
            </div>
            {startLogs.length > 0 && (
              <div className="rounded border border-slate-800 bg-slate-950 p-3 font-mono text-[11px] text-slate-300 space-y-1 overflow-x-auto max-h-48">
                {startLogs.map((logLine, idx) => (
                  <div
                    key={idx}
                    className={
                      logLine.includes("[ERROR]") || logLine.includes("Stderr")
                        ? "text-rose-400"
                        : logLine.includes("[WARNING]")
                          ? "text-amber-400"
                          : logLine.includes("[SUCCESS]")
                            ? "text-emerald-400"
                            : "text-slate-300"
                    }
                  >
                    {logLine}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

import {
  CheckCircle2,
  Cpu,
  HardDrive,
  Loader2,
  Play,
  Search,
  Server,
  ShieldCheck,
  XCircle,
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
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            System Insight
          </h2>
          <p className="text-slate-400 text-sm">
            Real-time status and operational health of FastSearch C++ engine
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchStatus}
            disabled={loading}
            className="border-slate-800 bg-slate-900 text-slate-300 hover:text-white"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-1" />
            ) : (
              "Refresh Health"
            )}
          </Button>
          <a href="/search">
            <Button
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-1.5"
            >
              <Search className="h-4 w-4" />
              Open Search Page
            </Button>
          </a>
        </div>
      </div>

      {/* Live Operational Status Bar */}
      <Card className="border-slate-800 bg-slate-950/60">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className={`p-3 rounded-xl ${isRunning ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}
              >
                <Server className="h-6 w-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">
                    C++ FastSearch Core Engine
                  </h3>
                  {isRunning ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                      <CheckCircle2 className="h-3 w-3" /> Running (Direct MFT
                      Mode)
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-2.5 py-0.5 text-xs font-medium text-rose-400 border border-rose-500/20">
                      <XCircle className="h-3 w-3" /> Service Offline
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  {isRunning
                    ? "Listening on named pipe \\\\.\\pipe\\FastSearchMCP. Direct NTFS Master File Table queries enabled."
                    : "FastSearch C++ Windows Service is offline. Click Start Service to elevate via UAC or run 'sc start FastSearchMCP' in Admin PowerShell."}
                </p>
              </div>
            </div>

            {!isRunning && (
              <Button
                onClick={handleStartService}
                disabled={actionLoading}
                className="bg-emerald-600 hover:bg-emerald-700 text-white shrink-0"
              >
                {actionLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                ) : (
                  <Play className="h-4 w-4 mr-1.5" />
                )}
                Start Service
              </Button>
            )}
          </div>

          {actionError && (
            <div className="mt-4 rounded-lg border border-red-800/60 bg-red-950/20 p-4 space-y-2">
              <div className="text-sm font-semibold text-red-400 flex items-center gap-2">
                <XCircle className="h-4 w-4 shrink-0" />
                Service Action Diagnostics: {actionError}
              </div>
              {startLogs.length > 0 && (
                <div className="mt-2 rounded border border-slate-800 bg-slate-950 p-3 font-mono text-[11px] text-slate-300 space-y-1 overflow-x-auto max-h-48">
                  <div className="text-slate-500 font-sans font-medium text-[10px] uppercase tracking-wider mb-1">
                    Diagnostic Execution Logs:
                  </div>
                  {startLogs.map((logLine, idx) => (
                    <div
                      key={idx}
                      className={
                        logLine.includes("[ERROR]") ||
                        logLine.includes("Stderr")
                          ? "text-red-400"
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
            </div>
          )}
        </CardContent>
      </Card>

      {/* Metric Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Engine Mode
            </CardTitle>
            <Cpu className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-white">Direct MFT</div>
            <p className="text-[11px] text-slate-500 mt-1">
              No background indexing overhead
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              IPC Transport
            </CardTitle>
            <Server className="h-4 w-4 text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-white">Named Pipe</div>
            <p className="text-[11px] text-slate-500 mt-1">
              \\.\pipe\FastSearchMCP
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Executable
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-white">
              {status?.executable_exists !== false ? "Installed" : "Missing"}
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              FastSearchServiceNew.exe
            </p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Supported FS
            </CardTitle>
            <HardDrive className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold text-white">NTFS</div>
            <p className="text-[11px] text-slate-500 mt-1">
              Direct volume access
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Architecture Info */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white text-base">
            Direct MFT Architecture
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-slate-300">
          <p>
            Unlike traditional file search utilities that run heavy background
            indexers and consume CPU/RAM, FastSearch queries the NTFS Master
            File Table directly at search time.
          </p>
          <div className="grid gap-3 sm:grid-cols-3 pt-2">
            <div className="p-3 rounded border border-slate-800 bg-slate-900/40">
              <span className="font-semibold text-white block mb-1">
                0% Idle CPU
              </span>
              <span className="text-xs text-slate-400">
                Zero background indexing services running when idle.
              </span>
            </div>
            <div className="p-3 rounded border border-slate-800 bg-slate-900/40">
              <span className="font-semibold text-white block mb-1">
                Instant Results
              </span>
              <span className="text-xs text-slate-400">
                Reads raw MFT records directly via Win32 volume handles.
              </span>
            </div>
            <div className="p-3 rounded border border-slate-800 bg-slate-900/40">
              <span className="font-semibold text-white block mb-1">
                SOTA Search UI
              </span>
              <span className="text-xs text-slate-400">
                Dedicated Search page with live status, filters, and file
                preview.
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

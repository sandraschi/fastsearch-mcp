import {
  Activity,
  CheckCircle2,
  Cpu,
  Loader2,
  Play,
  RefreshCw,
  RotateCcw,
  Server,
  ShieldCheck,
  Square,
  XCircle,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { mcpClient } from "@/common/mcp-client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ServiceStatus = {
  success?: boolean;
  running?: boolean;
  service_state?: string;
  pipe_connected?: boolean;
  executable_path?: string;
  pipe_name?: string;
  pipe_info?: unknown;
  error?: string;
};

type ProbeResult = { latencyMs: number; count: number; error?: string };

export function Service() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [probe, setProbe] = useState<ProbeResult | null>(null);
  const [probeLoading, setProbeLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setActionError(null);
    try {
      const res = (await mcpClient.callTool("service_status", {
        level: "intermediate",
      })) as ServiceStatus;
      setStatus(res);
    } catch (e) {
      setStatus({
        success: false,
        running: false,
        error: e instanceof Error ? e.message : "Failed to get status",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const runAction = async (action: "start" | "stop" | "restart") => {
    const tool =
      action === "start"
        ? "service_start_fastsearch"
        : action === "stop"
          ? "service_stop_fastsearch"
          : "service_restart_fastsearch";
    setActionLoading(action);
    setActionError(null);
    try {
      await mcpClient.callTool(tool, {});
      await fetchStatus();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
    } finally {
      setActionLoading(null);
    }
  };

  const runProbe = async () => {
    setProbeLoading(true);
    setProbe(null);
    try {
      const start = performance.now();
      const res = (await mcpClient.callTool("fastsearch_search", {
        pattern: "*.txt",
        path: "C:\\",
        max_results: 5,
      })) as { results?: unknown[]; count?: number };
      const end = performance.now();
      const count = Array.isArray(res?.results)
        ? res.results.length
        : (res?.count ?? 0);
      setProbe({ latencyMs: Math.round(end - start), count });
    } catch (e: unknown) {
      setProbe({
        latencyMs: 0,
        count: 0,
        error: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setProbeLoading(false);
    }
  };

  const running = status?.running === true;
  const pipeOk = status?.pipe_connected === true;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <Server className="h-7 w-7 text-slate-400" />
          NTFS Search Service
        </h2>
        <p className="text-slate-400">
          Windows service for direct NTFS Master File Table access. Install via
          MSI; start/stop/restart require admin.
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center justify-between text-white">
            <span className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-blue-400" />
              Service status
            </span>
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-white"
              onClick={fetchStatus}
              disabled={loading}
            >
              <RefreshCw
                className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
              />
            </Button>
          </CardTitle>
          <CardDescription className="text-slate-400">
            FastSearchMCP service and named pipe (\\\.\pipe\FastSearchMCP)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <div className="flex items-center gap-2 text-slate-400">
              <Loader2 className="h-4 w-4 animate-spin" />
              Checking...
            </div>
          ) : (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
                  {running ? (
                    <CheckCircle2 className="h-8 w-8 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="h-8 w-8 text-amber-400 shrink-0" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      Process
                    </p>
                    <p className="text-xs text-slate-400">
                      {running ? "Running" : "Stopped"}
                      {status?.service_state
                        ? ` (${status.service_state})`
                        : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
                  {pipeOk ? (
                    <CheckCircle2 className="h-8 w-8 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="h-8 w-8 text-amber-400 shrink-0" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      Named pipe
                    </p>
                    <p className="text-xs text-slate-400">
                      {pipeOk ? "Connected" : "Not connected"}
                      {status?.pipe_name ? ` — ${status.pipe_name}` : ""}
                    </p>
                  </div>
                </div>
              </div>
              {status?.executable_path && (
                <p className="text-xs text-slate-500 font-mono break-all">
                  Executable: {status.executable_path}
                </p>
              )}
              {status?.error && (
                <p className="text-sm text-amber-400 bg-amber-400/10 p-2 rounded border border-amber-400/20">
                  {status.error}
                </p>
              )}

              <div className="flex flex-wrap gap-2 pt-2">
                <Button
                  className="bg-emerald-600 hover:bg-emerald-700"
                  disabled={!running || actionLoading !== null}
                  onClick={() => runAction("stop")}
                >
                  {actionLoading === "stop" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Square className="h-4 w-4 mr-2" />
                  )}
                  Stop
                </Button>
                <Button
                  variant="outline"
                  className="border-slate-700"
                  disabled={running || actionLoading !== null}
                  onClick={() => runAction("start")}
                >
                  {actionLoading === "start" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4 mr-2" />
                  )}
                  Start
                </Button>
                <Button
                  variant="outline"
                  className="border-slate-700"
                  disabled={!running || actionLoading !== null}
                  onClick={() => runAction("restart")}
                >
                  {actionLoading === "restart" ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RotateCcw className="h-4 w-4 mr-2" />
                  )}
                  Restart
                </Button>
              </div>
              {actionError && (
                <p className="text-sm text-red-400 bg-red-400/10 p-2 rounded border border-red-400/20">
                  {actionError}
                </p>
              )}
              <p className="text-xs text-slate-500">
                Start/Stop/Restart require administrator privileges. Install the
                service via fastsearch-mcp-setup.msi (see README).
              </p>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Zap className="h-5 w-5 text-amber-400" />
            Search probe
          </CardTitle>
          <CardDescription className="text-slate-400">
            Run a tiny search (C:\*.txt, max 5) to confirm the service returns
            results at speed
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            className="border-slate-700"
            onClick={runProbe}
            disabled={!running || probeLoading}
          >
            {probeLoading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Activity className="h-4 w-4 mr-2" />
            )}
            Run probe
          </Button>
          {probe !== null && (
            <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/50 p-4">
              {probe.error ? (
                <p className="text-sm text-amber-400">{probe.error}</p>
              ) : (
                <p className="text-sm text-slate-200">
                  Latency:{" "}
                  <span className="font-mono text-emerald-400">
                    {probe.latencyMs} ms
                  </span>
                  {" · "}
                  Results: <span className="font-mono">{probe.count}</span>
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <ShieldCheck className="h-5 w-5 text-blue-400" />
            Privilege Separation Architecture
          </CardTitle>
          <CardDescription className="text-slate-400">
            Security and design model for zero-overhead NTFS MFT search
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs text-slate-300">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 font-mono text-[11px] leading-relaxed text-slate-300">
            <div className="text-amber-400 font-semibold mb-1">Elevated Service Domain (Installed ONCE)</div>
            <div className="text-slate-400">├── FastSearchMCP Windows Service (LocalSystem / Admin)</div>
            <div className="text-slate-400">├── Reads raw NTFS MFT volume structures (\\.\C:, \\.\D:)</div>
            <div className="text-slate-400">└── Listens on IPC Named Pipe (\\.\pipe\FastSearchMCP)</div>
            <div className="text-blue-400 my-1 font-sans font-medium text-center">▲ IPC Named Pipe Connection (Local RPC) ▼</div>
            <div className="text-emerald-400 font-semibold mb-1">Unprivileged User Domain (Standard User Space)</div>
            <div className="text-slate-400">├── Python MCP Server / REST API Bridge / Web UI</div>
            <div className="text-slate-400">├── ZERO elevation required at runtime for searches</div>
            <div className="text-slate-400">└── Connects via Win32 Named Pipe client</div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="rounded-md border border-slate-800 bg-slate-900/40 p-3 space-y-1">
              <div className="font-semibold text-slate-200">Elevated Engine (LocalSystem)</div>
              <p className="text-slate-400 leading-normal">
                Installed once as a Windows Service. Accesses raw volume handles (<code className="text-amber-200">\\.\C:</code>) to parse MFT file records directly without background indexing.
              </p>
            </div>
            <div className="rounded-md border border-slate-800 bg-slate-900/40 p-3 space-y-1">
              <div className="font-semibold text-slate-200">Standard User Client</div>
              <p className="text-slate-400 leading-normal">
                The web application and MCP bridge run in normal user space. No admin prompts or elevated rights are needed when running queries over named pipes.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

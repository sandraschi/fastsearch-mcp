import {
  CheckCircle2,
  FlaskConical,
  Loader2,
  Play,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { mcpClient } from "@/common/mcp-client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type TestResult = {
  name: string;
  passed: boolean;
  message: string;
  duration_ms: number;
  details?: unknown;
};

type RunResult = {
  passed: number;
  total: number;
  results: TestResult[];
};

export function Tests() {
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunResult | null>(null);
  const [pattern, setPattern] = useState("*.txt");
  const [directory, setDirectory] = useState("C:\\");
  const [maxResults, setMaxResults] = useState(5);

  const runTests = async () => {
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const res = await mcpClient.runTests({
        pattern,
        directory,
        max_results: maxResults,
      });
      setResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <FlaskConical className="h-7 w-7 text-slate-400" />
          Live Tests
        </h2>
        <p className="text-slate-400">
          Run integration tests against the FastSearch service: pipe connection,
          service info, and real search via pipe.
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Test parameters</CardTitle>
          <CardDescription className="text-slate-400">
            Used for the &quot;search_via_pipe&quot; test (pattern, directory,
            max_results).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className="text-xs font-medium text-slate-400">
                Pattern
              </label>
              <input
                type="text"
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
                placeholder="*.txt"
                className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">
                Directory
              </label>
              <input
                type="text"
                value={directory}
                onChange={(e) => setDirectory(e.target.value)}
                placeholder="C:\\"
                className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400">
                Max results
              </label>
              <input
                type="number"
                min={1}
                max={100}
                value={maxResults}
                onChange={(e) =>
                  setMaxResults(parseInt(e.target.value, 10) || 5)
                }
                className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <Button
            className="bg-blue-600 hover:bg-blue-700"
            disabled={running}
            onClick={runTests}
          >
            {running ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Run tests
          </Button>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded border border-red-800 bg-red-950/30 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {result && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">
              Results: {result.passed}/{result.total} passed
            </CardTitle>
            <CardDescription className="text-slate-400">
              service_process, pipe_connect, get_service_info, search_via_pipe
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {result.results.map((r) => (
                <li
                  key={r.name}
                  className="flex items-start gap-3 rounded border border-slate-800 bg-slate-900/50 p-3"
                >
                  {r.passed ? (
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />
                  ) : (
                    <XCircle className="h-5 w-5 shrink-0 text-red-500" />
                  )}
                  <div className="min-w-0 flex-1">
                    <span className="font-medium text-slate-200">{r.name}</span>
                    <span className="ml-2 text-slate-400">
                      ({r.duration_ms} ms)
                    </span>
                    <p className="mt-1 text-sm text-slate-300">{r.message}</p>
                    {r.details != null && (
                      <pre className="mt-2 overflow-auto rounded bg-slate-950 p-2 text-xs text-slate-400">
                        {JSON.stringify(r.details, null, 2)}
                      </pre>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

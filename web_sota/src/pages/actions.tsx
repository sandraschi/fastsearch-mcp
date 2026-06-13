import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Search, FolderSearch, Loader2, CheckCircle2, AlertCircle, Layers } from "lucide-react";
import { mcpClient } from "@/common/mcp-client";

interface SearchResult {
    path: string;
    size?: number;
}

export function Actions() {
    const [loading, setLoading] = useState<string | null>(null);
    const [results, setResults] = useState<SearchResult[] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [status, setStatus] = useState<string | null>(null);

    const handleDiscoverWebapps = async () => {
        setLoading("discover");
        setError(null);
        setResults(null);
        setStatus("Scanning d:/Dev/repos for webapp directories...");
        try {
            const response = await mcpClient.callTool("fastsearch_search_advanced", {
                pattern: "*webapp*",
                path: "d:/Dev/repos",
                include_directories: true,
                max_results: 50
            });

            if (response && response.results) {
                setResults(response.results);
                setStatus(`Found ${response.results.length} webapp directories.`);
            } else {
                setError("No results found or unexpected response format.");
            }
        } catch (err: any) {
            setError(err.message || "Failed to execute search");
        } finally {
            setLoading(null);
        }
    };

    const handleScanRepos = async () => {
        setLoading("scan");
        setError(null);
        setResults(null);
        setStatus("Scanning d:/Dev/repos for package.json (repository identification)...");
        try {
            const response = await mcpClient.callTool("fastsearch_search_advanced", {
                pattern: "package.json",
                path: "d:/Dev/repos",
                max_results: 50
            });

            if (response && response.results) {
                setResults(response.results);
                setStatus(`Identified ${response.results.length} active Node.js repositories.`);
            } else {
                setError("No repositories found.");
            }
        } catch (err: any) {
            setError(err.message || "Scan failed");
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Search Operations</h2>
                <p className="text-slate-400">High-impact indexing and discovery tasks</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white text-base">
                            <FolderSearch className="h-4 w-4 text-blue-400" />
                            Discover Webapps
                        </CardTitle>
                        <CardDescription className="text-xs text-slate-400">
                            Scan d:/Dev/repos/ for folders containing "webapp", "frontend", or "ui".
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button
                            className="w-full bg-blue-600 hover:bg-blue-700"
                            onClick={handleDiscoverWebapps}
                            disabled={!!loading}
                        >
                            {loading === "discover" ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : "Run Webapp Scan"}
                        </Button>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white text-base">
                            <Search className="h-4 w-4 text-emerald-400" />
                            Scan Repositories
                        </CardTitle>
                        <CardDescription className="text-xs text-slate-400">
                            Identify active development repositories by locating project manifest files.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button
                            variant="outline"
                            className="w-full border-slate-800 text-emerald-400 hover:bg-emerald-950/30"
                            onClick={handleScanRepos}
                            disabled={!!loading}
                        >
                            {loading === "scan" ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : "Run Repo Scan"}
                        </Button>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white text-base">
                            <Layers className="h-4 w-4 text-purple-400" />
                            Artifact Cleanup
                        </CardTitle>
                        <CardDescription className="text-xs text-slate-400">
                            Search and remove orphaned brain artifacts older than 30 days.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button variant="outline" className="w-full border-slate-800 text-purple-400 hover:bg-purple-950/30">Run Cleanup</Button>
                    </CardContent>
                </Card>
            </div>

            {/* Status and Results Area */}
            {(status || error || results) && (
                <Card className="border-slate-800 bg-slate-900/30">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
                            {error ? <AlertCircle className="h-4 w-4 text-red-400" /> : <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
                            Operation Status
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {status && <p className="text-xs text-slate-400">{status}</p>}
                        {error && <p className="text-xs text-red-400 bg-red-400/10 p-2 rounded border border-red-400/20">{error}</p>}

                        {results && (
                            <div className="max-h-[300px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                                {results.map((res, idx) => (
                                    <div key={idx} className="text-[10px] font-mono p-2 rounded bg-slate-950 border border-slate-800 text-slate-300 flex justify-between">
                                        <span className="truncate mr-4">{res.path}</span>
                                        {res.size !== undefined && <span className="text-slate-500 flex-shrink-0">{(res.size / 1024 / 1024).toFixed(2)} MB</span>}
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">Active Operational Parameters</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">Indexing Scope</span>
                        <span className="text-slate-100 font-mono">D:\Dev\repos; C:\Users\sandr\.gemini\antigravity</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">Ignore Patterns</span>
                        <span className="text-slate-100 font-mono">node_modules; .git; dist; build</span>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

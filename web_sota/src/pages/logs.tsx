import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Terminal, Trash2, Download, Search } from "lucide-react";

export function Logs() {
    const logs = [
        { time: "15:24:08", type: "INFO", message: "FastSearch Bridge initialized on port 10845" },
        { time: "15:24:10", type: "INFO", message: "Scanning NTFS volume C:\ (Serial: 4A2C-9E1F)..." },
        { time: "15:24:15", type: "DEBUG", message: "USN Journal read complete: 14,203 entries processed" },
        { time: "15:24:20", type: "INFO", message: "Index update successful (1.2s)" },
        { time: "15:25:01", type: "WARN", message: "Disk pressure detected on D:\ (8% free)" },
    ];

    return (
        <div className="space-y-6 h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex items-center justify-between shrink-0">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">System Logs</h2>
                    <p className="text-slate-400">Real-time indexing and bridge activity</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="border-slate-800 text-slate-400">
                        <Download className="h-4 w-4 mr-2" />
                        Export
                    </Button>
                    <Button variant="outline" size="sm" className="border-slate-800 text-red-400">
                        <Trash2 className="h-4 w-4 mr-2" />
                        Clear
                    </Button>
                </div>
            </div>

            <Card className="border-slate-800 bg-slate-950/50 flex-1 overflow-hidden flex flex-col">
                <CardHeader className="bg-slate-900/30 border-b border-slate-800 py-3 shrink-0">
                    <div className="flex items-center gap-2 text-slate-400 font-mono text-xs">
                        <Terminal className="h-4 w-4" />
                        fastsearch_bridge.log
                    </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-y-auto p-0 font-mono text-sm leading-6">
                    <div className="p-4 space-y-1">
                        {logs.map((log, i) => (
                            <div key={i} className="flex gap-4 border-b border-slate-900 pb-1 last:border-0 hover:bg-slate-900/20 px-2 rounded">
                                <span className="text-slate-500 shrink-0 select-none w-20">{log.time}</span>
                                <span className={`shrink-0 w-12 ${log.type === 'WARN' ? 'text-amber-400' :
                                        log.type === 'INFO' ? 'text-blue-400' : 'text-slate-500'
                                    }`}>[{log.type}]</span>
                                <span className="text-slate-300 break-all">{log.message}</span>
                            </div>
                        ))}
                        <div className="text-slate-600 animate-pulse mt-4">_</div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

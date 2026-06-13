import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Search, HardDrive, Zap, Clock, Activity } from "lucide-react";

export function Dashboard() {
    const stats = [
        { label: "Indexed Records", value: "1,240,432", icon: Database, color: "text-blue-400" },
        { label: "Volumes Scanned", value: "3", icon: HardDrive, color: "text-purple-400" },
        { label: "Avg Search Time", value: "34ms", icon: Zap, color: "text-amber-400" },
        { label: "Last Rebuild", value: "2h ago", icon: Clock, color: "text-slate-400" },
    ];

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">System Insight</h2>
                <p className="text-slate-400">FastSearch engine operational status and metrics</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {stats.map((stat) => (
                    <Card key={stat.label} className="border-slate-800 bg-slate-950/50">
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                                {stat.label}
                            </CardTitle>
                            <stat.icon className={`h-4 w-4 ${stat.color}`} />
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">{stat.value}</div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
                <Card className="col-span-4 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Recent Activity</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex items-center gap-4 p-3 rounded-lg bg-slate-900/50 border border-slate-800">
                                    <div className="w-8 h-8 rounded bg-blue-500/10 flex items-center justify-center">
                                        <Search className="w-4 h-4 text-blue-400" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-slate-200">System-wide search executed</p>
                                        <p className="text-xs text-slate-500">Query: "*.log" | Results: 4,021 | 12ms</p>
                                    </div>
                                    <div className="text-xs text-slate-600">5m ago</div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card className="col-span-3 border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Indexer Health</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs text-slate-400">
                                <span>Memory Usage</span>
                                <span>124 MB</span>
                            </div>
                            <div className="h-2 rounded-full bg-slate-900">
                                <div className="h-full w-[15%] rounded-full bg-blue-500" />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs text-slate-400">
                                <span>Disk I/O Latency</span>
                                <span>Active</span>
                            </div>
                            <div className="h-2 rounded-full bg-slate-900">
                                <div className="h-full w-[5%] rounded-full bg-emerald-500" />
                            </div>
                        </div>
                        <div className="pt-4 border-t border-slate-800">
                            <div className="flex items-start gap-3">
                                <Activity className="w-4 h-4 text-emerald-400 mt-1" />
                                <div>
                                    <p className="text-xs font-semibold text-emerald-400">Service Synchronized</p>
                                    <p className="text-[10px] text-slate-500 leading-tight">FastSearch Windows service is reporting 100% USN consistency across all attached volumes.</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

// Helper icons
import { Database } from "lucide-react";

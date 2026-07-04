import { useState, useEffect } from "react";
import { API_BASE } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Database, BrainCircuit, RefreshCw, Loader2, Save } from "lucide-react";
import { mcpClient } from "@/common/mcp-client";
import { getLlmConfig, setLlmConfig, type LlmConfig } from "@/common/llm-config";

interface Provider {
    id: string;
    label: string;
    base_url: string;
    models: string[];
    needs_key: boolean;
}

export function Settings() {
    const [config, setConfig] = useState<LlmConfig>(getLlmConfig);
    const [models, setModels] = useState<string[]>([]);
    const [modelsError, setModelsError] = useState<string | null>(null);
    const [loadingModels, setLoadingModels] = useState(false);
    const [saved, setSaved] = useState(false);
    const [providers, setProviders] = useState<Provider[]>([]);
    const [providerMap, setProviderMap] = useState<Record<string, Provider>>({});

    // Fetch providers from backend
    useEffect(() => {
        fetch(API_BASE + "/api/llm/providers")
            .then((r) => r.json())
            .then((d) => {
                const list: Provider[] = d.providers || [];
                setProviders(list);
                const map: Record<string, Provider> = {};
                list.forEach((p) => { map[p.id] = p; });
                setProviderMap(map);
                // Auto-populate models for current provider
                const cur = getLlmConfig().provider;
                if (map[cur]?.models?.length) {
                    setModels(map[cur].models);
                    if (!getLlmConfig().model) {
                        setConfig((c) => ({ ...c, model: map[cur].models[0] }));
                    }
                }
            })
            .catch(() => {});
    }, []);

    // Refresh models from provider list or backend
    const loadModels = async () => {
        setLoadingModels(true);
        setModelsError(null);
        try {
            // Prefer cached models from provider map
            const cached = providerMap[config.provider]?.models;
            if (cached && cached.length > 0) {
                setModels(cached);
                if (!config.model) setConfig((c) => ({ ...c, model: cached[0] }));
                setLoadingModels(false);
                return;
            }
            const res = await mcpClient.getLlmModels(config.provider, config.baseUrl || undefined);
            setModels(res.models || []);
            if (res.error) setModelsError(res.error);
            if (!config.model && res.models?.length) setConfig((c) => ({ ...c, model: res.models[0] }));
        } catch (e) {
            setModelsError(e instanceof Error ? e.message : "Failed to fetch models");
            setModels([]);
        } finally {
            setLoadingModels(false);
        }
    };

    useEffect(() => {
        loadModels();
    }, [config.provider, config.baseUrl]);

    const handleSave = () => {
        setLlmConfig(config);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">FastSearch Configuration</h2>
                <p className="text-slate-400">Manage indexing behavior and local LLM integration</p>
            </div>

            <div className="grid gap-6">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <BrainCircuit className="h-5 w-5 text-purple-400" />
                            Local LLM Stack
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                            Provider, model discovery, and base URL for Chat and Advanced Result Analysis
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label className="text-slate-300 font-semibold text-xs uppercase tracking-wider">Provider</Label>
                                <Select
                                    value={config.provider}
                                    onValueChange={(v: string) => {
                                        setConfig((c) => ({ ...c, provider: v }));
                                        const p = providerMap[v];
                                        if (p) {
                                            setConfig((c) => ({ ...c, baseUrl: p.base_url }));
                                            if (p.models.length) {
                                                setModels(p.models);
                                                setConfig((c) => ({ ...c, model: p.models[0] }));
                                            }
                                        }
                                    }}
                                >
                                    <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-100">
                                        <SelectValue placeholder="Select provider" />
                                    </SelectTrigger>
                                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                                        {providers.length
                                            ? providers.map((p) => (
                                                <SelectItem key={p.id} value={p.id}>{p.label}</SelectItem>
                                            ))
                                            : <SelectItem value="ollama">Ollama</SelectItem>
                                        }
                                        {!providers.length && <SelectItem value="lmstudio">LM Studio</SelectItem>}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="grid gap-2">
                                <Label className="text-slate-300 font-semibold text-xs uppercase tracking-wider">Base URL (optional)</Label>
                                <Input
                                    className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                                    placeholder={config.provider === "ollama" ? "http://localhost:11434" : "http://localhost:1234"}
                                    value={config.baseUrl}
                                    onChange={(e) => setConfig((c) => ({ ...c, baseUrl: e.target.value }))}
                                />
                            </div>
                        </div>
                        <div className="grid gap-2">
                            <Label className="text-slate-300 font-semibold text-xs uppercase tracking-wider flex items-center justify-between">
                                Model
                                {loadingModels && <Loader2 className="h-3 w-3 animate-spin text-blue-400" />}
                            </Label>
                            <div className="flex gap-2">
                                <Select
                                    value={config.model || (models[0] ?? "")}
                                    onValueChange={(v) => setConfig((c) => ({ ...c, model: v }))}
                                >
                                    <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-100 flex-1">
                                        <SelectValue placeholder={loadingModels ? "Discovering..." : "Select model"} />
                                    </SelectTrigger>
                                    <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                                        {models.length
                                            ? models.map((m) => (
                                                <SelectItem key={m} value={m}>{m}</SelectItem>
                                            ))
                                            : <SelectItem value="none" disabled>No models found</SelectItem>}
                                    </SelectContent>
                                </Select>
                                <Button
                                    size="icon"
                                    variant="outline"
                                    className="border-slate-800 shrink-0"
                                    onClick={loadModels}
                                    disabled={loadingModels}
                                >
                                    <RefreshCw className={`h-4 w-4 ${loadingModels ? "animate-spin" : ""}`} />
                                </Button>
                            </div>
                            {modelsError && <p className="text-xs text-amber-400">{modelsError}</p>}
                        </div>
                        <div className="grid gap-2">
                            <Label className="text-slate-300 font-semibold text-xs uppercase tracking-wider">System prompt (Chat)</Label>
                            <Textarea
                                className="bg-slate-900 border-slate-800 text-slate-100 min-h-[80px]"
                                value={config.systemPrompt}
                                onChange={(e) => setConfig((c) => ({ ...c, systemPrompt: e.target.value }))}
                                placeholder="Assistant behavior for chat..."
                            />
                        </div>
                        <div className="flex justify-end">
                            <Button className="bg-blue-600 hover:bg-blue-700" onClick={handleSave}>
                                {saved ? "Saved" : <><Save className="mr-2 h-4 w-4" /> Save LLM config</>}
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-white">
                            <Database className="h-5 w-5 text-blue-400" />
                            Indexer Settings
                        </CardTitle>
                        <CardDescription className="text-slate-400">File system monitoring and performance</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-slate-300 font-semibold text-xs uppercase tracking-wider">FastSearch Utility Path</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                                defaultValue="C:\Program Files\FastSearch\fs.exe"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="grid gap-2">
                                <Label className="text-slate-300 font-semibold text-xs uppercase tracking-wider">Max Result Count</Label>
                                <Input type="number" className="bg-slate-900 border-slate-800 text-slate-100" defaultValue="1000" />
                            </div>
                            <div className="grid gap-2 pt-8">
                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        id="monitor-usn"
                                        className="rounded bg-slate-900 border-slate-800"
                                        defaultChecked
                                        title="Monitor NTFS USN Journal"
                                    />
                                    <Label htmlFor="monitor-usn" className="text-sm text-slate-300 cursor-pointer">Monitor NTFS USN Journal</Label>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

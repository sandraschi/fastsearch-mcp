import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Bot, Send, User, Loader2, Settings as SettingsIcon } from "lucide-react";
import { mcpClient } from "@/common/mcp-client";
import { getLlmConfig, setLlmConfig } from "@/common/llm-config";
import { Link } from "react-router-dom";

type Message = { role: "user" | "assistant"; content: string };

export function Chat() {
    const config = getLlmConfig();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [systemPrompt, setSystemPrompt] = useState(config.systemPrompt);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const send = async () => {
        const text = input.trim();
        if (!text || loading) return;
        setInput("");
        setError(null);
        const userMsg: Message = { role: "user", content: text };
        setMessages((m) => [...m, userMsg]);
        setLoading(true);
        try {
            const cfg = getLlmConfig();
            const history = [...messages, userMsg].map((msg) => ({ role: msg.role, content: msg.content }));
            const apiMessages = [
                { role: "system" as const, content: systemPrompt },
                ...history,
            ];
            const res = await mcpClient.llmChat({
                messages: apiMessages,
                model: cfg.model || undefined,
                provider: cfg.provider,
                base_url: cfg.baseUrl || undefined,
            });
            setMessages((m) => [...m, { role: "assistant", content: res.content }]);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Request failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)]">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Search AI Assistant</h2>
                    <p className="text-slate-400">Local LLM chat with prompt refinement for file search guidance</p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-400">Model: {getLlmConfig().model || "Not set"}</span>
                    <Button variant="outline" size="sm" className="border-slate-800" asChild>
                        <Link to="/settings">Settings</Link>
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
                <Card className="lg:col-span-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
                    <div className="px-4 py-2 border-b border-slate-800 flex items-center gap-2">
                        <SettingsIcon className="h-4 w-4 text-slate-400" />
                        <span className="text-sm font-medium text-slate-300">System prompt (refinement)</span>
                    </div>
                    <CardContent className="p-4 flex-1 overflow-hidden flex flex-col">
                        <Textarea
                            className="flex-1 min-h-[120px] bg-slate-900 border-slate-800 text-slate-200 text-sm resize-none"
                            placeholder="Define how the assistant should behave..."
                            value={systemPrompt}
                            onChange={(e) => setSystemPrompt(e.target.value)}
                            onBlur={() => setLlmConfig({ systemPrompt })}
                        />
                        <p className="text-xs text-slate-500 mt-2">Used for every message. Persisted on blur.</p>
                    </CardContent>
                </Card>

                <Card className="lg:col-span-2 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
                    <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                        {messages.length === 0 && (
                            <div className="text-center text-slate-500 py-8">
                                <Bot className="w-12 h-12 mx-auto mb-3 text-slate-600" />
                                <p>Ask for search suggestions, patterns, or follow-up actions.</p>
                                <p className="text-xs mt-2">Example: &quot;Find all .pdf files larger than 50MB in D:\Documents&quot;</p>
                            </div>
                        )}
                        {messages.map((msg, i) => (
                            <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                                <div
                                    className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center ${
                                        msg.role === "assistant" ? "bg-blue-600/20 border border-blue-500/30" : "bg-slate-800 border border-slate-700"
                                    }`}
                                >
                                    {msg.role === "assistant" ? <Bot className="w-5 h-5 text-blue-400" /> : <User className="w-5 h-5 text-slate-300" />}
                                </div>
                                <div
                                    className={`flex-1 space-y-1 ${
                                        msg.role === "user" ? "text-right" : ""
                                    }`}
                                >
                                    <p className="text-xs font-medium text-slate-400">{msg.role === "user" ? "You" : "Search AI"}</p>
                                    <p className="text-sm text-slate-300 whitespace-pre-wrap bg-slate-900/50 p-3 rounded-md border border-slate-800">
                                        {msg.content}
                                    </p>
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0">
                                    <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
                                </div>
                                <div className="text-sm text-slate-500">Thinking...</div>
                            </div>
                        )}
                        <div ref={scrollRef} />
                    </CardContent>
                    <div className="p-4 border-t border-slate-800 bg-slate-900/20">
                        {error && <p className="text-xs text-amber-400 mb-2">{error}</p>}
                        <div className="flex gap-2">
                            <Textarea
                                className="min-h-[44px] max-h-32 bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500 resize-none"
                                placeholder="Ask Search AI..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" && !e.shiftKey) {
                                        e.preventDefault();
                                        send();
                                    }
                                }}
                                rows={2}
                            />
                            <Button className="bg-blue-600 hover:bg-blue-700 shrink-0" onClick={send} disabled={loading}>
                                <Send className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
}

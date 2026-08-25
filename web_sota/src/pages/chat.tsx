import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, Download, Eraser, Loader2, Send, User } from "lucide-react";
import { mcpClient } from "@/common/mcp-client";
import { getLlmConfig, setLlmConfig } from "@/common/llm-config";

const HISTORY_KEY = "fastsearch-chat-history";
const PERSONALITY_KEY = "fastsearch-chat-personality";

const PERSONALITIES: Record<string, string> = {
  "Search Expert": "You are a search expert specializing in high-performance file indexing and search. Provide guidance on search patterns, MFT queries, and file system navigation.",
  "Data Analyst": "You are a data analyst focused on file system analytics. Help with file patterns, storage analysis, and data organization strategies.",
  "Quick Summarizer": "Keep responses to 2-3 sentences. Focus on key facts.",
  "Custom": "Custom prompt \u2014 editable below.",
};

const EXAMPLE_PROMPTS = [
  { group: "Search", prompts: ["Find all .pdf files larger than 50MB", "Search for files modified today", "Find duplicate files by name"] },
  { group: "Index", prompts: ["Show indexing status", "Reindex the Documents folder", "Check search database health"] },
  { group: "Files", prompts: ["Find recently created files", "Search by file type pattern", "List files by size"] },
];

type Message = { role: "user" | "assistant"; content: string };

export function Chat() {
  const [personality, setPersonality] = useState(() => localStorage.getItem(PERSONALITY_KEY) || "Search Expert");
  const [messages, setMessages] = useState<Message[]>(() => {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch { return []; }
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => { localStorage.setItem(HISTORY_KEY, JSON.stringify(messages)); }, [messages]);
  useEffect(() => { localStorage.setItem(PERSONALITY_KEY, personality); }, [personality]);
  useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError(null);
    const userMsg: Message = { role: "user", content: text };
    const updatedMessages: Message[] = [...messages, userMsg];
    setMessages(updatedMessages);
    setLoading(true);
    try {
      const cfg = getLlmConfig();
      const history = updatedMessages.map((msg) => ({ role: msg.role, content: msg.content }));
      const apiMessages = [
        { role: "system" as const, content: PERSONALITIES[personality] },
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
  }, [input, messages, loading, personality]);

  const exportChat = () => {
    const text = messages.map((m) => `[${m.role.toUpperCase()}] ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "fastsearch-chat.txt"; a.click();
    URL.revokeObjectURL(url);
  };

  const clearChat = () => { setMessages([]); };

  return (
    <div data-testid="chat-page" className="flex flex-col h-[calc(100vh-8rem)]">
      <div data-testid="chat-controls" className="flex items-center justify-between mb-6 flex-wrap gap-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Search AI Assistant</h2>
          <p className="text-slate-400">Local LLM chat with prompt refinement for file search guidance</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 bg-slate-800 px-2 py-1 rounded">skill:fastsearch-expert</span>
          <span className="text-sm text-slate-400">Model: {getLlmConfig().model || "Not set"}</span>
          <select data-testid="personality-select" className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200" value={personality} onChange={(e) => setPersonality(e.target.value)}>
            {Object.keys(PERSONALITIES).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <button data-testid="chat-export" onClick={exportChat} disabled={messages.length === 0} className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30" title="Export"><Download className="h-4 w-4" /></button>
          <button data-testid="chat-clear" onClick={clearChat} disabled={messages.length === 0} className="p-1.5 rounded hover:bg-slate-800 text-slate-400 disabled:opacity-30" title="Clear"><Eraser className="h-4 w-4" /></button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
        <div className="lg:col-span-1 border border-slate-800 bg-slate-950/50 rounded-lg flex flex-col overflow-hidden">
          <div className="px-4 py-2 border-b border-slate-800 flex items-center gap-2">
            <span className="text-sm font-medium text-slate-300">System prompt (refinement)</span>
          </div>
          <div className="p-4 flex-1 overflow-hidden flex flex-col">
            <textarea className="flex-1 min-h-[120px] bg-slate-900 border border-slate-800 text-slate-200 text-sm rounded p-2 resize-none"
              placeholder="Define how the assistant should behave..." value={PERSONALITIES[personality]}
              onChange={() => { /* Personality-managed */ }}
              onBlur={() => setLlmConfig({ systemPrompt: PERSONALITIES[personality] })}
            />
            <p className="text-xs text-slate-500 mt-2">Managed by personality selector above.</p>
          </div>
        </div>

        <div className="lg:col-span-2 border border-slate-800 bg-slate-950/50 rounded-lg flex flex-col overflow-hidden">
          <div data-testid="chat-messages" className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-slate-500 py-8">
                <Bot className="w-12 h-12 mx-auto mb-3 text-slate-600" />
                <p>Ask for search suggestions, patterns, or follow-up actions.</p>
                <p className="text-xs mt-2">Example: &quot;Find all .pdf files larger than 50MB in D:\Documents&quot;</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
                <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center ${msg.role === "assistant" ? "bg-blue-600/20 border border-blue-500/30" : "bg-slate-800 border border-slate-700"}`}>
                  {msg.role === "assistant" ? <Bot className="w-5 h-5 text-blue-400" /> : <User className="w-5 h-5 text-slate-300" />}
                </div>
                <div className={`flex-1 space-y-1 ${msg.role === "user" ? "text-right" : ""}`}>
                  <p className="text-xs font-medium text-slate-400">{msg.role === "user" ? "You" : "Search AI"}</p>
                  <p className="text-sm text-slate-300 whitespace-pre-wrap bg-slate-900/50 p-3 rounded-md border border-slate-800">{msg.content}</p>
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
          </div>

          <div className="p-4 border-t border-slate-800 bg-slate-900/20">
            <div data-testid="example-prompts" className="flex flex-wrap gap-2 mb-3">
              {EXAMPLE_PROMPTS.map((group) => (
                <div key={group.group} className="flex flex-wrap items-center gap-1">
                  <span className="text-xs text-slate-500 mr-1">{group.group}:</span>
                  {group.prompts.map((p) => (
                    <button key={p} onClick={() => setInput(p)} className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded">{p}</button>
                  ))}
                </div>
              ))}
            </div>
            {error && <p className="text-xs text-amber-400 mb-2">{error}</p>}
            <div className="flex gap-2">
              <textarea className="min-h-[44px] max-h-32 flex-1 bg-slate-900 border border-slate-800 text-slate-100 placeholder:text-slate-500 rounded p-2 text-sm resize-none" placeholder="Ask Search AI..." value={input}
                onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} rows={2} />
              <button data-testid="chat-send" onClick={send} disabled={loading} className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md shrink-0">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

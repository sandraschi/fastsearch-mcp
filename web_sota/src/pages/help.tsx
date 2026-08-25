import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Key,
  Layers,
  Server,
  ShieldCheck,
  Terminal,
  Zap,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function Help() {
  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <HelpCircle className="h-7 w-7 text-blue-500" />
          Documentation & Help
        </h2>
        <p className="text-slate-400">
          Complete guide to FastSearch-MCP architecture, service privilege
          separation, and usage.
        </p>
      </div>

      {/* Core Architecture Card */}
      <Card className="border-blue-900/60 bg-slate-950/80 shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white text-xl">
            <ShieldCheck className="h-6 w-6 text-blue-400" />
            Privilege Separation Architecture
          </CardTitle>
          <CardDescription className="text-slate-300">
            The fundamental architecture: Elevated Windows Service (installed
            ONCE) + Unprivileged IPC Named Pipe Client.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="text-sm text-slate-300 leading-relaxed">
            FastSearch-MCP is modeled after WizFile and Voidtools Everything. It
            achieves zero-indexing speed by directly parsing the NTFS Master
            File Table (MFT) disk records. Because Windows restricts raw volume
            access (
            <code className="text-amber-300 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
              \\.\C:
            </code>
            ) to kernel and administrator handles, FastSearch strictly separates
            the elevated kernel domain from standard user tools.
          </p>

          {/* Visual Architecture Diagram */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 font-mono text-xs leading-relaxed">
            <div className="flex items-center gap-2 text-amber-400 font-bold mb-2">
              <Key className="h-4 w-4" />
              1. Elevated Service Domain (Installed ONCE as Administrator)
            </div>
            <div className="text-slate-300 pl-4 border-l-2 border-amber-500/40 space-y-1">
              <div>• FastSearchMCP Windows Service (LocalSystem / Admin)</div>
              <div>
                • Opens raw NTFS volume handles (
                <code className="text-amber-200">\\.\C:</code>,{" "}
                <code className="text-amber-200">\\.\D:</code>)
              </div>
              <div>
                • Hosts IPC Named Pipe (
                <code className="text-amber-200">\\.\pipe\FastSearchMCP</code>)
              </div>
            </div>

            <div className="my-3 flex items-center justify-center gap-2 text-blue-400 font-sans font-semibold text-xs py-1.5 bg-blue-950/40 rounded border border-blue-800/50">
              ▲ Local RPC / Named Pipe IPC Connection (Fast, Security ACL
              Protected) ▼
            </div>

            <div className="flex items-center gap-2 text-emerald-400 font-bold mb-2">
              <Layers className="h-4 w-4" />
              2. Unprivileged User Domain (Standard User Space)
            </div>
            <div className="text-slate-300 pl-4 border-l-2 border-emerald-500/40 space-y-1">
              <div>• Python MCP Server / REST API Bridge / Web UI</div>
              <div>• ZERO elevation required at runtime (no UAC prompts)</div>
              <div>
                • Connects to named pipe via Win32 client & reads live results
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-2">
              <div className="font-semibold text-white flex items-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Why Elevated Service?
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Direct MFT volume reads bypass the standard slow Windows
                filesystem directory crawler, returning millions of file records
                in milliseconds. Opening raw physical volume structures requires
                Windows kernel/admin privileges.
              </p>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-2">
              <div className="font-semibold text-white flex items-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Why Unprivileged Client?
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Applications like Claude Desktop, Python MCP, and this web
                interface run as normal unprivileged user processes. You never
                need to run Claude or your browser as Administrator.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Setup & Commands Card */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Terminal className="h-5 w-5 text-amber-400" />
            Elevated Windows Service Commands
          </CardTitle>
          <CardDescription className="text-slate-400">
            Run these commands ONCE in an elevated (Administrator) terminal to
            manage the background service.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs">
          <div className="space-y-3">
            <div className="rounded-lg border border-emerald-900/60 bg-emerald-950/20 p-4 space-y-2">
              <div className="font-semibold text-emerald-300 flex items-center gap-2 text-sm">
                <Zap className="h-4 w-4 text-emerald-400" />
                Automated 1-Click First-Time Onboarding
              </div>
              <code className="block bg-slate-950 p-2.5 rounded border border-slate-800 font-mono text-emerald-300 font-bold">
                just onboard
              </code>
              <p className="text-slate-300 leading-relaxed">
                Executes the complete onboarding sequence: prompts for
                Administrator elevation <b>ONCE</b> via UAC to register & start
                the <code className="text-slate-200">FastSearchMCP</code>{" "}
                Windows Service, then automatically runs Win32 Named Pipe IPC
                diagnostics (
                <code className="text-slate-200">\\.\pipe\FastSearchMCP</code>)
                to verify latency and connectivity.
              </p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 space-y-2">
              <div className="font-semibold text-slate-200 flex items-center gap-2">
                <Server className="h-4 w-4 text-blue-400" />
                Install & Start Service (Manual Admin PowerShell)
              </div>
              <code className="block bg-slate-950 p-2 rounded border border-slate-800 font-mono text-amber-200">
                just install-service
              </code>
              <p className="text-slate-400">
                Builds and registers{" "}
                <code className="text-slate-200">FastSearchMCP</code> in Windows
                Service Control Manager (SCM).
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 space-y-1">
                <div className="font-medium text-slate-200">Start Service</div>
                <code className="block bg-slate-950 p-2 rounded border border-slate-800 font-mono text-amber-200">
                  sc start FastSearchMCP
                </code>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 space-y-1">
                <div className="font-medium text-slate-200">Check Status</div>
                <code className="block bg-slate-950 p-2 rounded border border-slate-800 font-mono text-amber-200">
                  sc query FastSearchMCP
                </code>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Troubleshooting & Gaps Card */}
      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            Troubleshooting Service Disconnection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-xs text-slate-300">
          <p>
            If the web app or MCP tools report <b>"Service Disconnected"</b>:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-slate-400">
            <li>
              <b>Service Not Installed</b>: Run{" "}
              <code className="text-amber-200 bg-slate-900 px-1 rounded">
                just install-service
              </code>{" "}
              in Administrator PowerShell.
            </li>
            <li>
              <b>Service Stopped</b>: Run{" "}
              <code className="text-amber-200 bg-slate-900 px-1 rounded">
                sc start FastSearchMCP
              </code>{" "}
              in Administrator PowerShell.
            </li>
            <li>
              <b>Pipe Availability</b>: Check status on the{" "}
              <a href="/service" className="text-blue-400 underline">
                NTFS Search Service
              </a>{" "}
              page or{" "}
              <a href="/logs" className="text-blue-400 underline">
                System Logs
              </a>{" "}
              page.
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default Help;

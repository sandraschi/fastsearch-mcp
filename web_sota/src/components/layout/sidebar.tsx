import {
  Activity,
  Bot,
  ChevronLeft,
  ChevronRight,
  FileSearch,
  FlaskConical,
  HelpCircle,
  LayoutDashboard,
  PieChart,
  Search,
  Server,
  Settings,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/common/utils";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  const navItems = [
    { href: "/", label: "Overview", icon: LayoutDashboard },
    { href: "/search", label: "Dedicated Search", icon: Search },
    { href: "/treemap", label: "Cushion Treemap", icon: PieChart },
    { href: "/service", label: "NTFS Search Service", icon: Server },
    { href: "/tests", label: "Tests", icon: FlaskConical },
    { href: "/tools", label: "Search Tools", icon: Search },
    { href: "/actions", label: "Quick Actions", icon: Activity },
    { href: "/chat", label: "AI Assistant", icon: Bot },
    { href: "/logs", label: "System Logs", icon: FileSearch },
    { href: "/settings", label: "Settings", icon: Settings },
    { href: "/help", label: "Help & Docs", icon: HelpCircle },
  ];

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-slate-950/50 backdrop-blur-xl transition-all duration-300 ease-in-out",
        collapsed ? "w-16" : "w-64",
      )}
    >
      {/* Top Header with Standard Show/Hide Sidebar Toggle */}
      <div className="flex h-16 items-center justify-between border-b border-slate-800 px-3.5">
        <div className="flex items-center gap-2 font-semibold text-slate-100 min-w-0">
          <Activity className="h-6 w-6 text-blue-500 shrink-0" />
          {!collapsed && (
            <span className="animate-in fade-in duration-300 font-bold truncate">
              FastSearch-MCP
            </span>
          )}
        </div>

        <button
          id="sidebar-toggle"
          onClick={onToggle}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="flex items-center justify-center rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors border border-slate-800/80 bg-slate-900/60 shrink-0"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4 text-blue-400" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-2 overflow-y-auto">
        {navItems
          .filter((item) => !["/control", "/visualizer"].includes(item.href))
          .map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.href}
                to={item.href}
                title={collapsed ? item.label : undefined}
                aria-label={item.label}
                className={cn(
                  "group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white",
                  isActive ? "bg-slate-800 text-white" : "text-slate-400",
                  collapsed ? "justify-center" : "justify-start",
                )}
              >
                <item.icon
                  className={cn(
                    "h-5 w-5",
                    !collapsed && "mr-3",
                    isActive && "text-blue-400",
                  )}
                />
                {!collapsed && <span>{item.label}</span>}

                {/* Tooltip for collapsed mode */}
                {collapsed && (
                  <div className="absolute left-full ml-2 hidden rounded bg-slate-800 px-2 py-1 text-xs text-white group-hover:block z-50 whitespace-nowrap">
                    {item.label}
                  </div>
                )}
              </Link>
            );
          })}
      </nav>
    </aside>
  );
}

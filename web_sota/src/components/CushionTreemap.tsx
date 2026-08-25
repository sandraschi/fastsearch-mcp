import {
  ArrowLeft,
  Camera,
  Maximize2,
  Minimize2,
  RotateCcw,
} from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";

export type FileItem = {
  name?: string;
  path?: string;
  file_path?: string;
  full_path?: string;
  size?: number;
  size_bytes?: number;
  length?: number;
  type?: string;
};

type TreeNode = {
  name: string;
  path: string;
  size: number;
  isDir: boolean;
  children: Map<string, TreeNode>;
  childrenList?: TreeNode[];
  ext?: string;
};

type TreemapRect = {
  node: TreeNode;
  x: number;
  y: number;
  w: number;
  h: number;
  depth: number;
};

const CATEGORY_COLORS: Record<string, string> = {
  // Code
  py: "#3b82f6",
  ts: "#3b82f6",
  tsx: "#2563eb",
  js: "#3b82f6",
  jsx: "#2563eb",
  cpp: "#1d4ed8",
  c: "#1d4ed8",
  h: "#1e40af",
  cs: "#3b82f6",
  java: "#3b82f6",
  rs: "#f97316",
  go: "#06b6d4",
  json: "#0284c7",
  html: "#e11d48",
  css: "#7c3aed",
  // Images
  png: "#10b981",
  jpg: "#10b981",
  jpeg: "#10b981",
  webp: "#059669",
  svg: "#34d399",
  gif: "#10b981",
  // Media
  mp4: "#8b5cf6",
  webm: "#8b5cf6",
  mkv: "#7c3aed",
  mp3: "#a855f7",
  wav: "#a855f7",
  flac: "#9333ea",
  // Archives & Executables
  zip: "#f59e0b",
  "7z": "#d97706",
  rar: "#d97706",
  tar: "#b45309",
  gz: "#b45309",
  exe: "#ef4444",
  dll: "#dc2626",
  msi: "#b91c1c",
  // Docs
  pdf: "#f43f5e",
  docx: "#38bdf8",
  txt: "#94a3b8",
  md: "#64748b",
  csv: "#10b981",
  xlsx: "#059669",
  log: "#64748b",
};

function getFileColor(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  return CATEGORY_COLORS[ext] || "#475569";
}

function getItemPath(item: FileItem): string {
  return item.path || item.file_path || item.full_path || item.name || "";
}

function getItemSize(item: FileItem): number {
  return item.size ?? item.size_bytes ?? item.length ?? 0;
}

function formatBytes(bytes?: number): string {
  if (bytes == null || Number.isNaN(bytes)) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

// Build hierarchical directory tree from flat FileItem list
function buildDirectoryTree(items: FileItem[]): TreeNode {
  const root: TreeNode = {
    name: "Root",
    path: "",
    size: 0,
    isDir: true,
    children: new Map(),
  };

  for (const item of items) {
    const fullPath = getItemPath(item);
    const size = getItemSize(item);
    if (!fullPath) continue;

    const parts = fullPath.split(/[/\\]/).filter(Boolean);
    let curr = root;
    curr.size += size;

    let pathAcc = "";
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isLast = i === parts.length - 1;
      pathAcc += (pathAcc ? "\\" : "") + part;

      let child = curr.children.get(part);
      if (!child) {
        child = {
          name: part,
          path: pathAcc,
          size: 0,
          isDir: !isLast,
          children: new Map(),
          ext: isLast ? part.split(".").pop()?.toLowerCase() : undefined,
        };
        curr.children.set(part, child);
      }

      child.size += size;
      if (isLast) {
        child.isDir = false;
      }
      curr = child;
    }
  }

  // Convert Map to sorted array
  function finalizeTree(node: TreeNode) {
    node.childrenList = Array.from(node.children.values()).sort(
      (a, b) => b.size - a.size,
    );
    for (const child of node.childrenList) {
      if (child.isDir) {
        finalizeTree(child);
      }
    }
  }

  finalizeTree(root);
  return root;
}

// Squarified Treemap algorithm (Bruls, Huizing, van Wijk)
function layoutSquarified(
  node: TreeNode,
  x: number,
  y: number,
  w: number,
  h: number,
  depth: number = 0,
  maxDepth: number = 4,
): TreemapRect[] {
  const rects: TreemapRect[] = [];
  if (
    w <= 2 ||
    h <= 2 ||
    !node.childrenList ||
    node.childrenList.length === 0
  ) {
    rects.push({ node, x, y, w, h, depth });
    return rects;
  }

  const children = node.childrenList.filter((c) => c.size > 0);
  if (children.length === 0) {
    rects.push({ node, x, y, w, h, depth });
    return rects;
  }

  const totalSize = children.reduce((sum, c) => sum + c.size, 0);
  if (totalSize <= 0) return rects;

  let containerX = x;
  let containerY = y;
  let containerW = w;
  let containerH = h;

  // Add inner padding for folder depth headers
  if (depth > 0 && node.isDir) {
    const pad = 2;
    containerX += pad;
    containerY += pad;
    containerW = Math.max(0, containerW - pad * 2);
    containerH = Math.max(0, containerH - pad * 2);
  }

  let currentY = containerY;
  const isHoriz = containerW > containerH;

  for (let i = 0; i < children.length; i++) {
    const child = children[i];
    const ratio = child.size / totalSize;

    let rx: number, ry: number, rw: number, rh: number;
    if (isHoriz) {
      rx = containerX + (currentY - containerY);
      ry = containerY;
      rw = containerW * ratio;
      rh = containerH;
    } else {
      rx = containerX;
      ry = currentY;
      rw = containerW;
      rh = containerH * ratio;
    }

    if (
      child.isDir &&
      depth < maxDepth &&
      child.childrenList &&
      child.childrenList.length > 0
    ) {
      const sub = layoutSquarified(child, rx, ry, rw, rh, depth + 1, maxDepth);
      rects.push(...sub);
    } else {
      rects.push({ node: child, x: rx, y: ry, w: rw, h: rh, depth: depth + 1 });
    }

    if (isHoriz) {
      containerX += rw;
    } else {
      currentY += rh;
    }
  }

  return rects;
}

export function CushionTreemap({
  items,
  onSelectFile,
  height = 560,
}: {
  items: FileItem[];
  onSelectFile?: (path: string) => void;
  height?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [hoveredRect, setHoveredRect] = useState<TreemapRect | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({
    x: 0,
    y: 0,
  });
  const [selectedNodePath, setSelectedNodePath] = useState<string>("");
  const [rects, setRects] = useState<TreemapRect[]>([]);

  // Build tree & layout rects
  const rootNode = useRef<TreeNode | null>(null);

  useEffect(() => {
    if (!items || items.length === 0) {
      setRects([]);
      return;
    }

    rootNode.current = buildDirectoryTree(items);
    let activeRoot = rootNode.current;

    if (selectedNodePath) {
      const findSub = (node: TreeNode): TreeNode | null => {
        if (node.path === selectedNodePath) return node;
        if (node.childrenList) {
          for (const child of node.childrenList) {
            const found = findSub(child);
            if (found) return found;
          }
        }
        return null;
      };
      const sub = findSub(rootNode.current);
      if (sub) activeRoot = sub;
    }

    const width = containerRef.current?.clientWidth || 900;
    const computedRects = layoutSquarified(
      activeRoot,
      0,
      0,
      width,
      height,
      0,
      4,
    );
    setRects(computedRects);
  }, [items, selectedNodePath, height]);

  // Render Canvas Cushion Treemap
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = containerRef.current?.clientWidth || 900;
    const dpr = window.devicePixelRatio || 1;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, width, height);

    if (rects.length === 0) {
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = "#64748b";
      ctx.font = "14px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No files to display in Treemap", width / 2, height / 2);
      return;
    }

    // Render each Cushion Rect
    for (const r of rects) {
      if (r.w < 1 || r.h < 1) continue;

      const baseColor = getFileColor(r.node.name);

      // Create 3D Cushion Lighting Gradient (WizTree / WinDirStat style)
      const centerX = r.x + r.w * 0.35;
      const centerY = r.y + r.h * 0.35;
      const radius = Math.max(r.w, r.h) * 0.9;

      const grad = ctx.createRadialGradient(
        centerX,
        centerY,
        0,
        r.x + r.w / 2,
        r.y + r.h / 2,
        radius,
      );

      // Highlight peak -> Base color -> Dark cushion bevel shadow
      grad.addColorStop(0, "rgba(255, 255, 255, 0.45)");
      grad.addColorStop(0.35, baseColor);
      grad.addColorStop(1, "#020617");

      ctx.fillStyle = grad;
      ctx.fillRect(r.x, r.y, r.w, r.h);

      // Bevel borders
      ctx.strokeStyle = "rgba(0, 0, 0, 0.6)";
      ctx.lineWidth = 1;
      ctx.strokeRect(r.x, r.y, r.w, r.h);

      // Render text label if rectangle is large enough
      if (r.w > 45 && r.h > 20) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(r.x + 2, r.y + 2, r.w - 4, r.h - 4);
        ctx.clip();

        ctx.fillStyle = "#ffffff";
        ctx.font =
          r.w > 80 && r.h > 40 ? "bold 11px sans-serif" : "10px sans-serif";
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.shadowColor = "rgba(0, 0, 0, 0.8)";
        ctx.shadowBlur = 3;

        ctx.fillText(r.node.name, r.x + 4, r.y + 4);

        if (r.h > 35 && r.w > 60) {
          ctx.fillStyle = "rgba(255, 255, 255, 0.75)";
          ctx.font = "9px monospace";
          ctx.fillText(formatBytes(r.node.size), r.x + 4, r.y + 18);
        }
        ctx.restore();
      }
    }

    // Hover Highlight Overlay
    if (hoveredRect) {
      ctx.strokeStyle = "#60a5fa";
      ctx.lineWidth = 2.5;
      ctx.strokeRect(
        hoveredRect.x,
        hoveredRect.y,
        hoveredRect.w,
        hoveredRect.h,
      );

      ctx.fillStyle = "rgba(96, 165, 250, 0.15)";
      ctx.fillRect(hoveredRect.x, hoveredRect.y, hoveredRect.w, hoveredRect.h);
    }
  }, [rects, hoveredRect, height]);

  // Handle Mouse Move & Hover
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setMousePos({ x: e.clientX, y: e.clientY });

    // Find hit rect
    const hit = rects.find(
      (r) => x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h,
    );
    setHoveredRect(hit || null);
  };

  const handleMouseLeave = () => {
    setHoveredRect(null);
  };

  const handleClick = () => {
    if (!hoveredRect) return;
    if (hoveredRect.node.isDir) {
      setSelectedNodePath(hoveredRect.node.path);
    } else if (onSelectFile && hoveredRect.node.path) {
      onSelectFile(hoveredRect.node.path);
    }
  };

  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Export Canvas Cushion Treemap as PNG Image
  const handleExportPNG = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const image = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.download = `cushion-treemap-${new Date().toISOString().slice(0, 10)}.png`;
    a.href = image;
    a.click();
  };

  const activeHeight = isFullscreen
    ? Math.max(400, window.innerHeight - 130)
    : height;

  const totalSize = rootNode.current?.size || 1;

  return (
    <div
      className={
        isFullscreen
          ? "fixed inset-0 z-[100] bg-slate-950 p-4 flex flex-col justify-between select-none animate-in fade-in duration-200"
          : "space-y-2 select-none"
      }
      ref={containerRef}
    >
      {/* Treemap Breadcrumbs & Action Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 bg-slate-900/90 border border-slate-800 rounded-lg p-2 text-xs">
        <div className="flex items-center gap-2 text-slate-300 font-mono truncate">
          <span className="text-slate-500 font-medium">Path:</span>
          {selectedNodePath ? (
            <div className="flex items-center gap-1.5 truncate">
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-1.5 text-xs text-blue-400 hover:text-white"
                onClick={() => setSelectedNodePath("")}
              >
                <RotateCcw className="h-3 w-3 mr-1" /> Root
              </Button>
              <span className="text-slate-600">\</span>
              <span className="font-semibold text-white truncate">
                {selectedNodePath}
              </span>
            </div>
          ) : (
            <span className="text-slate-400 font-semibold">
              Entire Search Set
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-slate-400 text-[11px]">
          <span className="mr-1">
            Total Volume:{" "}
            <strong className="text-white font-mono">
              {formatBytes(totalSize)}
            </strong>
          </span>
          {selectedNodePath && (
            <Button
              variant="outline"
              size="sm"
              className="h-6 px-2 text-[11px] border-slate-700 text-slate-300 hover:text-white"
              onClick={() => setSelectedNodePath("")}
            >
              <ArrowLeft className="h-3 w-3 mr-1" /> Zoom Out
            </Button>
          )}

          {/* Export PNG Image Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPNG}
            className="h-6 px-2 text-[11px] border-slate-700 bg-slate-800 text-slate-200 hover:text-white hover:bg-slate-700"
            title="Export Treemap High-Res PNG Image"
          >
            <Camera className="h-3 w-3 mr-1 text-emerald-400" /> Export Image
          </Button>

          {/* Fullscreen Toggle Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="h-6 px-2 text-[11px] border-slate-700 bg-blue-900/40 text-blue-300 hover:text-white hover:bg-blue-800"
            title={isFullscreen ? "Exit Fullscreen" : "Full Screen View"}
          >
            {isFullscreen ? (
              <>
                <Minimize2 className="h-3 w-3 mr-1" /> Exit Fullscreen
              </>
            ) : (
              <>
                <Maximize2 className="h-3 w-3 mr-1" /> Full Screen
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Canvas Viewport */}
      <div className="relative flex-1 rounded-lg border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl">
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
          className="w-full cursor-pointer block"
          style={{ height: `${activeHeight}px` }}
        />

        {/* Hover Tooltip Card */}
        {hoveredRect && (
          <div
            className="pointer-events-none fixed z-50 rounded-lg border border-slate-700 bg-slate-950/95 p-3 text-xs shadow-2xl backdrop-blur-md max-w-sm space-y-1.5 animate-in fade-in-50 duration-100"
            style={{
              left: `${Math.min(mousePos.x + 12, window.innerWidth - 320)}px`,
              top: `${Math.min(mousePos.y + 12, window.innerHeight - 150)}px`,
            }}
          >
            <div className="flex items-center gap-2 border-b border-slate-800 pb-1.5">
              <div
                className="h-3 w-3 rounded-full shrink-0"
                style={{ backgroundColor: getFileColor(hoveredRect.node.name) }}
              />
              <span className="font-bold text-white truncate">
                {hoveredRect.node.name}
              </span>
            </div>
            <div className="font-mono text-[11px] text-slate-300 break-all leading-tight">
              {hoveredRect.node.path}
            </div>
            <div className="flex items-center justify-between text-[11px] pt-1 text-slate-400 font-mono">
              <span>
                Size:{" "}
                <strong className="text-white">
                  {formatBytes(hoveredRect.node.size)}
                </strong>
              </span>
              <span>
                {((hoveredRect.node.size / totalSize) * 100).toFixed(1)}% of
                total
              </span>
            </div>
            <div className="text-[10px] text-blue-400 italic pt-0.5">
              {hoveredRect.node.isDir
                ? "Click to zoom into subfolder"
                : "Click to preview file"}
            </div>
          </div>
        )}
      </div>

      {/* Cushion Treemap Legend */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400 px-1 pt-1">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-semibold text-slate-300">Legend:</span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-blue-500" /> Code
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Images
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-purple-500" /> Media
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> Archives
            / Exe
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-slate-500" /> Docs /
            Text
          </span>
        </div>
        <span className="text-slate-500 italic">
          💡 WizTree 3D cushion algorithm • Canvas 2D engine
        </span>
      </div>
    </div>
  );
}

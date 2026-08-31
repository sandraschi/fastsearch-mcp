"""Disk usage treemap HTML generator -- WizTree-style visualization.

Generates a self-contained HTML file with an interactive D3.js squarified
treemap of directory disk usage, using the same scanning backend as
analyze_disk_usage but rendered as a visual treemap.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fastsearch_mcp.logging_config import get_logger
from fastsearch_mcp.mcp_instance import mcp
from fastsearch_mcp.tools.disk_analyzer import get_disk_usage

logger = get_logger(__name__)

_TREEMAP_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Disk Treemap</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #09090b; color: #e4e4e7; font-family: system-ui, sans-serif; padding: 16px; }
h1 { font-size: 18px; margin-bottom: 8px; color: #f4f4f5; }
#chart { width: 100%; height: calc(100vh - 120px); }
.tooltip {
  position: absolute; background: #18181b; border: 1px solid #27272a; color: #e4e4e7;
  padding: 8px 12px; border-radius: 6px; font-size: 13px; pointer-events: none; display: none;
  z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}
.stats { display: flex; gap: 16px; font-size: 13px; color: #a1a1aa; margin-bottom: 8px; }
rect { stroke: #09090b; stroke-width: 1; }
rect:hover { stroke: #f59e0b; stroke-width: 2; }
</style>
</head>
<body>
<div class="stats">
  <span>Path: <strong id="scanPath">--</strong></span>
  <span>Total: <strong id="totalSize">--</strong></span>
</div>
<div id="chart"></div>
<div class="tooltip" id="tooltip"></div>
<script>
const DATA = %DATA%;
const extColor = d3.scaleOrdinal(d3.schemeCategory10);

function isLeaf(d) { return !d.children || d.children.length === 0; }

const root = d3.hierarchy(DATA, d => d.children)
  .sum(d => d.size)
  .sort((a, b) => b.value - a.value);

const width = document.getElementById('chart').clientWidth;
const height = window.innerHeight - 140;

const treemap = d3.treemap().size([width, height]).paddingOuter(2).paddingInner(1).round(true);
treemap(root);

const svg = d3.select('#chart').append('svg').attr('width', width).attr('height', height);
const tooltip = d3.select('#tooltip');

document.getElementById('scanPath').textContent = DATA.path || '';
document.getElementById('totalSize').textContent = (DATA.size / 1e9).toFixed(2) + ' GB';

const leaf = svg.selectAll('g').data(root.leaves()).join('g')
  .attr('transform', d => `translate(${d.x0},${d.y0})`);

leaf.append('rect')
  .attr('width', d => d.x1 - d.x0)
  .attr('height', d => d.y1 - d.y0)
  .attr('fill', (d, i) => {
    const cat = d.data.path ? d.data.path.split('.').pop() : 'other';
    return extColor(cat);
  })
  .attr('opacity', d => Math.min(1, 0.4 + (d.value / root.value) * 3))
  .on('mouseover', (e, d) => {
    tooltip.style('display', 'block')
      .html(`<strong>${d.data.path || 'unknown'}</strong><br>
             Size: ${(d.value / 1e9).toFixed(2)} GB<br>
             Files: ${d.data.file_count || 0}`)
      .style('left', (e.pageX+12)+'px')
      .style('top', (e.pageY-10)+'px');
  })
  .on('mousemove', e => tooltip.style('left', (e.pageX+12)+'px').style('top', (e.pageY-10)+'px'))
  .on('mouseout', () => tooltip.style('display', 'none'));

leaf.append('text')
  .attr('font-size', d => Math.min(11, Math.max(7, (d.x1-d.x0) / 10)))
  .attr('x', 3).attr('y', 14).attr('fill', '#fff')
  .style('text-shadow', '0 1px 2px #000')
  .text(d => {
    const name = (d.data.path || '').split('\\').pop() || d.data.path || '';
    return (d.x1-d.x0 > 40) ? name : '';
  })
  .append('tspan').attr('x', 3).attr('dy', 13).attr('fill', '#a1a1aa')
  .text(d => (d.x1-d.x0 > 60) ? (d.value / 1e9).toFixed(2) + ' GB' : '');
</script>
</body>
</html>"""


@mcp.tool(name="disk_treemap")
def generate_disk_treemap(
    path: str,
    max_depth: int = 3,
    max_entries: int = 5000,
) -> dict:
    """Generate a WizTree-style interactive treemap of disk usage for a directory.

    Creates a self-contained HTML file with an embedded D3.js squarified treemap,
    colored by file extension with hover tooltips showing file count and size.

    ## Return Format
    {"success": bool, "file_path": str, "total_bytes": int, "path": str, "error": str | None}

    ## Examples
        disk_treemap(path="C:\\Users", max_depth=3)
        disk_treemap(path="D:\\Projects", max_depth=2, max_entries=2000)
    """
    try:
        usage = get_disk_usage(path, max_depth=max_depth, max_entries=max_entries)
        tree_dict = usage.to_dict()

        html = _TREEMAP_HTML.replace(
            "%DATA%",
            json.dumps(tree_dict, indent=2, default=str),
        )

        out_path = Path(tempfile.gettempdir()) / "fastsearch-mcp" / "disk_treemap.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")

        return {
            "success": True,
            "file_path": str(out_path),
            "total_bytes": usage.size,
            "path": path,
            "error": None,
        }
    except Exception as e:
        logger.exception("disk_treemap failed")
        return {"success": False, "file_path": "", "total_bytes": 0, "path": path, "error": str(e)}

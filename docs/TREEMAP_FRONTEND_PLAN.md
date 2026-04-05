# FastSearch MCP - WizTree-like Treemap Frontend Plan

**Status**: Feasibility Study → Implementation Ready  
**Created**: 2025-11-17  
**Target**: Build interactive treemap visualizer leveraging MFT backend

## Vision

Build a **WizTree/WizFile-like treemap visualizer** leveraging FastSearch's MFT backend for massive scalability. Display directory structures as interactive heat maps showing file counts, sizes, and type distributions. Make it fast enough to handle million-file drives.

## Key Insight

WizTree and WizFile are fast because they read the NTFS Master File Table (MFT) directly—the same approach FastSearch uses in its C++ backend. **We already have the MFT reader built.** This plan leverages that existing capability.

## Architecture

### Backend Layer (Python MCP Bridge)

**New MCP Tool**: `fastsearch.get_directory_tree`

**Input Parameters**:
- `root_path`: Starting directory (e.g., `"C:\\"`)
- `max_depth`: Recursion depth (1-6)
- `sort_by`: `"size"`, `"count"`, `"time"`, or `"name"`

**Output**: Hierarchical JSON structure
```json
{
  "name": "C:\\",
  "path": "C:\\",
  "type": "directory",
  "size_bytes": 549755813888,
  "file_count": 127540,
  "file_count_recursive": 892150,
  "avg_age_days": 180,
  "newest_date": "2025-11-17T10:00:00Z",
  "oldest_date": "2020-01-01T00:00:00Z",
  "extension_breakdown": {
    ".exe": 245,
    ".dll": 1230,
    ".sys": 89,
    ".txt": 5400
  },
  "color_value": 0.65,
  "children": [
    {
      "name": "Windows",
      "path": "C:\\Windows",
      "type": "directory",
      "size_bytes": 87654321,
      "file_count": 45000,
      ...
    },
    ...
  ]
}
```

**Reuse Existing**: The C++ `fastsearch_service.cpp` already iterates MFT tables efficiently. Pipeline to Python bridge, format as tree hierarchy.

### Frontend Layer (React + Plotly/D3)

**Tech Stack**:
- React 18+ (Vite build)
- Plotly.js treemap component (or D3.js for more control)
- TailwindCSS for styling
- HTTP bridge server (Flask/FastAPI) on `localhost:3001`

**Core Components**:

1. **TreemapView** - Main visualization
   - Click rectangles to drill down (zoom)
   - Hover for detailed stats
   - Color encoding: age (heatmap), file type, or frequency
   - Breadcrumb navigation at top

2. **StatsPanel** - Right sidebar
   - Total storage used / file count
   - Top 10 extensions by count and size
   - Largest directories
   - Age distribution chart

3. **ControlsBar** - Top control panel
   - Drive selector (C:, D:, E:, etc.)
   - Sort mode (size, count, age, name)
   - Color mode toggle (age, type, frequency)
   - Max depth slider (1-6 levels visible)
   - Refresh button

### HTTP Bridge Layer (Flask/FastAPI)

**Port**: `localhost:3001`

**Endpoints**:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/treemap` | Request directory tree structure |
| GET | `/api/drives` | List available Windows drives |
| GET | `/api/health` | Check service connectivity |
| GET | `/api/status` | Get indexed file statistics |

**Request/Response Example**:

```bash
POST /api/treemap
Content-Type: application/json

{
  "path": "C:\\",
  "max_depth": 3,
  "sort_by": "size"
}

# Response: 200 OK
{
  "success": true,
  "data": { /* hierarchical tree */ },
  "elapsed_ms": 342
}
```

**Bridge Translation Logic**:
```
HTTP POST → Validate params → Translate to MCP tool format 
    ↓
Call NamedPipeClient with search request 
    ↓
C++ FastSearch service iterates MFT 
    ↓
Returns JSON results → Format for frontend → Send HTTP response
```

## Implementation Phases

### Phase 1: Backend Tool (2-3 hours)

Add `get_directory_tree` to `src/fastsearch_mcp/tool_wrappers.py`:

- [ ] Define tool schema and parameters
- [ ] Call underlying C++ service for directory listing
- [ ] Aggregate file statistics (sizes, counts, ages, extensions)
- [ ] Build hierarchical JSON tree structure
- [ ] **Test**: Scan `D:\` with 100K+ files → response in <500ms

**Success Criteria**:
- Tool appears in MCP inventory
- Returns valid hierarchical JSON
- Handles max_depth correctly
- Performance: <1 second for single drive root

### Phase 2: HTTP Bridge Server (2-3 hours)

Create new `src/fastsearch_mcp/http_bridge.py`:

- [ ] Flask app listening on port 3001
- [ ] Implement `/api/treemap`, `/api/drives`, `/api/health` endpoints
- [ ] Translate HTTP params to MCP tool calls
- [ ] Add NamedPipeClient integration
- [ ] CORS headers for frontend origin
- [ ] Comprehensive error handling
- [ ] Request/response logging
- [ ] Graceful shutdown on service disconnection

**Success Criteria**:
- HTTP server starts without errors
- All endpoints return proper JSON
- Timeout handling (max 30s per request)
- Clear error messages on pipe disconnection

### Phase 3: Frontend React App (3-4 hours)

Rewrite `frontend/src/` with React + Vite:

- [ ] Set up React project structure (Vite)
- [ ] Install dependencies (React, Plotly.js, TailwindCSS)
- [ ] Implement TreemapView component
- [ ] Implement StatsPanel component
- [ ] Implement ControlsBar component
- [ ] API client module (fetch wrapper)
- [ ] State management (useState hooks or Context)
- [ ] Drill-down / breadcrumb navigation
- [ ] **Test**: Load C:\ treemap, interact with drill-down

**Success Criteria**:
- Frontend loads without errors
- Treemap renders with data
- Drilling down updates visualization
- All controls respond properly
- Stats panel updates with selection

### Phase 4: Polish & Performance (1-2 hours)

- [ ] Add request caching (avoid re-fetching same paths)
- [ ] Loading spinners and skeletons
- [ ] Error boundary components
- [ ] Dark/light mode toggle
- [ ] Export functionality (CSV/JSON of tree data)
- [ ] Keyboard shortcuts (Esc to zoom out, arrow keys to navigate)
- [ ] Responsive layout (mobile friendly)

**Success Criteria**:
- Smooth UX with all feedback states
- <200ms perceived latency
- Professional appearance

## Performance Targets

| Scenario | Target |
|----------|--------|
| First load (C: root) | <1 second |
| Drill down (1 level deeper) | <500ms |
| Max files handled | 1M+ on single drive |
| Responsive depth | 4-5 levels |
| Caching hit | <50ms |

## Competitive Advantages vs WizTree

| Aspect | FastSearch Treemap | WizTree |
|--------|-------------------|---------|
| Real-time search | ✅ Live query results | ❌ Static snapshot |
| IDE integration | ✅ MCP tools in Claude/Cursor | ❌ Standalone only |
| Extensibility | ✅ Add metrics via MCP | ❌ Binary closed-source |
| Source | ✅ Open-source | ❌ Proprietary |
| MFT-based | ✅ Direct MFT reading | ✅ (likely) |

## File Structure

```
fastsearch-mcp/
├── src/fastsearch_mcp/
│   ├── tool_wrappers.py          ← UPDATE: add get_directory_tree
│   ├── http_bridge.py            ← NEW: Flask server
│   └── ... (existing)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TreemapView.jsx   ← NEW
│   │   │   ├── StatsPanel.jsx    ← NEW
│   │   │   ├── ControlsBar.jsx   ← NEW
│   │   │   └── index.js          ← NEW: exports
│   │   ├── api/
│   │   │   └── client.js         ← NEW: fetch wrapper
│   │   ├── App.jsx               ← REWRITE
│   │   ├── index.jsx             ← NEW: React entry point
│   │   └── App.css               ← REWRITE
│   ├── public/                   ← Keep existing
│   ├── vite.config.js            ← NEW: build config
│   ├── package.json              ← UPDATE: React, Plotly deps
│   ├── tailwind.config.js        ← NEW or UPDATE
│   └── index.html                ← UPDATE: React mount point
│
├── docs/
│   ├── TREEMAP_FRONTEND_PLAN.md  ← THIS FILE
│   └── ... (existing)
│
└── README.md                      ← UPDATE: mention treemap feature
```

## Data Flow Example

```
User selects "C:\" drive and clicks "Visualize"
           ↓
React sends: POST /api/treemap {path: "C:\\", max_depth: 3, sort_by: "size"}
           ↓
Flask bridge validates, translates to MCP call
           ↓
MCP NamedPipeClient sends to C++ FastSearch service
           ↓
C++ service iterates MFT table, collects stats for each directory
           ↓
Returns: JSON hierarchy {C:\: {Windows, Users, Program Files, ...}}
           ↓
Flask formats response, sends HTTP 200 with JSON
           ↓
React receives → Plotly renders treemap visualization
           ↓
User sees interactive rectangles, clicks "Users" folder
           ↓
React sends: POST /api/treemap {path: "C:\\Users", max_depth: 3, ...}
           ↓
(Process repeats at deeper level)
           ↓
Treemap zooms in, breadcrumb shows "C:\ > Users"
```

## Security Considerations

- **Drive access**: Only user-accessible drives (respect NTFS permissions)
- **Path traversal**: Validate input paths (no `..` traversal attacks)
- **Rate limiting**: Limit requests to prevent DOS (e.g., 1 request per 100ms per path)
- **CORS**: Allow only localhost:3000 (dev frontend) or production domain

## Testing Strategy

### Unit Tests
- `test_get_directory_tree()` - Tool returns valid JSON
- `test_tree_aggregation()` - Statistics calculated correctly
- `test_tree_depth_limiting()` - max_depth respected

### Integration Tests
- Flask bridge connects to pipe client
- Full HTTP request/response cycle
- Pipe disconnection handling

### E2E Tests
- Frontend loads C:\ → sees treemap
- Click drill down → data updates
- All controls respond

### Performance Tests
- Benchmark 100K+ file scan
- Response time <500ms threshold
- Memory usage monitoring

## Rollout Plan

1. **Create docs/TREEMAP_FRONTEND_PLAN.md** (this file)
2. **Phase 1**: Backend tool development → merge to main
3. **Phase 2**: HTTP bridge → merge to main
4. **Phase 3**: Frontend React rewrite → create PR for review
5. **Phase 4**: Polish & final testing → merge
6. **Release**: Tag as v0.5.0 with treemap feature

## Dependencies to Add

**Python**:
```
flask>=2.3.0
flask-cors>=4.0.0
```

**Node.js**:
```
react@^18.0.0
react-dom@^18.0.0
plotly.js@^2.26.0
tailwindcss@^3.0.0
```

(Or use D3.js instead of Plotly for more control)

## References

- [Plotly Treemap Docs](https://plotly.com/javascript/treemaps/)
- [D3 Hierarchy & Treemaps](https://d3js.org/d3-hierarchy/treemap)
- [WizTree Features](https://wiztree.en.softonic.com/) (for inspiration)
- [NTFS MFT Structure](https://en.wikipedia.org/wiki/Master_file_table)

## Questions & Decisions

**Q: Plotly vs D3 for visualization?**  
A: Start with Plotly (simpler), migrate to D3 if we need more customization

**Q: Cache aggressively or always fresh?**  
A: Cache with 60-second TTL, manual refresh button available

**Q: Multi-drive view or single drive at a time?**  
A: Single drive MVP, then add multi-drive comparison

**Q: Export format?**  
A: JSON and CSV for spreadsheet analysis

---

**Next Action**: Brief Cursor on Phase 1 backend implementation

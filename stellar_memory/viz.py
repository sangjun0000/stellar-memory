"""Memory Visualization - generates self-contained HTML visualization.

Opens in the user's browser with 4 views:
1. Solar System - zone rings with memory dots
2. Memory List - searchable, filterable table
3. Graph - node-link diagram of memory relationships
4. Stats - zone usage, score distribution, source breakdown
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryVisualizer:
    """Generates self-contained HTML visualization of memory state."""

    def __init__(self, memory):
        self._memory = memory

    def generate_html(self) -> str:
        """Generate complete HTML visualization page."""
        data = self._collect_data()
        return _VIZ_TEMPLATE.replace("/*__DATA__*/null", json.dumps(data))

    def save_and_open(self, output_path: str | None = None,
                      open_browser: bool = True) -> str:
        """Save HTML to file and optionally open in browser."""
        html = self.generate_html()
        if output_path is None:
            import tempfile
            fd, output_path = tempfile.mkstemp(
                suffix=".html", prefix="stellar-viz-")
            os.close(fd)
        Path(output_path).write_text(html, encoding="utf-8")
        if open_browser:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(output_path)}")
        return output_path

    def _collect_data(self) -> dict:
        """Collect all data needed for visualization."""
        stats = self._memory.stats()
        zones_data = []
        all_items = []

        for zone_id in range(5):
            count = stats.zone_counts.get(zone_id, 0)
            cap = stats.zone_capacities.get(zone_id)
            zone_items = []
            if count > 0:
                results = self._memory.recall("", limit=min(count, 200))
                zone_items = [self._item_to_dict(i) for i in results
                              if i.zone == zone_id]
            zones_data.append({
                "id": zone_id,
                "name": self._memory.config.zones[zone_id].name
                        if zone_id < len(self._memory.config.zones) else f"zone-{zone_id}",
                "count": count,
                "capacity": cap,
                "items": zone_items,
            })
            all_items.extend(zone_items)

        # Graph edges
        edges = []
        if hasattr(self._memory, '_graph') and self._memory._graph:
            try:
                for item in all_items:
                    full_id = self._find_full_id(item["id"])
                    if full_id:
                        item_edges = self._memory._graph.get_edges(full_id)
                        for edge in item_edges:
                            edges.append({
                                "source": edge.source_id[:8],
                                "target": edge.target_id[:8],
                                "type": edge.edge_type,
                            })
            except Exception:
                pass

        return {
            "stats": {
                "total": stats.total_memories,
                "zones": {str(k): v for k, v in stats.zone_counts.items()},
            },
            "zones": zones_data,
            "edges": edges,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _item_to_dict(self, item) -> dict:
        return {
            "id": item.id[:8],
            "content": item.content[:200],
            "zone": item.zone,
            "importance": round(item.arbitrary_importance, 2),
            "score": round(item.total_score, 3),
            "recall_count": item.recall_count,
            "created_at": time.strftime(
                "%Y-%m-%d", time.localtime(item.created_at)),
            "category": (item.metadata or {}).get("category", ""),
            "type": (item.metadata or {}).get("type", "general"),
            "source": (item.metadata or {}).get("source", "manual"),
        }

    def _find_full_id(self, short_id: str) -> str | None:
        """Try to find full UUID from short 8-char id."""
        item = self._memory.get(short_id)
        if item:
            return item.id
        return None


# ── HTML Template ──────────────────────────────────────────────

_VIZ_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stellar Memory Visualization</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#c9d1d9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow-x:hidden}
.header{background:#161b22;border-bottom:1px solid #30363d;padding:16px 24px;display:flex;align-items:center;gap:16px}
.header h1{font-size:20px;color:#f0f6fc}
.header .total{color:#8b949e;font-size:14px}
.tabs{display:flex;gap:0;background:#161b22;border-bottom:1px solid #30363d;padding:0 24px}
.tab{padding:12px 20px;cursor:pointer;color:#8b949e;border-bottom:2px solid transparent;font-size:14px;transition:all .2s}
.tab:hover{color:#c9d1d9}
.tab.active{color:#58a6ff;border-bottom-color:#58a6ff}
.content{padding:24px;max-width:1400px;margin:0 auto}
.panel{display:none}
.panel.active{display:block}

/* Solar System */
#solar-svg{width:100%;max-width:700px;margin:0 auto;display:block}
.zone-ring{fill:none;stroke:#30363d;stroke-width:1}
.zone-label{fill:#8b949e;font-size:11px}
.memory-dot{cursor:pointer;transition:r .2s}
.memory-dot:hover{r:6}
.detail-panel{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px;margin-top:16px;min-height:100px}
.detail-panel h3{color:#58a6ff;margin-bottom:8px;font-size:14px}
.detail-panel .content-text{white-space:pre-wrap;font-size:13px;line-height:1.5;max-height:200px;overflow-y:auto}
.detail-panel .meta{color:#8b949e;font-size:12px;margin-top:8px}

/* Memory List */
.search-bar{display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.search-bar input,.search-bar select{background:#0d1117;border:1px solid #30363d;color:#c9d1d9;padding:8px 12px;border-radius:6px;font-size:14px}
.search-bar input{flex:1;min-width:200px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#161b22;color:#8b949e;text-align:left;padding:8px 12px;border-bottom:1px solid #30363d;cursor:pointer;user-select:none}
th:hover{color:#c9d1d9}
td{padding:8px 12px;border-bottom:1px solid #21262d;max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
tr:hover td{background:#161b22}
.zone-badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.zone-0{background:#1f6feb33;color:#58a6ff}
.zone-1{background:#23882033;color:#3fb950}
.zone-2{background:#9e6a0333;color:#d29922}
.zone-3{background:#da363333;color:#f85149}
.zone-4{background:#8b949e33;color:#8b949e}

/* Graph */
#graph-svg{width:100%;height:500px;background:#0d1117;border:1px solid #30363d;border-radius:8px}
.graph-node{cursor:pointer}
.graph-edge{stroke:#30363d;stroke-width:1}
.graph-label{fill:#c9d1d9;font-size:10px;pointer-events:none}

/* Stats */
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.stat-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}
.stat-card h3{color:#8b949e;font-size:12px;text-transform:uppercase;margin-bottom:12px}
.bar-chart{display:flex;flex-direction:column;gap:8px}
.bar-row{display:flex;align-items:center;gap:8px}
.bar-label{width:80px;font-size:12px;color:#8b949e}
.bar-track{flex:1;height:20px;background:#21262d;border-radius:4px;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;transition:width .3s}
.bar-value{width:60px;font-size:12px;text-align:right;color:#c9d1d9}
.pie-container{display:flex;justify-content:center;align-items:center;gap:24px}
.legend{font-size:12px}
.legend-item{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.legend-dot{width:10px;height:10px;border-radius:50%}
</style>
</head>
<body>

<div class="header">
  <h1>Stellar Memory</h1>
  <span class="total" id="header-total"></span>
  <span class="total" id="header-time"></span>
</div>

<div class="tabs">
  <div class="tab active" onclick="showTab('solar')">Solar System</div>
  <div class="tab" onclick="showTab('list')">Memory List</div>
  <div class="tab" onclick="showTab('graph')">Graph</div>
  <div class="tab" onclick="showTab('stats')">Stats</div>
</div>

<div class="content">
  <!-- Solar System -->
  <div class="panel active" id="panel-solar">
    <svg id="solar-svg" viewBox="0 0 700 700"></svg>
    <div class="detail-panel" id="solar-detail">
      <h3>Click a memory dot to view details</h3>
    </div>
  </div>

  <!-- Memory List -->
  <div class="panel" id="panel-list">
    <div class="search-bar">
      <input type="text" id="search-input" placeholder="Search memories..." oninput="filterList()">
      <select id="filter-zone" onchange="filterList()">
        <option value="">All Zones</option>
        <option value="0">Zone 0 (Core)</option>
        <option value="1">Zone 1 (Inner)</option>
        <option value="2">Zone 2 (Outer)</option>
        <option value="3">Zone 3 (Belt)</option>
        <option value="4">Zone 4 (Cloud)</option>
      </select>
      <select id="filter-source" onchange="filterList()">
        <option value="">All Sources</option>
        <option value="manual">Manual</option>
        <option value="auto-import">Auto Import</option>
        <option value="ai-config-sync">AI Config</option>
      </select>
    </div>
    <table>
      <thead><tr>
        <th onclick="sortList('content')">Content</th>
        <th onclick="sortList('zone')">Zone</th>
        <th onclick="sortList('importance')">Importance</th>
        <th onclick="sortList('score')">Score</th>
        <th onclick="sortList('recall_count')">Recalls</th>
        <th onclick="sortList('created_at')">Created</th>
        <th onclick="sortList('source')">Source</th>
      </tr></thead>
      <tbody id="list-body"></tbody>
    </table>
  </div>

  <!-- Graph -->
  <div class="panel" id="panel-graph">
    <svg id="graph-svg"></svg>
  </div>

  <!-- Stats -->
  <div class="panel" id="panel-stats">
    <div class="stat-grid" id="stats-grid"></div>
  </div>
</div>

<script>
var DATA = /*__DATA__*/null;
var allItems = [];
var sortKey = 'zone';
var sortAsc = true;

function init() {
  if (!DATA) return;
  document.getElementById('header-total').textContent = DATA.stats.total + ' memories';
  document.getElementById('header-time').textContent = 'Generated: ' + DATA.generated_at;
  DATA.zones.forEach(function(z) { allItems = allItems.concat(z.items); });
  renderSolar();
  renderList();
  renderStats();
  renderGraph();
}

function showTab(name) {
  document.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
  document.querySelectorAll('.panel').forEach(function(p) { p.classList.remove('active'); });
  document.getElementById('panel-' + name).classList.add('active');
  event.target.classList.add('active');
}

// ── Solar System ──
function renderSolar() {
  var svg = document.getElementById('solar-svg');
  var cx = 350, cy = 350;
  var radii = [60, 120, 190, 260, 320];
  var colors = ['#58a6ff','#3fb950','#d29922','#f85149','#8b949e'];
  var html = '';
  radii.forEach(function(r, i) {
    html += '<circle cx="'+cx+'" cy="'+cy+'" r="'+r+'" class="zone-ring"/>';
    html += '<text x="'+(cx+r+4)+'" y="'+(cy-4)+'" class="zone-label">Zone '+i+'</text>';
  });
  DATA.zones.forEach(function(zone) {
    var r = radii[zone.id] || 320;
    var items = zone.items;
    items.forEach(function(item, j) {
      var angle = (j / Math.max(items.length, 1)) * Math.PI * 2 - Math.PI/2;
      var jitter = (Math.sin(j*7.3)*0.15 + 1) * r;
      var x = cx + Math.cos(angle) * jitter;
      var y = cy + Math.sin(angle) * jitter;
      var sz = 3 + item.importance * 4;
      html += '<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="'+sz+'" ' +
              'fill="'+colors[zone.id]+'" class="memory-dot" ' +
              'onclick="showDetail(\''+item.id+'\')" opacity="0.8"/>';
    });
  });
  // Center star
  html += '<circle cx="'+cx+'" cy="'+cy+'" r="12" fill="#f0f6fc" opacity="0.9"/>';
  html += '<text x="'+cx+'" y="'+(cy+4)+'" text-anchor="middle" fill="#0d1117" font-size="10" font-weight="bold">SM</text>';
  svg.innerHTML = html;
}

function showDetail(id) {
  var item = allItems.find(function(i) { return i.id === id; });
  if (!item) return;
  var panel = document.getElementById('solar-detail');
  panel.innerHTML = '<h3><span class="zone-badge zone-'+item.zone+'">Zone '+item.zone+'</span> '+item.id+'</h3>' +
    '<div class="content-text">'+escHtml(item.content)+'</div>' +
    '<div class="meta">Importance: '+item.importance+' | Score: '+item.score+' | Recalls: '+item.recall_count+' | Source: '+item.source+' | '+item.created_at+'</div>';
}

// ── Memory List ──
function renderList() { filterList(); }

function filterList() {
  var query = document.getElementById('search-input').value.toLowerCase();
  var zone = document.getElementById('filter-zone').value;
  var source = document.getElementById('filter-source').value;
  var filtered = allItems.filter(function(i) {
    if (query && i.content.toLowerCase().indexOf(query) === -1) return false;
    if (zone !== '' && String(i.zone) !== zone) return false;
    if (source && i.source !== source) return false;
    return true;
  });
  filtered.sort(function(a, b) {
    var va = a[sortKey], vb = b[sortKey];
    if (typeof va === 'number') return sortAsc ? va - vb : vb - va;
    return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
  });
  var html = '';
  filtered.forEach(function(i) {
    html += '<tr onclick="showDetail(\''+i.id+'\')">' +
      '<td title="'+escAttr(i.content)+'">'+escHtml(i.content.substring(0,80))+'</td>' +
      '<td><span class="zone-badge zone-'+i.zone+'">'+i.zone+'</span></td>' +
      '<td>'+i.importance+'</td><td>'+i.score+'</td><td>'+i.recall_count+'</td>' +
      '<td>'+i.created_at+'</td><td>'+i.source+'</td></tr>';
  });
  document.getElementById('list-body').innerHTML = html;
}

function sortList(key) {
  if (sortKey === key) sortAsc = !sortAsc;
  else { sortKey = key; sortAsc = true; }
  filterList();
}

// ── Graph ──
function renderGraph() {
  var svg = document.getElementById('graph-svg');
  if (!DATA.edges || DATA.edges.length === 0) {
    svg.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#8b949e" font-size="14">No graph edges to display</text>';
    return;
  }
  var w = svg.clientWidth || 800, h = 500;
  svg.setAttribute('viewBox', '0 0 '+w+' '+h);
  var nodeMap = {};
  var nodes = [];
  allItems.forEach(function(item) {
    nodeMap[item.id] = { id: item.id, zone: item.zone, x: Math.random()*w, y: Math.random()*h, vx:0, vy:0 };
    nodes.push(nodeMap[item.id]);
  });
  var edges = DATA.edges.filter(function(e) { return nodeMap[e.source] && nodeMap[e.target]; });
  // Simple force simulation (50 iterations)
  for (var iter = 0; iter < 50; iter++) {
    nodes.forEach(function(a) {
      nodes.forEach(function(b) {
        if (a === b) return;
        var dx = a.x - b.x, dy = a.y - b.y;
        var d = Math.sqrt(dx*dx + dy*dy) || 1;
        var f = 500 / (d * d);
        a.vx += dx/d * f; a.vy += dy/d * f;
      });
    });
    edges.forEach(function(e) {
      var a = nodeMap[e.source], b = nodeMap[e.target];
      var dx = b.x - a.x, dy = b.y - a.y;
      var d = Math.sqrt(dx*dx + dy*dy) || 1;
      var f = (d - 80) * 0.05;
      a.vx += dx/d*f; a.vy += dy/d*f;
      b.vx -= dx/d*f; b.vy -= dy/d*f;
    });
    nodes.forEach(function(n) {
      n.x += n.vx * 0.1; n.y += n.vy * 0.1;
      n.vx *= 0.9; n.vy *= 0.9;
      n.x = Math.max(20, Math.min(w-20, n.x));
      n.y = Math.max(20, Math.min(h-20, n.y));
    });
  }
  var colors = ['#58a6ff','#3fb950','#d29922','#f85149','#8b949e'];
  var html = '';
  edges.forEach(function(e) {
    var a = nodeMap[e.source], b = nodeMap[e.target];
    html += '<line x1="'+a.x.toFixed(1)+'" y1="'+a.y.toFixed(1)+'" x2="'+b.x.toFixed(1)+'" y2="'+b.y.toFixed(1)+'" class="graph-edge"/>';
  });
  nodes.forEach(function(n) {
    html += '<circle cx="'+n.x.toFixed(1)+'" cy="'+n.y.toFixed(1)+'" r="6" fill="'+colors[n.zone]+'" class="graph-node" onclick="showDetail(\''+n.id+'\')"/>';
    html += '<text x="'+(n.x+8).toFixed(1)+'" y="'+(n.y+3).toFixed(1)+'" class="graph-label">'+n.id+'</text>';
  });
  svg.innerHTML = html;
}

// ── Stats ──
function renderStats() {
  var grid = document.getElementById('stats-grid');
  var colors = ['#58a6ff','#3fb950','#d29922','#f85149','#8b949e'];
  // Zone usage
  var zoneHtml = '<div class="stat-card"><h3>Zone Usage</h3><div class="bar-chart">';
  DATA.zones.forEach(function(z) {
    var pct = z.capacity ? Math.min(100, z.count / z.capacity * 100) : (z.count > 0 ? 30 : 0);
    var label = z.capacity ? z.count+'/'+z.capacity : z.count+'';
    zoneHtml += '<div class="bar-row"><span class="bar-label">Zone '+z.id+' ('+z.name+')</span>' +
      '<div class="bar-track"><div class="bar-fill" style="width:'+pct+'%;background:'+colors[z.id]+'"></div></div>' +
      '<span class="bar-value">'+label+'</span></div>';
  });
  zoneHtml += '</div></div>';

  // Source breakdown
  var srcCounts = {};
  allItems.forEach(function(i) { srcCounts[i.source] = (srcCounts[i.source]||0)+1; });
  var srcHtml = '<div class="stat-card"><h3>Import Sources</h3><div class="bar-chart">';
  var srcColors = {'manual':'#58a6ff','auto-import':'#3fb950','ai-config-sync':'#d29922','user':'#a371f7','auto-detect':'#f0883e'};
  Object.keys(srcCounts).forEach(function(src) {
    var pct = allItems.length > 0 ? srcCounts[src]/allItems.length*100 : 0;
    srcHtml += '<div class="bar-row"><span class="bar-label">'+src+'</span>' +
      '<div class="bar-track"><div class="bar-fill" style="width:'+pct+'%;background:'+(srcColors[src]||'#8b949e')+'"></div></div>' +
      '<span class="bar-value">'+srcCounts[src]+'</span></div>';
  });
  srcHtml += '</div></div>';

  // Type breakdown
  var typeCounts = {};
  allItems.forEach(function(i) { typeCounts[i.type] = (typeCounts[i.type]||0)+1; });
  var typeHtml = '<div class="stat-card"><h3>Memory Types</h3><div class="bar-chart">';
  Object.keys(typeCounts).forEach(function(t) {
    var pct = allItems.length > 0 ? typeCounts[t]/allItems.length*100 : 0;
    typeHtml += '<div class="bar-row"><span class="bar-label">'+t+'</span>' +
      '<div class="bar-track"><div class="bar-fill" style="width:'+pct+'%;background:#a371f7"></div></div>' +
      '<span class="bar-value">'+typeCounts[t]+'</span></div>';
  });
  typeHtml += '</div></div>';

  // Summary card
  var summaryHtml = '<div class="stat-card"><h3>Summary</h3>' +
    '<p style="font-size:36px;font-weight:bold;color:#f0f6fc;margin:8px 0">'+DATA.stats.total+'</p>' +
    '<p style="color:#8b949e">Total Memories</p>' +
    '<p style="margin-top:12px;color:#8b949e">Edges: '+DATA.edges.length+'</p>' +
    '<p style="color:#8b949e">Generated: '+DATA.generated_at+'</p></div>';

  grid.innerHTML = summaryHtml + zoneHtml + srcHtml + typeHtml;
}

function escHtml(s) { var d=document.createElement('div');d.textContent=s;return d.innerHTML; }
function escAttr(s) { return s.replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }

init();
</script>
</body>
</html>"""

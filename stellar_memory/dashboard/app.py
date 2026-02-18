"""FastAPI dashboard application for Stellar Memory."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

_stellar_ref: Any = None
_event_queue: asyncio.Queue | None = None


def create_app(stellar_memory=None):
    """Create and return a FastAPI app for the memory dashboard."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, JSONResponse
        from starlette.responses import StreamingResponse
    except ImportError:
        raise ImportError(
            "fastapi is required for the dashboard. "
            "Install with: pip install stellar-memory[dashboard]"
        )

    global _stellar_ref
    _stellar_ref = stellar_memory

    app = FastAPI(title="Stellar Memory Dashboard", version="0.7.0")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return _index_html()

    @app.get("/api/stats")
    async def stats():
        if _stellar_ref is None:
            return {"error": "No StellarMemory instance connected"}
        s = _stellar_ref.stats()
        return {
            "total": s.total_memories,
            "zones": {
                str(k): v for k, v in s.zone_counts.items()
            },
            "capacities": {
                str(k): v for k, v in s.zone_capacities.items()
            },
        }

    @app.get("/api/memories")
    async def memories(zone: int | None = None, limit: int = 50):
        if _stellar_ref is None:
            return []
        items = []
        for z in _stellar_ref._zones.values():
            if zone is not None and z.config.zone_id != zone:
                continue
            for item in z.get_all():
                items.append({
                    "id": item.id,
                    "content": item.content[:200],
                    "zone": item.zone,
                    "score": round(item.total_score, 4),
                    "recall_count": item.recall_count,
                    "importance": item.arbitrary_importance,
                })
                if len(items) >= limit:
                    break
        return items

    @app.get("/api/health")
    async def health():
        if _stellar_ref is None:
            return {"status": "no_instance"}
        h = _stellar_ref.health()
        return {
            "healthy": h.healthy,
            "total": h.total_memories,
            "warnings": h.warnings,
        }

    @app.get("/api/graph")
    async def graph():
        if _stellar_ref is None or not hasattr(_stellar_ref, '_graph'):
            return {"nodes": [], "edges": []}
        g = _stellar_ref._graph
        if g is None:
            return {"nodes": [], "edges": []}
        edges = []
        for e in g.get_all_edges():
            edges.append({
                "source": e.source_id,
                "target": e.target_id,
                "type": e.edge_type,
                "weight": e.weight,
            })
        return {"edges": edges}

    @app.get("/api/events")
    async def events():
        """Server-Sent Events endpoint for real-time updates."""
        import json as _json

        async def event_stream():
            q: asyncio.Queue = asyncio.Queue()
            # Register listener on event bus
            if _stellar_ref and hasattr(_stellar_ref, '_event_bus'):
                bus = _stellar_ref._event_bus

                def _push(event_name, *args):
                    data = {"event": event_name, "ts": time.time()}
                    if args:
                        try:
                            data["detail"] = str(args[0])[:200]
                        except Exception:
                            pass
                    try:
                        q.put_nowait(data)
                    except asyncio.QueueFull:
                        pass

                for evt in ("on_store", "on_recall", "on_forget",
                            "on_reorbit", "on_decay"):
                    bus.on(evt, lambda *a, en=evt: _push(en, *a))

            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {_json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {_json.dumps({'event': 'heartbeat', 'ts': time.time()})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


def start_dashboard(stellar_memory=None, host: str = "127.0.0.1",
                    port: int = 8080) -> None:
    """Start the dashboard server in a daemon thread."""
    app = create_app(stellar_memory)
    try:
        import uvicorn
    except ImportError:
        raise ImportError(
            "uvicorn is required for the dashboard. "
            "Install with: pip install stellar-memory[dashboard]"
        )

    def _run():
        uvicorn.run(app, host=host, port=port, log_level="warning")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    logger.info("Dashboard started at http://%s:%d", host, port)


def _index_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Stellar Memory Dashboard</title>
<style>
body{font-family:system-ui;margin:0;padding:20px;background:#0d1117;color:#c9d1d9}
h1{color:#58a6ff}
.zone{display:inline-block;padding:8px 16px;margin:4px;border-radius:8px;background:#161b22;border:1px solid #30363d}
.zone .count{font-size:1.5em;font-weight:bold;color:#58a6ff}
.zone .name{font-size:0.85em;color:#8b949e}
#memories{margin-top:20px}
.mem{padding:8px;margin:4px 0;background:#161b22;border-radius:4px;border-left:3px solid #58a6ff}
.mem .score{color:#3fb950;font-size:0.85em}
#solar{margin:20px auto;display:block}
#events{margin-top:10px;max-height:120px;overflow-y:auto;font-size:0.8em;color:#8b949e}
.evt{padding:2px 0;border-bottom:1px solid #21262d}
</style>
</head>
<body>
<h1>Stellar Memory Dashboard</h1>
<svg id="solar" width="500" height="500" viewBox="0 0 500 500"></svg>
<div id="zones"></div>
<h2>Live Events</h2>
<div id="events"></div>
<h2>Memories</h2>
<div id="memories"></div>
<script>
const ZONE_NAMES=['Core','Inner','Outer','Belt','Cloud'];
const ZONE_COLORS=['#f0883e','#58a6ff','#3fb950','#8b949e','#6e7681'];

function drawSolar(stats){
  const svg=document.getElementById('solar');
  const cx=250,cy=250;
  let html='<circle cx="'+cx+'" cy="'+cy+'" r="20" fill="#f0883e" opacity="0.9"/>';
  html+='<text x="'+cx+'" y="'+(cy+4)+'" text-anchor="middle" fill="#0d1117" font-size="10">Core</text>';
  const radii=[60,110,160,210,250];
  for(let i=0;i<5;i++){
    const r=radii[i];
    html+='<circle cx="'+cx+'" cy="'+cy+'" r="'+r+'" fill="none" stroke="'+ZONE_COLORS[i]+'" stroke-width="1" opacity="0.3" stroke-dasharray="4,4"/>';
    const cnt=(stats.zones||{})[String(i)]||0;
    if(cnt>0){
      const dots=Math.min(cnt,20);
      for(let d=0;d<dots;d++){
        const angle=(2*Math.PI/dots)*d - Math.PI/2;
        const px=cx+r*Math.cos(angle);
        const py=cy+r*Math.sin(angle);
        const sz=Math.max(3,6-i);
        html+='<circle cx="'+px.toFixed(1)+'" cy="'+py.toFixed(1)+'" r="'+sz+'" fill="'+ZONE_COLORS[i]+'" opacity="0.7"><title>'+ZONE_NAMES[i]+' ('+cnt+')</title></circle>';
      }
    }
    html+='<text x="'+(cx+r+5)+'" y="'+(cy-5)+'" fill="'+ZONE_COLORS[i]+'" font-size="9">'+ZONE_NAMES[i]+' ('+((stats.zones||{})[String(i)]||0)+')</text>';
  }
  svg.innerHTML=html;
}

async function load(){
  const s=await(await fetch('/api/stats')).json();
  drawSolar(s);
  const zd=document.getElementById('zones');
  zd.innerHTML='';
  for(const[z,c]of Object.entries(s.zones||{})){
    const cap=s.capacities[z];
    zd.innerHTML+='<div class="zone"><div class="count">'+c+'</div><div class="name">'+
      (ZONE_NAMES[z]||'Zone '+z)+(cap?' / '+cap:'')+'</div></div>';
  }
  const ms=await(await fetch('/api/memories?limit=30')).json();
  const md=document.getElementById('memories');
  md.innerHTML='';
  for(const m of ms){
    md.innerHTML+='<div class="mem"><b>'+m.content+'</b><br><span class="score">zone='+
      m.zone+' score='+m.score+' recalls='+m.recall_count+'</span></div>';
  }
}

// SSE event stream
try{
  const es=new EventSource('/api/events');
  es.onmessage=function(e){
    const d=JSON.parse(e.data);
    if(d.event==='heartbeat')return;
    const el=document.getElementById('events');
    const div=document.createElement('div');
    div.className='evt';
    div.textContent=new Date(d.ts*1000).toLocaleTimeString()+' '+d.event+(d.detail?' - '+d.detail:'');
    el.prepend(div);
    while(el.children.length>50)el.removeChild(el.lastChild);
    load();
  };
}catch(e){}

load();setInterval(load,5000);
</script>
</body>
</html>"""

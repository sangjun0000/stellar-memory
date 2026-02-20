"""Standalone REST API server for Stellar Memory."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time

logger = logging.getLogger(__name__)


def create_api_app(config=None, namespace: str | None = None):
    """Create FastAPI application for REST API server mode."""
    try:
        from fastapi import FastAPI, HTTPException, Depends, Request
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel, Field
        from starlette.responses import Response
    except ImportError:
        raise ImportError(
            "fastapi is required. Install with: pip install stellar-memory[server]"
        )

    from stellar_memory.config import StellarConfig
    from stellar_memory.stellar import StellarMemory

    try:
        from stellar_memory import __version__
    except Exception:
        __version__ = "0.9.0-dev"

    cfg = config or StellarConfig()
    memory = StellarMemory(cfg, namespace=namespace)

    # ── Billing system initialization ──
    _billing_enabled = cfg.billing.enabled
    _db_pool = None
    _auth_mgr = None
    _lemon_provider = None
    _stripe_provider = None
    _toss_provider = None

    app = FastAPI(
        title="Stellar Memory API",
        version=__version__,
        description="""# Stellar Memory API

Celestial-structure-based AI memory management system.
Give any AI human-like memory.

## Authentication
Set `X-API-Key` header or `Authorization: Bearer <key>`.
Configure via `STELLAR_API_KEY` environment variable.
If no key is set, authentication is disabled.

## Rate Limiting
Default: 60 requests per minute per IP.
Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## Zones
| Zone | Name | Description |
|------|------|-------------|
| 0 | Core | Most important, always accessible |
| 1 | Inner | Important memories |
| 2 | Outer | Regular memories |
| 3 | Belt | Less important |
| 4 | Cloud | Near-forgotten, candidates for auto-deletion |
""",
        openapi_tags=[
            {"name": "Memories", "description": "Store, recall, and manage memories"},
            {"name": "Timeline", "description": "Time-based memory access and narratives"},
            {"name": "System", "description": "Health checks, statistics, and event streams"},
            {"name": "Auth", "description": "User registration and API key management"},
            {"name": "Billing", "description": "Subscription checkout and management"},
            {"name": "Webhooks", "description": "Payment provider webhook handlers"},
        ],
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.server.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting (simple in-memory, tier-aware)
    _rate_store: dict[str, list[float]] = {}
    _default_rate_limit = cfg.server.rate_limit
    RATE_WINDOW = 60

    async def check_rate_limit(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        # Use tier-based rate limit if user is authenticated
        rate_limit = _default_rate_limit
        if hasattr(request.state, "user_tier") and _billing_enabled:
            from stellar_memory.billing.tiers import get_tier_limits
            rate_limit = get_tier_limits(request.state.user_tier)["rate_limit"]

        now = time.time()
        times = _rate_store.get(client_ip, [])
        times = [t for t in times if now - t < RATE_WINDOW]
        if len(times) >= rate_limit:
            raise HTTPException(429, "Rate limit exceeded")
        times.append(now)
        _rate_store[client_ip] = times
        # Set rate limit headers
        remaining = rate_limit - len(times)
        request.state.rate_limit = rate_limit
        request.state.rate_remaining = max(0, remaining)
        request.state.rate_reset = int(now + RATE_WINDOW)

    # API key auth (supports both env-var mode and DB-backed mode)
    API_KEY = os.environ.get(cfg.server.api_key_env)

    async def check_api_key(request: Request):
        """Authenticate via API key. Supports legacy env-var and DB-backed modes."""
        key = request.headers.get("X-API-Key") or ""
        if not key:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                key = auth[7:]

        # DB-backed auth (billing enabled)
        if _billing_enabled and _auth_mgr and key:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            user = await _auth_mgr.get_user_by_api_key(key_hash)
            if user:
                request.state.user_id = user.id
                request.state.user_tier = user.tier
                request.state.user_email = user.email
                return
            raise HTTPException(401, "Invalid API key")

        # Legacy env-var auth
        if API_KEY is None:
            return
        if not key or key != API_KEY:
            raise HTTPException(401, "Invalid API key")

    # Rate limit header middleware
    @app.middleware("http")
    async def add_rate_limit_headers(request: Request, call_next):
        response = await call_next(request)
        if hasattr(request.state, "rate_limit"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_remaining)
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_reset)
        return response

    # Pydantic models with full documentation
    class StoreRequest(BaseModel):
        """Request body for storing a new memory."""
        content: str = Field(
            ...,
            description="The text content to memorize",
            min_length=1,
            max_length=10000,
            json_schema_extra={"examples": ["User prefers dark mode"]},
        )
        importance: float = Field(
            0.5, ge=0.0, le=1.0,
            description="Manual importance score (0.0=trivial, 1.0=critical)",
        )
        metadata: dict = Field(
            default_factory=dict,
            description="Optional key-value metadata",
        )
        auto_evaluate: bool = Field(
            False,
            description="Use AI to automatically evaluate importance (requires LLM config)",
        )

    class StoreResponse(BaseModel):
        """Response after storing a memory."""
        id: str = Field(description="Unique memory ID")
        zone: int = Field(description="Assigned zone (0=Core, 1=Inner, 2=Outer, 3=Belt, 4=Cloud)")
        score: float = Field(description="Calculated importance score")

    class RecallItem(BaseModel):
        """A single recalled memory item."""
        id: str = Field(description="Memory ID")
        content: str = Field(description="Memory content text")
        zone: int = Field(description="Current zone (0-4)")
        importance: float = Field(description="Importance score")
        recall_count: int = Field(description="Number of times recalled")
        emotion: dict | None = Field(None, description="Emotion vector if available")

    class MemoryListItem(BaseModel):
        """Memory item in list view."""
        id: str = Field(description="Memory ID")
        content: str = Field(description="Content preview (max 200 chars)")
        zone: int = Field(description="Current zone")
        score: float = Field(description="Total score")
        recall_count: int = Field(description="Recall count")
        importance: float = Field(description="Importance score")
        created_at: float = Field(description="Creation timestamp")

    class MemoryListResponse(BaseModel):
        """Paginated memory list response."""
        total: int = Field(description="Total matching memories")
        items: list[MemoryListItem] = Field(description="Memory items")

    class TimelineItem(BaseModel):
        """A timeline entry."""
        timestamp: float = Field(description="Event timestamp")
        memory_id: str = Field(description="Memory ID")
        content: str = Field(description="Memory content")
        zone: int = Field(description="Current zone")
        importance: float = Field(description="Importance score")
        emotion: dict | None = Field(None, description="Emotion vector")

    class NarrateRequest(BaseModel):
        """Request body for narrative generation."""
        topic: str = Field(
            ..., description="Topic or question for narrative generation",
            json_schema_extra={"examples": ["What happened this week?"]},
        )
        limit: int = Field(10, ge=1, le=50, description="Max memories to include")

    class NarrateResponse(BaseModel):
        """Narrative generation response."""
        narrative: str = Field(description="Generated narrative text")

    class StatsResponse(BaseModel):
        """Memory statistics."""
        total_memories: int = Field(description="Total number of memories")
        zones: dict[str, int] = Field(description="Memory count per zone")
        capacities: dict[str, int | None] = Field(description="Zone capacities")

    class HealthResponse(BaseModel):
        """System health status."""
        healthy: bool = Field(description="Overall health status")
        total_memories: int = Field(description="Total memories stored")
        warnings: list[str] = Field(description="Active warnings")

    class ErrorResponse(BaseModel):
        """Standard error response."""
        detail: str = Field(description="Error description")

    # Routes
    @app.post(
        "/api/v1/store",
        response_model=StoreResponse,
        summary="Store a memory",
        description="Store new content as a memory. It will be scored and placed in the appropriate zone.",
        responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
        tags=["Memories"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def store(req: StoreRequest, request: Request):
        user_id = getattr(request.state, "user_id", None)
        item = memory.store(
            req.content, importance=req.importance,
            metadata=req.metadata, auto_evaluate=req.auto_evaluate,
            user_id=user_id,
        )
        return StoreResponse(
            id=item.id, zone=item.zone,
            score=round(item.total_score, 4),
        )

    @app.get(
        "/api/v1/recall",
        response_model=list[RecallItem],
        summary="Recall memories",
        description="Search memories by query. Returns ranked results by relevance.",
        responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
        tags=["Memories"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def recall(q: str, limit: int = 5, emotion: str | None = None,
                     request: Request = None):
        user_id = getattr(request.state, "user_id", None) if request else None
        results = memory.recall(q, limit=min(limit, 50), emotion=emotion,
                                user_id=user_id)
        return [RecallItem(
            id=item.id, content=item.content,
            zone=item.zone,
            importance=round(item.arbitrary_importance, 4),
            recall_count=item.recall_count,
            emotion=item.emotion.to_dict() if item.emotion else None,
        ) for item in results]

    @app.delete(
        "/api/v1/forget/{memory_id}",
        summary="Forget a memory",
        description="Permanently delete a memory by its ID.",
        responses={404: {"model": ErrorResponse}},
        tags=["Memories"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def forget(memory_id: str, request: Request):
        user_id = getattr(request.state, "user_id", None)
        removed = memory.forget(memory_id, user_id=user_id)
        if not removed:
            raise HTTPException(404, "Memory not found")
        return {"removed": True}

    @app.get(
        "/api/v1/memories",
        response_model=MemoryListResponse,
        summary="List memories",
        description="List all memories with optional zone filter and pagination.",
        tags=["Memories"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def memories(zone: int | None = None, limit: int = 50,
                       offset: int = 0, request: Request = None):
        user_id = getattr(request.state, "user_id", None) if request else None
        all_items = memory._orbit_mgr.get_all_items(user_id=user_id)
        if zone is not None:
            all_items = [i for i in all_items if i.zone == zone]
        all_items.sort(key=lambda x: x.total_score, reverse=True)
        page = all_items[offset:offset + limit]
        return MemoryListResponse(
            total=len(all_items),
            items=[MemoryListItem(
                id=item.id, content=item.content[:200],
                zone=item.zone,
                score=round(item.total_score, 4),
                recall_count=item.recall_count,
                importance=round(item.arbitrary_importance, 4),
                created_at=item.created_at,
            ) for item in page],
        )

    @app.get(
        "/api/v1/timeline",
        response_model=list[TimelineItem],
        summary="Get memory timeline",
        description="Retrieve memories ordered by time, optionally filtered by date range.",
        tags=["Timeline"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def timeline(start: str | None = None, end: str | None = None,
                       limit: int = 100, request: Request = None):
        user_id = getattr(request.state, "user_id", None) if request else None
        entries = memory.timeline(start, end, limit, user_id=user_id)
        return [TimelineItem(
            timestamp=e.timestamp,
            memory_id=e.memory_id,
            content=e.content,
            zone=e.zone,
            importance=round(e.importance, 4),
            emotion=e.emotion.to_dict() if e.emotion else None,
        ) for e in entries]

    @app.post(
        "/api/v1/narrate",
        response_model=NarrateResponse,
        summary="Generate narrative",
        description="Generate a narrative summary from memories about a given topic.",
        tags=["Timeline"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def narrate(req: NarrateRequest, request: Request = None):
        user_id = getattr(request.state, "user_id", None) if request else None
        text = memory.narrate(req.topic, req.limit, user_id=user_id)
        return NarrateResponse(narrative=text)

    @app.get(
        "/api/v1/stats",
        response_model=StatsResponse,
        summary="Memory statistics",
        description="Get current memory statistics including zone distribution.",
        tags=["System"],
        dependencies=[Depends(check_api_key)],
    )
    async def stats(request: Request = None):
        user_id = getattr(request.state, "user_id", None) if request else None
        if user_id:
            # Tenant-scoped stats: count only this user's memories
            all_items = memory._orbit_mgr.get_all_items(user_id=user_id)
            zone_counts: dict[int, int] = {}
            for item in all_items:
                zone_counts[item.zone] = zone_counts.get(item.zone, 0) + 1
            s = memory.stats()
            return StatsResponse(
                total_memories=len(all_items),
                zones={str(k): v for k, v in zone_counts.items()},
                capacities={str(k): v for k, v in s.zone_capacities.items()},
            )
        s = memory.stats()
        return StatsResponse(
            total_memories=s.total_memories,
            zones={str(k): v for k, v in s.zone_counts.items()},
            capacities={str(k): v for k, v in s.zone_capacities.items()},
        )

    @app.get(
        "/api/v1/health",
        response_model=HealthResponse,
        summary="Health check",
        description="Check system health status. No authentication required.",
        tags=["System"],
    )
    async def health():
        h = memory.health()
        return HealthResponse(
            healthy=h.healthy,
            total_memories=h.total_memories,
            warnings=h.warnings,
        )

    @app.get(
        "/api/v1/events",
        summary="Event stream (SSE)",
        description="Server-Sent Events stream for real-time memory updates.",
        tags=["System"],
        dependencies=[Depends(check_api_key)],
    )
    async def events():
        """SSE endpoint for real-time updates."""
        import asyncio
        from starlette.responses import StreamingResponse

        async def event_stream():
            q: asyncio.Queue = asyncio.Queue()
            bus = memory._event_bus

            def _push(event_name, *args):
                data = {"event": event_name, "ts": time.time()}
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
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'heartbeat'})}\n\n"

        return StreamingResponse(
            event_stream(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    # ── P9: Metacognition, Self-Learning, Reasoning, Benchmark ──

    class IntrospectResponse(BaseModel):
        """Introspection result."""
        topic: str = Field(description="Analyzed topic")
        confidence: float = Field(description="Knowledge confidence (0.0-1.0)")
        coverage: list[str] = Field(description="Covered subtopics")
        gaps: list[str] = Field(description="Knowledge gaps")
        memory_count: int = Field(description="Related memory count")
        avg_freshness: float = Field(description="Average freshness (0.0-1.0)")
        zone_distribution: dict[str, int] = Field(description="Zone distribution")

    class ConfidentRecallItem(BaseModel):
        """Confident recall result."""
        memories: list[RecallItem] = Field(description="Recalled memories")
        confidence: float = Field(description="Recall confidence (0.0-1.0)")
        warning: str | None = Field(None, description="Low confidence warning")

    class OptimizeResponse(BaseModel):
        """Weight optimization result."""
        before_weights: dict[str, float] = Field(description="Weights before optimization")
        after_weights: dict[str, float] = Field(description="Weights after optimization")
        improvement: str = Field(description="Improvement description")
        pattern: str = Field(description="Detected pattern")
        simulation_score: float = Field(description="Simulation score")
        rolled_back: bool = Field(description="Whether optimization was rolled back")

    class ReasonRequest(BaseModel):
        """Reasoning request body."""
        query: str = Field(..., description="Reasoning question")
        max_sources: int = Field(10, ge=1, le=50, description="Max source memories")

    class ReasonResponse(BaseModel):
        """Reasoning result."""
        query: str = Field(description="Original query")
        insights: list[str] = Field(description="Derived insights")
        contradictions: list[dict] = Field(description="Found contradictions")
        confidence: float = Field(description="Reasoning confidence")
        reasoning_chain: list[str] = Field(description="Reasoning chain")
        source_count: int = Field(description="Number of source memories")

    class ContradictionItem(BaseModel):
        """Contradiction detection result."""
        memory_a_id: str = Field(description="First memory ID")
        memory_b_id: str = Field(description="Second memory ID")
        description: str = Field(description="Contradiction description")
        severity: float = Field(description="Severity (0.0-1.0)")

    class BenchmarkRequest(BaseModel):
        """Benchmark request body."""
        queries: int = Field(100, ge=1, le=1000, description="Number of queries to run")
        dataset: str = Field("standard", description="Dataset: small, standard, large")
        seed: int = Field(42, description="Random seed for reproducibility")

    class BenchmarkResponse(BaseModel):
        """Benchmark result."""
        recall_at_5: float = Field(description="Top-5 recall accuracy")
        recall_at_10: float = Field(description="Top-10 recall accuracy")
        precision_at_5: float = Field(description="Top-5 precision")
        avg_store_latency_ms: float = Field(description="Average store latency (ms)")
        avg_recall_latency_ms: float = Field(description="Average recall latency (ms)")
        avg_reorbit_latency_ms: float = Field(description="Average reorbit latency (ms)")
        total_memories: int = Field(description="Total memories after benchmark")
        dataset_name: str = Field(description="Dataset used")
        queries_run: int = Field(description="Number of queries run")

    @app.get(
        "/api/v1/introspect",
        response_model=IntrospectResponse,
        summary="Introspect knowledge state",
        description="Analyze knowledge state for a topic. Returns confidence, coverage, and gaps.",
        tags=["Memories"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def introspect(topic: str, depth: int = 1):
        result = memory.introspect(topic, depth=depth)
        return IntrospectResponse(
            topic=result.topic,
            confidence=result.confidence,
            coverage=result.coverage,
            gaps=result.gaps,
            memory_count=result.memory_count,
            avg_freshness=result.avg_freshness,
            zone_distribution={str(k): v for k, v in result.zone_distribution.items()},
        )

    @app.get(
        "/api/v1/recall/confident",
        response_model=ConfidentRecallItem,
        summary="Recall with confidence",
        description="Search memories with confidence scoring. Includes warning for low confidence.",
        tags=["Memories"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def recall_confident(query: str, top_k: int = 5):
        result = memory.recall_with_confidence(query, top_k=top_k)
        return ConfidentRecallItem(
            memories=[RecallItem(
                id=item.id, content=item.content, zone=item.zone,
                importance=round(item.arbitrary_importance, 4),
                recall_count=item.recall_count,
                emotion=item.emotion.to_dict() if item.emotion else None,
            ) for item in result.memories],
            confidence=result.confidence,
            warning=result.warning,
        )

    @app.post(
        "/api/v1/optimize",
        response_model=OptimizeResponse,
        summary="Optimize weights",
        description="Analyze recall patterns and auto-optimize memory function weights.",
        tags=["System"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def optimize():
        try:
            report = memory.optimize()
        except ValueError as e:
            raise HTTPException(400, str(e))
        return OptimizeResponse(
            before_weights=report.before_weights,
            after_weights=report.after_weights,
            improvement=report.improvement,
            pattern=report.pattern,
            simulation_score=report.simulation_score,
            rolled_back=report.rolled_back,
        )

    @app.post(
        "/api/v1/rollback-weights",
        summary="Rollback weights",
        description="Rollback to previous memory function weights.",
        tags=["System"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def rollback_weights():
        try:
            weights = memory.rollback_weights()
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        return {"weights": weights}

    @app.post(
        "/api/v1/reason",
        response_model=ReasonResponse,
        summary="Memory reasoning",
        description="Derive insights by reasoning over related memories.",
        tags=["Memories"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def reason(req: ReasonRequest):
        result = memory.reason(req.query, max_sources=req.max_sources)
        return ReasonResponse(
            query=result.query,
            insights=result.insights,
            contradictions=result.contradictions,
            confidence=result.confidence,
            reasoning_chain=result.reasoning_chain,
            source_count=len(result.source_memories),
        )

    @app.get(
        "/api/v1/contradictions",
        response_model=list[ContradictionItem],
        summary="Detect contradictions",
        description="Detect contradictions among stored memories.",
        tags=["Memories"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def contradictions(scope: str | None = None):
        results = memory.detect_contradictions(scope=scope)
        return [ContradictionItem(
            memory_a_id=c.memory_a_id,
            memory_b_id=c.memory_b_id,
            description=c.description,
            severity=c.severity,
        ) for c in results]

    @app.post(
        "/api/v1/benchmark",
        response_model=BenchmarkResponse,
        summary="Run benchmark",
        description="Run comprehensive memory system benchmark.",
        tags=["System"],
        dependencies=[Depends(check_api_key), Depends(check_rate_limit)],
    )
    async def run_benchmark(req: BenchmarkRequest):
        report = memory.benchmark(
            queries=req.queries, dataset=req.dataset, seed=req.seed,
        )
        return BenchmarkResponse(
            recall_at_5=report.recall_at_5,
            recall_at_10=report.recall_at_10,
            precision_at_5=report.precision_at_5,
            avg_store_latency_ms=round(report.avg_store_latency_ms, 2),
            avg_recall_latency_ms=round(report.avg_recall_latency_ms, 2),
            avg_reorbit_latency_ms=round(report.avg_reorbit_latency_ms, 2),
            total_memories=report.total_memories,
            dataset_name=report.dataset_name,
            queries_run=report.queries_run,
        )

    # ── Auth & Billing Routes (only when billing enabled) ──

    if _billing_enabled:

        class RegisterRequest(BaseModel):
            email: str = Field(..., description="User email address")

        class RegisterResponse(BaseModel):
            user_id: str
            email: str
            tier: str
            api_key: str = Field(description="API key (shown only once)")

        class CreateKeyRequest(BaseModel):
            name: str = Field("Unnamed", description="Key name")

        class CreateKeyResponse(BaseModel):
            id: str
            prefix: str
            name: str
            api_key: str = Field(description="Full API key (shown only once)")
            created_at: str

        class CheckoutRequest(BaseModel):
            tier: str = Field(..., description="Plan tier: pro or promax")
            email: str = Field(..., description="Customer email")

        class TossConfirmRequest(BaseModel):
            customer_key: str
            auth_key: str
            tier: str = Field("pro")
            email: str

        # POST /auth/register
        @app.post(
            "/auth/register",
            response_model=RegisterResponse,
            summary="Register user",
            description="Register a new user and receive an API key.",
            tags=["Auth"],
        )
        async def register(req: RegisterRequest):
            if not _auth_mgr:
                raise HTTPException(503, "Billing not initialized")
            user_info, raw_key = await _auth_mgr.register_user(req.email)
            return RegisterResponse(
                user_id=user_info["user_id"],
                email=user_info["email"],
                tier=user_info["tier"],
                api_key=raw_key,
            )

        # GET /auth/api-keys
        @app.get(
            "/auth/api-keys",
            summary="List API keys",
            description="List all API keys for the authenticated user.",
            tags=["Auth"],
            dependencies=[Depends(check_api_key)],
        )
        async def list_api_keys(request: Request):
            if not hasattr(request.state, "user_id"):
                raise HTTPException(401, "Authentication required")
            keys = await _auth_mgr.list_api_keys(request.state.user_id)
            return {"keys": keys}

        # POST /auth/api-keys
        @app.post(
            "/auth/api-keys",
            response_model=CreateKeyResponse,
            summary="Create API key",
            description="Create a new API key. Full key shown only in this response.",
            tags=["Auth"],
            dependencies=[Depends(check_api_key)],
        )
        async def create_key(request: Request, req: CreateKeyRequest):
            if not hasattr(request.state, "user_id"):
                raise HTTPException(401, "Authentication required")
            try:
                key_info, raw_key = await _auth_mgr.create_api_key(
                    request.state.user_id, req.name
                )
            except ValueError as e:
                raise HTTPException(403, str(e))
            return CreateKeyResponse(
                id=key_info["id"],
                prefix=key_info["prefix"],
                name=key_info["name"],
                api_key=raw_key,
                created_at=key_info["created_at"],
            )

        # DELETE /auth/api-keys/{key_id}
        @app.delete(
            "/auth/api-keys/{key_id}",
            summary="Revoke API key",
            description="Deactivate an API key.",
            tags=["Auth"],
            dependencies=[Depends(check_api_key)],
        )
        async def revoke_key(request: Request, key_id: str):
            if not hasattr(request.state, "user_id"):
                raise HTTPException(401, "Authentication required")
            ok = await _auth_mgr.revoke_api_key(
                request.state.user_id, key_id
            )
            if not ok:
                raise HTTPException(404, "Key not found or already revoked")
            return {"deleted": True}

        # GET /auth/usage
        @app.get(
            "/auth/usage",
            summary="Usage statistics",
            description="Get current usage for the authenticated user.",
            tags=["Auth"],
            dependencies=[Depends(check_api_key)],
        )
        async def usage(request: Request):
            if not hasattr(request.state, "user_id"):
                raise HTTPException(401, "Authentication required")
            from stellar_memory.billing.tiers import get_tier_limits

            tier = getattr(request.state, "user_tier", "free")
            limits = get_tier_limits(tier)
            memory_count = await _auth_mgr.get_memory_count(
                request.state.user_id
            )
            return {
                "tier": tier,
                "memories": {"used": memory_count, "limit": limits["max_memories"]},
                "rate_limit": limits["rate_limit"],
                "max_api_keys": limits["max_api_keys"],
            }

        # ── Billing checkout endpoints ──

        # POST /billing/stripe/checkout
        @app.post(
            "/billing/stripe/checkout",
            summary="Create Stripe checkout",
            tags=["Billing"],
        )
        async def stripe_checkout(req: CheckoutRequest):
            if not _stripe_provider:
                raise HTTPException(503, "Stripe not configured")
            result = await _stripe_provider.create_checkout(
                tier=req.tier,
                customer_email=req.email,
                success_url="https://stellar-memory.com/?checkout=success",
                cancel_url="https://stellar-memory.com/#pricing",
            )
            return {"checkout_url": result.checkout_url, "session_id": result.session_id}

        # POST /billing/lemonsqueezy/checkout
        @app.post(
            "/billing/lemonsqueezy/checkout",
            summary="Create Lemon Squeezy checkout",
            tags=["Billing"],
        )
        async def lemon_checkout(req: CheckoutRequest):
            if not _lemon_provider:
                raise HTTPException(503, "Lemon Squeezy not configured")
            result = await _lemon_provider.create_checkout(
                tier=req.tier,
                customer_email=req.email,
                success_url="https://stellar-memory.com/?checkout=success",
                cancel_url="https://stellar-memory.com/#pricing",
            )
            return {"checkout_url": result.checkout_url, "session_id": result.session_id}

        # POST /billing/toss/checkout
        @app.post(
            "/billing/toss/checkout",
            summary="Create Toss checkout session",
            tags=["Billing"],
        )
        async def toss_checkout(req: CheckoutRequest):
            if not _toss_provider:
                raise HTTPException(503, "TossPayments not configured")
            result = await _toss_provider.create_checkout(
                tier=req.tier,
                customer_email=req.email,
                success_url="https://stellar-memory.com/?checkout=success",
                cancel_url="https://stellar-memory.com/#pricing",
            )
            return {
                "customer_key": result.session_id,
                "client_key": result.client_key,
            }

        # POST /billing/toss/confirm - Confirm Toss billing key
        @app.post(
            "/billing/toss/confirm",
            summary="Confirm Toss billing key",
            tags=["Billing"],
        )
        async def toss_confirm(req: TossConfirmRequest):
            if not _toss_provider:
                raise HTTPException(503, "TossPayments not configured")
            billing_key = await _toss_provider.issue_billing_key(
                req.customer_key, req.auth_key
            )
            # Create/update user with billing key
            user = await _auth_mgr.get_or_create_user(
                req.email, provider="toss"
            )
            await _auth_mgr.update_user_tier(
                email=req.email,
                tier=req.tier,
                provider="toss",
                provider_subscription_id=billing_key,
            )
            return {"billing_key_issued": True, "tier": req.tier}

        # GET /billing/portal
        @app.get(
            "/billing/portal",
            summary="Billing portal redirect",
            tags=["Billing"],
            dependencies=[Depends(check_api_key)],
        )
        async def billing_portal(request: Request):
            if not hasattr(request.state, "user_id"):
                raise HTTPException(401, "Authentication required")
            async with _db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT provider, provider_customer_id, provider_subscription_id FROM users WHERE id = $1",
                    request.state.user_id,
                )
            if not user or not user["provider"]:
                raise HTTPException(404, "No active subscription")

            provider_name = user["provider"]
            customer_id = user["provider_customer_id"] or user["provider_subscription_id"]

            if provider_name == "stripe" and _stripe_provider:
                url = await _stripe_provider.get_portal_url(customer_id)
            elif provider_name == "lemonsqueezy" and _lemon_provider:
                url = await _lemon_provider.get_portal_url(customer_id)
            elif provider_name == "toss" and _toss_provider:
                url = await _toss_provider.get_portal_url(customer_id)
            else:
                raise HTTPException(404, "Provider not available")

            return {"portal_url": url}

        # ── Webhook endpoints ──

        @app.post("/webhook/lemonsqueezy", tags=["Webhooks"])
        async def lemon_webhook(request: Request):
            if not _lemon_provider:
                raise HTTPException(503, "Lemon Squeezy not configured")
            payload = await request.body()
            sig = request.headers.get("X-Signature", "")
            from stellar_memory.billing.webhooks import handle_subscription_event

            event = await _lemon_provider.verify_webhook(payload, sig)
            await handle_subscription_event(event, _auth_mgr)
            return {"ok": True}

        @app.post("/webhook/stripe", tags=["Webhooks"])
        async def stripe_webhook(request: Request):
            if not _stripe_provider:
                raise HTTPException(503, "Stripe not configured")
            payload = await request.body()
            sig = request.headers.get("Stripe-Signature", "")
            from stellar_memory.billing.webhooks import handle_subscription_event

            event = await _stripe_provider.verify_webhook(payload, sig)
            await handle_subscription_event(event, _auth_mgr)
            return {"ok": True}

        @app.post("/webhook/toss", tags=["Webhooks"])
        async def toss_webhook(request: Request):
            if not _toss_provider:
                raise HTTPException(503, "TossPayments not configured")
            payload = await request.body()
            sig = request.headers.get("Toss-Signature", "")
            from stellar_memory.billing.webhooks import handle_subscription_event

            event = await _toss_provider.verify_webhook(payload, sig)
            await handle_subscription_event(event, _auth_mgr)
            return {"ok": True}

    # ── Memory count enforcement middleware ──

    if _billing_enabled:
        @app.middleware("http")
        async def enforce_memory_limits(request: Request, call_next):
            """Check memory limits on store endpoints."""
            if (
                request.url.path.endswith("/store")
                and request.method == "POST"
                and hasattr(request.state, "user_id")
                and _auth_mgr
            ):
                from stellar_memory.billing.tiers import get_tier_limits, next_tier

                tier = getattr(request.state, "user_tier", "free")
                limits = get_tier_limits(tier)
                count = await _auth_mgr.get_memory_count(request.state.user_id)
                if count >= limits["max_memories"]:
                    upgrade = next_tier(tier)
                    msg = (
                        f"Memory limit reached ({count}/{limits['max_memories']}). "
                    )
                    if upgrade:
                        msg += f"Upgrade to {upgrade} for more."
                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        status_code=403, content={"detail": msg}
                    )
            return await call_next(request)

    # ── Startup / Shutdown ──

    @app.on_event("startup")
    async def startup():
        nonlocal _db_pool, _auth_mgr
        nonlocal _lemon_provider, _stripe_provider, _toss_provider

        memory.start()

        if _billing_enabled:
            db_url = os.environ.get(cfg.billing.db_url_env)
            if db_url:
                try:
                    import asyncpg
                    _db_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)

                    from stellar_memory.auth import AuthManager
                    _auth_mgr = AuthManager(_db_pool)
                    await _auth_mgr.init_schema()
                    logger.info("Billing DB initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize billing DB: {e}")

            # Initialize payment providers from env vars
            lemon_key = os.environ.get(cfg.billing.lemon_api_key_env)
            if lemon_key:
                from stellar_memory.billing.lemonsqueezy import LemonSqueezyProvider
                _lemon_provider = LemonSqueezyProvider(
                    api_key=lemon_key,
                    store_id=os.environ.get(cfg.billing.lemon_store_id_env, ""),
                    variant_pro=os.environ.get(cfg.billing.lemon_variant_pro_env, ""),
                    variant_team=os.environ.get(cfg.billing.lemon_variant_team_env, ""),
                    webhook_secret=os.environ.get(cfg.billing.lemon_webhook_secret_env, ""),
                )
                logger.info("Lemon Squeezy provider initialized")

            stripe_key = os.environ.get(cfg.billing.stripe_secret_key_env)
            if stripe_key:
                try:
                    from stellar_memory.billing.stripe_provider import StripeProvider
                    _stripe_provider = StripeProvider(
                        secret_key=stripe_key,
                        webhook_secret=os.environ.get(cfg.billing.stripe_webhook_secret_env, ""),
                        price_pro=os.environ.get(cfg.billing.stripe_price_pro_env, ""),
                        price_team=os.environ.get(cfg.billing.stripe_price_team_env, ""),
                    )
                    logger.info("Stripe provider initialized")
                except ImportError:
                    logger.warning("stripe package not installed, skipping Stripe")

            toss_key = os.environ.get(cfg.billing.toss_secret_key_env)
            if toss_key:
                from stellar_memory.billing.toss_provider import TossProvider
                _toss_provider = TossProvider(
                    secret_key=toss_key,
                    client_key=os.environ.get(cfg.billing.toss_client_key_env, ""),
                    webhook_secret=os.environ.get(cfg.billing.toss_webhook_secret_env, ""),
                )
                logger.info("TossPayments provider initialized")

    @app.on_event("shutdown")
    async def shutdown():
        memory.stop()
        if _db_pool:
            await _db_pool.close()

    return app, memory

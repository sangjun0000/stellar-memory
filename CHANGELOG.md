# Changelog

All notable changes to Stellar Memory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.9.0] - 2026-02-17 (P8)

### Added
- Product README with quick start, architecture diagrams, and usage examples
- CI/CD pipeline (GitHub Actions: test matrix, PyPI publish, Docker push)
- OpenAPI documentation with Pydantic response models, Swagger UI, and ReDoc
- MCP auto-configuration CLI (`stellar-memory init-mcp`)
- Interactive quickstart wizard (`stellar-memory quickstart`)
- Rate limit response headers (X-RateLimit-Limit, Remaining, Reset)
- MkDocs Material documentation site
- Example projects (basic, chatbot, mcp-agent)
- CHANGELOG.md and CONTRIBUTING.md

### Changed
- Version management: single source via `importlib.metadata`
- Dockerfile: non-root user, HEALTHCHECK
- server.py: full Pydantic models with Field descriptions and OpenAPI tags

## [0.8.0] - 2026-02-17 (P7)

### Added
- Emotional Memory Engine with 6-dimensional emotion vectors
- Emotion-weighted memory function: `E(m) = emotional_intensity`
- Memory Stream / Timeline API
- Narrative generation from memory timeline
- REST API Server (FastAPI) with Swagger UI
- LangChain and OpenAI adapter integrations
- PyPI packaging and Docker support
- Korean text emotion analysis

## [0.7.0] - 2026-02-17 (P6)

### Added
- Distributed Storage backend (PostgreSQL + pgvector)
- Multi-agent sync with CRDT conflict resolution
- WebSocket real-time synchronization
- Security layer: AES-256 encryption, RBAC, audit logging
- External connectors (Notion, Slack, GitHub)
- Dashboard API endpoints

## [0.6.0] - 2026-02-17 (P5)

### Added
- Graph Analytics engine (communities, centrality, pathfinding)
- Memory summarization with LLM integration
- Adaptive decay (per-zone decay rates, reinforcement learning)
- CLI graph commands (stats, communities, centrality, path, export)
- DOT and GraphML graph export formats

## [0.5.0] - 2026-02-17 (P4)

### Added
- LLM-based importance evaluation (Anthropic, OpenAI, Ollama providers)
- Auto-tuning of memory function weights via feedback loop
- Session-based memory consolidation
- Event-driven architecture with EventBus
- Structured event logging (JSONL)

## [0.4.0] - 2026-02-17 (P3)

### Added
- Embedding-based semantic recall (sentence-transformers)
- Vector indexing (BruteForce, BallTree) with HNSW-ready interface
- Multi-namespace memory isolation
- Persistent graph storage (SQLite)
- Decay manager with periodic scheduling

## [0.3.0] - 2026-02-17 (P2)

### Added
- Memory graph with relationship tracking
- JSON export/import for backup and migration
- CLI tool with store, recall, stats, export, import commands
- Event bus for memory lifecycle events
- Health check system

## [0.2.0] - 2026-02-17 (P1)

### Added
- Core memory function: `I(m) = w₁·R(m) + w₂·F(m) + w₃·A(m)`
- 5-zone orbital system (Core, Inner, Outer, Belt, Cloud)
- Black hole prevention via logarithmic recall bounding
- Freshness decay with recall-triggered reset
- Periodic reorbit scheduling
- SQLite persistence

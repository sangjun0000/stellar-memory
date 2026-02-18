# REST API

Stellar Memory provides a full REST API via FastAPI.

## Starting the Server

```bash
# Basic
stellar-memory serve-api

# Custom host and port
stellar-memory serve-api --host 0.0.0.0 --port 8080

# With auto-reload for development
stellar-memory serve-api --reload
```

The server starts at `http://localhost:9000` by default.

## Interactive Documentation

- **Swagger UI**: `http://localhost:9000/docs`
- **ReDoc**: `http://localhost:9000/redoc`
- **OpenAPI JSON**: `http://localhost:9000/openapi.json`

## Authentication

Set the `STELLAR_API_KEY` environment variable to enable authentication:

```bash
export STELLAR_API_KEY=your-secret-key
stellar-memory serve-api
```

Include the key in requests:

```bash
# Header
curl -H "X-API-Key: your-secret-key" http://localhost:9000/api/v1/stats

# Bearer token
curl -H "Authorization: Bearer your-secret-key" http://localhost:9000/api/v1/stats
```

If `STELLAR_API_KEY` is not set, authentication is disabled.

## Rate Limiting

Default: 60 requests per minute per IP address.

Response headers on every request:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Remaining requests |
| `X-RateLimit-Reset` | Window reset timestamp |

## Endpoints

### POST /api/v1/store

Store a new memory.

```bash
curl -X POST http://localhost:9000/api/v1/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "User prefers dark mode",
    "importance": 0.8,
    "metadata": {"source": "chat"}
  }'
```

**Response**:
```json
{
  "id": "a1b2c3d4-...",
  "zone": 0,
  "score": 0.7234
}
```

### GET /api/v1/recall

Search memories by query.

```bash
curl "http://localhost:9000/api/v1/recall?q=user+preference&limit=5"
```

**Response**:
```json
[
  {
    "id": "a1b2c3d4-...",
    "content": "User prefers dark mode",
    "zone": 0,
    "importance": 0.8,
    "recall_count": 1,
    "emotion": null
  }
]
```

### DELETE /api/v1/forget/{memory_id}

Delete a memory by ID.

```bash
curl -X DELETE http://localhost:9000/api/v1/forget/a1b2c3d4-...
```

### GET /api/v1/memories

List all memories with optional filtering.

```bash
curl "http://localhost:9000/api/v1/memories?zone=0&limit=10&offset=0"
```

### GET /api/v1/timeline

Get memories ordered by time.

```bash
curl "http://localhost:9000/api/v1/timeline?limit=20"
```

### POST /api/v1/narrate

Generate a narrative summary from memories.

```bash
curl -X POST http://localhost:9000/api/v1/narrate \
  -H "Content-Type: application/json" \
  -d '{"topic": "What happened this week?", "limit": 10}'
```

### GET /api/v1/stats

Get memory statistics.

```bash
curl http://localhost:9000/api/v1/stats
```

### GET /api/v1/health

Health check (no authentication required).

```bash
curl http://localhost:9000/api/v1/health
```

### GET /api/v1/events

Server-Sent Events stream for real-time updates.

```bash
curl -N http://localhost:9000/api/v1/events
```

## Docker

```bash
docker-compose up stellar
# API available at http://localhost:9000
# Swagger UI at http://localhost:9000/docs
```

With PostgreSQL backend:

```bash
docker-compose up stellar-pg postgres
# API available at http://localhost:9001
```

# Stellar Memory - Docker

> Give any AI human-like memory. Celestial-structure-based memory system.

## Quick Start

```bash
docker pull sangjun0000/stellar-memory:latest
docker run -p 9000:9000 -v stellar-data:/data sangjun0000/stellar-memory
```

The REST API will be available at `http://localhost:9000`.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/memories` | POST | Store a memory |
| `/api/v1/memories/recall` | POST | Recall memories |
| `/api/v1/memories/stats` | GET | Memory statistics |
| `/api/v1/memories/timeline` | GET | Memory timeline |
| `/api/v1/memories/introspect` | POST | Knowledge state analysis |
| `/api/v1/memories/reason` | POST | Memory reasoning |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `STELLAR_DB_PATH` | `/data/stellar_memory.db` | Database file path |
| `STELLAR_HOST` | `0.0.0.0` | Server host |
| `STELLAR_PORT` | `9000` | Server port |

## Persistent Storage

Mount a volume to `/data` to persist memories:

```bash
docker run -p 9000:9000 -v stellar-data:/data sangjun0000/stellar-memory
```

## Tags

- `latest` - Latest stable release
- `1.0.0` - v1.0.0 release

## Links

- [GitHub Repository](https://github.com/sangjun0000/stellar-memory)
- [Documentation](https://stellar-memory.com/docs/)
- [PyPI Package](https://pypi.org/project/stellar-memory/)
- [Landing Page](https://stellar-memory.com/)

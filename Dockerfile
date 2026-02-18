FROM python:3.11-slim AS base

RUN groupadd -r stellar && useradd -r -g stellar stellar

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY stellar_memory/ stellar_memory/

RUN pip install --no-cache-dir .[server]

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/api/v1/health')"

ENV STELLAR_DB_PATH=/data/stellar_memory.db
ENV STELLAR_HOST=0.0.0.0
ENV STELLAR_PORT=9000

EXPOSE 9000

RUN mkdir -p /data && chown stellar:stellar /data
VOLUME /data

USER stellar
CMD ["stellar-memory", "serve-api", "--host", "0.0.0.0", "--port", "9000"]

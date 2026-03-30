# ─── Stage 1: builder ─────────────────────────────────────────────────────────
# uv exporte le lockfile en requirements.txt pur PyPI (sans chemins locaux/editables).
FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv export --frozen --no-dev --no-emit-project --output-file /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv .venv \
 && .venv/bin/pip install --no-cache-dir --compile -r /tmp/requirements.txt


# ─── Stage 2: runtime ─────────────────────────────────────────────────────────
# Image finale : pas d'uv, pas d'outils de build, user non-root, layers minimaux.
FROM python:3.13-slim-bookworm AS runtime

RUN groupadd --gid 1001 app \
 && useradd --uid 1001 --gid app --shell /sbin/nologin --no-create-home app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv

COPY --chown=app:app domain/         domain/
COPY --chown=app:app application/    application/
COPY --chown=app:app adapters/       adapters/
COPY --chown=app:app infrastructure/ infrastructure/
COPY --chown=app:app main.py __init__.py ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \

    # Transport à activer — surcharger avec: docker run -e MODE=mcp_http …
    # Valeurs: api | mcp_http | mcp_sse | all
    MODE=api

USER app

# Probe HTTP :9000 — health/ready/info/metrics (indépendant du MODE)
# Service REST    :8000 (MODE=api ou all)
# Service MCP     :8001 (MODE=mcp_http, mcp_sse ou all)
EXPOSE 9000 8000 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9000/health')" || exit 1

CMD ["python", "main.py"]


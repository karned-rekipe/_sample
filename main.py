"""Universal entry point — reads MODE env var to select the transport.

    MODE=api          FastAPI REST  :8000  (default)
    MODE=mcp_http     MCP streamable-HTTP  :8001
    MODE=mcp_sse      MCP SSE              :8001
    MODE=mcp_stdio    MCP stdio            (no network port)
    MODE=all          API + MCP HTTP simultaneously (dev / POC)

ProbeServer always starts on :9000 (probe.enabled=true in config.yaml).
"""
from __future__ import annotations

from pathlib import Path

import os
import sys

from adapters.input.fastapi.router import register_routers
from adapters.input.fastmcp.prompts import IngredientPrompts
from adapters.input.fastmcp.resources import IngredientResources
from adapters.input.fastmcp.tools import IngredientMCP
from arclith import Arclith
from infrastructure.container import build_ingredient_service
from infrastructure.logging_setup import setup_logging

_logger = setup_logging()
_CONFIG = Path(__file__).parent / "config.yaml"
_VALID_MODES = {"api", "mcp_http", "mcp_sse", "mcp_stdio", "all"}

MODE = os.getenv("MODE", "api")

if MODE not in _VALID_MODES:
    _logger.error(f"MODE invalide: {MODE!r} — valeurs acceptées: {sorted(_VALID_MODES)}")
    sys.exit(1)

arclith = Arclith(_CONFIG)

# ── FastAPI app exposed at module level for PyCharm / uvicorn ─────────────────
app = arclith.fastapi()
register_routers(app, arclith)


# ── runner factories ──────────────────────────────────────────────────────────

def _make_api_runner():
    def _run() -> None:
        arclith.run_api("main:app")

    return _run


def _make_mcp_runner(transport: str):
    service, logger = build_ingredient_service(arclith)
    mcp = arclith.fastmcp(f"Rekipe-sample ({transport})")
    IngredientMCP(service, logger, mcp)
    IngredientResources(service, logger, mcp)
    IngredientPrompts(service, logger, mcp)
    arclith.instrument_mcp(mcp)

    match transport:
        case "mcp_http":
            def _run() -> None:
                arclith.run_mcp_http(mcp)
        case "mcp_sse":
            def _run() -> None:
                arclith.run_mcp_sse(mcp)
        case "mcp_stdio":
            def _run() -> None:
                arclith.run_mcp_stdio(mcp)
        case _:
            raise ValueError(f"Unknown MCP transport: {transport}")

    return _run


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _logger.info("🚀 Starting", mode=MODE)

    match MODE:
        case "api":
            arclith.run_with_probes(_make_api_runner(), transports=["api"])

        case "mcp_http" | "mcp_sse":
            arclith.run_with_probes(_make_mcp_runner(MODE), transports=[MODE])

        case "mcp_stdio":
            # stdio monopolises stdin/stdout — probes still run on :9000 in a daemon thread
            arclith.run_with_probes(_make_mcp_runner("mcp_stdio"), transports=["mcp_stdio"])

        case "all":
            _logger.info("🧩 MODE=all — API :8000 + MCP HTTP :8001 + probes :9000")
            arclith.run_with_probes(
                _make_api_runner(),
                _make_mcp_runner("mcp_http"),
                transports=["api", "mcp_http"],
            )


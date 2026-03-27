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

# ── MCP registration imports ──────────────────────────────────────────────────
# Structure :
#   - tools.py / prompts.py / resources.py → fichiers de registration (register_*)
#   - tools/ prompts/ resources/ → sous-dossiers avec les implémentations par entité
#
# Nommage pour éviter les conflits Python (package vs module) :
#   import adapters.input.fastmcp.tools as tools_module
#
# Pour ajouter une nouvelle entité (ex: Recipe) :
#   1. Créer tools/recipe_tools.py, prompts/recipe_prompts.py, resources/recipe_resources.py
#   2. Exporter dans les __init__.py respectifs : from .recipe_tools import RecipeMCP
#   3. Ajouter l'instanciation dans les fonctions register_* (tools.py, prompts.py, resources.py)

import adapters.input.fastmcp.prompts as prompts_module
import adapters.input.fastmcp.resources as resources_module
import adapters.input.fastmcp.tools as tools_module
from arclith import Arclith
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
    mcp = arclith.fastmcp(f"Rekipe-sample ({transport})")
    tools_module.register_tools(mcp, arclith)
    prompts_module.register_prompts(mcp, arclith)
    resources_module.register_resources(mcp, arclith)
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


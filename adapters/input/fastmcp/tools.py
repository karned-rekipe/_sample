"""MCP tools registration."""

import fastmcp

from arclith import Arclith
from adapters.input.fastmcp.tools import IngredientMCP
from infrastructure.ingredient_container import build_ingredient_service


def register_tools(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    """Register all MCP tools."""
    service, logger = build_ingredient_service(arclith)
    IngredientMCP(service, logger, mcp)


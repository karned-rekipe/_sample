"""MCP tools registration."""

import fastmcp
from adapters.input.fastmcp.tools import AdminMCP, IngredientMCP
from arclith import Arclith
from infrastructure.containers.ingredient_container import build_ingredient_service
from infrastructure.purge_registry import purge_registry


def register_tools(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    """Register all MCP tools."""
    service, logger = build_ingredient_service(arclith)
    purge_registry.register("ingredients", service.purge)
    IngredientMCP(service, logger, mcp)
    AdminMCP(purge_registry, logger, mcp)


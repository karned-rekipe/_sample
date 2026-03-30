"""MCP resources registration."""

import fastmcp

from arclith import Arclith
from adapters.input.fastmcp.resources import IngredientResources
from infrastructure.containers.ingredient_container import build_ingredient_service


def register_resources(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    """Register all MCP resources."""
    service, logger = build_ingredient_service(arclith)
    IngredientResources(service, logger, mcp)


"""MCP prompts registration."""

import fastmcp

from arclith import Arclith
from adapters.input.fastmcp.prompts.ingredient_prompts import IngredientPrompts
from infrastructure.containers.ingredient_container import build_ingredient_service


def register_prompts(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    """Register all MCP prompts."""
    service, logger = build_ingredient_service(arclith)
    IngredientPrompts(service, logger, mcp)


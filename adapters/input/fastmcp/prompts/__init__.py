"""MCP prompts."""

import fastmcp

from arclith import Arclith
from adapters.input.fastmcp.prompts.ingredient_prompts import IngredientPrompts
from infrastructure.containers.ingredient_container import build_ingredient_service

__all__ = ["IngredientPrompts"]


def register_prompts(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    service, logger = build_ingredient_service(arclith)
    IngredientPrompts(service, logger, mcp)

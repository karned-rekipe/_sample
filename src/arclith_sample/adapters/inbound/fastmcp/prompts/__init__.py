"""MCP prompts."""

import fastmcp

from arclith import Arclith
from arclith_sample.adapters.inbound.fastmcp.prompts.ingredient_prompts import IngredientPrompts
from arclith_sample.infrastructure.containers.ingredient_container import build_ingredient_service

__all__ = ["IngredientPrompts"]


def register_prompts(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    service, logger = build_ingredient_service(arclith)
    IngredientPrompts(service, logger, mcp)

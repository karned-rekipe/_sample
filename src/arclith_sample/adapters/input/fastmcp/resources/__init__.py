"""MCP resources."""

import fastmcp

from arclith import Arclith
from arclith_sample.adapters.input.fastmcp.resources.ingredient_resources import IngredientResources
from arclith_sample.infrastructure.containers.ingredient_container import build_ingredient_service

__all__ = ["IngredientResources"]


def register_resources(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    service, logger = build_ingredient_service(arclith)
    IngredientResources(service, logger, mcp)

import fastmcp

from arclith import Arclith
from adapters.input.fastmcp.prompts import IngredientPrompts
from infrastructure.ingredient_container import build_ingredient_service


def register_prompts(mcp: fastmcp.FastMCP, arclith: Arclith) -> None:
    service, logger = build_ingredient_service(arclith)
    IngredientPrompts(service, logger, mcp)


import fastmcp

from adapters.input.ingredient_fastmcp import IngredientMCP
from infrastructure.container import build_ingredient_service


def create_mcp() -> fastmcp.FastMCP:
    mcp = fastmcp.FastMCP("Rekipe - Ingredients")

    ingredient_service, logger = build_ingredient_service()
    IngredientMCP(ingredient_service, logger, mcp)

    return mcp


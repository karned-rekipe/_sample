from pathlib import Path
from arclith import Arclith
from adapters.input.fastmcp.tools import IngredientMCP
from adapters.input.fastmcp.resources import IngredientResources
from adapters.input.fastmcp.prompts import IngredientPrompts
from infrastructure.container import build_ingredient_service

arclith = Arclith(Path(__file__).parent / "config.yaml")
service, logger = build_ingredient_service(arclith)
mcp = arclith.fastmcp("Rekipe - Ingredients")
IngredientMCP(service, logger, mcp)
IngredientResources(service, logger, mcp)
IngredientPrompts(service, logger, mcp)

if __name__ == "__main__":
    arclith.run_mcp_sse(mcp)

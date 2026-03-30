import fastmcp

from adapters.input.fastmcp.dependencies import inject_tenant_uri
from application.services.ingredient_service import IngredientService
from arclith.domain.ports.logger import Logger

_EXPLORE_PREVIEW_LIMIT = 20


class IngredientPrompts:
    def __init__(self, service: IngredientService, logger: Logger, mcp: fastmcp.FastMCP) -> None:
        self._service = service
        self._logger = logger
        self._mcp = mcp
        self._register_prompts()

    def _register_prompts(self) -> None:
        service = self._service

        @self._mcp.prompt
        def check_duplicate(ingredient_name: str) -> str:
            """Check for duplicates before creating a new ingredient.

            Use this prompt before calling create_ingredient.
            The LLM will guide you to call list_ingredients with a partial
            name filter to surface any existing match.
            """
            return (
                f"Before creating the ingredient '{ingredient_name}', "
                "call list_ingredients with a partial name filter to check for existing similar entries. "
                "If a match is found, suggest using the existing one instead of creating a duplicate."
            )

        @self._mcp.prompt
        async def explore_ingredients(ctx: fastmcp.Context) -> str:
            """Explore and discover available ingredients.

            Loads the current catalog and guides the LLM to help the user
            search by name or identify what is available.
            """
            await inject_tenant_uri(ctx)
            items = await service.find_all()
            if not items:
                snapshot = "No ingredients available yet. Use create_ingredient to add the first one."
            else:
                names = ", ".join(i.name for i in items[:_EXPLORE_PREVIEW_LIMIT])
                total = len(items)
                snapshot = f"{total} ingredient(s) available: {names}{'...' if total > _EXPLORE_PREVIEW_LIMIT else '.'}"
            return (
                f"{snapshot}\n\n"
                "Help me explore these ingredients: search by name, "
                "or suggest which ones to use for a given dish."
            )

        @self._mcp.prompt
        def mcp_help() -> str:
            """Overview of all MCP capabilities exposed by this server.

            Lists every tool, prompt, and resource with a short description.
            Use this as a starting point when discovering what this server can do.
            """
            return (
                "Here are all the capabilities exposed by this MCP server:\n\n"
                "**Tools** (actions):\n"
                "- create_ingredient(name) — create a new ingredient\n"
                "- get_ingredient(uuid) — retrieve by UUID\n"
                "- update_ingredient(uuid, name) — full replacement (PUT semantics)\n"
                "- delete_ingredient(uuid) — soft-delete\n"
                "- list_ingredients(name?) — list all active, optional partial name filter\n"
                "- duplicate_ingredient(uuid) — clone with a new UUID\n"
                "- purge_ingredients() — permanently remove expired soft-deleted entries\n\n"
                "**Prompts** (LLM guidance):\n"
                "- check_duplicate(ingredient_name) — avoid duplicates before creating\n"
                "- explore_ingredients — discover and filter available ingredients\n"
                "- mcp_help — this overview\n\n"
                "**Resources** (read-only data):\n"
                "- ingredients://sample — first 5 ingredients (quick dataset preview)\n"
                "- ingredients://recent — last 10 ingredients by creation date, newest first\n"
                "- ingredient://{uuid} — single ingredient by UUID\n"
            )


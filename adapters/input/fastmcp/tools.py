from uuid import UUID as StdUUID
from uuid6 import UUID

import fastmcp

from adapters.input.fastmcp.dependencies import inject_tenant_uri
from adapters.input.schemas.ingredient_schema import IngredientSchema
from domain.models.ingredient import Ingredient
from arclith.domain.ports.logger import Logger
from application.services.ingredient_service import IngredientService


class IngredientMCP:
    def __init__(self, service: IngredientService, logger: Logger, mcp: fastmcp.FastMCP) -> None:
        self._service = service
        self._logger = logger
        self._mcp = mcp
        self._register_tools()

    @staticmethod
    def _to_uuid6(uuid: StdUUID) -> UUID:
        return UUID(str(uuid))

    def _register_tools(self) -> None:
        service = self._service
        logger = self._logger
        to_uuid6 = self._to_uuid6

        @self._mcp.tool
        async def create_ingredient(name: str, unit: str | None = None, ctx: fastmcp.Context = None) -> dict:
            """Create a new ingredient."""
            await inject_tenant_uri(ctx)
            result = await service.create(Ingredient(name=name, unit=unit))
            return IngredientSchema.model_validate(result).model_dump()

        @self._mcp.tool
        async def get_ingredient(uuid: str, ctx: fastmcp.Context = None) -> dict | None:
            """Get an ingredient by its UUID."""
            await inject_tenant_uri(ctx)
            result = await service.read(to_uuid6(StdUUID(uuid)))
            if result is None:
                logger.warning("⚠️ Ingredient not found via MCP", uuid=uuid)
                return None
            return IngredientSchema.model_validate(result).model_dump()

        @self._mcp.tool
        async def update_ingredient(uuid: str, name: str, unit: str | None = None, ctx: fastmcp.Context = None) -> dict:
            """Update an existing ingredient."""
            await inject_tenant_uri(ctx)
            result = await service.update(Ingredient(uuid=to_uuid6(StdUUID(uuid)), name=name, unit=unit))
            return IngredientSchema.model_validate(result).model_dump()

        @self._mcp.tool
        async def delete_ingredient(uuid: str, ctx: fastmcp.Context = None) -> None:
            """Delete an ingredient by its UUID."""
            await inject_tenant_uri(ctx)
            await service.delete(to_uuid6(StdUUID(uuid)))

        @self._mcp.tool
        async def list_ingredients(ctx: fastmcp.Context = None) -> list[dict]:
            """List all ingredients."""
            await inject_tenant_uri(ctx)
            return [IngredientSchema.model_validate(i).model_dump() for i in await service.find_all()]

        @self._mcp.tool
        async def duplicate_ingredient(uuid: str, ctx: fastmcp.Context = None) -> dict:
            """Duplicate an ingredient, assigning it a new UUID."""
            await inject_tenant_uri(ctx)
            result = await service.duplicate(to_uuid6(StdUUID(uuid)))
            return IngredientSchema.model_validate(result).model_dump()

        @self._mcp.tool
        async def find_ingredients_by_name(name: str, ctx: fastmcp.Context = None) -> list[dict]:
            """Find ingredients whose name contains the given string."""
            await inject_tenant_uri(ctx)
            return [IngredientSchema.model_validate(i).model_dump() for i in await service.find_by_name(name)]

        @self._mcp.tool
        async def purge_ingredients(ctx: fastmcp.Context = None) -> dict:
            """Purge all soft-deleted ingredients that have exceeded the retention period."""
            await inject_tenant_uri(ctx)
            purged = await service.purge()
            return {"purged": purged}


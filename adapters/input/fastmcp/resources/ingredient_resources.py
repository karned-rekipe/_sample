import json
from uuid import UUID as StdUUID

import fastmcp
from uuid6 import UUID

from adapters.input.fastmcp.dependencies import inject_tenant_uri
from adapters.input.schemas.ingredient_schema import IngredientSchema
from application.services.ingredient_service import IngredientService
from arclith.domain.ports.logger import Logger

_SAMPLE_LIMIT = 5
_RECENT_LIMIT = 10


class IngredientResources:
    def __init__(self, service: IngredientService, logger: Logger, mcp: fastmcp.FastMCP) -> None:
        self._service = service
        self._logger = logger
        self._mcp = mcp
        self._register_resources()

    @staticmethod
    def _to_uuid6(uuid: StdUUID) -> UUID:
        return UUID(str(uuid))

    def _register_resources(self) -> None:
        service = self._service
        logger = self._logger
        to_uuid6 = self._to_uuid6

        @self._mcp.resource("ingredients://sample")
        async def sample_ingredients_resource(ctx: fastmcp.Context) -> str:
            """First 5 ingredients ordered by creation date — quick dataset preview."""
            await inject_tenant_uri(ctx)
            items = await service.find_all()
            sample = sorted(items, key=lambda i: i.created_at)[:_SAMPLE_LIMIT]
            return json.dumps([IngredientSchema.model_validate(i).model_dump(mode="json") for i in sample])

        @self._mcp.resource("ingredients://recent")
        async def recent_ingredients_resource(ctx: fastmcp.Context) -> str:
            """Last 10 ingredients by creation date, newest first."""
            await inject_tenant_uri(ctx)
            items = await service.find_all()
            recent = sorted(items, key=lambda i: i.created_at, reverse=True)[:_RECENT_LIMIT]
            return json.dumps([IngredientSchema.model_validate(i).model_dump(mode="json") for i in recent])

        @self._mcp.resource("ingredient://{uuid}")
        async def get_ingredient_resource(uuid: str, ctx: fastmcp.Context) -> str:
            """A single ingredient by UUID."""
            await inject_tenant_uri(ctx)
            result = await service.read(to_uuid6(StdUUID(uuid)))
            if result is None:
                logger.warning("⚠️ Ingredient not found via MCP resource", uuid=uuid)
                return json.dumps(None)
            return json.dumps(IngredientSchema.model_validate(result).model_dump(mode="json"))


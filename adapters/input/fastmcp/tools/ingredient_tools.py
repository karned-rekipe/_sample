from typing import Annotated
from uuid import UUID as StdUUID

import fastmcp
from pydantic import Field
from uuid6 import UUID

from adapters.input.fastmcp.dependencies import inject_tenant_uri, require_auth_mcp
from adapters.input.schemas.ingredient_schema import IngredientSchema
from application.services.ingredient_service import IngredientService
from arclith.domain.ports.logger import Logger
from domain.models.ingredient import Ingredient


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
        async def create_ingredient(
                name: Annotated[str, Field(
                    description = "Nom de l'ingrédient (ex. 'Farine de blé', 'Sel fin'). Sera normalisé (espaces rognés).",
                    examples = ["Farine de blé", "Sel fin"])],
                unit: Annotated[str | None, Field(default = None,
                                                  description = "Unité de mesure associée (ex. 'g', 'kg', 'ml', 'cl'). Omettre si non applicable.",
                                                  examples = ["g", "kg", "ml", None])] = None,
                ctx: fastmcp.Context | None = None,
        ) -> dict:
            """Create a new reusable ingredient.

            Returns the created ingredient with its generated UUID.
            Once created, use `link_ingredient_to_recipe` to attach it to a recipe.
            Fields returned: uuid, name, unit, created_at, updated_at, version.
            """
            await require_auth_mcp(ctx)
            await inject_tenant_uri(ctx)
            result = await service.create(Ingredient(name=name, unit=unit))
            logger.info("✅ Ingredient created via MCP", uuid = str(result.uuid), name = result.name)
            return IngredientSchema.model_validate(result).model_dump()

        @self._mcp.tool
        async def get_ingredient(
                uuid: Annotated[str, Field(description = "UUID (UUIDv7) de l'ingrédient à récupérer.",
                                           examples = ["01951234-5678-7abc-def0-123456789abc"])],
                ctx: fastmcp.Context | None = None,
        ) -> dict | None:
            """Get an ingredient by its UUID.

            Returns the full ingredient object or null if not found.
            Fields: uuid, name, unit, created_at, updated_at, version.
            """
            await inject_tenant_uri(ctx)
            result = await service.read(to_uuid6(StdUUID(uuid)))
            if result is None:
                logger.warning("⚠️ Ingredient not found via MCP", uuid=uuid)
                return None
            logger.info("✅ Ingredient fetched via MCP", uuid = uuid, name = result.name)
            return IngredientSchema.model_validate(result).model_dump()

        @self._mcp.tool
        async def update_ingredient(
                uuid: Annotated[str, Field(description = "UUID (UUIDv7) de l'ingrédient à modifier.",
                                           examples = ["01951234-5678-7abc-def0-123456789abc"])],
                name: Annotated[str, Field(description = "Nouveau nom de l'ingrédient.",
                                           examples = ["Farine complète", "Gros sel"])],
                unit: Annotated[str | None, Field(default = None,
                                                  description = "Nouvelle unité de mesure. Passer null pour la supprimer.",
                                                  examples = ["g", None])] = None,
                ctx: fastmcp.Context | None = None,
        ) -> dict:
            """Replace name and unit of an existing ingredient.

            Full replacement (PUT semantics): both name and unit are overwritten.
            Returns the updated ingredient.
            Note: updating an ingredient does not propagate to recipes where it is already linked (snapshot model).
            """
            await inject_tenant_uri(ctx)
            result = await service.update(Ingredient(uuid=to_uuid6(StdUUID(uuid)), name=name, unit=unit))
            logger.info("✅ Ingredient updated via MCP", uuid = uuid, name = result.name)
            return IngredientSchema.model_validate(result).model_dump()

        @self._mcp.tool
        async def delete_ingredient(
                uuid: Annotated[str, Field(description = "UUID (UUIDv7) de l'ingrédient à supprimer.",
                                           examples = ["01951234-5678-7abc-def0-123456789abc"])],
                ctx: fastmcp.Context | None = None,
        ) -> None:
            """Soft-delete an ingredient.

            The ingredient is marked as deleted and excluded from list results.
            It is retained until the purge retention period expires.
            Use `purge_ingredients` to permanently remove expired entries.
            """
            await require_auth_mcp(ctx)
            await inject_tenant_uri(ctx)
            await service.delete(to_uuid6(StdUUID(uuid)))
            logger.info("✅ Ingredient deleted via MCP", uuid = uuid)

        @self._mcp.tool
        async def list_ingredients(
                name: Annotated[str | None, Field(default = None,
                                                  description = "Filtre optionnel : recherche partielle sur le nom, insensible à la casse. Ex: 'far' retournera 'Farine de blé'.",
                                                  examples = ["farine", None])] = None,
                ctx: fastmcp.Context | None = None,
        ) -> list[dict]:
            """List all active (non-deleted) ingredients.

            Pass `name` for a partial, case-insensitive name filter.
            Each item: uuid, name, unit, created_at, updated_at, version.
            Use these UUIDs with `link_ingredient_to_recipe` to attach ingredients to a recipe.
            """
            await inject_tenant_uri(ctx)
            items = await service.find_by_name(name) if name else await service.find_all()
            logger.info("✅ Ingredients listed via MCP", count = len(items), filter = name)
            return [IngredientSchema.model_validate(i).model_dump() for i in items]

        @self._mcp.tool
        async def duplicate_ingredient(
                uuid: Annotated[str, Field(description = "UUID (UUIDv7) de l'ingrédient à dupliquer.",
                                           examples = ["01951234-5678-7abc-def0-123456789abc"])],
                ctx: fastmcp.Context | None = None,
        ) -> dict:
            """Duplicate an ingredient, assigning it a new UUID.

            Creates an independent copy with the same name and unit.
            Returns the new ingredient with its own UUID.
            """
            await inject_tenant_uri(ctx)
            result = await service.duplicate(to_uuid6(StdUUID(uuid)))
            logger.info("✅ Ingredient duplicated via MCP", source_uuid = uuid, new_uuid = str(result.uuid))
            return IngredientSchema.model_validate(result).model_dump()



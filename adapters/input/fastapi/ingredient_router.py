from uuid import UUID as StdUUID

from fastapi import APIRouter, Depends, HTTPException, Query
from uuid6 import UUID

from adapters.input.fastapi.dependencies import inject_tenant_uri
from adapters.input.schemas.ingredient_schema import (
    IngredientCreateSchema,
    IngredientPatchSchema,
    IngredientSchema,
    IngredientUpdateSchema,
    IngredientCreatedSchema,
)
from application.services.ingredient_service import IngredientService
from arclith.domain.ports.logger import Logger
from domain.models.ingredient import Ingredient


class IngredientRouter:
    def __init__(self, service: IngredientService, logger: Logger) -> None:
        self._service = service
        self._logger = logger
        self.router = APIRouter(prefix="/v1/ingredients", tags=["ingredients"], dependencies=[Depends(inject_tenant_uri)])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route(
            methods = ["POST"],
            path = "/",
            endpoint = self.create_ingredient,
            summary = "Create ingredient",
            response_model = IngredientCreatedSchema,
            response_description = "UUID of the created ingredient",
            status_code = 201,
        )
        self.router.add_api_route(
            methods = ["GET"],
            path = "/",
            endpoint = self.list_ingredients,
            summary = "List ingredients",
            response_model = list[IngredientSchema],
            response_description = "List of active ingredients",
        )
        self.router.add_api_route(
            methods = ["DELETE"],
            path = "/purge",
            endpoint = self.purge_ingredients,
            summary = "Purge soft-deleted ingredients",
            response_description = "Number of permanently deleted records",
            status_code = 200,
        )
        self.router.add_api_route(
            methods = ["GET"],
            path = "/{uuid}",
            endpoint = self.get_ingredient,
            summary = "Get ingredient",
            response_model = IngredientSchema,
            response_description = "The ingredient",
            responses = {404: {"description": "Ingredient not found"}},
        )
        self.router.add_api_route(
            methods = ["PUT"],
            path = "/{uuid}",
            endpoint = self.update_ingredient,
            summary = "Replace ingredient",
            status_code = 204,
            responses = {404: {"description": "Ingredient not found"}},
        )
        self.router.add_api_route(
            methods = ["PATCH"],
            path = "/{uuid}",
            endpoint = self.patch_ingredient,
            summary = "Partially update ingredient",
            status_code = 204,
            responses = {404: {"description": "Ingredient not found"}},
        )
        self.router.add_api_route(
            methods = ["DELETE"],
            path = "/{uuid}",
            endpoint = self.delete_ingredient,
            summary = "Delete ingredient",
            status_code = 204,
        )
        self.router.add_api_route(
            methods = ["POST"],
            path = "/{uuid}/duplicate",
            endpoint = self.duplicate_ingredient,
            summary = "Duplicate ingredient",
            response_model = IngredientCreatedSchema,
            response_description = "UUID of the duplicated ingredient",
            status_code = 201,
        )

    @staticmethod
    def _to_uuid6(uuid: StdUUID) -> UUID:
        return UUID(str(uuid))

    async def create_ingredient(self, payload: IngredientCreateSchema) -> IngredientCreatedSchema:
        """Create a new reusable ingredient.

        Returns the UUID of the created ingredient.
        Once created, use `POST /v1/recipes/{uuid}/ingredients/{ingredient_uuid}` to attach it to a recipe.
        """
        result = await self._service.create(Ingredient(name=payload.name, unit=payload.unit))
        return IngredientCreatedSchema(uuid = result.uuid)

    async def get_ingredient(self, uuid: StdUUID) -> IngredientSchema:
        """Get an ingredient by its UUID.

        Returns the full ingredient object.
        Fields: uuid, name, unit, created_at, updated_at, version.
        """
        result = await self._service.read(self._to_uuid6(uuid))
        if result is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")
        return IngredientSchema.model_validate(result, from_attributes = True)

    async def update_ingredient(self, uuid: StdUUID, payload: IngredientUpdateSchema) -> None:
        """Replace name and unit of an existing ingredient (PUT semantics).

        Both fields are fully overwritten.
        Note: changes do not propagate to recipes where this ingredient is already linked (snapshot model).
        """
        await self._service.update(Ingredient(uuid = self._to_uuid6(uuid), name = payload.name, unit = payload.unit))

    async def patch_ingredient(self, uuid: StdUUID, payload: IngredientPatchSchema) -> None:
        """Partially update an ingredient (PATCH semantics).

        Only the fields provided in the body are updated; omitted fields keep their current value.
        Note: changes do not propagate to recipes where this ingredient is already linked (snapshot model).
        """
        existing = await self._service.read(self._to_uuid6(uuid))
        if existing is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")
        await self._service.update(Ingredient(
            uuid=existing.uuid,
            name=payload.name if payload.name is not None else existing.name,
            unit=payload.unit if payload.unit is not None else existing.unit,
        ))

    async def delete_ingredient(self, uuid: StdUUID) -> None:
        """Soft-delete an ingredient.

        The ingredient is marked as deleted and excluded from list results.
        It is retained until the purge retention period expires.
        Use `DELETE /v1/ingredients/purge` to permanently remove expired entries.
        """
        await self._service.delete(self._to_uuid6(uuid))

    async def list_ingredients(
        self,
        name: str | None = Query(
            default=None,
            min_length=1,
            description = "Filtre optionnel : recherche partielle sur le nom, insensible à la casse. Ex: 'far' retournera 'Farine de blé'.",
            examples=["farine"],
        ),
    ) -> list[IngredientSchema]:
        """List all active (non-deleted) ingredients.

        Pass `name` for a partial, case-insensitive name filter.
        Each item: uuid, name, unit, created_at, updated_at, version.
        """
        items = await self._service.find_by_name(name) if name else await self._service.find_all()
        return [IngredientSchema.model_validate(i, from_attributes = True) for i in items]

    async def duplicate_ingredient(self, uuid: StdUUID) -> IngredientCreatedSchema:
        """Duplicate an ingredient, assigning it a new UUID.

        Creates an independent copy with the same name and unit.
        Returns the UUID of the new ingredient.
        """
        result = await self._service.duplicate(self._to_uuid6(uuid))
        return IngredientCreatedSchema(uuid = result.uuid)

    async def purge_ingredients(self) -> dict:
        """Permanently delete soft-deleted ingredients that have exceeded the retention period.

        Returns {"purged": <count>} with the number of permanently deleted records.
        This operation is irreversible.
        """
        purged = await self._service.purge()
        return {"purged": purged}


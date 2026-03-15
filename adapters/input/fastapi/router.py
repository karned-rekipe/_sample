from fastapi import APIRouter, Depends, HTTPException

from adapters.input.fastapi.dependencies import inject_tenant_uri
from uuid import UUID as StdUUID
from uuid6 import UUID

from adapters.input.schemas.ingredient_schema import (
    IngredientCreateSchema,
    IngredientPatchSchema,
    IngredientUpdateSchema,
    IngredientSchema,
)
from domain.models.ingredient import Ingredient
from arclith.domain.ports.logger import Logger
from application.services.ingredient_service import IngredientService


class IngredientRouter:
    def __init__(self, service: IngredientService, logger: Logger) -> None:
        self._service = service
        self._logger = logger
        self.router = APIRouter(prefix="/ingredient/v1", tags=["ingredients"], dependencies=[Depends(inject_tenant_uri)])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route("/", self.create_ingredient, methods=["POST"], response_model=IngredientSchema, status_code=201)
        self.router.add_api_route("/", self.list_ingredients, methods=["GET"], response_model=list[IngredientSchema])
        self.router.add_api_route("/search", self.find_ingredients_by_name, methods=["GET"], response_model=list[IngredientSchema])
        self.router.add_api_route("/purge", self.purge_ingredients, methods=["DELETE"], status_code=200)
        self.router.add_api_route("/{uuid}", self.get_ingredient, methods=["GET"], response_model=IngredientSchema)
        self.router.add_api_route("/{uuid}", self.update_ingredient, methods=["PUT"], response_model=IngredientSchema)
        self.router.add_api_route("/{uuid}", self.patch_ingredient, methods=["PATCH"], response_model=IngredientSchema)
        self.router.add_api_route("/{uuid}", self.delete_ingredient, methods=["DELETE"], status_code=204)
        self.router.add_api_route("/{uuid}/duplicate", self.duplicate_ingredient, methods=["POST"], response_model=IngredientSchema, status_code=201)

    @staticmethod
    def _to_uuid6(uuid: StdUUID) -> UUID:
        return UUID(str(uuid))

    async def create_ingredient(self, payload: IngredientCreateSchema) -> IngredientSchema:
        """Create a new ingredient."""
        result = await self._service.create(Ingredient(name=payload.name, unit=payload.unit))
        return IngredientSchema.model_validate(result)

    async def get_ingredient(self, uuid: StdUUID) -> IngredientSchema:
        """Get an ingredient by its UUID."""
        result = await self._service.read(self._to_uuid6(uuid))
        if result is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")
        return IngredientSchema.model_validate(result)

    async def update_ingredient(self, uuid: StdUUID, payload: IngredientUpdateSchema) -> IngredientSchema:
        """Update an existing ingredient."""
        result = await self._service.update(Ingredient(uuid=self._to_uuid6(uuid), name=payload.name, unit=payload.unit))
        return IngredientSchema.model_validate(result)

    async def patch_ingredient(self, uuid: StdUUID, payload: IngredientPatchSchema) -> IngredientSchema:
        """Partially update an ingredient."""
        existing = await self._service.read(self._to_uuid6(uuid))
        if existing is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")
        result = await self._service.update(Ingredient(
            uuid=existing.uuid,
            name=payload.name if payload.name is not None else existing.name,
            unit=payload.unit if payload.unit is not None else existing.unit,
        ))
        return IngredientSchema.model_validate(result)

    async def delete_ingredient(self, uuid: StdUUID) -> None:
        """Delete an ingredient by its UUID."""
        await self._service.delete(self._to_uuid6(uuid))

    async def list_ingredients(self) -> list[IngredientSchema]:
        """List all ingredients."""
        return [IngredientSchema.model_validate(i) for i in await self._service.find_all()]

    async def duplicate_ingredient(self, uuid: StdUUID) -> IngredientSchema:
        """Duplicate an ingredient, assigning it a new UUID."""
        result = await self._service.duplicate(self._to_uuid6(uuid))
        return IngredientSchema.model_validate(result)

    async def find_ingredients_by_name(self, name: str) -> list[IngredientSchema]:
        """Find ingredients whose name contains the given string."""
        return [IngredientSchema.model_validate(i) for i in await self._service.find_by_name(name)]

    async def purge_ingredients(self) -> dict:
        """Purge all soft-deleted ingredients that have exceeded the retention period."""
        purged = await self._service.purge()
        return {"purged": purged}

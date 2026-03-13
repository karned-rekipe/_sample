from fastapi import APIRouter, HTTPException
from uuid import UUID as StdUUID
from uuid6 import UUID

from adapters.input.schemas.ingredient_schema import (
    IngredientCreateSchema,
    IngredientPatchSchema,
    IngredientUpdateSchema,
    IngredientSchema,
)
from domain.models.ingredient import Ingredient
from kcrud.domain.ports.logger import Logger
from domain.services.ingredient_service import IngredientService


class IngredientRouter:
    def __init__(self, service: IngredientService, logger: Logger) -> None:
        self._service = service
        self._logger = logger
        self.router = APIRouter(prefix="/ingredient/v1", tags=["ingredients"])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route("/", self.create, methods=["POST"], response_model=IngredientSchema, status_code=201)
        self.router.add_api_route("/", self.find_all, methods=["GET"], response_model=list[IngredientSchema])
        self.router.add_api_route("/search", self.find_by_name, methods=["GET"], response_model=list[IngredientSchema])
        self.router.add_api_route("/{uuid}", self.read, methods=["GET"], response_model=IngredientSchema)
        self.router.add_api_route("/{uuid}", self.update, methods=["PUT"], response_model=IngredientSchema)
        self.router.add_api_route("/{uuid}", self.patch, methods=["PATCH"], response_model=IngredientSchema)
        self.router.add_api_route("/{uuid}", self.delete, methods=["DELETE"], status_code=204)
        self.router.add_api_route("/{uuid}/duplicate", self.duplicate, methods=["POST"], response_model=IngredientSchema, status_code=201)

    @staticmethod
    def _to_uuid6(uuid: StdUUID) -> UUID:
        return UUID(str(uuid))

    async def create(self, payload: IngredientCreateSchema) -> IngredientSchema:
        ingredient = Ingredient(name=payload.name, unit=payload.unit)
        result = await self._service.create(ingredient)
        return IngredientSchema.model_validate(result)

    async def read(self, uuid: StdUUID) -> IngredientSchema:
        result = await self._service.read(self._to_uuid6(uuid))
        if result is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")
        return IngredientSchema.model_validate(result)

    async def update(self, uuid: StdUUID, payload: IngredientUpdateSchema) -> IngredientSchema:
        ingredient = Ingredient(uuid=self._to_uuid6(uuid), name=payload.name, unit=payload.unit)
        result = await self._service.update(ingredient)
        return IngredientSchema.model_validate(result)

    async def patch(self, uuid: StdUUID, payload: IngredientPatchSchema) -> IngredientSchema:
        existing = await self._service.read(self._to_uuid6(uuid))
        if existing is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")
        patched = Ingredient(
            uuid=existing.uuid,
            name=payload.name if payload.name is not None else existing.name,
            unit=payload.unit if payload.unit is not None else existing.unit,
        )
        result = await self._service.update(patched)
        return IngredientSchema.model_validate(result)

    async def delete(self, uuid: StdUUID) -> None:
        await self._service.delete(self._to_uuid6(uuid))

    async def find_all(self) -> list[IngredientSchema]:
        return [IngredientSchema.model_validate(i) for i in await self._service.find_all()]

    async def duplicate(self, uuid: StdUUID) -> IngredientSchema:
        result = await self._service.duplicate(self._to_uuid6(uuid))
        return IngredientSchema.model_validate(result)

    async def find_by_name(self, name: str) -> list[IngredientSchema]:
        return [IngredientSchema.model_validate(i) for i in await self._service.find_by_name(name)]

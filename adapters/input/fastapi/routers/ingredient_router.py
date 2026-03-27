from typing import Annotated
from uuid import UUID as StdUUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from uuid6 import UUID

from adapters.input.fastapi.dependencies import inject_tenant_uri
from adapters.input.schemas.ingredient_schema import (
    IngredientCreateSchema,
    IngredientPatchSchema,
    IngredientSchema,
    IngredientUpdateSchema,
)
from application.services.ingredient_service import IngredientService
from arclith.adapters.input.fastapi.dependencies import get_duration_ms
from arclith.adapters.input.schemas.response_wrapper import (
    ApiResponse,
    PaginatedResponse,
    ResponseMetadata,
    paginated_response,
    success_response,
)
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
            methods=["POST"],
            path="/",
            endpoint=self.create_ingredient,
            summary="Create ingredient",
            response_model=ApiResponse[IngredientSchema],
            status_code=201,
        )
        self.router.add_api_route(
            methods=["GET"],
            path="/",
            endpoint=self.list_ingredients,
            summary="List ingredients",
            response_model=PaginatedResponse[IngredientSchema],
            status_code=200,
        )
        self.router.add_api_route(
            methods=["DELETE"],
            path="/purge",
            endpoint=self.purge_ingredients,
            summary="Purge soft-deleted ingredients",
            status_code=200,
        )
        self.router.add_api_route(
            methods=["GET"],
            path="/{uuid}",
            endpoint=self.get_ingredient,
            summary="Get ingredient",
            response_model=ApiResponse[IngredientSchema],
            status_code=200,
            responses={404: {"description": "Ingredient not found"}},
        )
        self.router.add_api_route(
            methods=["PUT"],
            path="/{uuid}",
            endpoint=self.update_ingredient,
            summary="Replace ingredient",
            status_code=204,
            responses={404: {"description": "Ingredient not found"}},
        )
        self.router.add_api_route(
            methods=["PATCH"],
            path="/{uuid}",
            endpoint=self.patch_ingredient,
            summary="Partially update ingredient",
            status_code=204,
            responses={404: {"description": "Ingredient not found"}},
        )
        self.router.add_api_route(
            methods=["DELETE"],
            path="/{uuid}",
            endpoint=self.delete_ingredient,
            summary="Delete ingredient",
            status_code=204,
            responses={404: {"description": "Ingredient not found"}},
        )
        self.router.add_api_route(
            methods=["POST"],
            path="/{uuid}/duplicate",
            endpoint=self.duplicate_ingredient,
            summary="Duplicate ingredient",
            response_model=ApiResponse[IngredientSchema],
            status_code=201,
            responses={404: {"description": "Ingredient not found"}},
        )

    @staticmethod
    def _to_uuid6(uuid: StdUUID) -> UUID:
        return UUID(str(uuid))

    async def create_ingredient(
        self,
        payload: IngredientCreateSchema,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
    ) -> ApiResponse[IngredientSchema]:
        """Create a new reusable ingredient.

        Returns the UUID of the created ingredient.
        Once created, use `POST /v1/recipes/{uuid}/ingredients/{ingredient_uuid}` to attach it to a recipe.
        """
        result = await self._service.create(Ingredient(name=payload.name, unit=payload.unit))
        return success_response(
            IngredientSchema.model_validate(result, from_attributes=True),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

    async def get_ingredient(
        self,
        uuid: StdUUID,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
    ) -> ApiResponse[IngredientSchema]:
        """Get an ingredient by its UUID.

        Returns the full ingredient object.
        Fields: uuid, name, unit, created_at, updated_at, version.
        """
        result = await self._service.read(self._to_uuid6(uuid))
        if result is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")
        return success_response(
            IngredientSchema.model_validate(result, from_attributes=True),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

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
        response: Response,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page"),
        name: str | None = Query(None, min_length=1, description="Filter by name (partial, case-insensitive)"),
    ) -> PaginatedResponse[IngredientSchema]:
        """List all active (non-deleted) ingredients.

        Pass `name` for a partial, case-insensitive name filter.
        Each item: uuid, name, unit, created_at, updated_at, version.
        Use the returned UUIDs with `POST /v1/recipes/{uuid}/ingredients/{ingredient_uuid}` to link them to a recipe.
        """
        offset = (page - 1) * per_page
        items, total = await self._service.find_page_filtered(name=name, offset=offset, limit=per_page)
        response.headers["X-Total-Count"] = str(total)
        return paginated_response(
            data=[IngredientSchema.model_validate(i, from_attributes=True) for i in items],
            total=total,
            page=page,
            per_page=per_page,
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

    async def duplicate_ingredient(
        self,
        uuid: StdUUID,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
    ) -> ApiResponse[IngredientSchema]:
        """Duplicate an ingredient, assigning it a new UUID.

        Creates an independent copy with the same name and unit.
        Returns the UUID of the new ingredient.
        """
        result = await self._service.duplicate(self._to_uuid6(uuid))
        return success_response(
            IngredientSchema.model_validate(result, from_attributes=True),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

    async def purge_ingredients(self) -> dict:
        """Permanently delete soft-deleted ingredients that have exceeded the retention period.

        Returns {"purged": <count>} with the number of permanently deleted records.
        This operation is irreversible.
        """
        purged = await self._service.purge()
        return {"purged": purged}


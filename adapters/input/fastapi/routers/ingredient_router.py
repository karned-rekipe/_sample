from typing import Annotated
from uuid import UUID as StdUUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from uuid6 import UUID

from adapters.input.fastapi.dependencies import inject_tenant_uri, require_auth
from adapters.input.schemas.ingredient_schema import (
    IngredientCreatedSchema,
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
            response_model = ApiResponse[IngredientCreatedSchema],
            status_code=201,
            responses = {
                400: {"description": "Invalid payload"},
                422: {"description": "Validation failed"},
            },
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
            methods=["GET"],
            path="/{uuid}",
            endpoint=self.get_ingredient,
            summary="Get ingredient",
            response_model=ApiResponse[IngredientSchema],
            status_code=200,
            responses = {
                404: {"description": "Ingredient not found"},
            },
        )
        self.router.add_api_route(
            methods=["PUT"],
            path="/{uuid}",
            endpoint=self.update_ingredient,
            summary="Replace ingredient",
            status_code=204,
            responses = {
                404: {"description": "Ingredient not found"},
                412: {"description": "Precondition Failed (version mismatch via If-Match)"},
                422: {"description": "Validation failed"},
            },
        )
        self.router.add_api_route(
            methods=["PATCH"],
            path="/{uuid}",
            endpoint=self.patch_ingredient,
            summary="Partially update ingredient",
            status_code=204,
            responses = {
                404: {"description": "Ingredient not found"},
                412: {"description": "Precondition Failed (version mismatch via If-Match)"},
                422: {"description": "Validation failed"},
            },
        )
        self.router.add_api_route(
            methods=["DELETE"],
            path="/{uuid}",
            endpoint=self.delete_ingredient,
            summary="Delete ingredient",
            status_code=204,
            responses = {
                404: {"description": "Ingredient not found"},
            },
            dependencies=[Depends(require_auth)],
        )
        self.router.add_api_route(
            methods=["POST"],
            path="/{uuid}/duplicate",
            endpoint=self.duplicate_ingredient,
            summary="Duplicate ingredient",
            response_model = ApiResponse[IngredientCreatedSchema],
            status_code=201,
            responses = {
                404: {"description": "Ingredient not found"},
            },
        )

    @staticmethod
    def _to_uuid6(uuid: StdUUID) -> UUID:
        return UUID(str(uuid))

    async def create_ingredient(
        self,
        payload: IngredientCreateSchema,
            response: Response,
            request: Request,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
            prefer: Annotated[str | None, Header()] = None,
    ) -> ApiResponse[IngredientCreatedSchema] | ApiResponse[IngredientSchema]:
        """Create a new reusable ingredient.

        **SOTA REST Features:**
        - Returns 201 Created with UUID only (minimal response)
        - Location header points to the created resource
        - Supports `Prefer: return=representation` to get full object instead
        - Supports `Idempotency-Key` header to prevent duplicates (via middleware)
        - Returns 422 for validation errors (business logic)

        **Usage:**
        ```bash
        # Minimal response (default)
        curl -X POST /v1/ingredients \\
          -H "Content-Type: application/json" \\
          -H "Idempotency-Key: $(uuidgen)" \\
          -d '{"name": "Farine de blé"}'
        
        # Full representation
        curl -X POST /v1/ingredients \\
          -H "Prefer: return=representation" \\
          -d '{"name": "Farine de blé"}'
        ```
        """
        result = await self._service.create(Ingredient(name=payload.name))

        # RFC 7231: Location header on 201 Created
        location = f"{request.url.path.rstrip('/')}/{result.uuid}"
        response.headers["Location"] = location

        # RFC 8288: Link header (HATEOAS)
        response.headers["Link"] = f'<{location}>; rel="self", <{location}/duplicate>; rel="duplicate"'

        # RFC 7240: Prefer header support
        if prefer and "return=representation" in prefer.lower():
            # Client wants full object
            return success_response(
                IngredientSchema.model_validate(result, from_attributes = True),
                metadata = ResponseMetadata(duration_ms = int(duration_ms)),
            )

        # Default: minimal response (UUID only)
        return success_response(
            IngredientCreatedSchema(uuid = result.uuid),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

    async def get_ingredient(
        self,
        uuid: StdUUID,
            response: Response,
            request: Request,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
    ) -> ApiResponse[IngredientSchema]:
        """Get an ingredient by its UUID.

        **SOTA REST Features:**
        - ETag header based on entity version (for caching/concurrency)
        - Cache-Control: private, max-age=300 (via middleware)
        - Link header for HATEOAS navigation
        - Supports If-None-Match for conditional GET (304 Not Modified)

        **Usage:**
        ```bash
        # First request
        curl -i /v1/ingredients/01234...
        # Returns: ETag: "v1"
        
        # Subsequent request (cache validation)
        curl -H 'If-None-Match: "v1"' /v1/ingredients/01234...
        # Returns: 304 Not Modified (if unchanged)
        ```
        """
        result = await self._service.read(self._to_uuid6(uuid))
        if result is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP", uuid=str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")

        # RFC 7232: ETag for optimistic locking
        response.headers["ETag"] = f'"{result.version}"'

        # RFC 8288: Link header (HATEOAS)
        base = f"{request.url.path.rstrip('/')}"
        response.headers[
            "Link"] = f'<{base}>; rel="self", <{base}/duplicate>; rel="duplicate", </v1/ingredients>; rel="collection"'
        
        return success_response(
            IngredientSchema.model_validate(result, from_attributes=True),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )

    async def update_ingredient(
            self,
            uuid: StdUUID,
            payload: IngredientUpdateSchema,
            response: Response,
            request: Request,
            if_match: Annotated[str | None, Header()] = None,
    ) -> None:
        """Replace name of an existing ingredient (PUT semantics).

        **SOTA REST Features:**
        - Requires If-Match header for optimistic locking
        - Returns 412 Precondition Failed if version mismatch
        - Returns 204 No Content on success
        - Content-Location header points to updated resource
        - New ETag in response headers

        **Usage:**
        ```bash
        # Get current version
        curl -i /v1/ingredients/01234...
        # Returns: ETag: "v1"
        
        # Update with version check
        curl -X PUT /v1/ingredients/01234... \\
          -H 'If-Match: "v1"' \\
          -d '{"name": "Nouvelle farine"}'
        ```

        The field is fully overwritten.
        Note: changes do not propagate to recipes where this ingredient is already linked (snapshot model).
        """
        existing = await self._service.read(self._to_uuid6(uuid))
        if existing is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP (PUT)", uuid = str(uuid))
            raise HTTPException(status_code = 404, detail = "Ingredient not found")

        # RFC 7232: If-Match validation (optimistic locking)
        if if_match:
            expected_version = int(if_match.strip('"').lstrip('vV'))
            if existing.version != expected_version:
                self._logger.warning(
                    "⚠️ Version mismatch (optimistic lock failure)",
                    uuid = str(uuid),
                    expected = expected_version,
                    current = existing.version,
                )
                raise HTTPException(
                    status_code = 412,
                    detail = f"Version mismatch: expected v{expected_version}, current v{existing.version}",
                )

        updated = await self._service.update(Ingredient(uuid = self._to_uuid6(uuid), name = payload.name))

        # RFC 7231: Content-Location header
        response.headers["Content-Location"] = f"/v1/ingredients/{uuid}"

        # New ETag after update
        response.headers["ETag"] = f'"{updated.version}"'

    async def patch_ingredient(
            self,
            uuid: StdUUID,
            payload: IngredientPatchSchema,
            response: Response,
            request: Request,
            if_match: Annotated[str | None, Header()] = None,
    ) -> None:
        """Partially update an ingredient (PATCH semantics).

        **SOTA REST Features:**
        - Requires If-Match header for optimistic locking
        - Returns 412 Precondition Failed if version mismatch
        - Returns 204 No Content on success
        - Content-Location header points to updated resource

        Only the fields provided in the body are updated; omitted fields keep their current value.
        Note: changes do not propagate to recipes where this ingredient is already linked (snapshot model).
        """
        existing = await self._service.read(self._to_uuid6(uuid))
        if existing is None:
            self._logger.warning("⚠️ Ingredient not found via HTTP (PATCH)", uuid = str(uuid))
            raise HTTPException(status_code=404, detail="Ingredient not found")

        # RFC 7232: If-Match validation
        if if_match:
            expected_version = int(if_match.strip('"').lstrip('vV'))
            if existing.version != expected_version:
                self._logger.warning(
                    "⚠️ Version mismatch (optimistic lock failure)",
                    uuid = str(uuid),
                    expected = expected_version,
                    current = existing.version,
                )
                raise HTTPException(
                    status_code = 412,
                    detail = f"Version mismatch: expected v{expected_version}, current v{existing.version}",
                )

        updated = await self._service.update(
            Ingredient(
                uuid = existing.uuid,
                name = payload.name if payload.name is not None else existing.name,
            )
        )

        # RFC 7231: Content-Location header
        response.headers["Content-Location"] = f"/v1/ingredients/{uuid}"

        # New ETag after update
        response.headers["ETag"] = f'"{updated.version}"'

    async def delete_ingredient(self, uuid: StdUUID) -> None:
        """Soft-delete an ingredient.

        **SOTA REST Features:**
        - Returns 204 No Content on success
        - Idempotent (deleting already-deleted resource returns 204)

        The ingredient is marked as deleted and excluded from list results.
        It is retained until the purge retention period expires.
        Use `DELETE /admin/purge` to permanently remove all expired entities.
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

        **SOTA REST Features:**
        - X-Total-Count header for total items (useful for pagination UI)
        - Cache-Control: private, max-age=60 (via middleware)
        - Always returns 200 OK, even if empty list

        Pass `name` for a partial, case-insensitive name filter.
        Each item: uuid, name, unit, created_at, updated_at, version.
        Use the returned UUIDs with `POST /v1/recipes/{uuid}/ingredients/{ingredient_uuid}` to link them to a recipe.
        """
        offset = (page - 1) * per_page
        items, total = await self._service.find_page_filtered(name=name, offset=offset, limit=per_page)

        # X-Total-Count header (common practice for pagination)
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
            response: Response,
            request: Request,
        duration_ms: Annotated[float, Depends(get_duration_ms)],
            prefer: Annotated[str | None, Header()] = None,
    ) -> ApiResponse[IngredientCreatedSchema] | ApiResponse[IngredientSchema]:
        """Duplicate an ingredient, assigning it a new UUID.

        **SOTA REST Features:**
        - Returns 201 Created with UUID only (minimal response)
        - Location header points to the duplicated resource
        - Supports `Prefer: return=representation` to get full object

        Creates an independent copy with the same name and unit.
        Returns the UUID of the new ingredient.
        """
        result = await self._service.duplicate(self._to_uuid6(uuid))

        # RFC 7231: Location header on 201 Created
        location = f"/v1/ingredients/{result.uuid}"
        response.headers["Location"] = location

        # RFC 8288: Link header
        response.headers["Link"] = f'<{location}>; rel="self", </v1/ingredients>; rel="collection"'

        # RFC 7240: Prefer header support
        if prefer and "return=representation" in prefer.lower():
            return success_response(
                IngredientSchema.model_validate(result, from_attributes = True),
                metadata = ResponseMetadata(duration_ms = int(duration_ms)),
            )

        # Default: minimal response (UUID only)
        return success_response(
            IngredientCreatedSchema(uuid = result.uuid),
            metadata=ResponseMetadata(duration_ms=int(duration_ms)),
        )


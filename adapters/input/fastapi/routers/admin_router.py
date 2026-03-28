from fastapi import APIRouter, Depends

from adapters.input.fastapi.dependencies import require_auth
from infrastructure.purge_registry import PurgeRegistry


class AdminRouter:
    def __init__(self, registry: PurgeRegistry) -> None:
        self._registry = registry
        self.router = APIRouter(prefix="/admin", tags=["admin"])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.add_api_route(
            methods=["DELETE"],
            path="/purge",
            endpoint=self.purge_all,
            summary="Purge all soft-deleted entities",
            status_code=200,
            dependencies=[Depends(require_auth)],
        )

    async def purge_all(self) -> dict:
        """Permanently delete all soft-deleted entities across all collections.

        Runs all registered entity purges in parallel.
        Returns ``{"purged": {"ingredients": N, ...}, "total": N}``.
        This operation is irreversible.
        """
        results = await self._registry.purge_all()
        return {"purged": results, "total": sum(results.values())}


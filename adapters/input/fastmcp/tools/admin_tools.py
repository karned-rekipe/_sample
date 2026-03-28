import fastmcp

from adapters.input.fastmcp.dependencies import require_auth_mcp
from arclith.domain.ports.logger import Logger
from infrastructure.purge_registry import PurgeRegistry


class AdminMCP:
    def __init__(self, registry: PurgeRegistry, logger: Logger, mcp: fastmcp.FastMCP) -> None:
        self._registry = registry
        self._logger = logger
        self._register_tools(mcp)

    def _register_tools(self, mcp: fastmcp.FastMCP) -> None:
        registry = self._registry
        logger = self._logger

        @mcp.tool
        async def purge_all(ctx: fastmcp.Context | None = None) -> dict:
            """Permanently delete all soft-deleted entities across all collections.

            Runs all registered entity purges in parallel.
            Returns {"purged": {"ingredients": N, ...}, "total": N}.
            This operation is irreversible.
            """
            await require_auth_mcp(ctx)
            results = await registry.purge_all()
            total = sum(results.values())
            logger.info("✅ Global purge via MCP", total=total, breakdown=results)
            return {"purged": results, "total": total}


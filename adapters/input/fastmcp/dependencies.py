from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Callable

import fastmcp

from arclith.adapters.input.fastmcp.dependencies import make_inject_tenant_uri
from arclith.infrastructure.config import load_config

_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config.yaml"


@cache
def _get_inject_fn() -> Callable:
    return make_inject_tenant_uri(load_config(_CONFIG_PATH))


async def inject_tenant_uri(ctx: fastmcp.Context | None) -> None:
    if ctx is not None:
        await _get_inject_fn()(ctx)


@cache
def _get_require_auth_mcp_fn() -> Callable:
    from arclith.adapters.input.fastmcp.auth import make_require_auth_tool
    from arclith.adapters.input.jwt.decoder import JWTDecoder
    from arclith.adapters.input.license.validator import RoleLicenseValidator
    from arclith.adapters.output.memory.cache_adapter import MemoryCacheAdapter

    config = load_config(_CONFIG_PATH)
    kc = config.keycloak
    if kc is None:
        raise RuntimeError("config.keycloak requis pour require_auth_mcp — ajouter la section dans config.yaml")
    decoder = JWTDecoder(
        jwks_uri=f"{kc.url}/realms/{kc.realm}/protocol/openid-connect/certs",
        audience=kc.audience,
        cache=MemoryCacheAdapter(),
        ttl_s=config.cache.jwks_ttl,
    )
    license_validator = RoleLicenseValidator(config.license.role) if config.license else None
    return make_require_auth_tool(jwt_decoder=decoder, license_validator=license_validator)


async def require_auth_mcp(ctx: fastmcp.Context | None) -> dict:
    if ctx is None:
        raise PermissionError("401: Authentification requise (transport stdio non supporté)")
    return await _get_require_auth_mcp_fn()(ctx)



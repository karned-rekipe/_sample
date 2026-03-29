from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Annotated, Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from arclith.adapters.input.fastapi.dependencies import make_inject_tenant_uri
from arclith.infrastructure.config import load_config_dir

_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config"
_http_bearer = HTTPBearer(auto_error=False)


@cache
def _get_inject_fn() -> Callable:
    return make_inject_tenant_uri(load_config_dir(_CONFIG_PATH))


async def inject_tenant_uri(request: Request) -> None:
    await _get_inject_fn()(request)


@cache
def _get_require_auth_fn() -> Callable:
    from arclith.adapters.input.fastapi.auth import make_require_auth
    from arclith.adapters.input.jwt.decoder import JWTDecoder
    from arclith.adapters.input.license.validator import RoleLicenseValidator
    from arclith.adapters.output.memory.cache_adapter import MemoryCacheAdapter

    config = load_config_dir(_CONFIG_PATH)
    kc = config.keycloak
    if kc is None:
        raise RuntimeError("config.keycloak requis pour require_auth — ajouter la section dans config.yaml")
    decoder = JWTDecoder(
        jwks_uri=f"{kc.url}/realms/{kc.realm}/protocol/openid-connect/certs",
        audience=kc.audience,
        cache=MemoryCacheAdapter(),
        ttl_s=config.cache.jwks_ttl,
    )
    license_validator = RoleLicenseValidator(config.license.role) if config.license else None
    return make_require_auth(jwt_decoder=decoder, license_validator=license_validator)


async def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
) -> dict:
    return await _get_require_auth_fn()(credentials)

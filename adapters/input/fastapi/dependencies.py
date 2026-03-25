from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Callable

from fastapi import Request

from arclith.adapters.input.fastapi.dependencies import make_inject_tenant_uri
from arclith.infrastructure.config import load_config

_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config.yaml"


@cache
def _get_inject_fn() -> Callable:
    return make_inject_tenant_uri(load_config(_CONFIG_PATH))


async def inject_tenant_uri(request: Request) -> None:
    await _get_inject_fn()(request)

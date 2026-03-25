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


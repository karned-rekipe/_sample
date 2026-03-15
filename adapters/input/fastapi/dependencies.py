from pathlib import Path

from kcrud.adapters.input.fastapi.dependencies import make_inject_tenant_uri
from kcrud.infrastructure.config import load_config

inject_tenant_uri = make_inject_tenant_uri(
    load_config(Path(__file__).parent.parent.parent.parent / "config.yaml")
)

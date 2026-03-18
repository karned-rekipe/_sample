from pathlib import Path

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel


class AgentSettings(BaseModel):
    model_name: str
    base_url: str
    api_key: str = "local"


def load_agent_settings(config_path: Path) -> AgentSettings:
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return AgentSettings.model_validate(data.get("agent", {}))


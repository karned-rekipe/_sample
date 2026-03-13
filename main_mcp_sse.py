from pathlib import Path
from kcrud.infrastructure.config import load_config
from infrastructure.mcp import create_mcp

_CONFIG_PATH = Path(__file__).parent / "config.yaml"

mcp = create_mcp()

if __name__ == "__main__":
    config = load_config(_CONFIG_PATH)
    mcp.run(transport="sse", host=config.mcp.host, port=config.mcp.port)

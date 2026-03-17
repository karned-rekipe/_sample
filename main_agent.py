from pathlib import Path

import chainlit as cl
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from arclith.infrastructure.config import load_config
from infrastructure.agent_config import load_agent_settings

_CONFIG_PATH = Path(__file__).parent / "config.yaml"
_config = load_config(_CONFIG_PATH)
_agent_settings = load_agent_settings(_CONFIG_PATH)

_mcp_server = MCPServerStreamableHTTP(
    f"http://{_config.mcp.host}:{_config.mcp.port}/mcp"
)

_model = OpenAIChatModel(
    _agent_settings.model_name,
    provider=OpenAIProvider(
        base_url=_agent_settings.base_url,
        api_key=_agent_settings.api_key,
    ),
)

_agent = Agent(
    _model,
    toolsets=[_mcp_server],
    system_prompt=(
        "Tu es un assistant culinaire pour l'application Rekipe. "
        "Tu gères les ingrédients en base de données via les tools disponibles. "
        "Réponds toujours en français, de façon concise et utile."
    ),
)


@cl.on_chat_start
async def on_chat_start() -> None:
    cl.user_session.set("history", [])


@cl.on_message
async def on_message(message: cl.Message) -> None:
    history = cl.user_session.get("history", [])
    response = cl.Message(content="")
    await response.send()

    try:
        async with _agent:
            async with _agent.run_stream(str(message.content), message_history=history) as result:
                async for chunk in result.stream_text(delta=True):
                    await response.stream_token(chunk)
                new_history = result.all_messages()

        cl.user_session.set("history", new_history)
    except Exception as e:
        response.content = f"⚠️ Erreur : {e}"

    await response.update()





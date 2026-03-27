from unittest.mock import AsyncMock, patch

import fastmcp
import pytest

from adapters.input.fastmcp.prompts import IngredientPrompts
from application.services.ingredient_service import IngredientService
from domain.models.ingredient import Ingredient


@pytest.fixture
def mcp_app():
    return fastmcp.FastMCP("test")


@pytest.fixture
def service(repo, logger):
    return IngredientService(repo, logger)


@pytest.fixture
async def client(service, logger, mcp_app):
    with patch("adapters.input.fastmcp.prompts.ingredient_prompts.inject_tenant_uri", new=AsyncMock()):
        IngredientPrompts(service, logger, mcp_app)
        async with fastmcp.Client(mcp_app) as c:
            yield c


def _text(result) -> str:
    return result.messages[0].content.text


# --- check_duplicate ---

async def test_check_duplicate_contains_name(client):
    result = await client.get_prompt("check_duplicate", {"ingredient_name": "Farine"})
    assert "Farine" in _text(result)


async def test_check_duplicate_mentions_list_tool(client):
    result = await client.get_prompt("check_duplicate", {"ingredient_name": "Sel"})
    assert "list_ingredients" in _text(result)


# --- explore_ingredients ---

async def test_explore_empty_catalog(client):
    result = await client.get_prompt("explore_ingredients", {})
    assert "No ingredients available" in _text(result)


async def test_explore_lists_ingredient_names(client, service):
    await service.create(Ingredient(name="Farine"))
    await service.create(Ingredient(name="Sel"))
    result = await client.get_prompt("explore_ingredients", {})
    text = _text(result)
    assert "Farine" in text
    assert "Sel" in text


async def test_explore_shows_total_count(client, service):
    for i in range(3):
        await service.create(Ingredient(name=f"Item {i}"))
    result = await client.get_prompt("explore_ingredients", {})
    assert "3" in _text(result)


# --- mcp_help ---

async def test_mcp_help_lists_tools(client):
    text = _text(await client.get_prompt("mcp_help", {}))
    assert "create_ingredient" in text
    assert "list_ingredients" in text
    assert "purge_ingredients" in text


async def test_mcp_help_lists_prompts(client):
    text = _text(await client.get_prompt("mcp_help", {}))
    assert "check_duplicate" in text
    assert "explore_ingredients" in text
    assert "mcp_help" in text


async def test_mcp_help_lists_resources(client):
    text = _text(await client.get_prompt("mcp_help", {}))
    assert "ingredients://sample" in text
    assert "ingredients://recent" in text
    assert "ingredient://{uuid}" in text


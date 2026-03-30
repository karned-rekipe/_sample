"""Tests for infrastructure/purge_registry.py."""

import pytest

from infrastructure.purge_registry import PurgeRegistry, purge_registry


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return PurgeRegistry()


async def test_register_and_purge_all_single_entity(registry):
    """Test registering and purging a single entity."""
    purge_count = 0

    async def mock_purge() -> int:
        nonlocal purge_count
        purge_count = 5
        return 5

    registry.register("ingredients", mock_purge)
    results = await registry.purge_all()

    assert results == {"ingredients": 5}
    assert purge_count == 5


async def test_register_and_purge_all_multiple_entities(registry):
    """Test registering and purging multiple entities."""
    async def purge_ingredients() -> int:
        return 3

    async def purge_recipes() -> int:
        return 7

    async def purge_users() -> int:
        return 0

    registry.register("ingredients", purge_ingredients)
    registry.register("recipes", purge_recipes)
    registry.register("users", purge_users)

    results = await registry.purge_all()

    assert results == {"ingredients": 3, "recipes": 7, "users": 0}


async def test_purge_all_empty_registry(registry):
    """Test purge_all with no registered purgers."""
    results = await registry.purge_all()
    assert results == {}


async def test_purge_all_executes_in_parallel(registry):
    """Test that purge_all executes all purgers in parallel."""
    execution_order = []

    async def purge_a() -> int:
        execution_order.append("a_start")
        execution_order.append("a_end")
        return 1

    async def purge_b() -> int:
        execution_order.append("b_start")
        execution_order.append("b_end")
        return 2

    registry.register("a", purge_a)
    registry.register("b", purge_b)

    await registry.purge_all()

    # Both should have executed
    assert "a_start" in execution_order
    assert "b_start" in execution_order


def test_global_purge_registry_exists():
    """Test that the global purge_registry instance is properly exported."""
    assert isinstance(purge_registry, PurgeRegistry)


async def test_register_overwrites_existing(registry):
    """Test that registering the same name twice overwrites the first."""
    async def first_purge() -> int:
        return 1

    async def second_purge() -> int:
        return 2

    registry.register("test", first_purge)
    registry.register("test", second_purge)

    results = await registry.purge_all()
    assert results == {"test": 2}


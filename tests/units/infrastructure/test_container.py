"""Tests for infrastructure/container.py."""

from infrastructure.container import build_ingredient_service, purge_registry


def test_build_ingredient_service_is_exported():
    """Test that build_ingredient_service is properly exported."""
    assert callable(build_ingredient_service)


def test_purge_registry_is_exported():
    """Test that purge_registry is properly exported."""
    from infrastructure.purge_registry import PurgeRegistry
    assert isinstance(purge_registry, PurgeRegistry)


def test_all_exports_are_defined():
    """Test that all items in __all__ are actually defined."""
    from infrastructure import container
    
    for name in container.__all__:
        assert hasattr(container, name), f"{name} should be exported"


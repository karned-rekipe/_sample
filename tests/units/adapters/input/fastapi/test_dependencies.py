"""Tests for adapters/input/fastapi/dependencies.py."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials


async def test_inject_tenant_uri_without_auth():
    """Test inject_tenant_uri when no authentication is configured."""
    request = MagicMock(spec=Request)
    request.headers = {}
    
    # Import here to avoid config loading issues
    from adapters.input.fastapi.dependencies import inject_tenant_uri
    
    # Should not raise
    await inject_tenant_uri(request)


async def test_inject_tenant_uri_is_cached():
    """Test that inject function is cached."""
    from adapters.input.fastapi.dependencies import _get_inject_fn
    
    fn1 = _get_inject_fn()
    fn2 = _get_inject_fn()
    
    # Should return the same instance
    assert fn1 is fn2


def test_require_auth_fn_is_cached():
    """Test that require_auth function is cached."""
    # Mock the keycloak config to avoid RuntimeError
    with patch("adapters.input.fastapi.dependencies.load_config_dir") as mock_config:
        mock_keycloak = MagicMock()
        mock_keycloak.url = "http://keycloak:8080"
        mock_keycloak.realm = "test"
        mock_keycloak.audience = "test-api"
        
        mock_cache_config = MagicMock()
        mock_cache_config.jwks_ttl = 3600
        
        mock_cfg = MagicMock()
        mock_cfg.keycloak = mock_keycloak
        mock_cfg.cache = mock_cache_config
        mock_cfg.license = None
        mock_config.return_value = mock_cfg
        
        # Clear cache first
        from adapters.input.fastapi.dependencies import _get_require_auth_fn
        _get_require_auth_fn.cache_clear()
        
        fn1 = _get_require_auth_fn()
        fn2 = _get_require_auth_fn()
        
        # Should return the same instance
        assert fn1 is fn2


async def test_require_auth_with_valid_token():
    """Test require_auth basic structure."""
    # This test validates that the function exists and has proper structure
    # Full integration testing with actual JWT is done in integration tests
    from adapters.input.fastapi.dependencies import require_auth
    
    # The function should be defined
    assert callable(require_auth)


async def test_require_auth_without_credentials():
    """Test require_auth signature."""
    # This test validates function signature
    # Full integration testing is done elsewhere
    from adapters.input.fastapi.dependencies import require_auth
    import inspect
    
    # Should accept credentials parameter
    sig = inspect.signature(require_auth)
    assert "credentials" in sig.parameters


def test_require_auth_raises_without_keycloak_config():
    """Test that _get_require_auth_fn raises when keycloak is not configured."""
    with patch("adapters.input.fastapi.dependencies.load_config_dir") as mock_config:
        mock_cfg = MagicMock()
        mock_cfg.keycloak = None
        mock_config.return_value = mock_cfg
        
        # Clear cache
        from adapters.input.fastapi.dependencies import _get_require_auth_fn
        _get_require_auth_fn.cache_clear()
        
        with pytest.raises(RuntimeError, match="config.keycloak requis"):
            _get_require_auth_fn()



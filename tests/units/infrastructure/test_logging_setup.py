"""Tests for infrastructure/logging_setup.py."""

import logging

from infrastructure.logging_setup import setup_logging
from arclith.adapters.output.console.logger import ConsoleLogger


def test_setup_logging_returns_console_logger():
    """Test that setup_logging returns a ConsoleLogger instance."""
    logger = setup_logging()
    assert isinstance(logger, ConsoleLogger)


def test_setup_logging_configures_root_logger():
    """Test that setup_logging configures the root logger."""
    # Setup logging
    setup_logging()
    
    # Get root logger after setup
    root_logger = logging.getLogger()
    
    # Root logger should have at least one handler (force=True replaces existing)
    assert len(root_logger.handlers) >= 1
    assert root_logger.level == logging.DEBUG


def test_intercept_handler_integration():
    """Test that standard logging is intercepted."""
    setup_logging()
    
    # Create a test logger
    test_logger = logging.getLogger("test_integration")
    
    # These should not raise exceptions
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")


def test_intercept_handler_with_exception():
    """Test that exceptions are properly logged."""
    setup_logging()
    
    test_logger = logging.getLogger("test_exception")
    
    try:
        raise ValueError("Test exception")
    except ValueError:
        # Should not raise
        test_logger.exception("Exception occurred")


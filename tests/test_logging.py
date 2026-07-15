import logging
import os
import shutil

import pytest

from warp_content_processor.main import setup_logging


@pytest.fixture
def isolated_logger(monkeypatch):
    """Fixture to isolate logging configuration for tests."""
    # Store original root logger state
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    original_disabled = root_logger.disabled

    # Clear existing handlers and reset state
    root_logger.handlers.clear()
    root_logger.setLevel(logging.NOTSET)
    root_logger.disabled = False

    # Mock basicConfig to force reconfiguration
    original_basicConfig = logging.basicConfig

    def force_basicConfig(*args, **kwargs):
        # Clear handlers first to force reconfiguration
        root_logger.handlers.clear()
        # Call original basicConfig
        original_basicConfig(*args, **kwargs)

    monkeypatch.setattr(logging, "basicConfig", force_basicConfig)

    yield root_logger

    # Restore original state
    root_logger.handlers.clear()
    root_logger.handlers.extend(original_handlers)
    root_logger.setLevel(original_level)
    root_logger.disabled = original_disabled


def test_logging_setup(isolated_logger):
    """Test logging setup with isolated logger configuration."""
    # Setup logging (returns None, configures root logger)
    setup_logging()

    # Get the root logger to test configuration
    logger = isolated_logger

    # Test logger level is INFO
    assert logger.level == logging.INFO

    # Test handlers configuration
    handlers = logger.handlers
    assert len(handlers) == 2  # Should have exactly 2 handlers

    # Look for specific handler types
    stream_handler_found = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in handlers
    )
    file_handler_found = any(isinstance(h, logging.FileHandler) for h in handlers)

    assert (
        stream_handler_found
    ), f"No StreamHandler found in {[type(h) for h in handlers]}"
    assert file_handler_found, f"No FileHandler found in {[type(h) for h in handlers]}"

    # Verify logs directory is created
    assert os.path.exists("logs")

    # Test basic logging functionality (message should appear in console logs)
    test_message = "Test log message"
    logger.info(test_message)

    # The test passes if logging setup completed without errors


@pytest.fixture(autouse=True)
def cleanup_logs():
    """Cleanup logs directory after test."""
    yield
    # Cleanup after test - Use exception handling instead of conditional
    logs_dir = "logs"
    try:
        shutil.rmtree(logs_dir)
    except FileNotFoundError:
        pass  # Directory doesn't exist, no cleanup needed

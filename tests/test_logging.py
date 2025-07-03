import logging
import os
import shutil

import pytest

from warp_content_processor.main import setup_logging


def test_logging_setup():
    # Setup logging (returns None, configures root logger)
    setup_logging()

    # Get the root logger to test configuration
    logger = logging.getLogger()

    # Test logger level is INFO
    assert logger.level == logging.INFO

    # Test handlers configuration
    handlers = logger.handlers
    assert len(handlers) >= 2  # May have additional handlers from other tests

    # Look for specific handler types or their pytest equivalents
    stream_handler_found = any('StreamHandler' in str(type(h)) for h in handlers)
    file_handler_found = any('FileHandler' in str(type(h)) for h in handlers)

    assert stream_handler_found, \
        f"No StreamHandler found in {[type(h) for h in handlers]}"
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
    # Cleanup after test
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)

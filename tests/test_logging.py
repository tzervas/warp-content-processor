import logging
import os
import shutil

from main import setup_logging


def test_logging_setup():
    # Setup logging
    logger = setup_logging()

    # Test logger level is INFO
    assert logger.level == logging.INFO

    # Test handlers configuration
    handlers = logger.handlers
    assert len(handlers) == 2

    # Check handler types
    handler_types = [type(h) for h in handlers]
    assert logging.StreamHandler in handler_types
    assert logging.FileHandler in handler_types

    # Test logging functionality
    test_message = "Test log message"
    logger.info(test_message)

    # Verify message in log file
    log_file = "logs/workflow_processing.log"
    assert os.path.exists(log_file)

    with open(log_file, "r") as f:
        log_content = f.read()
        assert test_message in log_content

    # Cleanup
    if os.path.exists("logs"):
        shutil.rmtree("logs")

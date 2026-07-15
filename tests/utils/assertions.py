"""
Custom test assertions for warp-content-processor tests.

This module provides custom assertion functions that provide more
detailed error messages and specific validation for the content processor.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


def assert_yaml_structure(
    data: Dict[str, Any], expected_keys: List[str], message: str = None
) -> None:
    """Assert that a YAML/dict structure contains expected keys."""
    missing_keys = [key for key in expected_keys if key not in data]
    if missing_keys:
        error_msg = f"Missing required keys: {missing_keys}"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_file_exists(file_path: Union[str, Path], message: str = None) -> None:
    """Assert that a file exists."""
    path = Path(file_path)
    if not path.exists():
        error_msg = f"File does not exist: {path}"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_file_content(
    file_path: Union[str, Path], expected_content: str, message: str = None
) -> None:
    """Assert that a file contains expected content."""
    assert_file_exists(file_path)

    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        actual_content = f.read()

    if actual_content != expected_content:
        error_msg = f"File content mismatch in {path}"
        if message:
            error_msg = f"{message}: {error_msg}"
        error_msg += (
            f"\nExpected: {repr(expected_content)}\nActual: {repr(actual_content)}"
        )
        raise AssertionError(error_msg)


def assert_yaml_valid(content: str, message: str = None) -> Dict[str, Any]:
    """Assert that YAML content is valid and return parsed data."""
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        error_msg = f"Invalid YAML content: {e}"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_json_valid(content: str, message: str = None) -> Dict[str, Any]:
    """Assert that JSON content is valid and return parsed data."""
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON content: {e}"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_security_safe(
    content: str, dangerous_patterns: List[str] = None, message: str = None
) -> None:
    """Assert that content is safe from common security vulnerabilities."""
    default_patterns = [
        "DROP TABLE",
        "<script>",
        "javascript:",
        "$(rm",
        "eval(",
        "__import__",
        "../../",
        "${jndi:",
    ]

    patterns = dangerous_patterns or default_patterns

    for pattern in patterns:
        if pattern.lower() in content.lower():
            error_msg = f"Potentially dangerous pattern found: {pattern}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)


def assert_validation_passes(
    data: Dict[str, Any], validator_func, message: str = None
) -> None:
    """Assert that data passes validation using the provided validator function."""
    try:
        result = validator_func(data)
        if not result:
            error_msg = "Validation failed"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)
    except Exception as e:
        error_msg = f"Validation error: {e}"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_workflow_structure(workflow: Dict[str, Any], message: str = None) -> None:
    """Assert that a workflow has the correct structure."""
    required_fields = ["name", "command"]
    optional_fields = ["description", "tags", "shells", "arguments"]

    # Check required fields
    assert_yaml_structure(workflow, required_fields, message)

    # Validate field types
    if not isinstance(workflow["name"], str) or not workflow["name"].strip():
        error_msg = "Workflow name must be a non-empty string"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)

    if not isinstance(workflow["command"], str) or not workflow["command"].strip():
        error_msg = "Workflow command must be a non-empty string"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)

    # Validate optional fields if present
    if "tags" in workflow and not isinstance(workflow["tags"], list):
        error_msg = "Workflow tags must be a list"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)

    if "shells" in workflow and not isinstance(workflow["shells"], list):
        error_msg = "Workflow shells must be a list"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_notebook_structure(notebook: Dict[str, Any], message: str = None) -> None:
    """Assert that a notebook has the correct structure."""
    required_fields = ["cells", "metadata", "nbformat", "nbformat_minor"]

    # Check required fields
    assert_yaml_structure(notebook, required_fields, message)

    # Validate field types
    if not isinstance(notebook["cells"], list):
        error_msg = "Notebook cells must be a list"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)

    if not isinstance(notebook["metadata"], dict):
        error_msg = "Notebook metadata must be a dictionary"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)

    if not isinstance(notebook["nbformat"], int):
        error_msg = "Notebook nbformat must be an integer"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_cell_structure(cell: Dict[str, Any], message: str = None) -> None:
    """Assert that a notebook cell has the correct structure."""
    required_fields = ["cell_type", "metadata", "source"]

    # Check required fields
    assert_yaml_structure(cell, required_fields, message)

    # Validate cell type
    valid_cell_types = ["code", "markdown", "raw"]
    if cell["cell_type"] not in valid_cell_types:
        error_msg = (
            f"Invalid cell type: {cell['cell_type']}. Must be one of {valid_cell_types}"
        )
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)

    # Validate source
    if not isinstance(cell["source"], (str, list)):
        error_msg = "Cell source must be a string or list of strings"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_processing_result(
    result: Dict[str, Any],
    expected_content_types: List[str] = None,
    message: str = None,
) -> None:
    """Assert that a processing result has the expected structure."""
    required_fields = ["content_types", "parsed_data", "metadata"]

    # Check required fields
    assert_yaml_structure(result, required_fields, message)

    # Validate content types
    if expected_content_types:
        actual_types = result.get("content_types", [])
        missing_types = [t for t in expected_content_types if t not in actual_types]
        if missing_types:
            error_msg = f"Missing expected content types: {missing_types}"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)


def assert_error_handling(func, expected_exception_type: type, *args, **kwargs) -> None:
    """Assert that a function raises the expected exception type."""
    try:
        func(*args, **kwargs)
        raise AssertionError(
            f"Expected {expected_exception_type.__name__} to be raised"
        )
    except expected_exception_type:
        # Expected exception was raised
        pass
    except Exception as e:
        raise AssertionError(
            f"Expected {expected_exception_type.__name__}, but got {type(e).__name__}: {e}"
        )


def assert_log_contains(
    log_records: List, expected_message: str, level: str = None, message: str = None
) -> None:
    """Assert that log records contain a specific message."""
    matching_records = []

    for record in log_records:
        record_message = getattr(record, "message", str(record))
        record_level = getattr(record, "levelname", "INFO")

        if expected_message in record_message:
            if level is None or record_level == level:
                matching_records.append(record)

    if not matching_records:
        error_msg = f"Expected log message not found: {expected_message}"
        if level:
            error_msg += f" (level: {level})"
        if message:
            error_msg = f"{message}: {error_msg}"

        # Add details about available log messages
        available_messages = [getattr(r, "message", str(r)) for r in log_records]
        error_msg += f"\nAvailable log messages: {available_messages}"

        raise AssertionError(error_msg)


def assert_performance_within_limits(
    execution_time: float, max_time: float, message: str = None
) -> None:
    """Assert that execution time is within acceptable limits."""
    if execution_time > max_time:
        error_msg = (
            f"Execution time {execution_time:.3f}s exceeds limit of {max_time:.3f}s"
        )
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_memory_usage_reasonable(
    memory_usage: int, max_memory_mb: int, message: str = None
) -> None:
    """Assert that memory usage is within reasonable limits."""
    memory_mb = memory_usage / (1024 * 1024)  # Convert to MB
    if memory_mb > max_memory_mb:
        error_msg = f"Memory usage {memory_mb:.2f}MB exceeds limit of {max_memory_mb}MB"
        if message:
            error_msg = f"{message}: {error_msg}"
        raise AssertionError(error_msg)


def assert_string_contains_pattern(
    text: str, pattern: str, message: str = None
) -> None:
    """Assert that a string contains a specific pattern."""
    if pattern not in text:
        error_msg = f"Pattern '{pattern}' not found in text"
        if message:
            error_msg = f"{message}: {error_msg}"
        error_msg += f"\nText content: {repr(text[:200])}..."  # Show first 200 chars
        raise AssertionError(error_msg)


def assert_lists_equal_unordered(
    list1: List[Any], list2: List[Any], message: str = None
) -> None:
    """Assert that two lists contain the same elements (order doesn't matter)."""
    set1, set2 = set(list1), set(list2)
    if set1 != set2:
        error_msg = f"Lists don't contain the same elements"
        if message:
            error_msg = f"{message}: {error_msg}"

        missing_from_first = set2 - set1
        missing_from_second = set1 - set2

        if missing_from_first:
            error_msg += f"\nMissing from first list: {missing_from_first}"
        if missing_from_second:
            error_msg += f"\nMissing from second list: {missing_from_second}"

        raise AssertionError(error_msg)


def assert_dict_subset(
    subset: Dict[str, Any], superset: Dict[str, Any], message: str = None
) -> None:
    """Assert that one dictionary is a subset of another."""
    for key, value in subset.items():
        if key not in superset:
            error_msg = f"Key '{key}' not found in superset"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)

        if superset[key] != value:
            error_msg = (
                f"Value mismatch for key '{key}': expected {value}, got {superset[key]}"
            )
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)

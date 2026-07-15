"""Shared validation utilities for content processors."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __init__(
        self,
        is_valid: bool = True,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []


def validate_placeholders(
    content: str, arguments: List[Dict], pattern: str = r"{{[a-zA-Z_][a-zA-Z0-9_]*}}"
) -> ValidationResult:
    """
    Validate command/prompt placeholders against provided arguments.

    Args:
        content: String containing placeholders
        arguments: List of argument dictionaries
        pattern: Regex pattern for placeholders (default: {{name}})

    Returns:
        Tuple[List[str], List[str]]: (errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(arguments, list):
        return ValidationResult(is_valid=False, errors=["'arguments' must be a list"])

    # Validate placeholders
    placeholder_pattern = re.compile(pattern)
    placeholders = set(placeholder_pattern.findall(content))
    placeholders = {p[2:-2] for p in placeholders}  # Remove {{ and }}

    # Extract argument names, handling invalid types
    valid_args = [arg for arg in arguments if isinstance(arg, dict)]
    if len(valid_args) != len(arguments):
        warnings.append("Some arguments are not dictionaries")

    arg_names = {arg.get("name") for arg in valid_args}
    if None in arg_names:
        warnings.append("Some arguments are missing 'name' field")
        arg_names.remove(None)

    # Check for missing and unused arguments
    missing_args = placeholders - arg_names
    unused_args = arg_names - placeholders

    if missing_args:
        warnings.append(f"References undefined arguments: {missing_args}")
    if unused_args:
        warnings.append(f"Defined arguments not used: {unused_args}")

    return ValidationResult(is_valid=True, warnings=warnings)


def validate_tags(
    tags: List[str], pattern: str = r"^[a-z0-9][a-z0-9-]*[a-z0-9]$"
) -> ValidationResult:
    """
    Validate tag format.

    Args:
        tags: List of tags to validate
        pattern: Regex pattern for valid tags

    Returns:
        Tuple[List[str], List[str]]: (errors, warnings)
    """
    if not isinstance(tags, list):
        return ValidationResult(is_valid=False, errors=["'tags' must be a list"])

    warnings = []
    tag_pattern = re.compile(pattern)
    invalid_tag_chars = re.compile(r"[^a-z0-9-]")

    for tag in tags:
        if not isinstance(tag, str):
            warnings.append(f"Tag '{tag}' is not a string")
            continue

        tag_str = str(tag)
        if not tag_str:
            warnings.append("Empty tag found")
            continue

        if not tag_pattern.match(tag_str):
            # Provide specific warning about the issue
            if invalid_tag_chars.search(tag_str):
                warnings.append(f"Tag '{tag_str}' contains invalid characters")
            elif tag_str.isupper():
                warnings.append(f"Tag '{tag_str}' should be lowercase")
            elif tag_str.endswith("-"):
                warnings.append(f"Tag '{tag_str}' ends with a hyphen")
            else:
                warnings.append(f"Tag '{tag_str}' does not match required format")

    return ValidationResult(is_valid=True, warnings=warnings)

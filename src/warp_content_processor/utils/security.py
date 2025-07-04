"""Security utilities for content processing."""

import re
from typing import Any, Dict, List, Optional

import yaml


class SecurityValidationError(Exception):
    """Raised when content fails security validation."""

    pass


class ContentSanitizer:
    """Utilities for sanitizing potentially unsafe content."""

    # Patterns for potentially dangerous content
    DANGEROUS_PATTERNS = [
        re.compile(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", re.IGNORECASE),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"vbscript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),  # event handlers
    ]

    # Binary data patterns
    BINARY_PATTERNS = [
        re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]+"),
    ]

    @classmethod
    def sanitize_string(cls, content: str, max_size: int = 10 * 1024 * 1024) -> str:
        """
        Sanitize string content by removing dangerous patterns.

        Args:
            content: The content to sanitize
            max_size: Maximum allowed content size

        Returns:
            str: Sanitized content

        Raises:
            SecurityValidationError: If content is deemed too dangerous
        """
        if len(content) > max_size:
            raise SecurityValidationError(
                f"Content size {len(content)} exceeds maximum {max_size}"
            )

        # Remove dangerous script patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            content = pattern.sub("", content)

        # Remove binary data
        for pattern in cls.BINARY_PATTERNS:
            content = pattern.sub("", content)

        return content

    @classmethod
    def validate_content(cls, content: str) -> List[str]:
        """
        Validate content and return list of security warnings.

        Args:
            content: Content to validate

        Returns:
            List[str]: List of security warnings
        """
        warnings = []

        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.search(content):
                warnings.append(
                    f"Potentially dangerous pattern detected: {pattern.pattern}"
                )

        for pattern in cls.BINARY_PATTERNS:
            if pattern.search(content):
                warnings.append("Binary data detected in content")

        return warnings


def secure_yaml_load(content: str) -> Any:
    """Securely load YAML content using SafeLoader.

    Args:
        content: YAML content to load

    Returns:
        Any: Parsed YAML data

    Raises:
        SecurityValidationError: If content is deemed unsafe
    """
    # Validate content first
    warnings = ContentSanitizer.validate_content(content)
    if warnings:
        raise SecurityValidationError(f"Content security warnings: {warnings}")

    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise SecurityValidationError(f"YAML parsing failed: {str(e)}")


def secure_yaml_dump(data: Any, **kwargs: Any) -> str:
    """Securely dump data to YAML using SafeDumper.

    Args:
        data: Data to dump
        **kwargs: Additional arguments for yaml.dump

    Returns:
        str: YAML representation of data
    """
    try:
        return yaml.safe_dump(data, **kwargs)
    except yaml.YAMLError as e:
        raise SecurityValidationError(f"YAML dumping failed: {str(e)}")

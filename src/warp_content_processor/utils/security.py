"""
Security utilities for sanitizing and validating content.
"""

import logging
import re
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Raised when content fails security validation."""
    pass


class ContentSanitizer:
    """Sanitizes content to prevent security issues."""

    # Patterns for potentially harmful content
    UNSAFE_PATTERNS = [
        r"[\x00-\x08\x0B\x0C\x0E-\x1F]",  # Control characters
        r"javascript:",  # JavaScript protocol
        r"data:",       # Data URI scheme
        r"vbscript:",   # VBScript protocol
        r"&lt;script",  # HTML script tags
        r"&#x?[0-9a-f]+;",  # HTML entities that could hide malicious content
    ]

    @classmethod
    def sanitize_string(cls, content: str) -> str:
        """
        Sanitize a string by removing potentially harmful content.

        Args:
            content: String to sanitize

        Returns:
            str: Sanitized string
        """
        if not content:
            return ""

        # Remove or replace potentially harmful patterns
        for pattern in cls.UNSAFE_PATTERNS:
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)

        # Normalize whitespace (but preserve intended indentation)
        lines = content.split("\n")
        normalized = []
        for line in lines:
            # Preserve leading whitespace
            leading = re.match(r"^[\t ]*", line)[0]
            # Strip other whitespace and control chars
            cleaned = re.sub(r"[\t ]+", " ", line.strip())
            normalized.append(leading + cleaned if cleaned else "")

        return "\n".join(normalized)

    @classmethod
    def validate_content(cls, content: str) -> None:
        """
        Validate content for security issues.

        Args:
            content: Content to validate

        Raises:
            SecurityValidationError: If content fails validation
        """
        if not content:
            raise SecurityValidationError("Empty content")

        # Check for excessive size
        if len(content) > 1_000_000:  # 1MB limit
            raise SecurityValidationError("Content exceeds maximum size limit")

        # Check for suspicious patterns
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                raise SecurityValidationError(f"Content contains unsafe pattern: {pattern}")

        # Check for deeply nested structures that could cause DoS
        if content.count("{") > 100 or content.count("[") > 100:
            raise SecurityValidationError("Content contains excessive nesting")


def secure_yaml_load(content: str) -> Optional[Dict[str, Any]]:
    """
    Safely load YAML content with security validation.

    Args:
        content: YAML content to load

    Returns:
        Optional[Dict[str, Any]]: Parsed YAML data or None if invalid
    """
    try:
        # Sanitize content first
        content = ContentSanitizer.sanitize_string(content)
        # Validate for security
        ContentSanitizer.validate_content(content)
        # Parse YAML safely
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            logger.warning("YAML content is not a dictionary")
            return None
        return data
    except SecurityValidationError as e:
        logger.error("Security validation failed: %s", str(e))
        return None
    except yaml.YAMLError as e:
        logger.error("YAML parsing failed: %s", str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error loading YAML: %s", str(e))
        return None


def secure_yaml_dump(data: Dict[str, Any]) -> str:
    """
    Safely dump data to YAML with security validation.

    Args:
        data: Data to dump to YAML

    Returns:
        str: YAML representation of data
    """
    try:
        # Convert to YAML
        content = yaml.safe_dump(data, sort_keys=False)
        # Sanitize output
        content = ContentSanitizer.sanitize_string(content)
        # Validate for security
        ContentSanitizer.validate_content(content)
        return content
    except SecurityValidationError as e:
        logger.error("Security validation failed: %s", str(e))
        return ""
    except yaml.YAMLError as e:
        logger.error("YAML dumping failed: %s", str(e))
        return ""
    except Exception as e:
        logger.error("Unexpected error dumping YAML: %s", str(e))
        return ""

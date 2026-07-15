"""
Security utilities for sanitizing and validating content.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Raised when content fails security validation."""

    pass


class InputValidator:
    """Validates input fields for security and format."""

    @staticmethod
    def validate_workflow_name(name: str) -> bool:
        """Validate workflow name for security and format.

        Args:
            name: The workflow name to validate

        Returns:
            bool: True if valid, raises SecurityValidationError if invalid

        Raises:
            SecurityValidationError: If the name fails validation
        """
        if not name or not isinstance(name, str):
            raise SecurityValidationError("Workflow name must be a non-empty string")

        # Check for dangerous characters
        if any(char in name for char in "<>;{}\\"):
            raise SecurityValidationError("Workflow name contains dangerous characters")

        # Check for null bytes
        if "\x00" in name:
            raise SecurityValidationError("Workflow name contains null bytes")

        # Allow letters, numbers, spaces, dashes, and underscores
        if not all(c.isalnum() or c in " -_" for c in name):
            raise SecurityValidationError(
                "Workflow name can only contain letters, numbers, spaces, dashes, and underscores"
            )

        return True

    @staticmethod
    def validate_tag(tag: str) -> bool:
        """Validate a tag for security and format.

        Args:
            tag: The tag to validate

        Returns:
            bool: True if valid, raises SecurityValidationError if invalid

        Raises:
            SecurityValidationError: If the tag fails validation
        """
        if not tag or not isinstance(tag, str):
            raise SecurityValidationError("Tag must be a non-empty string")

        # Only allow lowercase letters, numbers, and dashes
        if not all(c.islower() or c.isdigit() or c == "-" for c in tag):
            raise SecurityValidationError(
                "Tag can only contain lowercase letters, numbers, and dashes"
            )

        # Don't allow tags starting with dash
        if tag.startswith("-"):
            raise SecurityValidationError("Tag cannot start with a dash")

        # Don't allow spaces
        if " " in tag:
            raise SecurityValidationError("Tag cannot contain spaces")

        return True


class ContentSanitizer:
    """Sanitizes content to prevent security issues."""

    # Patterns for potentially harmful content
    UNSAFE_PATTERNS = [
        r"[\x00-\x08\x0B\x0C\x0E-\x1F]",  # Control characters
        r"javascript:",  # JavaScript protocol
        r"data:",  # Data URI scheme
        r"vbscript:",  # VBScript protocol
        r"&lt;script",  # HTML script tags
    ]

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
                raise SecurityValidationError(
                    f"Content contains unsafe pattern: {pattern}"
                )

        # Check for deeply nested structures that could cause DoS
        if content.count("{") > 100 or content.count("[") > 100:
            raise SecurityValidationError("Content contains excessive nesting")

    @staticmethod
    def validate_file_path(file_path: str) -> Path:
        """Validate a file path for security.

        Args:
            file_path: Path to validate

        Returns:
            Path: Validated Path object

        Raises:
            SecurityValidationError: If the path fails validation
        """
        if not file_path or not isinstance(file_path, str):
            raise SecurityValidationError("File path must be a non-empty string")

        # Only allow relative paths within project
        if file_path.startswith("/") or file_path.startswith("~"):
            raise SecurityValidationError("Absolute paths are not allowed")

        # Check for directory traversal
        if ".." in file_path:
            raise SecurityValidationError("Directory traversal is not allowed")

        # Check for UNC paths
        if file_path.startswith("\\"):
            raise SecurityValidationError("UNC paths are not allowed")

        # Only allow specific file extensions
        ALLOWED_EXTENSIONS = {".yaml", ".yml", ".md", ".txt"}
        path = Path(file_path)
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise SecurityValidationError("File extension not allowed")

        return path

    @staticmethod
    def validate_command_content(command: str) -> None:
        """Validate command content for security.

        Args:
            command: Command content to validate

        Raises:
            SecurityValidationError: If command content fails validation
        """
        DANGEROUS_PATTERNS = [
            ";",  # Command chaining
            "&&",  # Command chaining
            "||",  # Command chaining
            "|",  # Pipe
            ">",  # Redirection
            "<",  # Redirection
            "$(",  # Command substitution
            "`",  # Command substitution
            "../",  # Path traversal
            "~",  # Home directory
            "sudo",  # Privilege escalation
            "rm -rf",  # Dangerous removal
        ]

        for pattern in DANGEROUS_PATTERNS:
            if pattern in command:
                raise SecurityValidationError(
                    f"Command contains dangerous pattern: {pattern}"
                )

    @staticmethod
    def validate_yaml_structure(data: Any) -> None:
        """Validate YAML structure for security.

        Args:
            data: Parsed YAML data to validate

        Raises:
            SecurityValidationError: If structure fails validation
        """
        def check_depth(obj: Any, depth: int = 0) -> int:
            """Check nesting depth of data structure."""
            if depth > 20:  # Max nesting depth
                raise SecurityValidationError("YAML structure too deeply nested")

            if isinstance(obj, dict):
                return max(
                    (check_depth(v, depth + 1) for v in obj.values()),
                    default=depth,
                )
            elif isinstance(obj, list):
                if len(obj) > 1000:  # Max array size
                    raise SecurityValidationError("YAML array too large")
                return max(
                    (check_depth(item, depth + 1) for item in obj),
                    default=depth,
                )
            return depth

        check_depth(data)

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
                raise SecurityValidationError(
                    f"Content contains unsafe pattern: {pattern}"
                )

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

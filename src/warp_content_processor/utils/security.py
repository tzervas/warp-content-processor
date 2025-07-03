"""
Security utilities for input validation and sanitization.
Prevents injection attacks and validates content integrity.
"""

import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Union

import yaml

# Maximum content size (10MB)
MAX_CONTENT_SIZE = 10 * 1024 * 1024

# Maximum nesting depth for YAML/JSON structures
MAX_NESTING_DEPTH = 20

# Maximum number of items in arrays/lists
MAX_ARRAY_LENGTH = 1000

# Allowed file extensions
ALLOWED_EXTENSIONS = {".yaml", ".yml", ".md", ".txt", ".json"}

# Dangerous patterns that should be rejected
DANGEROUS_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # Script tags
    r"javascript:",  # JavaScript URLs
    r"data:.*base64",  # Base64 data URLs
    r"vbscript:",  # VBScript URLs
    r"file://",  # File URLs
    r"\\x[0-9a-fA-F]{2}",  # Hex-encoded characters
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",  # Control characters
    r"(?i)eval\s*\(",  # Eval calls
    r"(?i)exec\s*\(",  # Exec calls
    r"(?i)system\s*\(",  # System calls
    r"(?i)popen\s*\(",  # Process calls
    r"(?i)subprocess",  # Subprocess module
    r"(?i)import\s+os",  # OS imports
    r"(?i)__import__",  # Dynamic imports
]

# Patterns for command injection
COMMAND_INJECTION_PATTERNS = [
    r"[;&|`$(){}<>]",  # Shell metacharacters
    r"\\[rntabfv]",  # Escape sequences
    r"\.\./+",  # Directory traversal
    r"~[/\\]",  # Home directory access
    r"/etc/",  # System directories
    r"/proc/",  # Process directories
    r"/dev/",  # Device directories
    r"\\\\",  # UNC paths (Windows)
]


class SecurityValidationError(Exception):
    """Raised when content fails security validation."""

    pass


class ContentSanitizer:
    """Sanitizes and validates input content for security."""

    @staticmethod
    def validate_file_path(file_path: Union[str, Path]) -> Path:
        """
        Validate and sanitize file paths.

        Args:
            file_path: Path to validate

        Returns:
            Path: Validated path object

        Raises:
            SecurityValidationError: If path is invalid or dangerous
        """
        try:
            path = Path(file_path).resolve()
        except (OSError, ValueError) as e:
            raise SecurityValidationError(f"Invalid file path: {e}")

        # Check file extension
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise SecurityValidationError(f"File extension {path.suffix} not allowed")

        # Check for directory traversal
        if ".." in path.parts:
            raise SecurityValidationError("Directory traversal not allowed")

        # Check file size
        try:
            if path.exists() and path.stat().st_size > MAX_CONTENT_SIZE:
                raise SecurityValidationError(
                    f"File size exceeds {MAX_CONTENT_SIZE} bytes"
                )
        except OSError:
            pass  # File might not exist yet

        return path

    @staticmethod
    def sanitize_string(content: str, max_length: int = 100000) -> str:
        """
        Sanitize string content.

        Args:
            content: String to sanitize
            max_length: Maximum allowed length

        Returns:
            str: Sanitized string

        Raises:
            SecurityValidationError: If content is dangerous
        """
        if not isinstance(content, str):
            raise SecurityValidationError("Content must be a string")

        if len(content) > max_length:
            raise SecurityValidationError(
                f"Content exceeds maximum length of {max_length}"
            )

        # Normalize Unicode characters first
        content = unicodedata.normalize("NFKC", content)

        # Remove null bytes and other control characters
        content = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", content)

        # Check for dangerous patterns (after cleaning)
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                raise SecurityValidationError(
                    f"Content contains dangerous pattern: {pattern}"
                )

        return content

    @staticmethod
    def validate_command_content(command: str) -> str:
        """
        Validate command content for injection attacks.

        Args:
            command: Command string to validate

        Returns:
            str: Validated command

        Raises:
            SecurityValidationError: If command is dangerous
        """
        command = ContentSanitizer.sanitize_string(command, max_length=10000)

        # Check for command injection patterns
        for pattern in COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, command):
                raise SecurityValidationError(
                    f"Command contains dangerous pattern: {pattern}"
                )

        return command

    @staticmethod
    def validate_yaml_structure(data: Union[Dict, List], depth: int = 0) -> None:
        """
        Validate YAML/JSON structure for security issues.

        Args:
            data: Data structure to validate
            depth: Current nesting depth

        Raises:
            SecurityValidationError: If structure is dangerous
        """
        if depth > MAX_NESTING_DEPTH:
            raise SecurityValidationError(f"Nesting depth exceeds {MAX_NESTING_DEPTH}")

        if isinstance(data, dict):
            if len(data) > MAX_ARRAY_LENGTH:
                raise SecurityValidationError(
                    f"Dictionary size exceeds {MAX_ARRAY_LENGTH}"
                )

            for key, value in data.items():
                if not isinstance(key, str):
                    raise SecurityValidationError("Dictionary keys must be strings")

                ContentSanitizer.sanitize_string(key, max_length=1000)

                if isinstance(value, (dict, list)):
                    ContentSanitizer.validate_yaml_structure(value, depth + 1)
                elif isinstance(value, str):
                    ContentSanitizer.sanitize_string(value, max_length=10000)

        elif isinstance(data, list):
            if len(data) > MAX_ARRAY_LENGTH:
                raise SecurityValidationError(f"Array size exceeds {MAX_ARRAY_LENGTH}")

            for item in data:
                if isinstance(item, (dict, list)):
                    ContentSanitizer.validate_yaml_structure(item, depth + 1)
                elif isinstance(item, str):
                    ContentSanitizer.sanitize_string(item, max_length=10000)

    @staticmethod
    def validate_content(content: str) -> str:
        """
        Comprehensive content validation and sanitization.

        Args:
            content: Raw content to validate

        Returns:
            str: Sanitized content

        Raises:
            SecurityValidationError: If content is dangerous or invalid
        """
        # Basic string sanitization
        content = ContentSanitizer.sanitize_string(content)

        # Try to parse as YAML and validate structure
        try:
            yaml_data = yaml.safe_load(content)
            if yaml_data is not None:
                ContentSanitizer.validate_yaml_structure(yaml_data)
        except yaml.YAMLError:
            # If not valid YAML, treat as plain text and validate
            pass

        return content


class InputValidator:
    """Validates specific input types and formats."""

    @staticmethod
    def validate_workflow_name(name: str) -> str:
        """Validate workflow name format."""
        # Check for dangerous characters before sanitization
        if re.search(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", name):
            raise SecurityValidationError("Workflow name contains control characters")

        name = ContentSanitizer.sanitize_string(name, max_length=100)

        if not re.match(r"^[a-zA-Z0-9\s\-_.]+$", name):
            raise SecurityValidationError("Workflow name contains invalid characters")

        return name.strip()

    @staticmethod
    def validate_tag(tag: str) -> str:
        """Validate tag format."""
        tag = ContentSanitizer.sanitize_string(tag, max_length=50)

        if not re.match(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$", tag):
            raise SecurityValidationError(f"Invalid tag format: {tag}")

        return tag

    @staticmethod
    def validate_shell(shell: str) -> str:
        """Validate shell name."""
        shell = ContentSanitizer.sanitize_string(shell, max_length=20)

        allowed_shells = {"bash", "zsh", "fish", "sh", "cmd", "powershell", "pwsh"}
        if shell.lower() not in allowed_shells:
            raise SecurityValidationError(f"Unsupported shell: {shell}")

        return shell.lower()

    @staticmethod
    def validate_argument_name(name: str) -> str:
        """Validate argument name format."""
        name = ContentSanitizer.sanitize_string(name, max_length=50)

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            raise SecurityValidationError("Argument name must be a valid identifier")

        return name


def secure_yaml_load(content: str) -> Union[Dict, List, None]:
    """
    Safely load YAML content with security validation.

    Args:
        content: YAML content to load

    Returns:
        Parsed YAML data

    Raises:
        SecurityValidationError: If content is dangerous
        yaml.YAMLError: If YAML is invalid
    """
    content = ContentSanitizer.validate_content(content)

    # Use safe_load to prevent arbitrary code execution
    data = yaml.safe_load(content)

    if data is not None:
        ContentSanitizer.validate_yaml_structure(data)

    return data


def secure_yaml_dump(data: Union[Dict, List]) -> str:
    """
    Safely dump data to YAML with validation.

    Args:
        data: Data to dump

    Returns:
        str: YAML string

    Raises:
        SecurityValidationError: If data structure is dangerous
    """
    ContentSanitizer.validate_yaml_structure(data)

    return yaml.safe_dump(
        data, default_flow_style=False, allow_unicode=True, sort_keys=False
    )

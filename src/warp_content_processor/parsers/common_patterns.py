"""Common regex patterns for document parsing."""

import re
from typing import List


class CommonPatterns:
    """Container for common regex patterns used in document parsing."""

    # YAML document separators
    DOCUMENT_SEPARATORS: List[str] = [
        r"^---\s*$",  # Standard YAML document separator
        r"^\+\+\+\s*$",  # Alternative YAML document separator
        r"^===\s*$",  # Alternative separator
    ]

    # Content type detection patterns
    YAML_PATTERNS: List[str] = [
        r"^\s*[\w\-_]+\s*:\s*.*$",  # key: value
        r"^\s*-\s+[\w\-_]+",  # - list items
        r"^\s*[\w\-_]+\s*:\s*\|",  # multiline strings
    ]

    JSON_PATTERNS: List[str] = [
        r'\{\s*"[\w\-_]+"\s*:\s*["\\d\\[\\{]',  # {"key": value
        r'"\s*:\s*\[',  # ": [
    ]

    MARKDOWN_PATTERNS: List[str] = [
        r"^#{1,6}\s+.+$",  # Markdown headers
        r"^```[\w]*\s*$",  # Code block fences
        r"^\*{3,}\s*$",  # Horizontal rules
        r"^-{3,}\s*$",  # Horizontal rules
    ]

    # Compile patterns for efficiency
    COMPILED_DOCUMENT_SEPARATORS = [
        re.compile(pattern, re.MULTILINE) for pattern in DOCUMENT_SEPARATORS
    ]
    COMPILED_YAML_PATTERNS = [
        re.compile(pattern, re.MULTILINE) for pattern in YAML_PATTERNS
    ]
    COMPILED_JSON_PATTERNS = [
        re.compile(pattern, re.MULTILINE) for pattern in JSON_PATTERNS
    ]
    COMPILED_MARKDOWN_PATTERNS = [
        re.compile(pattern, re.MULTILINE) for pattern in MARKDOWN_PATTERNS
    ]

"""
Common patterns and utilities for content parsing.

Following DRY principle: Shared patterns and utilities used across multiple parsers.
Now using intelligent token-based cleaning instead of complex regex patterns.
"""

from typing import List, Optional, Tuple

from .intelligent_cleaner import IntelligentCleaner


class CommonPatterns:
    CONTENT_TYPE_PATTERNS = {
        "workflow": [
            r"command:\s*\S+",
            r"shells?:\s*\[?\s*\w+",
            r"arguments:\s*\[?",
            r"(?:name|id):\s*\S+",
            r"tags:\s*\[?\s*\w+",
        ],
        "prompt": [
            r"description:\s*\S+",
            r"prompt:\s*\S+",
            r"(?:name|id):\s*\S+",
            r"parameters:\s*\[?",
        ],
        "rule": [
            r"condition:\s*\S+",
            r"action:\s*\S+",
            r"(?:name|id):\s*\S+",
            r"tags:\s*\[?\s*\w+",
        ],
        "notebook": [
            r"cells:\s*\[?",
            r"metadata:\s*{?",
            r"kernelspec:\s*{?",
            r"nbformat:\s*\d",
        ],
        "env_var": [
            r"variable:\s*\S+",
            r"value:\s*\S+",
            r"(?:name|id):\s*\S+",
            r"description:\s*\S+",
        ],
    }
    """
    Shared regex patterns and text processing utilities.

    DRY: All parsers use these common patterns instead of duplicating regex.
    KISS: Simple, focused utility functions with clear purposes.
    """

    # Common document separators (in order of preference)
    DOCUMENT_SEPARATORS = [
        r"^---\s*$",  # Standard YAML separator
        r"^\s*---\s*$",  # YAML separator with leading whitespace
        r"^\+\+\+\s*$",  # TOML-style separator
        r"^\s*\+\+\+\s*$",  # TOML with leading whitespace
        r"^={3,}\s*$",  # Equals separator
        r"^-{4,}\s*$",  # Extended dash separator
    ]

    # Content type detection patterns
    CONTENT_TYPE_PATTERNS = {
        "workflow": [
            r"name\s*[：:]\s*.+command\s*[：:]",  # Basic workflow pattern
            # (including unicode colons)
            r"shells\s*[：:]\s*[\[\-]",  # Shell specifications
            r"command\s*[：:]\s*.+",  # Command field present
            r"name\s*[：:].*tags\s*[：:]",  # Name and tags (workflow indicators)
            r"arguments\s*[：:]\s*\n\s*\-",  # Arguments list
        ],
        "prompt": [
            r"name\s*:\s*.+prompt\s*:",  # Basic prompt pattern
            r"prompt\s*:\s*.+\{\{.*\}\}",  # Prompt with template variables
            r"arguments\s*:\s*\-\s*name\s*:",  # Prompt arguments
        ],
        "notebook": [
            r"title\s*:\s*.+description\s*:.+tags\s*:\s*\n\s*\-",  # Notebook metadata
            r"```[^`]*```",  # Code blocks
            r"^#+\s+[^\n]*\n.*```",  # Markdown headers with code
        ],
        "env_var": [
            r"variables\s*:\s*\n\s+\w+\s*:",  # Variables block
            r"scope\s*:\s*(user|system|session)",  # Scope indicator
        ],
        "rule": [
            r"title\s*:\s*.+description\s*:.+guidelines\s*:\s*\-",  # Rule structure
            r"category\s*:\s*\w+",  # Category field
            r"guidelines\s*:\s*\n\s*\-",  # Guidelines list
        ],
    }

    # YAML cleaning patterns
    YAML_FIXES = [
        # Missing spaces after colons
        (r"(\w):([^\s\n])", r"\1: \2"),
        # Missing spaces in lists
        (r"^(\s*)-([^\s])", r"\1- \2"),
        # Tabs to spaces
        (r"\t", "  "),
        # Windows line endings
        (r"\r\n", "\n"),
        # Multiple consecutive blank lines
        (r"\n\s*\n\s*\n+", "\n\n"),
        # Trailing whitespace
        (r"[ \t]+$", ""),
        # Missing quotes around strings with special characters (but not arrays/objects)
        (r':\s*([^"\'\n\[\{]*[\&\*|\>@`][^"\'\n\[\{]*)\s*$', r': "\1"'),
    ]

    @staticmethod
    def normalize_indentation(content: str) -> str:
        """
        Normalize indentation by removing common leading whitespace.

        KISS: Simple algorithm that handles the most common indentation issues.
        """
        if not content.strip():
            return content

        lines = content.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        if not non_empty_lines:
            return content

        # Find minimum indentation
        min_indent = min(len(line) - len(line.lstrip()) for line in non_empty_lines)

        if min_indent == 0:
            return content

        # Remove common indentation
        normalized_lines = []
        for line in lines:
            if line.strip():  # Non-empty line
                normalized_lines.append(
                    line[min_indent:] if len(line) > min_indent else line.lstrip()
                )
            else:  # Empty line
                normalized_lines.append("")

        return "\n".join(normalized_lines)

    @staticmethod
    def extract_key_value_pairs(content: str) -> List[Tuple[str, str]]:
        """
        Extract key-value pairs using basic string splitting.

        Follows KISS principle: Simple splitting on colons for key-value extraction.
        """
        pairs = []

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Try to split on colon
            parts = line.split(":", 1)
            if len(parts) != 2:
                continue

            key = parts[0].strip()
            value = parts[1].strip()

            # Skip empty keys or values
            if not key or not value:
                continue

            pairs.append((key, value))

        return pairs

    @staticmethod
    def clean_yaml_content(content: str) -> str:
        """
        Apply intelligent YAML cleaning.

        DRY: Centralized YAML cleaning used by all YAML parsers.
        """
        if not content:
            return content

        cleaner = IntelligentCleaner()
        cleaned_content, fixes_applied, errors = cleaner.clean_content(content)
        return cleaned_content

    @staticmethod
    def detect_content_type(content: str) -> Tuple[str, float]:
        """
        Detect content type using intelligent token-based analysis.

        Returns:
            Tuple[str, float]: (content_type, confidence_score)
        """
        if not content or not content.strip():
            return "unknown", 0.0

        cleaner = IntelligentCleaner()
        return cleaner.detect_content_type(content)


class MangledContentCleaner:
    """
    Specialized cleaner for heavily mangled content using intelligent
    token-based approach.

    SRP: Single responsibility - clean up mangled text to make it parseable.
    KISS: Use intelligent cleaner instead of complex regex patterns.
    """

    @classmethod
    def clean_mangled_content(cls, content: str) -> str:
        """
        Apply aggressive cleaning to heavily mangled content.

        This uses the intelligent cleaner for more maintainable processing.
        """
        if not content:
            return content

        # Use intelligent cleaner for aggressive cleaning
        cleaner = IntelligentCleaner()
        cleaned_content, fixes_applied, errors = cleaner.clean_content(content)

        return cleaned_content

    @classmethod
    def reconstruct_from_lines(cls, content: str) -> Optional[dict]:
        """
        Attempt to reconstruct structured data from mangled content using
        intelligent parsing.

        This is the most aggressive parsing strategy - use only as a last resort.
        """
        if not content:
            return None

        # Extract key-value pairs using intelligent tokenization
        pairs = CommonPatterns.extract_key_value_pairs(content)
        if not pairs:
            return None

        # Build basic structure
        result = {}
        for key, value in pairs:
            try:
                # Try to parse value as YAML
                import yaml

                parsed_value = yaml.safe_load(value)
                result[key] = parsed_value
            except (yaml.YAMLError, ValueError, TypeError):
                # Fall back to string value
                result[key] = value.strip("\"'")

        return result or None

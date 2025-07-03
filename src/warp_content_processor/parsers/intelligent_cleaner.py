"""
Intelligent content cleaner using token-based parsing for better maintainability.

This replaces regex-heavy approaches with a structured token-based system that can:
- Handle unclosed brackets, braces, and quotes
- Fix common typos and formatting issues
- Recover partial structures intelligently
- Maintain readability and extensibility
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Types of tokens we can encounter in content."""

    KEY = "key"
    COLON = "colon"
    VALUE = "value"
    LIST_START = "list_start"
    LIST_END = "list_end"
    DICT_START = "dict_start"
    DICT_END = "dict_end"
    COMMA = "comma"
    DASH = "dash"
    QUOTE = "quote"
    NEWLINE = "newline"
    WHITESPACE = "whitespace"
    UNKNOWN = "unknown"


@dataclass
class Token:
    """A single token in the content."""

    type: TokenType
    value: str
    line: int
    column: int
    original_value: Optional[str] = None  # Store original for error reporting


class ContentTokenizer:
    """
    Tokenizes content into meaningful units for intelligent processing.

    Much more maintainable than regex patterns - each token type has clear rules.
    """

    def __init__(self) -> None:
        """Initialize the content tokenizer."""
        self.tokens: List[Token] = []
        self.current_line: int = 1
        self.current_column: int = 1

    def tokenize(self, content: str) -> List[Token]:
        """Convert content into tokens for intelligent processing."""
        self.tokens = []
        self.current_line = 1
        self.current_column = 1

        i = 0
        while i < len(content):
            char = content[i]

            # Handle newlines
            if char == "\n":
                self._add_token(TokenType.NEWLINE, char)
                self.current_line += 1
                self.current_column = 1
                i += 1
                continue

            # Handle whitespace
            if char.isspace():
                ws_start = i
                while i < len(content) and content[i].isspace() and content[i] != "\n":
                    i += 1
                self._add_token(TokenType.WHITESPACE, content[ws_start:i])
                continue

            # Handle structural characters
            if char == ":" or char == "：":  # Include unicode colon
                self._add_token(TokenType.COLON, char, ":")
                i += 1
                continue

            if char == "[":
                self._add_token(TokenType.LIST_START, char)
                i += 1
                continue

            if char == "]":
                self._add_token(TokenType.LIST_END, char)
                i += 1
                continue

            if char == "{":
                self._add_token(TokenType.DICT_START, char)
                i += 1
                continue

            if char == "}":
                self._add_token(TokenType.DICT_END, char)
                i += 1
                continue

            if char == "," or char == "，":  # Include unicode comma
                self._add_token(TokenType.COMMA, char, ",")
                i += 1
                continue

            if char == "-":
                self._add_token(TokenType.DASH, char)
                i += 1
                continue

            if char in ['"', "'", "”", "“", "‘", "’"]:  # Various quote types
                self._add_token(TokenType.QUOTE, char, '"')
                i += 1
                continue

            # Handle text content (keys, values, etc.)
            text_start = i
            while i < len(content) and not self._is_structural_char(content[i]):
                i += 1

            text = content[text_start:i].strip()
            if text:
                # Determine if this is likely a key or value based on context
                token_type = self._determine_text_type(text)
                self._add_token(token_type, text)

        return self.tokens

    def _add_token(
        self, token_type: TokenType, value: str, normalized_value: str = None
    ):
        """Add a token to the list."""
        token = Token(
            type=token_type,
            value=normalized_value or value,
            line=self.current_line,
            column=self.current_column,
            original_value=value if normalized_value else None,
        )
        self.tokens.append(token)
        self.current_column += len(value)

    def _is_structural_char(self, char: str) -> bool:
        """Check if character has structural meaning in YAML/JSON."""
        return char in ":\n[]{},-\"':：，“”‘’" or char.isspace()

    def _determine_text_type(self, text: str) -> TokenType:
        """Determine if text is likely a key, value, or unknown."""

        # Enhanced heuristics to handle Unicode and various key patterns

        # Check for common key patterns
        common_keys = [
            "name",
            "command",
            "shells",
            "arguments",
            "tags",
            "description",
            "prompt",
            "template",
            "variables",
            "title",
            "scope",
            "category",
            "guidelines",
            "rules",
            "env",
            "cells",
            "default_value",
        ]

        if text.lower() in common_keys:
            return TokenType.KEY

        # Detect keys with Unicode or similar patterns
        if (
            text.isidentifier()
            or "_" in text
            or "-" in text
            or self.is_unicode_key(text)
        ):
            return TokenType.KEY

        # For short text that could be a key, assume it's a key
        if len(text) <= 20 and all(char not in text for char in ' "()[]{}'):
            return TokenType.KEY

        return TokenType.VALUE

    def is_unicode_key(self, text: str) -> bool:
        """Check if a token is likely a key with Unicode content."""
        # Include logic to detect keys that might be in different languages
        return any(
            ord(char) > 127 for char in text.strip().replace("_", "").replace("-", "")
        )


class StructureRecovery:
    """Recovers structure from tokenized content."""

    def __init__(self) -> None:
        self.errors: List[str] = []
        self.fixes_applied: List[str] = []

    def recover_structures(self, tokens: List[Token]) -> List[Token]:
        """Apply intelligent recovery to fix structural issues."""
        self.errors = []
        self.fixes_applied = []

        # Apply recovery strategies in order
        tokens = self._fix_unclosed_structures(tokens)
        tokens = self._fix_missing_commas(tokens)
        tokens = self._fix_malformed_lists(tokens)
        tokens = self._fix_key_value_spacing(tokens)
        tokens = self._clean_incomplete_tokens(tokens)

        return tokens

    def _fix_unclosed_structures(self, tokens: List[Token]) -> List[Token]:
        """Fix unclosed brackets, braces, and quotes by removing problematic lines."""
        fixed_tokens = []

        # Group tokens by line to analyze line-by-line
        lines: Dict[int, List[Token]] = {}
        for token in tokens:
            if token.line not in lines:
                lines[token.line] = []
            lines[token.line].append(token)

        # Process each line to check for unclosed structures
        for line_num in sorted(lines.keys()):
            line_tokens = lines[line_num]

            # Check if line has unclosed structures
            if self._line_has_unclosed_structures(line_tokens):
                # Skip this entire line
                self._record_fix(f"Removed line {line_num} with unclosed structures")
                continue

            # Add tokens from valid lines
            fixed_tokens.extend(line_tokens)

        return fixed_tokens

    def _line_has_unclosed_structures(self, line_tokens: List[Token]) -> bool:
        """Determine if a line of tokens has unclosed structures (brackets/braces)."""
        stack = []
        """Check if a line has unclosed brackets or braces."""
        stack = []

        for token in line_tokens:
            if token.type == TokenType.LIST_START:
                stack.append("list")
            elif token.type == TokenType.DICT_START:
                stack.append("dict")
            elif token.type == TokenType.LIST_END:
                if stack and stack[-1] == "list":
                    stack.pop()
                else:
                    return True  # Orphaned closing bracket
            elif token.type == TokenType.DICT_END:
                if stack and stack[-1] == "dict":
                    stack.pop()
                else:
                    return True  # Orphaned closing brace

        # If stack is not empty, we have unclosed structures
        return len(stack) > 0

    def _fix_missing_commas(self, tokens: List[Token]) -> List[Token]:
        """Add missing commas in lists and objects."""
        fixed_tokens = []

        for i, token in enumerate(tokens):
            fixed_tokens.append(token)

            # Look for value followed by value in list/dict context
            if (
                token.type == TokenType.VALUE
                and i + 1 < len(tokens)
                and tokens[i + 1].type == TokenType.VALUE
            ):
                # Add missing comma
                fixed_tokens.append(
                    Token(TokenType.COMMA, ",", token.line, token.column)
                )
                self._record_fix(
                    f"Added missing comma after value at line {token.line}"
                )

        return fixed_tokens

    def _fix_malformed_lists(self, tokens: List[Token]) -> List[Token]:
        # TODO: Implement list malformation fixes
        return tokens

    def _fix_key_value_spacing(self, tokens: List[Token]) -> List[Token]:
        """Ensure proper spacing around colons in key-value pairs."""
        fixed_tokens = []

        for i, token in enumerate(tokens):
            if token.type == TokenType.COLON:
                # Ensure space after colon if missing
                if (
                    i + 1 < len(tokens)
                    and tokens[i + 1].type != TokenType.WHITESPACE
                    and tokens[i + 1].type != TokenType.NEWLINE
                ):
                    fixed_tokens.append(token)
                    fixed_tokens.append(
                        Token(TokenType.WHITESPACE, " ", token.line, token.column)
                    )
                    self._record_fix(f"Added space after colon at line {token.line}")
                else:
                    fixed_tokens.append(token)
            else:
                fixed_tokens.append(token)

        return fixed_tokens

    def _clean_incomplete_tokens(self, tokens: List[Token]) -> List[Token]:
        """Remove or fix incomplete/broken tokens."""
        cleaned_tokens = []

        for token in tokens:
            # Skip tokens that are clearly broken
            if token.type == TokenType.UNKNOWN and len(token.value.strip()) == 0:
                self._record_fix(f"Removed empty unknown token at line {token.line}")
                continue

            # Fix obvious typos in common keywords
            if token.type == TokenType.KEY:
                fixed_value = self._fix_common_typos(token.value)
                if fixed_value != token.value:
                    token.value = fixed_value
                    old_val = token.original_value or token.value
                    self._record_fix(
                        f"Fixed typo: '{old_val}' -> '{fixed_value}' "
                        f"at line {token.line}"
                    )

            cleaned_tokens.append(token)

        return cleaned_tokens

    def _needs_quoting(self, value: str) -> bool:
        """Check if a value needs to be quoted."""
        special_chars = set("[]{}:,\n\r\t\"'")
        return any(char in special_chars for char in value)

    def _fix_common_typos(self, key: str) -> str:
        """Fix common typos in YAML keys."""
        typo_fixes = {
            "nmae": "name",
            "comand": "command",
            "commnd": "command",
            "descripion": "description",
            "descriptio": "description",
            "aruments": "arguments",
            "argments": "arguments",
        }
        return typo_fixes.get(key.lower(), key)

    def _record_fix(self, message: str) -> None:
        """Record a fix that was applied."""
        self.fixes_applied.append(message)


class IntelligentCleaner:
    """
    Main intelligent cleaner that orchestrates tokenization and recovery.

    This replaces the regex-heavy approach with a maintainable, extensible system.
    """

    def __init__(self) -> None:
        self.tokenizer = ContentTokenizer()
        self.recovery = StructureRecovery()

    def clean_content(self, content: str) -> Tuple[str, List[str], List[str]]:
        """Clean content intelligently. Returns cleaned content, fixes, and errors found."""
        if not content or not content.strip():
            return content, [], []
        """
        Clean content intelligently.

        Returns:
            Tuple of (cleaned_content, fixes_applied, errors_found)
        """
        if not content or not content.strip():
            return content, [], []

        # Step 1: Tokenize the content
        tokens = self.tokenizer.tokenize(content)

        # Step 2: Apply intelligent recovery
        recovered_tokens = self.recovery.recover_structures(tokens)

        # Step 3: Reconstruct clean content
        cleaned_content = self._reconstruct_content(recovered_tokens)

        return cleaned_content, self.recovery.fixes_applied, self.recovery.errors

    def _reconstruct_content(self, tokens: List[Token]) -> str:
        """Reconstruct content from tokens."""
        result = []

        for token in tokens:
            result.append(token.value)

        return "".join(result)

    def extract_key_value_pairs(self, content: str) -> List[Tuple[str, str]]:
        """Extract key-value pairs from content using token-based analysis."""
        """Extract key-value pairs using intelligent tokenization."""
        tokens = self.tokenizer.tokenize(content)
        pairs: List[Tuple[str, str]] = []

        # First check if content is likely to contain valid YAML/structured data
        has_colon = any(token.type == TokenType.COLON for token in tokens)
        if not has_colon:
            return pairs  # No colons = no key-value pairs

        i = 0
        while i < len(tokens):
            # Look for key : value pattern
            if (
                i + 2 < len(tokens)
                and tokens[i].type == TokenType.KEY
                and tokens[i + 1].type == TokenType.COLON
            ):
                key = tokens[i].value

                # Find the value (skip whitespace)
                j = i + 2
                while j < len(tokens) and tokens[j].type == TokenType.WHITESPACE:
                    j += 1

                if j < len(tokens) and tokens[j].type == TokenType.VALUE:
                    value = tokens[j].value
                    # Only include pairs that look like valid YAML keys
                    if self._is_valid_yaml_key(key):
                        pairs.append((key, value))
                    i = j + 1
                else:
                    i += 1
            else:
                i += 1

        return pairs

    def _is_valid_yaml_key(self, key: str) -> bool:
        """Check if a key looks like a valid YAML key."""
        if not key or len(key.strip()) == 0:
            return False

        # Keys should be reasonable length and contain valid characters
        if len(key) > 50:  # Unreasonably long
            return False

        # Should contain letters or underscores
        if not any(c.isalpha() or c == "_" for c in key):
            return False

        # Common YAML key patterns
        common_keys = {
            "name",
            "description",
            "command",
            "tags",
            "arguments",
            "shells",
            "prompt",
            "template",
            "variables",
            "title",
            "scope",
            "category",
            "guidelines",
            "rules",
            "env",
            "cells",
        }

        return (
            key.lower() in common_keys
            or key.replace("_", "").replace("-", "").isalnum()
        )

    def detect_content_type(self, content: str) -> Tuple[str, float]:
        """Detect content type using token-based analysis."""
        tokens = self.tokenizer.tokenize(content)
        indicators: Dict[str, int] = {
            "workflow": 0,
            "prompt": 0,
            "notebook": 0,
            "env_var": 0,
            "rule": 0,
        }
        """Detect content type using token-based analysis."""
        tokens = self.tokenizer.tokenize(content)
        indicators: Dict[str, int] = {
            "workflow": 0,
            "prompt": 0,
            "notebook": 0,
            "env_var": 0,
            "rule": 0,
        }

        # Look for key patterns and also check value content
        for _i, token in enumerate(tokens):
            if token.type == TokenType.KEY:
                key = token.value.lower()

                # Workflow indicators
                if key in [
                    "name",
                    "command",
                    "shells",
                    "arguments",
                    "tags",
                    "description",
                ]:
                    indicators["workflow"] += 1

                # Prompt indicators
                if key in ["prompt", "template", "variables"]:
                    indicators["prompt"] += 1

                # Notebook indicators
                if key in ["title", "description", "tags", "cells"]:
                    indicators["notebook"] += 1

                # Environment variable indicators
                if key in ["variables", "scope", "env"]:
                    indicators["env_var"] += 1

                # Rule indicators
                if key in ["guidelines", "category", "rules"]:
                    indicators["rule"] += 1

            # Also look for workflow indicators in values
            elif token.type == TokenType.VALUE:
                value = token.value.lower()

                # Check for command-like content
                if any(cmd in value for cmd in ["echo", "ls", "bash", "sh", "git"]):
                    indicators["workflow"] += 1

                # Check for shell names
                if any(shell in value for shell in ["bash", "zsh", "fish", "sh"]):
                    indicators["workflow"] += 1

        # Find the type with the highest score
        if not any(indicators.values()):
            return "unknown", 0.0

        best_type = max(indicators.items(), key=lambda x: x[1])
        confidence = float(best_type[1]) / max(
            1, len([t for t in tokens if t.type == TokenType.KEY])
        )

        return best_type[0], min(confidence, 1.0)

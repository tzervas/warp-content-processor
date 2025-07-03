"""
Robust parser for handling severely mangled content.

Implements various strategies for extracting structured data from malformed content.
"""

import re

import yaml

from .base import ParseResult, SimpleParser


class RobustParser(SimpleParser):
    FALLBACK_STRATEGIES = [
        "standard_yaml",
        "cleaned_yaml",
        "mangled_yaml",
        "reconstructed_yaml",
    ]
    """
    Parser that can handle severely mangled content through multiple strategies.
    """

    @property
    def parser_name(self) -> str:
        """Name of this parser for logging and debugging."""
        return "robust_yaml"

    def __init__(self):
        super().__init__()
        self.stats = {
            "total_attempts": 0,
            "successful_parses": 0,
            "strategy_successes": dict.fromkeys(self.FALLBACK_STRATEGIES, 0),
        }
        self.strategies = [
            self._parse_standard,
            self._parse_with_cleaning,
            self._parse_aggressively,
            self._extract_key_value_pairs,
        ]

    def get_stats(self) -> dict:
        """Get parsing statistics."""
        return self.stats.copy()

    def attempt_parse(self, content: str) -> ParseResult:
        """Parse content using progressively more aggressive strategies.

        Interface method for strategy-style usage.
        """
        return self.parse(content)

    def parse(self, content: str) -> ParseResult:
        """Parse content using progressively more aggressive strategies."""
        self.stats["total_attempts"] += 1

        for strategy_name, strategy in zip(self.FALLBACK_STRATEGIES, self.strategies):
            try:
                result = strategy(content)
                if result.success:
                    self.stats["successful_parses"] += 1
                    self.stats["strategy_successes"][strategy_name] += 1
                    return result
            except Exception:  # nosec B112 - Intentional strategy fallback
                continue

        return ParseResult.failure_result("All parsing strategies failed", content)

    def _parse_standard(self, content: str) -> ParseResult:
        """Try standard YAML parsing first."""
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict) and data:
                return ParseResult.success_result(data, content)
        except Exception:  # nosec B110 - Graceful fallback with proper error result
            pass
        return ParseResult.failure_result("Standard parsing failed", content)

    def _parse_with_cleaning(self, content: str) -> ParseResult:
        """Parse with basic cleaning applied."""
        try:
            # Replace Unicode punctuation
            cleaned = content.replace("\uff1a", ":").replace("\uff0c", ",")
            # Normalize whitespace
            cleaned = re.sub(r"\s+:", ":", cleaned)
            cleaned = re.sub(r":\s*", ": ", cleaned)

            data = yaml.safe_load(cleaned)
            if isinstance(data, dict) and data:
                return ParseResult.success_result(data, content)
        except Exception:  # nosec B110 - Graceful fallback with proper error result
            pass
        return ParseResult.failure_result("Cleaned parsing failed", content)

    def _parse_aggressively(self, content: str) -> ParseResult:
        """Parse with aggressive cleaning and normalization."""
        try:
            # Normalize line endings and indentation
            lines = []
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Fix common formatting issues
                    line = re.sub(
                        r"[\uff1a:](?=\S)", ": ", line
                    )  # Add space after colon
                    line = re.sub(r"\s*,\s*", ", ", line)  # Normalize comma spacing
                    line = re.sub(r"&+", "&&", line)  # Fix repeated ampersands
                    lines.append(line)

            cleaned = "\n".join(lines)
            data = yaml.safe_load(cleaned)
            if isinstance(data, dict) and data:
                return ParseResult.success_result(data, content)
        except Exception:  # nosec B110 - Graceful fallback with proper error result
            pass
        return ParseResult.failure_result("Aggressive parsing failed", content)

    def _extract_key_value_pairs(self, content: str) -> ParseResult:
        """Extract key-value pairs as last resort."""
        try:
            result = {}
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Try to split on colon (including Unicode variants)
                parts = re.split(r"[\uff1a:]", line, maxsplit=1)
                if len(parts) != 2:
                    continue

                key = parts[0].strip().lower()
                value = parts[1].strip()

                # Basic key validation
                if not key or key.startswith("#") or len(key) > 50:
                    continue
                if not (key.isidentifier() or "_" in key or "-" in key):
                    continue

                # Try to parse value as YAML
                try:
                    if value.startswith("[") or value.startswith("{"):
                        parsed = yaml.safe_load(value)
                        if parsed is not None:
                            result[key] = parsed
                            continue
                except Exception:  # nosec B110 - Expected YAML parsing failure
                    pass

                # Fall back to string value
                result[key] = value.strip("\"'")

            if result:
                return ParseResult.success_result(result, content)
        except Exception:  # nosec B110 - Graceful fallback with proper error result
            pass
        return ParseResult.failure_result("Key-value extraction failed", content)

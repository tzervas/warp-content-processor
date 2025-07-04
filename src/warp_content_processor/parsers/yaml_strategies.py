"""YAML parsing strategies for robust content extraction."""

from typing import Any, Dict, Optional

import yaml

from .base import ErrorTolerantParser, ParseResult, ParsingStrategy


class StandardYAMLStrategy(ParsingStrategy):
    """Standard YAML parsing strategy."""

    def attempt_parse(self, content: str) -> ParseResult:
        """Attempt to parse content using standard YAML parser."""
        try:
            data = yaml.safe_load(content)
            return ParseResult.success_result(data, content)
        except yaml.YAMLError as e:
            return ParseResult.failure_result(f"YAML parsing failed: {str(e)}", content)

    @property
    def strategy_name(self) -> str:
        return "standard_yaml"


class TolerateYAMLStrategy(ParsingStrategy):
    """More tolerant YAML parsing strategy."""

    def attempt_parse(self, content: str) -> ParseResult:
        """Attempt to parse content with more tolerant YAML parsing."""
        try:
            # Try with allow_duplicate_keys and other tolerant options
            data = yaml.load(content, Loader=yaml.SafeLoader)
            return ParseResult.success_result(data, content)
        except yaml.YAMLError as e:
            return ParseResult.failure_result(
                f"Tolerant YAML parsing failed: {str(e)}", content
            )

    @property
    def strategy_name(self) -> str:
        return "tolerant_yaml"


def create_yaml_parser() -> ErrorTolerantParser:
    """Create a YAML parser with multiple fallback strategies."""
    strategies = [
        StandardYAMLStrategy(),
        TolerateYAMLStrategy(),
    ]
    return ErrorTolerantParser(strategies)

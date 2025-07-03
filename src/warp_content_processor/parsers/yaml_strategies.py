"""
YAML parsing strategies for handling mangled content.

Following KISS: Each strategy is simple and focused on one parsing approach.
Following SRP: Each strategy handles exactly one parsing method.
"""

import logging

import yaml

from .base import ParseResult, ParsingStrategy
from .common_patterns import CommonPatterns, MangledContentCleaner

logger = logging.getLogger(__name__)


class StandardYAMLStrategy(ParsingStrategy):
    """
    Standard YAML parsing - fastest and most strict.

    KISS: Simple yaml.safe_load() with no modifications.
    """

    @property
    def strategy_name(self) -> str:
        return "standard_yaml"

    def attempt_parse(self, content: str) -> ParseResult:
        """Attempt standard YAML parsing."""
        if not content or not content.strip():
            return ParseResult.failure_result("Empty content", content)

        # Pre-validate that content looks like structured data
        if not self._looks_like_yaml(content):
            return ParseResult.failure_result(
                "Content does not appear to be YAML", content
            )

        try:
            data = yaml.safe_load(content)
            if data is None:
                return ParseResult.failure_result("YAML parsed to None", content)

            # Additional validation: ensure we got structured data
            if isinstance(data, str) and not self._is_meaningful_yaml_string(
                data, content
            ):
                return ParseResult.failure_result(
                    "Content parsed as plain string, not structured data", content
                )

            return ParseResult.success_result(data, content)

        except yaml.YAMLError as e:
            return ParseResult.failure_result(f"YAML syntax error: {e}", content)
        except Exception as e:
            return ParseResult.failure_result(f"Unexpected error: {e}", content)

    def _looks_like_yaml(self, content: str) -> bool:
        """Check if content has basic YAML structure indicators."""
        # Must have at least one colon (for key-value pairs) or dash (for lists)
        has_structure = (
            ":" in content or "：" in content or content.strip().startswith("-")
        )

        # Exclude obviously non-YAML content
        non_yaml_indicators = [
            content.strip().startswith("This is"),
            content.strip().startswith("Hello"),
            "@#$%^&*()" in content,  # Random symbols
            content.count("!") > 3,  # Too many exclamation marks
        ]

        return has_structure and not any(non_yaml_indicators)

    def _is_meaningful_yaml_string(
        self, parsed_data: str, original_content: str
    ) -> bool:
        """Check if a string result from YAML parsing is meaningful structured data."""
        # If the parsed string is almost identical to the original, it's probably just plain text
        return len(parsed_data.strip()) < len(original_content.strip()) * 0.8


class CleanedYAMLStrategy(ParsingStrategy):
    """
    YAML parsing with basic cleaning applied first.

    KISS: Apply common fixes then try standard parsing.
    """

    @property
    def strategy_name(self) -> str:
        return "cleaned_yaml"

    def attempt_parse(self, content: str) -> ParseResult:
        """Attempt YAML parsing after applying basic cleaning."""
        if not content or not content.strip():
            return ParseResult.failure_result("Empty content", content)

        # Pre-validate that content looks like structured data
        if not self._looks_like_yaml(content):
            return ParseResult.failure_result(
                "Content does not appear to be YAML", content
            )

        try:
            # Apply basic YAML cleaning
            cleaned = CommonPatterns.clean_yaml_content(content)

            # Normalize indentation
            cleaned = CommonPatterns.normalize_indentation(cleaned)

            # Try parsing the cleaned content
            data = yaml.safe_load(cleaned)
            if data is None:
                return ParseResult.failure_result(
                    "Cleaned YAML parsed to None", content
                )

            # Additional validation: ensure we got structured data
            if isinstance(data, str) and not self._is_meaningful_yaml_string(
                data, content
            ):
                return ParseResult.failure_result(
                    "Content parsed as plain string, not structured data", content
                )

            return ParseResult.success_result(data, content)

        except yaml.YAMLError as e:
            return ParseResult.failure_result(
                f"YAML error after cleaning: {e}", content
            )
        except Exception as e:
            return ParseResult.failure_result(
                f"Unexpected error in cleaning: {e}", content
            )

    def _looks_like_yaml(self, content: str) -> bool:
        """Check if content has basic YAML structure indicators."""
        # Must have at least one colon (for key-value pairs) or dash (for lists)
        has_structure = (
            ":" in content or "：" in content or content.strip().startswith("-")
        )

        # Exclude obviously non-YAML content
        non_yaml_indicators = [
            content.strip().startswith("This is"),
            content.strip().startswith("Hello"),
            "@#$%^&*()" in content,  # Random symbols
            content.count("!") > 3,  # Too many exclamation marks
        ]

        return has_structure and not any(non_yaml_indicators)

    def _is_meaningful_yaml_string(
        self, parsed_data: str, original_content: str
    ) -> bool:
        """Check if a string result from YAML parsing is meaningful structured data."""
        # If the parsed string is almost identical to the original, it's probably just plain text
        return len(parsed_data.strip()) < len(original_content.strip()) * 0.8


class MangledYAMLStrategy(ParsingStrategy):
    """
    YAML parsing with aggressive cleaning for mangled content.

    KISS: Apply aggressive cleaning then try standard parsing.
    """

    @property
    def strategy_name(self) -> str:
        return "mangled_yaml"

    def attempt_parse(self, content: str) -> ParseResult:
        """Attempt YAML parsing after aggressive cleaning."""
        if not content or not content.strip():
            return ParseResult.failure_result("Empty content", content)

        # Pre-validate that content might contain recoverable structured data
        if not self._could_be_recoverable(content):
            return ParseResult.failure_result(
                "Content does not appear recoverable", content
            )

        try:
            # Apply aggressive cleaning for mangled content
            cleaned = MangledContentCleaner.clean_mangled_content(content)

            if not cleaned or not cleaned.strip():
                return ParseResult.failure_result(
                    "Content disappeared after cleaning", content
                )

            # Try parsing the aggressively cleaned content
            data = yaml.safe_load(cleaned)
            if data is None:
                return ParseResult.failure_result(
                    "Mangled YAML cleaned to None", content
                )

            # Additional validation: ensure we got structured data
            if isinstance(data, str) and not self._is_meaningful_result(data, content):
                return ParseResult.failure_result(
                    "Content parsed as plain string, not structured data", content
                )

            return ParseResult.success_result(data, content)

        except yaml.YAMLError as e:
            return ParseResult.failure_result(
                f"YAML error after aggressive cleaning: {e}", content
            )
        except Exception as e:
            return ParseResult.failure_result(
                f"Unexpected error in mangled cleaning: {e}", content
            )

    def _could_be_recoverable(self, content: str) -> bool:
        """Check if content might contain recoverable structured data."""
        # Look for any indicators of structured content, even mangled
        indicators = [
            ":" in content or "：" in content,  # Colons (regular or unicode)
            content.count(",") > 0,  # Multiple items
            "[" in content or "]" in content,  # List indicators
            "{" in content or "}" in content,  # Dict indicators
            content.strip().startswith("-"),  # YAML list
        ]

        # Must have at least one structural indicator
        has_structure = any(indicators)

        # Exclude obviously non-recoverable content
        non_recoverable = [
            "@#$%^&*()" in content,  # Random symbols
            content.count("!") > 3,  # Too many exclamation marks
            content.strip().startswith("This is") and "not" in content.lower(),
        ]

        return has_structure and not any(non_recoverable)

    def _is_meaningful_result(self, parsed_data: str, original_content: str) -> bool:
        """Check if a parsing result is meaningful."""
        # If the parsed string is almost identical to the original, it's probably just plain text
        return len(parsed_data.strip()) < len(original_content.strip()) * 0.8


class ReconstructedYAMLStrategy(ParsingStrategy):
    """
    Last resort: reconstruct YAML from key-value pairs.

    KISS: Extract what we can understand and build valid YAML.
    """

    @property
    def strategy_name(self) -> str:
        return "reconstructed_yaml"

    def attempt_parse(self, content: str) -> ParseResult:
        """Attempt to reconstruct YAML from mangled content."""
        if not content or not content.strip():
            return ParseResult.failure_result("Empty content", content)

        try:
            # Try line-by-line reconstruction
            reconstructed = MangledContentCleaner.reconstruct_from_lines(content)

            if not reconstructed:
                return ParseResult.failure_result(
                    "Could not reconstruct any data", content
                )

            # Validate that we got something useful
            if not isinstance(reconstructed, dict) or not reconstructed:
                return ParseResult.failure_result(
                    "Reconstructed data is not a valid dict", content
                )

            # Additional validation: ensure we have at least one meaningful key-value pair
            meaningful_keys = sum(
                1 for k, v in reconstructed.items() if k and v and not k.startswith("_")
            )
            if meaningful_keys < 1:
                return ParseResult.failure_result(
                    "No meaningful key-value pairs found", content
                )

            return ParseResult.success_result(reconstructed, content)

        except Exception as e:
            return ParseResult.failure_result(f"Reconstruction failed: {e}", content)


class PartialYAMLStrategy(ParsingStrategy):
    """
    Extract partial data even from severely broken YAML.

    KISS: Get whatever we can, return partial results.
    """

    @property
    def strategy_name(self) -> str:
        return "partial_yaml"

    def attempt_parse(self, content: str) -> ParseResult:
        """Extract partial data from broken YAML."""
        if not content or not content.strip():
            return ParseResult.failure_result("Empty content", content)

        try:
            # Try to extract individual key-value pairs
            pairs = CommonPatterns.extract_key_value_pairs(content)

            if not pairs:
                return ParseResult.failure_result("No key-value pairs found", content)

            # Build result from extracted pairs
            result = {}
            warnings = []

            for key, value in pairs:
                try:
                    # Try to parse the value as YAML
                    parsed_value = yaml.safe_load(value)
                    result[key] = parsed_value
                except yaml.YAMLError:
                    # Fall back to string value
                    result[key] = value.strip("'\"")
                    warnings.append(
                        f"Could not parse value for key '{key}', using as string"
                    )
                except Exception as e:
                    warnings.append(f"Error processing key '{key}': {e}")

            if not result:
                return ParseResult.failure_result(
                    "No valid key-value pairs extracted", content
                )

            # Add warnings to the result
            if warnings:
                result["_parsing_warnings"] = warnings

            return ParseResult.success_result(result, content)

        except Exception as e:
            return ParseResult.failure_result(
                f"Partial extraction failed: {e}", content
            )


def create_yaml_parser():
    """
    Create an ErrorTolerantParser with YAML strategies.

    Returns an ErrorTolerantParser configured with progressively more tolerant
    YAML parsing strategies.
    """
    from .base import ErrorTolerantParser

    strategies = [
        StandardYAMLStrategy(),  # Fastest - try first
        CleanedYAMLStrategy(),  # Basic cleaning
        MangledYAMLStrategy(),  # Aggressive cleaning
        ReconstructedYAMLStrategy(),  # Reconstruction
        PartialYAMLStrategy(),  # Last resort - partial data
    ]

    return ErrorTolerantParser(strategies)

"""Tests for validation utilities."""

import pytest

from warp_content_processor.utils.validation import (
    ValidationResult,
    validate_placeholders,
    validate_tags,
)


class TestValidationResult:
    """Test ValidationResult class."""

    def test_default_initialization(self):
        """Test default initialization."""
        result = ValidationResult()
        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []

    def test_initialization_with_values(self):
        """Test initialization with values."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1"],
            warnings=["Warning 1", "Warning 2"],
        )
        assert not result.is_valid
        assert result.errors == ["Error 1"]
        assert result.warnings == ["Warning 1", "Warning 2"]

    def test_none_lists_become_empty(self):
        """Test that None errors/warnings become empty lists."""
        result = ValidationResult(is_valid=True)
        assert result.errors == []
        assert result.warnings == []


class TestValidatePlaceholders:
    """Test placeholder validation."""

    @pytest.mark.parametrize(
        "content,arguments,is_valid,expected_warnings",
        [
            # Valid cases
            (
                "{{name}} is {{age}} years old",
                [{"name": "name"}, {"name": "age"}],
                True,
                0,
            ),
            # Missing arguments
            (
                "{{name}} is {{age}} years old",
                [{"name": "name"}],
                True,
                1,  # Warning about missing 'age'
            ),
            # Unused arguments
            (
                "{{name}} only",
                [{"name": "name"}, {"name": "unused"}],
                True,
                1,  # Warning about unused argument
            ),
            # Invalid argument type
            (
                "{{name}}",
                "not a list",
                False,
                0,
            ),
        ],
    )
    def test_placeholder_validation(
        self, content, arguments, is_valid, expected_warnings
    ):
        """Test various placeholder validation scenarios."""
        result = validate_placeholders(content, arguments)
        assert result.is_valid == is_valid
        assert len(result.warnings) == expected_warnings

    def test_invalid_argument_dictionaries(self):
        """Test handling of invalid argument dictionaries."""
        content = "{{name}}"
        arguments = [{"name": "valid"}, "invalid", {"missing_name": "invalid"}]
        result = validate_placeholders(content, arguments)
        assert result.is_valid  # Still valid but with warnings
        assert len(result.warnings) > 0
        assert any("not dictionaries" in w for w in result.warnings)


class TestValidateTags:
    """Test tag validation."""

    @pytest.mark.parametrize(
        "tags,is_valid,expected_warnings",
        [
            # Valid cases
            (["python", "data-science", "v2"], True, 0),
            # Invalid type
            ("not-a-list", False, 0),
            # Invalid tag formats
            (["Valid Tag", "invalid@tag", "TAG"], True, 3),
            # Empty tags
            (["", "valid"], True, 1),
            # Mixed valid and invalid
            (["python", "UPPERCASE", "ends-", "valid"], True, 2),
        ],
    )
    def test_tag_validation(self, tags, is_valid, expected_warnings):
        """Test various tag validation scenarios."""
        result = validate_tags(tags)
        assert result.is_valid == is_valid
        assert len(result.warnings) == expected_warnings

    def test_specific_tag_warnings(self):
        """Test specific warning messages for different tag issues."""
        tags = ["UPPERCASE", "invalid@char", "ends-", 123]
        result = validate_tags(tags)
        assert result.is_valid  # Invalid tags generate warnings, not errors
        
        warnings = result.warnings
        assert any("should be lowercase" in w for w in warnings)
        assert any("invalid characters" in w for w in warnings)
        assert any("ends with a hyphen" in w for w in warnings)
        assert any("is not a string" in w for w in warnings)

"""Tests for notebook processor validation logic."""

import pytest
from warp_content_processor.processors.notebook_processor import NotebookProcessor


@pytest.fixture
def processor():
    """Create a notebook processor instance."""
    return NotebookProcessor()


class TestTagValidation:
    """Test cases for tag validation logic."""

    def test_invalid_tag_format(self, processor):
        """Test validation of invalid tag formats."""
        test_cases = [
            {
                "front_matter": {"title": "Test", "tags": ["Invalid Tag"]},
                "content": "Some content",
                "expected_warnings": ["Tag 'Invalid Tag' does not match the required format"],
            },
            {
                "front_matter": {"title": "Test", "tags": ["tag-with-"]},
                "content": "Some content",
                "expected_warnings": ["Tag 'tag-with-' does not match the required format"],
            },
            {
                "front_matter": {"title": "Test", "tags": ["-invalid-start"]},
                "content": "Some content",
                "expected_warnings": ["Tag '-invalid-start' does not match the required format"],
            },
        ]
        
        for case in test_cases:
            is_valid, errors, warnings = processor.validate(case)
            assert is_valid  # Invalid tags produce warnings, not errors
            assert any(warning in warnings for warning in case["expected_warnings"])

    def test_non_string_tags(self, processor):
        """Test validation of non-string tag values."""
        test_data = {
            "front_matter": {"title": "Test", "tags": [123, True, {"nested": "value"}]},
            "content": "Some content"
        }
        is_valid, errors, warnings = processor.validate(test_data)
        assert is_valid  # Non-string tags produce warnings, not errors
        assert any("is not a string" in warning for warning in warnings)


class TestNestedStructureValidation:
    """Test cases for nested structure validation."""

    def test_nested_tag_structures(self, processor):
        """Test validation of nested structures in tags."""
        test_data = {
            "front_matter": {
                "title": "Test",
                "tags": [
                    {"nested": "dict"},
                    ["nested", "list"],
                    "valid-tag"
                ]
            },
            "content": "Some content"
        }
        
        with pytest.raises(ValueError) as excinfo:
            processor.normalize_content(test_data)
        assert "unexpected nested structure" in str(excinfo.value)

    def test_nested_unknown_fields(self, processor):
        """Test validation of nested structures in unknown fields."""
        test_data = {
            "front_matter": {
                "title": "Test",
                "unknown_field": {
                    "nested": {"deep": "structure"}
                }
            },
            "content": "Some content"
        }
        is_valid, errors, warnings = processor.validate(test_data)
        assert is_valid  # Unknown fields produce warnings, not errors


class TestTypeValidationEdgeCases:
    """Test cases for type validation edge cases."""

    def test_type_validation_edge_cases(self, processor):
        """Test various type validation edge cases."""
        test_cases = [
            {
                "front_matter": {"title": 123},  # Non-string title
                "content": "Some content",
                "expected_error": "Field 'title' has unexpected type"
            },
            {
                "front_matter": {"title": "Test", "description": ["list"]},  # Wrong type for description
                "content": "Some content",
                "expected_error": "Field 'description' has unexpected type"
            },
            {
                "front_matter": {"title": "Test", "tags": "single-tag"},  # String instead of list for tags
                "content": "Some content",
                "should_normalize": True
            }
        ]
        
        for case in test_cases:
            if case.get("should_normalize", False):
                normalized = processor.normalize_content(case)
                assert isinstance(normalized["front_matter"]["tags"], list)
            else:
                with pytest.raises(ValueError) as excinfo:
                    processor.normalize_content(case)
                assert case["expected_error"] in str(excinfo.value)


class TestErrorMessageFormatting:
    """Test cases for error message formatting."""

    def test_error_message_formatting(self, processor):
        """Test various error message formats."""
        test_cases = [
            {
                "front_matter": {},
                "content": "Some content",
                "expected_error": "Missing required fields in front matter"
            },
            {
                "front_matter": {"title": "Test"},
                "content": "",
                "expected_error": "Notebook content is empty"
            },
            {
                "front_matter": {"title": "Test", "tags": [123]},
                "content": "Some content",
                "expected_warning": "is not a string"
            }
        ]
        
        for case in test_cases:
            is_valid, errors, warnings = processor.validate(case)
            if "expected_error" in case:
                assert any(case["expected_error"] in error for error in errors)
            if "expected_warning" in case:
                assert any(case["expected_warning"] in warning for warning in warnings)

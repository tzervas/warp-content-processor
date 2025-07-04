"""Tests for notebook processor validation."""

import pytest

from warp_content_processor.processors.notebook_processor import NotebookProcessor


class TestValidate:
    """Test validation functionality."""

    @pytest.fixture
    def processor(self):
        """Create a NotebookProcessor instance."""
        return NotebookProcessor()

    @pytest.mark.parametrize(
        "front_matter,expected_valid",
        [
            # Valid front matter cases
            ({"title": "Test Notebook"}, True),
            ({"title": "Test Notebook", "description": "A test notebook"}, True),
            ({"title": "Test Notebook", "tags": ["python", "jupyter"]}, True),
            (
                {"title": "Test Notebook", "description": "A test", "tags": ["python"]},
                True,
            ),
            # Invalid front matter cases
            ({}, False),  # Missing title
            ({"description": "No title"}, False),  # Missing title
            ({"title": 123}, False),  # Non-string title
            ({"title": "Test", "description": 123}, False),  # Non-string description
            ({"title": "Test", "tags": "not-a-list"}, False),  # Non-list tags
            (
                {"title": "Test", "tags": [123, "valid"]},
                True,
            ),  # Invalid tag type generates warning, not error
        ],
    )
    def test_validate_front_matter(self, processor, front_matter, expected_valid):
        """Test front matter validation with various cases."""
        data = {
            "front_matter": front_matter,
            "content": "# Test Content\n\n```python\nprint('hello')\n```",
        }
        is_valid, errors, warnings = processor.validate(data)
        assert is_valid == expected_valid

    @pytest.mark.parametrize(
        "tags,expected_warnings",
        [
            # Valid tags - note: the regex allows numbers at start/end and single chars
            (["python", "jupyter-notebook", "data-science"], 0),
            (["a2", "b2", "test-tag"], 0),  # All valid according to regex
            # Invalid tags that should generate warnings
            (["Invalid Tag", "valid-tag"], 1),  # Space in tag
            (["python", "123invalid"], 0),  # Actually valid according to regex
            (["valid", "tag-", "another"], 1),  # Ends with hyphen
            (["python", "UPPERCASE"], 1),  # Uppercase
            (["special@char"], 1),  # Special character
        ],
    )
    def test_validate_tag_formats(self, processor, tags, expected_warnings):
        """Test tag format validation."""
        data = {
            "front_matter": {"title": "Test", "tags": tags},
            "content": "```python\nprint('hello')\n```",
        }
        is_valid, errors, warnings = processor.validate(data)
        assert is_valid  # Should be valid but may have warnings
        assert len(warnings) == expected_warnings

    def test_validate_missing_data(self, processor):
        """Test validation with missing data fields."""
        # Missing front matter
        data = {"content": "# Test content"}
        is_valid, errors, warnings = processor.validate(data)
        assert not is_valid
        assert any("Missing front matter" in error for error in errors)

        # Missing content
        data = {"front_matter": {"title": "Test"}, "content": ""}
        is_valid, errors, warnings = processor.validate(data)
        assert not is_valid
        assert any("empty" in error.lower() for error in errors)

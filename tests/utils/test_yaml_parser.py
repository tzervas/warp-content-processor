"""Tests for enhanced YAML parsing functionality."""

import pytest

from warp_content_processor.utils.yaml_parser import (
    YAMLParsingResult,
    parse_yaml_enhanced,
    parse_yaml_documents,
)

class TestYAMLParsingResult:
    """Test YAMLParsingResult class functionality."""

    def test_valid_result(self):
        """Test valid parsing result."""
        result = YAMLParsingResult(content={"key": "value"})
        assert result.is_valid
        assert result.content == {"key": "value"}
        assert result.error is None
        assert result.warnings == []
        assert result.line_number is None
        assert result.column is None

    def test_error_result(self):
        """Test error parsing result."""
        result = YAMLParsingResult(error="Test error")
        assert not result.is_valid
        assert result.content is None
        assert result.error == "Test error"

    def test_result_with_warnings(self):
        """Test parsing result with warnings."""
        result = YAMLParsingResult(
            content={"key": "value"},
            warnings=["Warning 1", "Warning 2"]
        )
        assert result.is_valid
        assert len(result.warnings) == 2

    def test_result_with_position(self):
        """Test parsing result with position information."""
        result = YAMLParsingResult(
            error="Test error",
            line_number=10,
            column=5
        )
        assert not result.is_valid
        assert result.line_number == 10
        assert result.column == 5

class TestParseYAMLEnhanced:
    """Test enhanced YAML parsing functionality."""

    @pytest.mark.parametrize(
        "content,expected_valid",
        [
            # Valid YAML
            ("key: value", True),
            ("nested:\n  key: value", True),
            ("list:\n  - item1\n  - item2", True),
            # Invalid YAML
            ("invalid: : value", False),
            ("key: 'unclosed string", False),
            ("[not a dictionary]", False),
            ("", False),
            ("   ", False),
        ]
    )
    def test_basic_parsing(self, content: str, expected_valid: bool):
        """Test basic YAML parsing scenarios."""
        result = parse_yaml_enhanced(content)
        assert result.is_valid == expected_valid

    def test_line_number_in_errors(self):
        """Test that errors include line numbers."""
        content = "valid: true\ninvalid: : value"
        result = parse_yaml_enhanced(content)
        assert not result.is_valid
        assert result.line_number == 2

    def test_warning_generation(self):
        """Test warning generation for suspicious content."""
        content = """
        empty_value: ""
        empty_dict: {}
        """
        result = parse_yaml_enhanced(content)
        assert result.is_valid
        assert len(result.warnings) > 0
        assert any("empty" in w.lower() for w in result.warnings)

class TestParseYAMLDocuments:
    """Test multi-document YAML parsing functionality."""

    def test_single_document(self):
        """Test parsing single document."""
        content = "key: value"
        results = parse_yaml_documents(content)
        assert len(results) == 1
        assert results[0].is_valid
        assert results[0].content == {"key": "value"}

    def test_multiple_documents(self):
        """Test parsing multiple documents."""
        content = """
        ---
        doc1: value1
        ---
        doc2: value2
        ---
        doc3: value3
        """
        results = parse_yaml_documents(content)
        assert len(results) == 3
        assert all(r.is_valid for r in results)
        assert [r.content.get("doc1", r.content.get("doc2", r.content.get("doc3"))) 
                for r in results] == ["value1", "value2", "value3"]

    def test_invalid_documents(self):
        """Test parsing with invalid documents."""
        content = """
        ---
        valid: true
        ---
        invalid: : value
        ---
        also_valid: true
        """
        results = parse_yaml_documents(content)
        assert len(results) >= 2
        assert results[0].is_valid
        assert not results[1].is_valid
        assert results[2].is_valid if len(results) > 2 else True

    def test_empty_documents(self):
        """Test parsing empty documents."""
        content = """
        ---
        ---
        valid: true
        ---
        """
        results = parse_yaml_documents(content)
        assert len(results) > 0
        assert any(not r.is_valid for r in results)  # At least one invalid
        assert any(r.is_valid for r in results)  # At least one valid

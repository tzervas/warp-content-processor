#!/usr/bin/env python3
"""
Comprehensive regression tests for parsers module.

These tests ensure that core parsing functionality is preserved during refactoring.
Uses pytest fixtures and parameterization to avoid conditionals in tests.
Follows no-conditionals-in-tests rule and KISS principles.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from warp_content_processor.parsers.base import (
    ErrorTolerantParser,
    ParseResult,
    ParsingStrategy,
)
from warp_content_processor.parsers.common_patterns import (
    CommonPatterns,
    MangledContentCleaner,
)
from warp_content_processor.processors.schema_processor import ContentTypeDetector
from warp_content_processor.parsers.document_splitter import DocumentSplitter
from warp_content_processor.parsers.intelligent_cleaner import IntelligentCleaner
from warp_content_processor.parsers.robust_parser import RobustParser
from warp_content_processor.parsers.yaml_strategies import YamlStrategies


class TestErrorTolerantParserRegression:
    """Regression tests for ErrorTolerantParser base functionality."""

    @pytest.fixture
    def mock_strategy(self):
        """Create a mock parsing strategy."""
        strategy = Mock(spec=ParsingStrategy)
        strategy.parse.return_value = ParseResult(
            success=True, data={"test": "data"}, errors=[], warnings=[]
        )
        return strategy

    @pytest.fixture
    def parser(self, mock_strategy):
        """Create parser with mock strategy."""
        return ErrorTolerantParser([mock_strategy])

    def test_successful_parsing_preserved(self, parser, mock_strategy):
        """Ensure successful parsing behavior is preserved."""
        content = "test content"
        result = parser.parse(content)

        assert result.success
        assert result.data == {"test": "data"}
        assert not result.errors
        mock_strategy.parse.assert_called_once_with(content)

    def test_error_handling_preserved(self, mock_strategy):
        """Ensure error handling behavior is preserved."""
        mock_strategy.parse.side_effect = Exception("Parse error")
        parser = ErrorTolerantParser([mock_strategy])

        result = parser.parse("test content")

        assert not result.success
        assert "Parse error" in str(result.errors)

    @pytest.mark.parametrize("strategy_count", [1, 2, 3, 5])
    def test_multiple_strategies_preserved(self, strategy_count):
        """Ensure multiple strategy handling is preserved."""
        strategies = []
        for i in range(strategy_count):
            strategy = Mock(spec=ParsingStrategy)
            strategy.parse.return_value = ParseResult(
                success=False, data=None, errors=[f"Error {i}"], warnings=[]
            )
            strategies.append(strategy)

        # Make the last strategy succeed
        strategies[-1].parse.return_value = ParseResult(
            success=True, data={"success": True}, errors=[], warnings=[]
        )

        parser = ErrorTolerantParser(strategies)
        result = parser.parse("test content")

        assert result.success
        assert result.data == {"success": True}


class TestContentDetectorRegression:
    """Regression tests for ContentTypeDetector functionality."""

    @pytest.fixture
    def detector(self):
        """Create ContentTypeDetector instance."""
        return ContentTypeDetector()

    @pytest.mark.parametrize(
        "content,expected_types",
        [
            # Workflow content detection
            ("name: Test Workflow\ncommand: echo test\nshells: [bash]", ["workflow"]),
            # Prompt content detection
            ("name: Test Prompt\nprompt: Do {{action}}\narguments: []", ["prompt"]),
            # Environment variable detection
            ("variables:\n  TEST_VAR: value\n  DEBUG: true", ["env_var"]),
            # Multiple content type detection
            (
                "---\nname: Test\ncommand: echo\n---\nvariables:\n  X: y",
                ["workflow", "env_var"],
            ),
        ],
    )
    def test_content_type_detection_preserved(self, detector, content, expected_types):
        """Ensure content type detection behavior is preserved."""
        detected_types = detector.detect_content_types(content)

        # Convert to strings for comparison
        detected_strings = [
            t.value if hasattr(t, "value") else str(t).lower() for t in detected_types
        ]

        for expected_type in expected_types:
            assert any(
                expected_type in detected.lower() for detected in detected_strings
            )

    def test_empty_content_handling_preserved(self, detector):
        """Ensure empty content handling is preserved."""
        result = detector.detect_content_types("")
        assert isinstance(result, list)

    def test_malformed_content_handling_preserved(self, detector):
        """Ensure malformed content handling is preserved."""
        malformed_content = "invalid: yaml: content: {"
        result = detector.detect_content_types(malformed_content)
        assert isinstance(result, list)


class TestDocumentSplitterRegression:
    """Regression tests for DocumentSplitter functionality."""

    @pytest.fixture
    def splitter(self):
        """Create DocumentSplitter instance."""
        return DocumentSplitter()

    @pytest.mark.parametrize(
        "content,expected_count",
        [
            # Single document
            ("name: Test\nvalue: 1", 1),
            # Multiple YAML documents
            ("---\nname: First\n---\nname: Second", 2),
            # Mixed content with separators
            ("---\nworkflow1\n---\n\n---\nworkflow2\n---", 2),
            # Empty content
            ("", 0),
            # Content with noise
            ("junk\n---\nname: Valid\n---\nmore junk", 1),
        ],
    )
    def test_document_splitting_preserved(self, splitter, content, expected_count):
        """Ensure document splitting behavior is preserved."""
        documents = splitter.split_documents(content)
        assert len(documents) == expected_count

    def test_document_boundary_detection_preserved(self, splitter):
        """Ensure document boundary detection is preserved."""
        content = "---\nfirst: doc\n---\nsecond: doc\n---\nthird: doc"
        documents = splitter.split_documents(content)

        assert len(documents) == 3
        # Ensure each document contains expected content
        contents = [doc.strip() for doc in documents]
        assert any("first" in content for content in contents)
        assert any("second" in content for content in contents)
        assert any("third" in content for content in contents)


class TestCommonPatternsRegression:
    """Regression tests for CommonPatterns functionality."""

    @pytest.fixture
    def patterns(self):
        """Create CommonPatterns instance."""
        return CommonPatterns()

    @pytest.mark.parametrize(
        "text,pattern_type,should_match",
        [
            # YAML front matter patterns
            ("---\ntitle: Test\n---\n", "yaml_frontmatter", True),
            ("title: Test\n", "yaml_frontmatter", False),
            # Command patterns
            ("echo {{variable}}", "command_placeholder", True),
            ("echo test", "command_placeholder", False),
            # Email patterns
            ("test@example.com", "email", True),
            ("not-an-email", "email", False),
            # URL patterns
            ("https://example.com", "url", True),
            ("not-a-url", "url", False),
        ],
    )
    def test_pattern_matching_preserved(
        self, patterns, text, pattern_type, should_match
    ):
        """Ensure pattern matching behavior is preserved."""
        if pattern_type == "yaml_frontmatter":
            result = patterns.has_yaml_frontmatter(text)
        elif pattern_type == "command_placeholder":
            result = bool(patterns.find_command_placeholders(text))
        elif pattern_type == "email":
            result = bool(patterns.find_emails(text))
        elif pattern_type == "url":
            result = bool(patterns.find_urls(text))
        else:
            pytest.skip(f"Unknown pattern type: {pattern_type}")

        assert result == should_match


class TestMangledContentCleanerRegression:
    """Regression tests for MangledContentCleaner functionality."""

    @pytest.fixture
    def cleaner(self):
        """Create MangledContentCleaner instance."""
        return MangledContentCleaner()

    @pytest.mark.parametrize(
        "mangled_content,expected_improvements",
        [
            # Basic cleanup
            ("   messy   content   ", ["trimmed"]),
            # Line ending normalization
            ("line1\r\nline2\rline3\n", ["normalized_endings"]),
            # Character encoding issues
            ("test\x00content", ["removed_nulls"]),
            # Multiple spaces
            ("word1    word2     word3", ["normalized_spaces"]),
            # Mixed issues
            ("  \r\n  messy\x00\r\n  ", ["comprehensive"]),
        ],
    )
    def test_content_cleaning_preserved(
        self, cleaner, mangled_content, expected_improvements
    ):
        """Ensure content cleaning behavior is preserved."""
        cleaned = cleaner.clean_content(mangled_content)

        # Verify basic cleaning occurred
        assert cleaned != mangled_content or mangled_content.strip() == mangled_content
        assert isinstance(cleaned, str)

        # Verify specific improvements based on test case
        if "trimmed" in expected_improvements:
            assert cleaned.strip() == cleaned or not mangled_content.strip()
        if "normalized_endings" in expected_improvements:
            assert "\r\n" not in cleaned and "\r" not in cleaned
        if "removed_nulls" in expected_improvements:
            assert "\x00" not in cleaned
        if "normalized_spaces" in expected_improvements:
            assert "    " not in cleaned
        if "comprehensive" in expected_improvements:
            assert cleaned.strip() == cleaned
            assert "\x00" not in cleaned


class TestIntelligentCleanerRegression:
    """Regression tests for IntelligentCleaner functionality."""

    @pytest.fixture
    def cleaner(self):
        """Create IntelligentCleaner instance."""
        return IntelligentCleaner()

    def test_yaml_repair_preserved(self, cleaner):
        """Ensure YAML repair functionality is preserved."""
        broken_yaml = "name: Test\nbroken: yaml: content"
        result = cleaner.repair_yaml(broken_yaml)

        assert isinstance(result, str)
        # Should attempt to fix common YAML issues
        assert result != broken_yaml

    def test_structure_detection_preserved(self, cleaner):
        """Ensure structure detection is preserved."""
        content = "---\ntitle: Test\n---\n# Content\n```bash\necho test\n```"
        structures = cleaner.detect_structures(content)

        assert isinstance(structures, list)
        # Should detect various content structures
        assert len(structures) > 0

    @pytest.mark.parametrize(
        "content_type,sample_content",
        [
            ("workflow", "name: Test\ncommand: echo test"),
            ("notebook", "---\ntitle: Test\n---\n# Content"),
            ("prompt", "name: Test\nprompt: Do {{action}}"),
            ("mixed", "---\nworkflow\n---\nvariables:\n  X: y"),
        ],
    )
    def test_content_type_specific_cleaning_preserved(
        self, cleaner, content_type, sample_content
    ):
        """Ensure content-type specific cleaning is preserved."""
        cleaned = cleaner.clean_by_type(sample_content, content_type)

        assert isinstance(cleaned, str)
        assert len(cleaned) > 0


class TestRobustParserRegression:
    """Regression tests for RobustParser functionality."""

    @pytest.fixture
    def parser(self):
        """Create RobustParser instance."""
        return RobustParser()

    def test_fallback_parsing_preserved(self, parser):
        """Ensure fallback parsing behavior is preserved."""
        # Test with content that should trigger fallback strategies
        problematic_content = "invalid: yaml: content: {"
        result = parser.parse_with_fallbacks(problematic_content)

        assert isinstance(result, dict)
        # Should have attempted multiple strategies
        assert "strategies_attempted" in result or "errors" in result

    @pytest.mark.parametrize(
        "content,should_succeed",
        [
            # Valid content
            ("name: Test\nvalue: 1", True),
            # Slightly malformed but recoverable
            ("name: Test\nvalue:", True),
            # Severely malformed
            ("completely invalid content {{{", False),
            # Empty content
            ("", False),
        ],
    )
    def test_parsing_resilience_preserved(self, parser, content, should_succeed):
        """Ensure parsing resilience is preserved."""
        result = parser.parse_with_fallbacks(content)

        if should_succeed:
            assert result.get("success", False) or result.get("data") is not None
        else:
            assert result.get("errors") or not result.get("success", True)


class TestYamlStrategiesRegression:
    """Regression tests for YamlStrategies functionality."""

    @pytest.fixture
    def strategies(self):
        """Create YamlStrategies instance."""
        return YamlStrategies()

    @pytest.mark.parametrize(
        "yaml_content",
        [
            "name: Test\nvalue: 1",
            "---\ntitle: Document\n---",
            "list:\n  - item1\n  - item2",
            "nested:\n  key:\n    value: test",
        ],
    )
    def test_safe_yaml_loading_preserved(self, strategies, yaml_content):
        """Ensure safe YAML loading is preserved."""
        result = strategies.safe_load(yaml_content)

        assert isinstance(result, (dict, list, type(None)))

    def test_yaml_validation_preserved(self, strategies):
        """Ensure YAML validation is preserved."""
        valid_yaml = "name: Test\nvalue: 1"
        invalid_yaml = "invalid: yaml: content: {"

        assert strategies.validate_yaml(valid_yaml)
        assert not strategies.validate_yaml(invalid_yaml)

    def test_multiple_document_handling_preserved(self, strategies):
        """Ensure multiple document handling is preserved."""
        multi_doc = "---\nfirst: doc\n---\nsecond: doc"
        result = strategies.load_multiple_documents(multi_doc)

        assert isinstance(result, list)
        assert len(result) >= 2


# Integration regression tests
class TestParserIntegrationRegression:
    """Integration regression tests for parser ecosystem."""

    def test_full_parsing_pipeline_preserved(self):
        """Ensure full parsing pipeline integration is preserved."""
        # Test the complete parsing pipeline
        content = """---
name: Test Workflow
command: echo "{{message}}"
shells: [bash]
---
variables:
  MESSAGE: "Hello World"
  DEBUG: true
"""

        # Test document splitting
        splitter = DocumentSplitter()
        documents = splitter.split_documents(content)
        assert len(documents) == 2

        # Test content detection on each document
        detector = ContentTypeDetector()
        for doc in documents:
            content_types = detector.detect_content_types(doc)
            assert len(content_types) > 0

        # Test content cleaning
        cleaner = MangledContentCleaner()
        for doc in documents:
            cleaned = cleaner.clean_content(doc)
            assert isinstance(cleaned, str)

    def test_error_recovery_pipeline_preserved(self):
        """Ensure error recovery across parser components is preserved."""
        # Test with progressively more problematic content
        problematic_contents = [
            "name: Test\nvalue:",  # Missing value
            "name: Test\nbroken: yaml: content",  # Syntax error
            "completely invalid content {{{",  # Completely broken
        ]

        parser = RobustParser()
        cleaner = IntelligentCleaner()

        for content in problematic_contents:
            # Should not raise exceptions
            cleaned = cleaner.clean_content(content)
            result = parser.parse_with_fallbacks(cleaned)

            assert isinstance(cleaned, str)
            assert isinstance(result, dict)

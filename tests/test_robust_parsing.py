#!/usr/bin/env python3

"""
Test suite for robust mangled content parsing.

Tests the new KISS/SRP/DRY parser infrastructure with extremely mangled content.
"""

import unittest

import pytest

from warp_content_processor.content_type import ContentType
from warp_content_processor.parsers import (
    CommonPatterns,
    ContentDetector,
    DocumentSplitter,
    MangledContentCleaner,
)
from warp_content_processor.parsers.robust_parser import RobustParser
from warp_content_processor.parsers.yaml_strategies import (
    CleanedYAMLStrategy,
    MangledYAMLStrategy,
    StandardYAMLStrategy,
)


class TestContentDetector:
    """Test the simplified ContentDetector."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.detector = ContentDetector()

    def test_simple_workflow_detection(self):
        """Test detection of a simple workflow."""
        content = """
        name: Test Workflow
        command: echo "hello"
        shells:
          - bash
        """

        content_type, confidence = self.detector.detect(content)
        assert content_type == ContentType.WORKFLOW
        assert confidence > 0.3

    def test_mangled_workflow_detection(self):
        """Test detection of mangled workflow content."""
        content = """
        name:Broken Workflow
        command:echo"test"&&ls -la
        shells:bash,zsh
        """

        content_type, confidence = self.detector.detect(content)
        assert content_type == ContentType.WORKFLOW

    def test_confidence_scoring(self):
        """Test that confidence scores work correctly."""
        # Strong workflow indicators
        strong_workflow = """
        name: Strong Workflow
        command: echo test
        shells: [bash]
        arguments:
          - name: input
        """

        # Weak workflow indicators
        weak_workflow = """
        command: echo test
        """

        strong_type, strong_conf = self.detector.detect(strong_workflow)
        weak_type, weak_conf = self.detector.detect(weak_workflow)

        assert strong_conf > weak_conf

    def test_unknown_content(self):
        """Test handling of unknown content types."""
        content = "This is just random text with no structure."

        content_type, confidence = self.detector.detect(content)
        assert content_type == ContentType.UNKNOWN
        assert confidence == 0.0


class TestDocumentSplitter(unittest.TestCase):
    """Test the simplified DocumentSplitter."""

    def setUp(self):
        self.splitter = DocumentSplitter()

    def test_yaml_separator_splitting(self):
        """Test splitting by YAML separators."""
        content = """
        name: First Doc
        value: 1
        ---
        name: Second Doc
        value: 2
        """

        documents = self.splitter.split(content)
        self.assertEqual(len(documents), 2)
        self.assertIn("First Doc", documents[0])
        self.assertIn("Second Doc", documents[1])

    def test_indented_separator_splitting(self):
        """Test splitting with indented separators."""
        content = """
            name: First Doc
            value: 1
            ---
            name: Second Doc
            value: 2
        """

        documents = self.splitter.split(content)
        self.assertEqual(len(documents), 2)

    def test_single_document(self):
        """Test handling of single document."""
        content = """
        name: Only Document
        value: single
        """

        documents = self.splitter.split(content)
        self.assertEqual(len(documents), 1)
        self.assertIn("Only Document", documents[0])

    def test_separator_type_detection(self):
        """Test detection of separator types."""
        yaml_content = "doc1\n---\ndoc2"
        markdown_content = "# Header 1\ncontent\n## Header 2\nmore content"

        self.assertEqual(self.splitter.detect_separator_type(yaml_content), "yaml")
        self.assertEqual(
            self.splitter.detect_separator_type(markdown_content), "markdown"
        )


class TestCommonPatterns(unittest.TestCase):
    """Test the common patterns utilities."""

    def test_indentation_normalization(self):
        """Test indentation normalization."""
        content = """
            name: Test
            command: echo test
              description: Indented desc
        """

        normalized = CommonPatterns.normalize_indentation(content)
        lines = normalized.split("\n")

        # Should have removed common indentation using helper
        self._assert_no_common_indentation(lines)

    def _assert_no_common_indentation(self, lines):
        """Helper method to assert no common indentation exists."""
        stripped_lines = [line.strip() for line in lines if line.strip()]
        indented_lines = [line for line in stripped_lines if line.startswith("    ")]
        self.assertEqual(len(indented_lines), 0, "Found lines with common indentation")

    def test_yaml_cleaning(self):
        """Test YAML content cleaning."""
        messy_yaml = """
        name:NoSpaceAfterColon
        tags:[item1,item2,item3]
        command:echo"test"
        """

        cleaned = CommonPatterns.clean_yaml_content(messy_yaml)

        # Should have fixed spacing issues
        self.assertIn("name: NoSpaceAfterColon", cleaned)
        self.assertIn("tags: [item1,item2,item3]", cleaned)

    def test_key_value_extraction(self):
        """Test key-value pair extraction."""
        content = """
        name: Test Workflow
        command: echo test
        description: A test workflow
        # This is a comment
        invalid line without colon
        empty_value:
        """

        pairs = CommonPatterns.extract_key_value_pairs(content)

        # Should extract valid pairs, skip comments and invalid lines
        self.assertEqual(len(pairs), 3)
        pair_dict = dict(pairs)
        self.assertEqual(pair_dict["name"], "Test Workflow")
        self.assertEqual(pair_dict["command"], "echo test")
        self.assertEqual(pair_dict["description"], "A test workflow")


class TestMangledContentCleaner(unittest.TestCase):
    """Test the mangled content cleaner."""

    def test_unicode_normalization(self):
        """Test unicode character normalization."""
        mangled = "name：Test Workflow，command：echo test"

        cleaned = MangledContentCleaner.clean_mangled_content(mangled)

        # Should convert unicode punctuation to ASCII
        self.assertIn("name: Test Workflow", cleaned)
        self.assertIn("command: echo test", cleaned)

    def test_broken_brackets_cleanup(self):
        """Test cleanup of broken brackets and braces."""
        mangled = """
        name: Test
        broken: {unclosed dict
        tags: [unclosed, list
        command: echo test
        """

        cleaned = MangledContentCleaner.clean_mangled_content(mangled)

        # Should remove broken structures
        self.assertNotIn("{unclosed", cleaned)
        self.assertNotIn("[unclosed,", cleaned)
        self.assertIn("name: Test", cleaned)
        self.assertIn("command: echo test", cleaned)

    def test_line_reconstruction(self):
        """Test reconstruction from severely mangled content."""
        mangled = """
        name:Completely Broken Workflow
        command:echo"hello world"66ls -la
        tags:git,test,broken
        description:This has many issues
        """
        parser = RobustParser()
        reconstructed = parser.parse(mangled).data

        self.assertIsInstance(reconstructed, dict)
        self.assertEqual(reconstructed["name"], "Completely Broken Workflow")
        self.assertIn("command", reconstructed)


class TestYAMLStrategies(unittest.TestCase):
    """Test YAML parsing strategies."""

    def test_standard_yaml_strategy(self):
        """Test standard YAML parsing strategy."""
        strategy = StandardYAMLStrategy()

        valid_yaml = """
        name: Test
        command: echo test
        """

        result = strategy.attempt_parse(valid_yaml)
        self.assertTrue(result.success)
        self.assertEqual(result.data["name"], "Test")

    def test_cleaned_yaml_strategy(self):
        """Test cleaned YAML parsing strategy."""
        strategy = CleanedYAMLStrategy()

        messy_yaml = """
        name:Test
        command:echo test
        tags:[item1,item2]
        """

        result = strategy.attempt_parse(messy_yaml)
        self.assertTrue(result.success)
        self.assertEqual(result.data["name"], "Test")

    def test_mangled_yaml_strategy(self):
        """Test mangled YAML parsing strategy."""
        strategy = MangledYAMLStrategy()

        mangled_yaml = """
        name: Test Workflow
        command: echo "test"
        tags: [git, test]
        """

        result = strategy.attempt_parse(mangled_yaml)
        self.assertTrue(result.success)
        self.assertIn("name", result.data)

    def test_reconstructed_yaml_strategy(self):
        """Test reconstructed YAML strategy."""
        strategy = RobustParser()

        broken_yaml = """
        name:Broken Workflow
        command:echo test
        tags:[git,broken
        description:Missing closing bracket
        """

        result = strategy.attempt_parse(broken_yaml)
        self.assertTrue(result.success)
        self.assertEqual(result.data["name"], "Broken Workflow")

    def test_partial_yaml_strategy(self):
        """Test partial YAML extraction strategy."""
        strategy = RobustParser()

        severely_broken = """
        name: Salvageable Workflow
        command: echo test
        {broken json object
        tags: [incomplete]
        description: At least this works
        invalid yaml: everywhere
        """

        result = strategy.attempt_parse(severely_broken)
        self.assertTrue(result.success)
        self.assertEqual(result.data["name"], "Salvageable Workflow")
        self.assertEqual(result.data["description"], "At least this works")


class TestErrorTolerantYAMLParser(unittest.TestCase):
    """Test the complete error-tolerant YAML parser."""

    def setUp(self):
        # Create a parser with all strategies
        self.parser = RobustParser()

    def test_valid_yaml_fast_path(self):
        """Test that valid YAML uses the fast path."""
        valid_yaml = """
        name: Test Workflow
        command: echo test
        shells: [bash, zsh]
        """

        result = self.parser.parse(valid_yaml)
        self.assertTrue(result.success)

        # Check that it used the standard strategy
        stats = self.parser.get_stats()
        self.assertEqual(stats["strategy_successes"]["standard_yaml"], 1)

    def test_standard_strategy_parsing(self):
        """Test parsing with standard strategy."""
        yaml_content = """
            name: Good Workflow
            command: echo test
            """
        result = self.parser.parse(yaml_content)
        self.assertTrue(result.success, "Failed to parse standard YAML")
        self.assertIn("name", result.data)

    def test_cleaned_strategy_parsing(self):
        """Test parsing with cleaned strategy."""
        yaml_content = """
            name:Needs Cleaning
            command:echo test
            tags:[item1,item2]
            """
        result = self.parser.parse(yaml_content)
        self.assertTrue(result.success, "Failed to parse cleanable YAML")
        self.assertIn("name", result.data)

    def test_mangled_strategy_parsing(self):
        """Test parsing with mangled strategy."""
        yaml_content = """
            name：Unicode Issues
            command：echo"test"
            """
        result = self.parser.parse(yaml_content)
        self.assertTrue(result.success, "Failed to parse mangled YAML")
        self.assertIn("name", result.data)

    def test_reconstruction_strategy_parsing(self):
        """Test parsing with reconstruction strategy."""
        yaml_content = """
            name:Reconstruction Needed
            command:echo test
            tags:[broken,list
            description:Missing brackets
            """
        result = self.parser.parse(yaml_content)
        self.assertTrue(result.success, "Failed to parse reconstructable YAML")
        self.assertIn("name", result.data)

    def test_completely_broken_content(self):
        """Test handling of completely unparseable content."""
        garbage = "This is not YAML at all!!! @#$%^&*()"

        result = self.parser.parse(garbage)
        # Should fail gracefully
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)

    def get_large_mangled_content(self):
        """Helper method to generate large mangled content for performance testing."""
        # Using list comprehension (already functional approach)
        mangled_parts = [
            f"""
            name：Workflow {i}
            command：echo"test{i}"&&ls -la
            tags：[git，test，item{i}
            description：Workflow number {i} with issues
            """
            for i in range(100)
        ]
        return "\n---\n".join(mangled_parts)

    @pytest.mark.timeout(60)
    def test_performance_with_mangled_content(self):
        """Test performance with large amounts of mangled content."""
        # Should complete within timeout
        large_mangled_content = self.get_large_mangled_content()
        parser = RobustParser()
        result = parser.parse(large_mangled_content)
        self.assertTrue(result.success)


class TestEndToEndRobustParsing(unittest.TestCase):
    """End-to-end tests of the complete robust parsing system."""

    def test_apes_with_keyboards_content(self):
        """Test parsing of content that looks like apes were at keyboards."""
        ape_content = """
        name：工作流程測試
        command：echo"hello world"&&ls-la
        tags：[git，test，broken]]
        description：This has unicode，missing spaces，broken brackets
        shells：bash，zsh，fish
        arguments：
        -name：input
         description missing quotes
         default_value：test
        """

        # Full pipeline test
        detector = ContentDetector()
        splitter = DocumentSplitter()
        yaml_parser = RobustParser()  # Use RobustParser for mangled content

        # Should detect as workflow despite mangling
        content_type, confidence = detector.detect(ape_content)
        self.assertEqual(content_type, ContentType.WORKFLOW)
        self.assertGreater(confidence, 0.3)

        # Should split into single document
        documents = splitter.split(ape_content)
        self.assertEqual(len(documents), 1)

        # Should parse successfully
        result = yaml_parser.parse(documents[0])
        self.assertTrue(result.success)
        self.assertIn("name", result.data)
        self.assertIn("command", result.data)


if __name__ == "__main__":
    unittest.main()

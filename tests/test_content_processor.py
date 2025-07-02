#!/usr/bin/env python3

"""
Test suite for content splitting and processing functionality.
Tests handling of mixed content files and content type detection.
"""

import os
import yaml
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, main

from warp_content_processor import (
    ContentProcessor,
    ContentSplitter,
    SchemaDetector,
    ContentType,
    ProcessingResult
)

class TestSchemaDetector(TestCase):
    """Test the schema detection functionality."""
    
    def test_workflow_detection(self):
        """Test detection of workflow content."""
        content = """
        name: Test Workflow
        command: echo "test"
        shells:
          - bash
        """
        self.assertEqual(
            SchemaDetector.detect_type(content),
            ContentType.WORKFLOW
        )
    
    def test_prompt_detection(self):
        """Test detection of prompt content."""
        content = """
        name: Test Prompt
        prompt: Please {{action}} the following
        arguments:
          - name: action
            description: Action to perform
        """
        self.assertEqual(
            SchemaDetector.detect_type(content),
            ContentType.PROMPT
        )
    
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
        self.assertEqual(
            SchemaDetector.detect_type(content),
            ContentType.NOTEBOOK
        )
    
    def test_env_var_detection(self):
        """Test detection of environment variable content."""
        content = """
        variables:
          TEST_VAR: value
          DEBUG: "true"
        """
        self.assertEqual(
            SchemaDetector.detect_type(content),
            ContentType.ENV_VAR
        )
    
    def test_rule_detection(self):
        """Test detection of rule content."""
        content = """
        title: Test Rule
        description: A test rule
        guidelines:
          - Follow this guideline
        """
        self.assertEqual(
            SchemaDetector.detect_type(content),
            ContentType.RULE
        )

class TestContentSplitter(TestCase):
    """Test the content splitting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.fixtures_dir = Path(__file__).parent / 'fixtures'
        self.mixed_content_file = self.fixtures_dir / 'mixed_content.yaml'
    
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

class TestContentProcessor(TestCase):
    """Test the content processor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / 'output'
        self.fixtures_dir = Path(__file__).parent / 'fixtures'
        
        # Create processor
        self.processor = ContentProcessor(self.output_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_mixed_content_processing(self):
        """Test processing of mixed content file."""
        # Process the mixed content file
        results = self.processor.process_file(
            self.fixtures_dir / 'mixed_content.yaml'
        )
        
        # Check that we got results for each content type
        result_types = {r.content_type for r in results}
        self.assertIn(ContentType.WORKFLOW, result_types)
        self.assertIn(ContentType.PROMPT, result_types)
        self.assertIn(ContentType.RULE, result_types)
        self.assertIn(ContentType.ENV_VAR, result_types)
        self.assertIn(ContentType.NOTEBOOK, result_types)
        
        # Check that files were created in correct directories
        for content_type in result_types:
            type_dir = self.output_dir / content_type
            self.assertTrue(type_dir.exists())
            self.assertTrue(any(type_dir.iterdir()))
    
    def test_invalid_content_handling(self):
        """Test handling of invalid content."""
        invalid_content = "Invalid: ]: content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
            f.write(invalid_content)
            f.flush()
            
            results = self.processor.process_file(f.name)
            
            # Check that we got an error result
            self.assertTrue(all(not r.is_valid for r in results))
            self.assertTrue(all(r.errors for r in results))
    
    def test_content_validation(self):
        """Test validation of each content type."""
        for content_type, processor in self.processor.processors.items():
            # Create minimal valid content for each type
            if content_type == ContentType.WORKFLOW:
                content = {"name": "test", "command": "echo test"}
            elif content_type == ContentType.PROMPT:
                content = {"name": "test", "prompt": "do {{action}}"}
            elif content_type == ContentType.NOTEBOOK:
                content = "---\ntitle: test\n---\n# Test\n```bash\necho test\n```"
            elif content_type == ContentType.ENV_VAR:
                content = {"variables": {"TEST": "value"}}
            elif content_type == ContentType.RULE:
                content = {
                    "title": "Test Rule",
                    "description": "A test rule",
                    "guidelines": ["Test guideline"]
                }
            else:
                continue
            
            # Process the content
            if isinstance(content, dict):
                content = yaml.dump(content)
            
            result = processor.process(content)
            
            # Check validation
            self.assertTrue(
                result.is_valid,
                f"Validation failed for {content_type}: {result.errors}"
            )

if __name__ == '__main__':
    main()

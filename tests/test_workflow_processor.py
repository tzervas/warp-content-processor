#!/usr/bin/env python3

"""
Test suite for the workflow processor.
Tests validation, processing, and file management functionality.
"""

import os
import yaml
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, main

from warp_content_processor import WorkflowProcessor, WorkflowValidator, ProcessingResult

class TestWorkflowValidator(TestCase):
    """Test the workflow validator functionality."""
    
    def setUp(self):
        self.validator = WorkflowValidator()
        
        # Valid workflow example
        self.valid_workflow = {
            'name': 'Test Workflow',
            'description': 'A test workflow',
            'command': 'echo "Hello {{name}}"',
            'arguments': [
                {
                    'name': 'name',
                    'description': 'Name to greet',
                    'default_value': 'World'
                }
            ],
            'tags': ['test', 'example'],
            'shells': ['bash', 'zsh']
        }
    
    def test_valid_workflow(self):
        """Test that a valid workflow passes validation."""
        result = self.validator.validate_yaml(yaml.dump(self.valid_workflow))
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.warnings), 0)
    
    def test_missing_required_fields(self):
        """Test that missing required fields are detected."""
        incomplete_workflow = {'name': 'Test'}
        result = self.validator.validate_yaml(yaml.dump(incomplete_workflow))
        self.assertFalse(result.is_valid)
        self.assertIn('command', result.error)
    
    def test_invalid_argument_reference(self):
        """Test that undefined argument references are detected."""
        workflow = self.valid_workflow.copy()
        workflow['command'] = 'echo "Hello {{undefined_arg}}"'
        result = self.validator.validate_yaml(yaml.dump(workflow))
        self.assertTrue(result.is_valid)
        self.assertTrue(any('undefined_arg' in w for w in result.warnings))
    
    def test_invalid_tag_format(self):
        """Test that invalid tag formats are detected."""
        workflow = self.valid_workflow.copy()
        workflow['tags'] = ['Invalid Tag', 'valid-tag']
        result = self.validator.validate_yaml(yaml.dump(workflow))
        self.assertTrue(result.is_valid)
        self.assertTrue(any('Invalid tag format' in w for w in result.warnings))
    
    def test_unknown_shell(self):
        """Test that unknown shell types are detected."""
        workflow = self.valid_workflow.copy()
        workflow['shells'] = ['bash', 'unknown_shell']
        result = self.validator.validate_yaml(yaml.dump(workflow))
        self.assertTrue(result.is_valid)
        self.assertTrue(any('unknown_shell' in w for w in result.warnings))

class TestWorkflowProcessor(TestCase):
    """Test the workflow processor functionality."""
    
    def setUp(self):
        """Set up temporary directories for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.test_dir) / 'source'
        self.output_dir = Path(self.test_dir) / 'output'
        self.source_dir.mkdir()
        self.output_dir.mkdir()
        
        # Create test workflows
        self.single_workflow = {
            'name': 'Single Test',
            'command': 'echo "test"'
        }
        
        self.multiple_workflows = [
            {
                'name': 'First Test',
                'command': 'echo "first"'
            },
            {
                'name': 'Second Test',
                'command': 'echo "second"'
            }
        ]
    
    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)
    
    def test_single_workflow_processing(self):
        """Test processing of a single workflow file."""
        # Create test file
        workflow_file = self.source_dir / 'single.yaml'
        workflow_file.write_text(yaml.dump(self.single_workflow))
        
        # Process workflows
        processor = WorkflowProcessor(str(self.source_dir), str(self.output_dir))
        processor.process_all()
        
        # Check results
        self.assertEqual(len(processor.processed_files), 1)
        self.assertEqual(len(processor.failed_files), 0)
        self.assertTrue((self.output_dir / 'single_test.yaml').exists())
    
    def test_multiple_workflow_processing(self):
        """Test processing of a file containing multiple workflows."""
        # Create test file
        workflow_file = self.source_dir / 'multiple.yaml'
        workflow_file.write_text(yaml.dump(self.multiple_workflows))
        
        # Process workflows
        processor = WorkflowProcessor(str(self.source_dir), str(self.output_dir))
        processor.process_all()
        
        # Check results
        self.assertEqual(len(processor.processed_files), 2)
        self.assertEqual(len(processor.failed_files), 0)
        self.assertTrue((self.output_dir / 'first_test.yaml').exists())
        self.assertTrue((self.output_dir / 'second_test.yaml').exists())
    
    def test_invalid_workflow_handling(self):
        """Test handling of invalid workflow files."""
        # Create invalid test file
        invalid_file = self.source_dir / 'invalid.yaml'
        invalid_file.write_text('invalid: yaml: content:')
        
        # Process workflows
        processor = WorkflowProcessor(str(self.source_dir), str(self.output_dir))
        processor.process_all()
        
        # Check results
        self.assertEqual(len(processor.processed_files), 0)
        self.assertEqual(len(processor.failed_files), 1)
    
    def test_duplicate_name_handling(self):
        """Test handling of workflows with duplicate names."""
        # Create two workflows with the same name
        workflow = self.single_workflow.copy()
        
        file1 = self.source_dir / 'first.yaml'
        file2 = self.source_dir / 'second.yaml'
        
        file1.write_text(yaml.dump(workflow))
        file2.write_text(yaml.dump(workflow))
        
        # Process workflows
        processor = WorkflowProcessor(str(self.source_dir), str(self.output_dir))
        processor.process_all()
        
        # Check results
        self.assertEqual(len(processor.processed_files), 2)
        self.assertEqual(len(processor.failed_files), 0)
        
        # Verify both files exist with different names
        files = list(self.output_dir.glob('*.yaml'))
        self.assertEqual(len(files), 2)
        self.assertNotEqual(files[0].name, files[1].name)

if __name__ == '__main__':
    main()

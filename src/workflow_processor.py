#!/usr/bin/env python3

"""
Workflow processor for Warp Terminal workflow files.

This module handles the validation, processing, and organization of workflow files
for the Warp Terminal. It includes functionality for:
- YAML validation
- Workflow splitting
- File organization
- Original file cleanup

Usage:
    from workflow_processor import WorkflowProcessor
    
    processor = WorkflowProcessor(source_dir, output_dir)
    processor.process_all()
"""

import os
import re
import yaml
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('workflow_processing.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Data class for storing validation results."""
    is_valid: bool
    data: Optional[Dict]
    error: str
    warnings: List[str]

class WorkflowValidator:
    """Validates workflow YAML files against schema requirements."""
    
    REQUIRED_FIELDS = {'name', 'command'}
    OPTIONAL_FIELDS = {'description', 'arguments', 'tags', 'source_url', 'author', 'author_url', 'shells'}
    KNOWN_SHELLS = {'bash', 'zsh', 'fish', 'pwsh', 'cmd'}
    
    # Regex patterns for validation
    COMMAND_PLACEHOLDER_PATTERN = re.compile(r'{{[a-zA-Z_][a-zA-Z0-9_]*}}')
    VALID_TAG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$')
    
    @staticmethod
    def validate_yaml(content: str) -> ValidationResult:
        """
        Validate YAML syntax and required fields.
        
        Returns:
            Tuple[bool, Optional[Dict], str]: (is_valid, parsed_yaml, error_message)
        """
        warnings = []
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return ValidationResult(False, None, "YAML content must be a dictionary", [])
            
            # Check required fields
            missing_fields = WorkflowValidator.REQUIRED_FIELDS - set(data.keys())
            if missing_fields:
                return ValidationResult(False, None, f"Missing required fields: {missing_fields}", [])
            
            # Validate types and content
            if not isinstance(data['name'], str):
                return ValidationResult(False, None, "Field 'name' must be a string", [])
            if not isinstance(data['command'], str):
                return ValidationResult(False, None, "Field 'command' must be a string", [])
            
            # Check command placeholders match arguments
            placeholders = set(WorkflowValidator.COMMAND_PLACEHOLDER_PATTERN.findall(data['command']))
            placeholders = {p[2:-2] for p in placeholders}  # Remove {{ and }}
            
            if 'arguments' in data:
                if not isinstance(data['arguments'], list):
                    return ValidationResult(False, None, "'arguments' must be a list", [])
                    
                arg_names = {arg.get('name') for arg in data['arguments'] if isinstance(arg, dict)}
                missing_args = placeholders - arg_names
                unused_args = arg_names - placeholders
                
                if missing_args:
                    warnings.append(f"Command references undefined arguments: {missing_args}")
                if unused_args:
                    warnings.append(f"Defined arguments not used in command: {unused_args}")
            
            # Validate tags
            if 'tags' in data:
                if not isinstance(data['tags'], list):
                    return ValidationResult(False, None, "'tags' must be a list", [])
                
                invalid_tags = [tag for tag in data['tags'] 
                               if not isinstance(tag, str) or 
                               not WorkflowValidator.VALID_TAG_PATTERN.match(tag)]
                if invalid_tags:
                    warnings.append(f"Invalid tag format: {invalid_tags}. Tags should be lowercase, "
                                  "start with a letter/number, and contain only letters, numbers, and hyphens.")
            
            # Validate shells
            if 'shells' in data:
                if not isinstance(data['shells'], list):
                    return ValidationResult(False, None, "'shells' must be a list", [])
                
                unknown_shells = set(data['shells']) - WorkflowValidator.KNOWN_SHELLS
                if unknown_shells:
                    warnings.append(f"Unknown shell types: {unknown_shells}")
            
            # Check for unknown fields
            unknown_fields = set(data.keys()) - WorkflowValidator.REQUIRED_FIELDS - WorkflowValidator.OPTIONAL_FIELDS
            if unknown_fields:
                warnings.append(f"Unknown fields present: {unknown_fields}")
            
            return ValidationResult(True, data, "", warnings)
            
        except yaml.YAMLError as e:
            return ValidationResult(False, None, f"Invalid YAML syntax: {str(e)}", [])

class WorkflowSplitter:
    """Handles splitting of files containing multiple workflows."""
    
    @staticmethod
    def detect_multiple_workflows(content: str) -> List[Dict]:
        """
        Detect if YAML content contains multiple workflows and split them.
        
        Returns:
            List[Dict]: List of individual workflow dictionaries
        """
        try:
            data = yaml.safe_load(content)
            if isinstance(data, list):
                return data
            return [data] if isinstance(data, dict) else []
        except yaml.YAMLError:
            return []

    @staticmethod
    def generate_filename(workflow: Dict) -> str:
        """Generate a filename based on workflow name."""
        name = workflow.get('name', 'unnamed_workflow')
        # Clean the name for use as filename
        clean_name = ''.join(c if c.isalnum() else '_' for c in name.lower())
        return f"{clean_name}.yaml"

class WorkflowProcessor:
    """Main class for processing workflow files."""
    
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.validator = WorkflowValidator()
        self.splitter = WorkflowSplitter()
        self.processed_files = []
        self.failed_files = []
        self.warnings = []
        
    @contextmanager
    def _atomic_write(self, filepath: Path):
        """Atomically write a file using a temporary file."""
        temp_dir = filepath.parent
        with tempfile.NamedTemporaryFile(mode='w', dir=temp_dir, delete=False) as tmp:
            try:
                yield tmp
                tmp.flush()
                os.fsync(tmp.fileno())
                os.replace(tmp.name, filepath)
            except:
                os.unlink(tmp.name)
                raise
        
    def process_file(self, file_path: Path) -> bool:
        """
        Process a single workflow file.
        
        Returns:
            bool: True if processing was successful
        """
        try:
            content = file_path.read_text()
            workflows = self.splitter.detect_multiple_workflows(content)
            
            if not workflows:
                logger.warning(f"No valid workflows found in {file_path}")
                self.failed_files.append((file_path, "No valid workflows found"))
                return False
            
            success = True
            for workflow in workflows:
                # Validate each workflow
                validation_result = self.validator.validate_yaml(yaml.dump(workflow))
                
                if not validation_result.is_valid:
                    logger.error(f"Validation failed for workflow in {file_path}: {validation_result.error}")
                    self.failed_files.append((file_path, validation_result.error))
                    success = False
                    continue
                
                # Log any warnings
                for warning in validation_result.warnings:
                    logger.warning(f"Warning for {file_path}: {warning}")
                    self.warnings.append((file_path, warning))
                
                # Generate output filename and save
                output_filename = self.splitter.generate_filename(validated_workflow)
                output_path = self.output_dir / output_filename
                
                # Ensure we don't overwrite existing files
                counter = 1
                while output_path.exists():
                    base_name = output_filename.rsplit('.', 1)[0]
                    output_path = self.output_dir / f"{base_name}_{counter}.yaml"
                    counter += 1
                
                # Write file atomically
                with self._atomic_write(output_path) as f:
                    yaml.dump(validation_result.data, f, sort_keys=False)
                logger.info(f"Created workflow file: {output_path}")
                self.processed_files.append((file_path, output_path))
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            self.failed_files.append((file_path, str(e)))
            return False
    
    def cleanup_originals(self):
        """Delete original files that were successfully processed."""
        successful_originals = {orig for orig, _ in self.processed_files}
        for original in successful_originals:
            try:
                original.unlink()
                logger.info(f"Deleted original file: {original}")
            except Exception as e:
                logger.error(f"Failed to delete {original}: {str(e)}")
    
    def process_all(self):
        """Process all YAML files in the source directory."""
        yaml_files = list(self.source_dir.rglob("*.yaml")) + list(self.source_dir.rglob("*.yml"))
        
        for file_path in yaml_files:
            logger.info(f"Processing: {file_path}")
            self.process_file(file_path)
        
        # Report results
        logger.info(f"Successfully processed {len(self.processed_files)} workflows")
        if self.failed_files:
            logger.warning(f"Failed to process {len(self.failed_files)} files:")
            for file_path, error in self.failed_files:
                logger.warning(f"  {file_path}: {error}")
        
        # Cleanup original files
        self.cleanup_originals()

def main():
    """Main entry point for workflow processing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process and validate workflow files")
    parser.add_argument("source_dir", help="Directory containing source workflow files")
    parser.add_argument("output_dir", help="Directory for processed workflow files")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    processor = WorkflowProcessor(args.source_dir, args.output_dir)
    processor.process_all()

if __name__ == "__main__":
    main()

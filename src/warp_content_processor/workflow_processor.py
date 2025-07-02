"""
Workflow processor for Warp Terminal workflow files.
"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base_processor import SchemaProcessor, ProcessingResult
from .schema_processor import ContentType

logger = logging.getLogger(__name__)

class WorkflowValidator(SchemaProcessor):
    """Validates workflow YAML files against schema requirements."""
    
    def __init__(self):
        super().__init__()
        self.required_fields = {'name', 'command'}
        self.optional_fields = {'description', 'arguments', 'tags',
                              'source_url', 'author', 'author_url', 'shells'}
        self.known_shells = {'bash', 'zsh', 'fish', 'pwsh', 'cmd'}
        
        # Regex patterns
        self.command_pattern = re.compile(r'{{[a-zA-Z_][a-zA-Z0-9_]*}}')
        self.valid_tag_pattern = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$')
    
    def validate(self, data: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate workflow data against schema."""
        errors = []
        warnings = []
        
        # Check required fields
        missing_fields = self.required_fields - set(data.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Validate types
        if 'name' in data and not isinstance(data['name'], str):
            errors.append("Field 'name' must be a string")
        if 'command' in data and not isinstance(data['command'], str):
            errors.append("Field 'command' must be a string")
        
        # Check for unknown fields
        unknown_fields = set(data.keys()) - self.required_fields - self.optional_fields
        if unknown_fields:
            warnings.append(f"Unknown fields present: {unknown_fields}")
        
        # Validate command placeholders match arguments
        if 'command' in data:
            placeholders = set(self.command_pattern.findall(data['command']))
            placeholders = {p[2:-2] for p in placeholders}  # Remove {{ and }}
            
            if 'arguments' in data:
                if not isinstance(data['arguments'], list):
                    errors.append("'arguments' must be a list")
                else:
                    arg_names = {arg.get('name') for arg in data['arguments']
                               if isinstance(arg, dict)}
                    missing_args = placeholders - arg_names
                    unused_args = arg_names - placeholders
                    
                    if missing_args:
                        warnings.append(f"Command references undefined arguments: {missing_args}")
                    if unused_args:
                        warnings.append(f"Defined arguments not used in command: {unused_args}")
        
        # Validate tags
        if 'tags' in data:
            if not isinstance(data['tags'], list):
                errors.append("'tags' must be a list")
            else:
                invalid_tags = [tag for tag in data['tags']
                              if not isinstance(tag, str) or
                              not self.valid_tag_pattern.match(tag)]
                if invalid_tags:
                    warnings.append(f"Invalid tag format: {invalid_tags}")
        
        # Validate shells
        if 'shells' in data:
            if not isinstance(data['shells'], list):
                errors.append("'shells' must be a list")
            else:
                unknown_shells = set(data['shells']) - self.known_shells
                if unknown_shells:
                    warnings.append(f"Unknown shell types: {unknown_shells}")
        
        return len(errors) == 0, errors, warnings
    
    def process(self, content: str) -> ProcessingResult:
        """Process and validate workflow content."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return ProcessingResult(
                    content_type=ContentType.WORKFLOW,
                    is_valid=False,
                    data=None,
                    errors=["Content must be a YAML dictionary"],
                    warnings=[]
                )
            
            is_valid, errors, warnings = self.validate(data)
            return ProcessingResult(
                content_type=ContentType.WORKFLOW,
                is_valid=is_valid,
                data=data if is_valid else None,
                errors=errors,
                warnings=warnings
            )
            
        except yaml.YAMLError as e:
            return ProcessingResult(
                content_type=ContentType.WORKFLOW,
                is_valid=False,
                data=None,
                errors=[f"Invalid YAML syntax: {str(e)}"],
                warnings=[]
            )
        except Exception as e:
            return ProcessingResult(
                content_type=ContentType.WORKFLOW,
                is_valid=False,
                data=None,
                errors=[f"Error processing workflow: {str(e)}"],
                warnings=[]
            )
    
    def generate_filename(self, data: Dict) -> str:
        """Generate filename for workflow content."""
        name = data.get('name', 'unnamed_workflow')
        # Clean name for use as filename
        clean_name = ''.join(c if c.isalnum() else '_' for c in name.lower())
        return f"{clean_name}.yaml"

class WorkflowProcessor(WorkflowValidator):
    """Main class for processing workflow files."""
    
    def __init__(self, output_dir: Path):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.processed_files = []
        self.failed_files = []
        self.warnings = []
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_file(self, file_path: Path) -> bool:
        """
        Process a single workflow file.
        
        Returns:
            bool: True if processing was successful
        """
        try:
            content = file_path.read_text()
            workflows = yaml.safe_load(content)
            
            if not isinstance(workflows, (dict, list)):
                logger.warning(f"No valid workflows found in {file_path}")
                self.failed_files.append((file_path, "No valid workflows found"))
                return False
            
            if isinstance(workflows, dict):
                workflows = [workflows]
            
            success = True
            for workflow in workflows:
                # Validate workflow
                result = self.process(yaml.dump(workflow))
                
                if not result.is_valid:
                    logger.error(f"Validation failed for workflow in {file_path}: {result.errors}")
                    self.failed_files.append((file_path, result.errors[0]))
                    success = False
                    continue
                
                # Log any warnings
                for warning in result.warnings:
                    logger.warning(f"Warning for {file_path}: {warning}")
                    self.warnings.append((file_path, warning))
                
                # Generate output filename and save
                filename = self.generate_filename(result.data)
                output_path = self.output_dir / filename
                
                # Ensure unique filename
                counter = 1
                while output_path.exists():
                    base_name = filename.rsplit('.', 1)[0]
                    output_path = self.output_dir / f"{base_name}_{counter}.yaml"
                    counter += 1
                
                output_path.write_text(yaml.dump(result.data))
                logger.info(f"Created workflow file: {output_path}")
                self.processed_files.append((file_path, output_path))
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            self.failed_files.append((file_path, str(e)))
            return False

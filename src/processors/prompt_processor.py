#!/usr/bin/env python3

"""
Processor for Warp Terminal prompt files.
Handles validation and processing of prompt schemas.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

from schema_processor import SchemaProcessor, ProcessingResult, ContentType

class PromptProcessor(SchemaProcessor):
    """Processor for prompt files."""
    
    def __init__(self):
        super().__init__()
        self.required_fields = {'name', 'prompt'}
        self.optional_fields = {'description', 'arguments', 'tags'}
        
        # Regex patterns for validation
        self.placeholder_pattern = re.compile(r'{{[a-zA-Z_][a-zA-Z0-9_]*}}')
        self.valid_tag_pattern = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$')
    
    def validate(self, data: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate prompt data against schema."""
        errors = []
        warnings = []
        
        # Check required fields
        missing_fields = self.required_fields - set(data.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")
        
        # Validate field types
        if 'name' in data and not isinstance(data['name'], str):
            errors.append("Field 'name' must be a string")
        if 'prompt' in data and not isinstance(data['prompt'], str):
            errors.append("Field 'prompt' must be a string")
        
        # Check for unknown fields
        unknown_fields = set(data.keys()) - self.required_fields - self.optional_fields
        if unknown_fields:
            warnings.append(f"Unknown fields present: {unknown_fields}")
        
        # Validate arguments
        if 'prompt' in data and 'arguments' in data:
            placeholders = set(self.placeholder_pattern.findall(data['prompt']))
            placeholders = {p[2:-2] for p in placeholders}  # Remove {{ and }}
            
            if not isinstance(data['arguments'], list):
                errors.append("'arguments' must be a list")
            else:
                arg_names = {arg.get('name') for arg in data['arguments'] 
                           if isinstance(arg, dict)}
                missing_args = placeholders - arg_names
                unused_args = arg_names - placeholders
                
                if missing_args:
                    warnings.append(f"Prompt references undefined arguments: {missing_args}")
                if unused_args:
                    warnings.append(f"Defined arguments not used in prompt: {unused_args}")
        
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
        
        return len(errors) == 0, errors, warnings
    
    def process(self, content: str) -> ProcessingResult:
        """Process and validate prompt content."""
        try:
            # Try to parse as YAML
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return ProcessingResult(
                    content_type=ContentType.PROMPT,
                    is_valid=False,
                    data=None,
                    errors=["Content must be a YAML dictionary"],
                    warnings=[]
                )
            
            # Validate the data
            is_valid, errors, warnings = self.validate(data)
            
            return ProcessingResult(
                content_type=ContentType.PROMPT,
                is_valid=is_valid,
                data=data if is_valid else None,
                errors=errors,
                warnings=warnings
            )
            
        except yaml.YAMLError as e:
            return ProcessingResult(
                content_type=ContentType.PROMPT,
                is_valid=False,
                data=None,
                errors=[f"Invalid YAML syntax: {str(e)}"],
                warnings=[]
            )
        except Exception as e:
            return ProcessingResult(
                content_type=ContentType.PROMPT,
                is_valid=False,
                data=None,
                errors=[f"Error processing prompt: {str(e)}"],
                warnings=[]
            )
    
    def generate_filename(self, data: Dict) -> str:
        """Generate filename for prompt content."""
        name = data.get('name', 'unnamed_prompt')
        # Clean name for use as filename
        clean_name = ''.join(c if c.isalnum() else '_' for c in name.lower())
        return f"{clean_name}.yaml"

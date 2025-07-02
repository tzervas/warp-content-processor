"""Shared validation utilities for content processors."""

import re
from typing import Dict, List, Set, Tuple

def validate_placeholders(content: str, arguments: List[Dict], pattern: str = r'{{[a-zA-Z_][a-zA-Z0-9_]*}}') -> Tuple[List[str], List[str]]:
    """
    Validate command/prompt placeholders against provided arguments.
    
    Args:
        content: String containing placeholders
        arguments: List of argument dictionaries
        pattern: Regex pattern for placeholders (default: {{name}})
        
    Returns:
        Tuple[List[str], List[str]]: (errors, warnings)
    """
    errors = []
    warnings = []
    
    placeholder_pattern = re.compile(pattern)
    placeholders = set(placeholder_pattern.findall(content))
    placeholders = {p[2:-2] for p in placeholders}  # Remove {{ and }}
    
    if not isinstance(arguments, list):
        errors.append("'arguments' must be a list")
        return errors, warnings
    
    arg_names = {arg.get('name') for arg in arguments if isinstance(arg, dict)}
    missing_args = placeholders - arg_names
    unused_args = arg_names - placeholders
    
    if missing_args:
        warnings.append(f"References undefined arguments: {missing_args}")
    if unused_args:
        warnings.append(f"Defined arguments not used: {unused_args}")
    
    return errors, warnings

def validate_tags(tags: List[str], pattern: str = r'^[a-z0-9][a-z0-9-]*[a-z0-9]$') -> Tuple[List[str], List[str]]:
    """
    Validate tag format.
    
    Args:
        tags: List of tags to validate
        pattern: Regex pattern for valid tags
        
    Returns:
        Tuple[List[str], List[str]]: (errors, warnings)
    """
    errors = []
    warnings = []
    
    if not isinstance(tags, list):
        errors.append("'tags' must be a list")
        return errors, warnings
    
    tag_pattern = re.compile(pattern)
    invalid_tags = [tag for tag in tags
                   if not isinstance(tag, str) or
                   not tag_pattern.match(tag)]
    
    if invalid_tags:
        warnings.append(f"Invalid tag format: {invalid_tags}")
    
    return errors, warnings

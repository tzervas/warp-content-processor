#!/usr/bin/env python3

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Tuple

def find_yaml_files(start_path: str) -> List[str]:
    """Find all YAML files in the given directory and its subdirectories."""
    yaml_files = []
    for root, _, files in os.walk(start_path):
        for file in files:
            if file.endswith(('.yml', '.yaml')):
                yaml_files.append(os.path.join(root, file))
    return yaml_files

def extract_frontmatter(content: str) -> Tuple[List[Dict[str, Any]], bool]:
    """Extract YAML frontmatter from mixed content files.
    
    Args:
        content: The file content to parse
        
    Returns:
        A tuple of (list of parsed documents, whether the file has frontmatter)
    """
    # Check for frontmatter delimiter
    if content.startswith('---\n'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:  # Valid frontmatter found
            try:
                # Parse the frontmatter (the middle part)
                frontmatter = yaml.safe_load(parts[1])
                if frontmatter is not None:
                    return [frontmatter], True
            except yaml.YAMLError:
                pass
    return [], False

def parse_yaml_file(file_path: str) -> List[Dict[str, Any]]:
    """Parse a YAML file and return its contents as a list of Python dictionaries.
    
    This function handles:
    - Single-document YAML files
    - Multi-document YAML files
    - Files with YAML frontmatter
    
    Args:
        file_path: Path to the YAML file to parse
        
    Returns:
        A list of dictionaries, where each dictionary represents a YAML document
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
            # First, try to extract frontmatter
            documents, has_frontmatter = extract_frontmatter(content)
            if has_frontmatter:
                return documents
            
            # If no frontmatter, try parsing as multi-document YAML
            try:
                documents = list(yaml.safe_load_all(content))
                # Filter out None values that might appear between documents
                documents = [doc for doc in documents if doc is not None]
                if documents:
                    return documents
                else:
                    print(f"Warning: No valid YAML documents found in {file_path}", file=sys.stderr)
                    return []
            except yaml.YAMLError as e:
                # If multi-document parsing fails, try single document
                try:
                    single_doc = yaml.safe_load(content)
                    return [single_doc] if single_doc is not None else []
                except yaml.YAMLError:
                    # If both parsing methods fail, raise the original error
                    raise e
    except yaml.YAMLError as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return []

def print_document_structure(doc: Union[Dict, List, Any], indent: str = "  ") -> None:
    """Print the structure of a YAML document with proper indentation."""
    if isinstance(doc, dict):
        for key in doc.keys():
            print(f"{indent}- {key}")
    elif isinstance(doc, list):
        print(f"{indent}- List with {len(doc)} items")
    else:
        print(f"{indent}- {type(doc).__name__}")

def main():
    # Get the current directory
    current_dir = os.getcwd()
    
    # Find all YAML files
    yaml_files = find_yaml_files(current_dir)
    
    # Track statistics
    total_files = len(yaml_files)
    successful_files = 0
    total_documents = 0
    
    # Parse each YAML file
    for file_path in yaml_files:
        relative_path = os.path.relpath(file_path, current_dir)
        print(f"\nProcessing: {relative_path}")
        
        documents = parse_yaml_file(file_path)
        if documents:
            successful_files += 1
            total_documents += len(documents)
            
            if len(documents) > 1:
                print(f"Successfully parsed {relative_path} ({len(documents)} documents)")
                for i, doc in enumerate(documents, 1):
                    print(f"Document {i} structure:")
                    print_document_structure(doc)
            else:
                print(f"Successfully parsed {relative_path}")
                print("Structure:")
                print_document_structure(documents[0])
        else:
            print(f"Failed to parse {relative_path}")

    print(f"\nSummary:")
    print(f"Total files processed: {total_files}")
    print(f"Successfully parsed files: {successful_files}")
    print(f"Failed files: {total_files - successful_files}")
    print(f"Total YAML documents parsed: {total_documents}")

if __name__ == "__main__":
    main()


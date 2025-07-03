"""
Processor for Warp Terminal notebook files.
"""

import re
from typing import Dict, List, Optional, Tuple

import yaml

from ..base_processor import ProcessingResult, SchemaProcessor
from ..content_type import ContentType


class NotebookProcessor(SchemaProcessor):
    """Processor for notebook files."""

    def __init__(self, output_dir=None) -> None:
        super().__init__()
        self.required_fields = {"title"}  # Only title is required in front matter
        self.optional_fields = {"description", "tags"}
        self.output_dir = output_dir

        # Regex patterns
        self.front_matter_pattern = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
        self.valid_tag_pattern = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
        self.code_block_pattern = re.compile(r"```.*?\n.*?```", re.DOTALL)
        self.command_pattern = re.compile(r"{{[a-zA-Z_][a-zA-Z0-9_]*}}")

    def _extract_front_matter(
        self, content: str
    ) -> Tuple[Optional[Dict], str, List[str]]:
        """
        Extract and parse YAML front matter from notebook content.

        Returns:
            Tuple[Optional[Dict], str, List[str]]: (front_matter, remaining_content,
                errors)
        """
        match = self.front_matter_pattern.match(content)
        if not match:
            return None, content, ["No YAML front matter found"]

        try:
            front_matter = yaml.safe_load(match.group(1))
            if not isinstance(front_matter, dict):
                return None, content, ["Front matter must be a YAML dictionary"]

            remaining_content = content[match.end() :]
            return front_matter, remaining_content, []

        except yaml.YAMLError as e:
            return None, content, [f"Invalid front matter YAML: {str(e)}"]

    def validate(self, data: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate notebook data against schema."""
        errors = []
        warnings = []

        front_matter = data.get("front_matter", {})
        content = data.get("content", "")

        # Validate front matter
        if not front_matter:
            errors.append("Missing front matter")
        else:
            # Check required fields
            missing_fields = self.required_fields - set(front_matter.keys())
            if missing_fields:
                errors.append(
                    f"Missing required fields in front matter: {missing_fields}"
                )

            # Validate field types
            if "title" in front_matter and not isinstance(front_matter["title"], str):
                errors.append("Field 'title' must be a string")
            if "description" in front_matter and not isinstance(
                front_matter["description"], str
            ):
                errors.append("Field 'description' must be a string")

            # Validate tags
            if "tags" in front_matter:
                if not isinstance(front_matter["tags"], list):
                    errors.append("'tags' must be a list")
                else:
                    invalid_tags = [
                        tag
                        for tag in front_matter["tags"]
                        if not isinstance(tag, str)
                        or not self.valid_tag_pattern.match(tag)
                    ]
                    if invalid_tags:
                        warnings.append(f"Invalid tag format: {invalid_tags}")

        # Validate content
        if not content.strip():
            errors.append("Notebook content is empty")
        else:
            # Check code blocks
            code_blocks = self.code_block_pattern.findall(content)
            if not code_blocks:
                warnings.append("No code blocks found in notebook")

            # Check for command placeholders in code blocks
            for block in code_blocks:
                placeholders = self.command_pattern.findall(block)
                if placeholders:
                    warnings.append(
                        f"Code block contains command placeholders: {placeholders}"
                    )

        return len(errors) == 0, errors, warnings

    def normalize_content(self, data: Dict) -> Dict:
        """Normalize notebook content to consistent format."""
        normalized = data.copy()
        
        # Normalize front matter
        if "front_matter" in normalized and isinstance(normalized["front_matter"], dict):
            front_matter = normalized["front_matter"].copy()
            
            # Normalize tags to lowercase
            if "tags" in front_matter and isinstance(front_matter["tags"], list):
                front_matter["tags"] = [
                    tag.lower() if isinstance(tag, str) else tag 
                    for tag in front_matter["tags"]
                ]
            
            normalized["front_matter"] = front_matter
        
        return normalized

    def process(self, content: str) -> ProcessingResult:
        """Process and validate notebook content."""
        try:
            # Try to parse as structured YAML first
            try:
                yaml_data = yaml.safe_load(content)
                if isinstance(yaml_data, dict) and "front_matter" in yaml_data and "content" in yaml_data:
                    # Content is already structured
                    data = yaml_data
                else:
                    # Fall back to front matter extraction
                    front_matter, remaining_content, errors = self._extract_front_matter(
                        content
                    )
                    if errors:
                        return ProcessingResult(
                            content_type=ContentType.NOTEBOOK,
                            is_valid=False,
                            data=None,
                            errors=errors,
                            warnings=[],
                        )
                    data = {"front_matter": front_matter, "content": remaining_content}
            except yaml.YAMLError:
                # Fall back to front matter extraction
                front_matter, remaining_content, errors = self._extract_front_matter(
                    content
                )
                if errors:
                    return ProcessingResult(
                        content_type=ContentType.NOTEBOOK,
                        is_valid=False,
                        data=None,
                        errors=errors,
                        warnings=[],
                    )
                data = {"front_matter": front_matter, "content": remaining_content}

            # Validate the data
            is_valid, errors, warnings = self.validate(data)

            return ProcessingResult(
                content_type=ContentType.NOTEBOOK,
                is_valid=is_valid,
                data=data if is_valid else None,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            return ProcessingResult(
                content_type=ContentType.NOTEBOOK,
                is_valid=False,
                data=None,
                errors=[f"Error processing notebook: {str(e)}"],
                warnings=[],
            )

    def generate_filename(self, data: Dict) -> str:
        """Generate filename for notebook content."""
        title = data.get("front_matter", {}).get("title", "unnamed_notebook")
        # Clean title for use as filename
        clean_title = "".join(c if c.isalnum() else "_" for c in title.lower())
        return f"{clean_title}.md"

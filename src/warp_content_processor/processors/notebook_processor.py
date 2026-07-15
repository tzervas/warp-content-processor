"""
Processor for Warp Terminal notebook files.
"""

import logging
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
                    for tag in front_matter["tags"]:
                        if not isinstance(tag, str):
                            warnings.append(f"Tag '{tag}' is not a string")
                        elif not self.valid_tag_pattern.match(str(tag)):
                            warnings.append(
                                f"Tag '{tag}' does not match the required format"
                            )

        # Validate content
        if not content or not content.strip():
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

    def _validate_front_matter_types(self, front_matter: Dict) -> List[str]:
        """Validate front matter field types and detect unexpected nested structures.

        Args:
            front_matter: Dictionary containing front matter fields

        Returns:
            List of error messages for type validation issues
        """
        errors = []
        logger = logging.getLogger(__name__)

        # Expected types for each field
        expected_types = {
            "title": str,
            "description": str,
            "tags": (list, str),  # Can be either list or string (will be normalized)
        }

        for field_name, field_value in front_matter.items():
            if field_name in expected_types:
                expected_type = expected_types[field_name]

                # Check if field value matches expected type(s)
                if not isinstance(field_value, expected_type):
                    # Special handling for nested structures
                    if isinstance(field_value, (dict, list)):
                        if field_name == "tags" and isinstance(field_value, list):
                            # Validate each tag in the list
                            for i, tag in enumerate(field_value):
                                if isinstance(tag, (dict, list)):
                                    error_msg = (
                                        f"Field '{field_name}[{i}]' contains "
                                        f"unexpected nested structure: "
                                        f"{type(tag).__name__}. Expected simple "
                                        f"string value."
                                    )
                                    errors.append(error_msg)
                                    logger.error(error_msg)
                                elif not isinstance(tag, str):
                                    error_msg = (
                                        f"Field '{field_name}[{i}]' has "
                                        f"unexpected type: {type(tag).__name__}. "
                                        f"Expected string."
                                    )
                                    errors.append(error_msg)
                                    logger.error(error_msg)
                        else:
                            # Unexpected nested structure for non-list fields
                            expected_str = (
                                " or ".join(t.__name__ for t in expected_type)
                                if isinstance(expected_type, tuple)
                                else expected_type.__name__
                            )
                            error_msg = (
                                f"Field '{field_name}' contains unexpected "
                                f"nested structure: {type(field_value).__name__}. "
                                f"Expected {expected_str}."
                            )
                            errors.append(error_msg)
                            logger.error(error_msg)
                    else:
                        # Wrong primitive type
                        expected_str = (
                            " or ".join(t.__name__ for t in expected_type)
                            if isinstance(expected_type, tuple)
                            else expected_type.__name__
                        )
                        error_msg = (
                            f"Field '{field_name}' has unexpected type: "
                            f"{type(field_value).__name__}. Expected {expected_str}."
                        )
                        errors.append(error_msg)
                        logger.error(error_msg)
            else:
                # Unknown field - log warning but don't error
                logger.warning(f"Unknown front matter field: '{field_name}'")

                # Still check for unexpected nested structures in unknown fields
                if isinstance(field_value, (dict, list)):
                    if isinstance(field_value, dict):
                        logger.warning(
                            f"Unknown field '{field_name}' contains nested "
                            f"dictionary structure"
                        )
                    elif isinstance(field_value, list):
                        for i, item in enumerate(field_value):
                            if isinstance(item, (dict, list)):
                                logger.warning(
                                    f"Unknown field '{field_name}[{i}]' contains "
                                    f"nested structure: {type(item).__name__}"
                                )

        return errors

    def normalize_content(self, data: Dict) -> Dict:
        """Normalize notebook content to consistent format.

        Validates front matter field types before normalization and raises errors
        for unexpected nested structures or types.
        """
        normalized = data.copy()

        # Normalize front matter
        if "front_matter" in normalized and isinstance(
            normalized["front_matter"], dict
        ):
            front_matter = normalized["front_matter"].copy()

            if type_errors := self._validate_front_matter_types(front_matter):
                # Raise an exception with all type validation errors
                raise ValueError(
                    f"Front matter type validation failed: {'; '.join(type_errors)}"
                )

            # Normalize title: strip whitespace and ensure string
            if "title" in front_matter and isinstance(front_matter["title"], str):
                front_matter["title"] = front_matter["title"].strip()

            # Normalize description: strip whitespace and ensure string
            if "description" in front_matter and isinstance(
                front_matter["description"], str
            ):
                front_matter["description"] = front_matter["description"].strip()

            # Normalize tags: always a list of lowercased strings
            if "tags" in front_matter:
                tags = front_matter["tags"]
                if isinstance(tags, str):
                    tags = [tags]
                elif not isinstance(tags, list):
                    tags = []
                front_matter["tags"] = [
                    tag.lower().strip() if isinstance(tag, str) else tag for tag in tags
                ]

            normalized["front_matter"] = front_matter

        return normalized

    def process(self, content: str) -> ProcessingResult:
        """Process and validate notebook content."""
        try:
            # Try to parse as structured YAML first
            try:
                yaml_data = yaml.safe_load(content)
                if (
                    isinstance(yaml_data, dict)
                    and "front_matter" in yaml_data
                    and "content" in yaml_data
                ):
                    # Content is already structured
                    data = yaml_data
                else:
                    # Fall back to front matter extraction
                    front_matter, remaining_content, errors = (
                        self._extract_front_matter(content)
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

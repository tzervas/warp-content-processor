"""
Processor for Warp Terminal rule files.
"""

import re
from typing import Dict, List, Tuple

import yaml

from ..base_processor import ProcessingResult, SchemaProcessor
from ..content_type import ContentType


class RuleProcessor(SchemaProcessor):
    """Processor for rule files."""

    def __init__(self) -> None:
        super().__init__()
        self.required_fields = {"title", "description"}
        self.optional_fields = {
            "examples",
            "guidelines",
            "standards",
            "rules",
            "priority",
            "category",
            "tags",
        }

        # Regex patterns
        self.title_pattern = re.compile(r"^[A-Z][\w\s-]*[a-zA-Z0-9]$")
        self.valid_tag_pattern = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")

    def _extract_guidelines(self, content: str) -> List[str]:
        """Extract guidelines from unstructured text."""
        guidelines = []

        # Look for numbered or bulleted lists
        list_patterns = [
            r"(?m)^\s*\d+\.\s*(.+)$",  # Numbered lists
            r"(?m)^\s*[-*•]\s*(.+)$",  # Bulleted lists
            r"(?m)^Guidelines?:\s*(.+)$",  # Guidelines heading
            r"(?m)^Rules?:\s*(.+)$",  # Rules heading
            r"(?m)^Standards?:\s*(.+)$",  # Standards heading
        ]

        for pattern in list_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                guideline = match.group(1).strip()
                if guideline and guideline not in guidelines:
                    guidelines.append(guideline)

        return guidelines

    def validate(self, data: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate rule data against schema."""
        errors = []
        warnings = []

        # Check required fields
        missing_fields = self.required_fields - set(data.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")

        # Validate title
        if "title" in data:
            if not isinstance(data["title"], str):
                errors.append("Field 'title' must be a string")
            elif not self.title_pattern.match(data["title"]):
                warnings.append(
                    "Title should start with a capital letter and contain only "
                    "letters, numbers, spaces, and hyphens"
                )

        # Validate description
        if "description" in data:
            if not isinstance(data["description"], str):
                errors.append("Field 'description' must be a string")
            elif len(data["description"]) < 10:
                warnings.append("Description seems too short")

        # Validate guidelines/standards/rules sections
        content_fields = {"guidelines", "standards", "rules"}
        has_content = False
        for field in content_fields:
            if field in data:
                has_content = True
                if isinstance(data[field], str):
                    data[field] = [data[field]]
                if not isinstance(data[field], list):
                    errors.append(
                        f"Field '{field}' must be a string or list of strings"
                    )
                else:
                    empty_items = [
                        i
                        for i, item in enumerate(data[field])
                        if not isinstance(item, str) or not item.strip()
                    ]
                    if empty_items:
                        errors.append(
                            f"Empty or invalid items in {field}: {empty_items}"
                        )

        if not has_content:
            warnings.append("No guidelines, standards, or rules content found")

        # Validate priority if present
        if "priority" in data:
            if not isinstance(data["priority"], (int, float)):
                errors.append("Priority must be a number")
            elif not 0 <= data["priority"] <= 1:
                errors.append("Priority must be between 0 and 1")

        # Validate category if present
        if "category" in data:
            if not isinstance(data["category"], str):
                errors.append("Category must be a string")

        # Validate tags
        if "tags" in data:
            if not isinstance(data["tags"], list):
                errors.append("Tags must be a list")
            else:
                invalid_tags = [
                    tag
                    for tag in data["tags"]
                    if not isinstance(tag, str) or not self.valid_tag_pattern.match(tag)
                ]
                if invalid_tags:
                    warnings.append(f"Invalid tag format: {invalid_tags}")

        return len(errors) == 0, errors, warnings

    def process(self, content: str) -> ProcessingResult:
        """Process and validate rule content."""
        try:
            # Try to parse as YAML first
            try:
                data = yaml.safe_load(content)
                if not isinstance(data, dict):
                    data = None
            except yaml.YAMLError:
                data = None

            # If YAML parsing failed, try to extract structured data from text
            if not data:
                lines = content.split("\n")
                data = {}

                # Try to find title
                for line in lines:
                    if line.strip() and not line.startswith("#"):
                        data["title"] = line.strip()
                        break

                # Try to find description
                desc_lines = []
                for line in lines[1:]:
                    if line.strip() and not line.startswith(("#", "-", "*", "1.")):
                        desc_lines.append(line.strip())
                    elif desc_lines:
                        break
                if desc_lines:
                    data["description"] = " ".join(desc_lines)

                # Extract guidelines
                guidelines = self._extract_guidelines(content)
                if guidelines:
                    data["guidelines"] = guidelines

            # Validate the data
            is_valid, errors, warnings = self.validate(data)

            return ProcessingResult(
                content_type=ContentType.RULE,
                is_valid=is_valid,
                data=data if is_valid else None,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            return ProcessingResult(
                content_type=ContentType.RULE,
                is_valid=False,
                data=None,
                errors=[f"Error processing rule: {str(e)}"],
                warnings=[],
            )

    def generate_filename(self, data: Dict) -> str:
        """Generate filename for rule content."""
        title = data.get("title", "unnamed_rule")
        # Clean title for use as filename
        clean_title = "".join(c if c.isalnum() else "_" for c in title.lower())

        # Add category prefix if present
        category = data.get("category", "").lower()
        if category:
            clean_category = "".join(c if c.isalnum() else "_" for c in category)
            return f"{clean_category}_{clean_title}.yaml"

        return f"{clean_title}.yaml"

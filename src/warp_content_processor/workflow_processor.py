"""
Workflow processor for Warp Terminal workflow files.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .base_processor import ProcessingResult, SchemaProcessor
from .content_type import ContentType
from .utils.validation import validate_placeholders, validate_tags

logger = logging.getLogger(__name__)


class WorkflowValidator(SchemaProcessor):
    """Validates workflow YAML files against schema requirements."""

    def __init__(self) -> None:
        super().__init__()
        self.required_fields = {"name", "command"}
        self.optional_fields = {
            "description",
            "arguments",
            "tags",
            "source_url",
            "author",
            "author_url",
            "shells",
        }
        self.known_shells = {"bash", "zsh", "fish", "pwsh", "cmd"}
        self.logger = logging.getLogger(__name__)

        # Regex patterns
        self.command_pattern = re.compile(r"{{[a-zA-Z_][a-zA-Z0-9_]*}}")
        self.valid_tag_pattern = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")

    def normalize_content(self, data: Dict) -> Dict:
        """Normalize workflow content to consistent format."""
        normalized = data.copy()

        # Normalize shells to lowercase
        if "shells" in normalized:
            normalized["shells"] = [
                s.lower() if isinstance(s, str) else s for s in normalized["shells"]
            ]

        # Normalize tags to lowercase
        if "tags" in normalized:
            normalized["tags"] = [
                t.lower() if isinstance(t, str) else t for t in normalized["tags"]
            ]

        # Ensure arguments is a list
        if "arguments" in normalized and not isinstance(normalized["arguments"], list):
            self.logger.warning(
                "'arguments' field is not a list (got type %s). Discarding its value.",
                type(normalized["arguments"]).__name__,
            )
            normalized["arguments"] = []

        # Normalize argument fields
        if "arguments" in normalized:
            for arg in normalized["arguments"]:
                if isinstance(arg, dict):
                    # Ensure required argument fields
                    if "name" not in arg:
                        arg["name"] = "unnamed_arg"
                    if "type" not in arg:
                        arg["type"] = "text"
                    # Convert type to lowercase
                    arg["type"] = arg["type"].lower()

        return normalized

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate workflow data against schema.

        Args:
            data: Dictionary of workflow data to validate

        Returns:
            Tuple containing:
                bool: Whether the data is valid
                List[str]: Error messages
                List[str]: Warning messages
                Optional[Dict[str, Any]]: Normalized data if valid, None otherwise
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Make a copy for normalization
        normalized_data = data.copy()

        # Check for empty data
        if not normalized_data:
            errors.append("Empty or invalid workflow data")
            return False, errors, warnings

        # Check required fields
        missing_fields = self.required_fields - set(normalized_data.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {missing_fields}")

        # Validate types
        if "name" in data and not isinstance(data["name"], str):
            errors.append("Field 'name' must be a string")
        if "command" in data and not isinstance(data["command"], str):
            errors.append("Field 'command' must be a string")

        # Check for unknown fields
        unknown_fields = (
            set(normalized_data.keys()) - self.required_fields - self.optional_fields
        )
        if unknown_fields:
            warnings.append(f"Unknown fields present: {unknown_fields}")

        # Validate command placeholders match arguments
        if "command" in data and isinstance(data["command"], str):
            if "arguments" in data:
                arg_errors, arg_warnings = validate_placeholders(
                    data["command"], data.get("arguments", [])
                )
                errors.extend(arg_errors)
                warnings.extend(arg_warnings)

        # Validate tags
        if "tags" in data:
            tag_errors, tag_warnings = validate_tags(
                data.get("tags", []), pattern=self.valid_tag_pattern.pattern
            )
            errors.extend(tag_errors)
            warnings.extend(tag_warnings)

        # Validate shells
        if "shells" in data:
            if not isinstance(data["shells"], list):
                errors.append("'shells' must be a list")
            else:
                # Make a copy of shells for normalization
                shells = data["shells"].copy()
                normalized_shells = [
                    s.lower() if isinstance(s, str) else s for s in shells
                ]
                unknown_shells = [
                    orig
                    for orig, norm in zip(shells, normalized_shells)
                    if norm not in self.known_shells
                ]
                if unknown_shells:
                    warnings.append(f"Unknown shell types: {unknown_shells}")
                # Update shells to normalized versions
                data["shells"] = normalized_shells

        # Only return normalized data if validation passed
        # Store normalized data for later use if validation passes
        self._last_normalized_data = normalized_data if len(errors) == 0 else None

        return len(errors) == 0, errors, warnings

    def process(self, content: str) -> ProcessingResult:
        """Process and validate workflow content."""
        errors: List[str] = []
        warnings: List[str] = []
        data = None

        # Early returns for invalid content
        if not content:
            errors.append("Empty content provided")
        elif content.isspace():
            errors.append("Content contains only whitespace")
        else:
            try:
                data = yaml.safe_load(content)
                # Handle None (empty YAML) and empty structures
                if data is None or (isinstance(data, (dict, list)) and not data):
                    errors.append(
                        "Empty YAML content (document contains no actual data)"
                    )
                elif not isinstance(data, dict):
                    errors.append("Content must be a YAML dictionary")
                else:
                    # Validate content
                    is_valid, val_errors, val_warnings = self.validate(data)
                    normalized_data = self._last_normalized_data
                    if is_valid:
                        return ProcessingResult(
                            content_type=ContentType.WORKFLOW,
                            is_valid=True,
                            data=normalized_data,
                            errors=[],
                            warnings=val_warnings,
                        )
                    errors.extend(val_errors)
                    warnings.extend(val_warnings)
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax: {str(e)}")
            except Exception as e:
                errors.append(f"Error processing workflow: {str(e)}")

        # Return error result if we get here
        return ProcessingResult(
            content_type=ContentType.WORKFLOW,
            is_valid=False,
            data=None,
            errors=errors,
            warnings=warnings,
        )

    def generate_filename(self, data: Dict) -> str:
        """Generate filename for workflow content."""
        name = data.get("name", "unnamed_workflow")
        # Clean name for use as filename
        clean_name = "".join(c if c.isalnum() else "_" for c in name.lower())
        return f"{clean_name}.yaml"


class WorkflowProcessor(WorkflowValidator):
    """Main class for processing workflow files."""

    def __init__(self, output_dir: Path) -> None:
        super().__init__()
        self.output_dir = Path(output_dir)
        self.processed_files: List[Tuple[Path, Path]] = []
        self.failed_files: List[Tuple[Path, str]] = []
        self.warnings: List[Tuple[Path, str]] = []
        self._last_normalized_data: Optional[Dict[str, Any]] = None

        os.makedirs(self.output_dir, exist_ok=True)

    def process_file(self, file_path: Path) -> bool:
        """
        Process a single workflow file.

        Returns:
            bool: True if processing was successful
        """
        try:
            content = file_path.read_text(encoding="utf-8")
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
                    logger.error(
                        f"Validation failed for workflow in {file_path}: "
                        f"{result.errors}"
                    )
                    self.failed_files.append((file_path, result.errors[0]))
                    success = False
                    continue

                # Log any warnings
                for warning in result.warnings:
                    logger.warning(f"Warning for {file_path}: {warning}")
                    self.warnings.append((file_path, warning))

                # Generate output filename and save
                if result.data is not None:
                    filename = self.generate_filename(result.data)
                    output_path = self.output_dir / filename
                else:
                    continue

                # Ensure unique filename
                counter = 1
                while output_path.exists():
                    base_name = filename.rsplit(".", 1)[0]
                    output_path = self.output_dir / f"{base_name}_{counter}.yaml"
                    counter += 1

                output_path.write_text(yaml.dump(result.data), encoding="utf-8")
                logger.info(f"Created workflow file: {output_path}")
                self.processed_files.append((file_path, output_path))

            return success

        except Exception as e:
            logger.error("Error processing %s: %s", file_path, str(e))
            self.failed_files.append((file_path, str(e)))
            return False

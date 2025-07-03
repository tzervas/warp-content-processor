"""
Processor for Warp Terminal environment variable files.
"""

import re
from typing import Dict, List, Optional, Tuple

import yaml

from ..base_processor import ProcessingResult, SchemaProcessor
from ..content_type import ContentType


class EnvVarProcessor(SchemaProcessor):
    """Processor for environment variable files."""

    def __init__(self, output_dir=None) -> None:
        super().__init__()
        self.required_fields = {"variables"}
        self.optional_fields = {"description", "scope", "platform"}
        self.output_dir = output_dir

        # Regex patterns
        self.var_name_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
        self.export_pattern = re.compile(r"^export\s+([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$")
        self.simple_assign_pattern = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)=(.*)$")

    def _parse_env_line(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse a single environment variable line."""
        line = line.strip()
        if not line or line.startswith("#"):
            return None, None

        # Try export format
        match = self.export_pattern.match(line)
        if match:
            name, value = match.groups()
            return str(name), str(value)

        # Try simple assignment format
        match = self.simple_assign_pattern.match(line)
        if match:
            name, value = match.groups()
            return str(name), str(value)

        return None, None

    def _extract_variables(self, content: str) -> Dict[str, str]:
        """Extract variables from content in various formats."""
        variables: Dict[str, str] = {}

        try:
            # Try YAML format first
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                if "variables" in data and isinstance(data["variables"], dict):
                    return {str(k): str(v) for k, v in data["variables"].items()}
                elif all(self.var_name_pattern.match(str(k)) for k in data.keys()):
                    return {str(k): str(v) for k, v in data.items()}
        except yaml.YAMLError:
            pass

        # If YAML parsing fails, try line-by-line parsing
        for line in content.split("\n"):
            name, value = self._parse_env_line(line)
            if name and value:
                variables[name] = value

        return variables

    def validate(self, data: Dict) -> Tuple[bool, List[str], List[str]]:
        """Validate environment variable data against schema."""
        errors = []
        warnings = []

        # Check for variables section
        variables = data.get("variables", {})
        if not variables:
            errors.append("No variables defined")

        # Validate variable names and values
        if isinstance(variables, dict):
            invalid_names = [
                name
                for name in variables.keys()
                if not self.var_name_pattern.match(name)
            ]
            if invalid_names:
                errors.append(f"Invalid variable names: {invalid_names}")

            # Check for empty values
            empty_vars = [
                name for name, value in variables.items() if not str(value).strip()
            ]
            if empty_vars:
                warnings.append(f"Variables with empty values: {empty_vars}")

            # Check for common patterns that might indicate secrets
            secret_patterns = [
                (r"password", "password"),
                (r"secret", "secret"),
                (r"token", "token"),
                (r"key", "key"),
                (r"cert", "certificate"),
            ]

            potential_secrets = []
            for name in variables.keys():
                for pattern, kind in secret_patterns:
                    if re.search(pattern, name, re.IGNORECASE):
                        potential_secrets.append(f"{name} (possible {kind})")

            if potential_secrets:
                warnings.append(
                    f"Potential secrets detected: {potential_secrets}. "
                    "Consider using a secrets management solution."
                )
        else:
            errors.append("'variables' must be a dictionary")

        # Validate platform specification if present
        if "platform" in data:
            valid_platforms = {"linux", "macos", "windows", "all"}
            platforms = data["platform"]
            if isinstance(platforms, str):
                platforms = [platforms]

            if not isinstance(platforms, list):
                errors.append("'platform' must be a string or list of strings")
            else:
                invalid_platforms = set(platforms) - valid_platforms
                if invalid_platforms:
                    errors.append(f"Invalid platforms: {invalid_platforms}")

        # Validate scope if present
        if "scope" in data:
            valid_scopes = {"user", "system", "session"}
            scope = data["scope"]
            if scope not in valid_scopes:
                errors.append(f"Invalid scope: {scope}")

        return len(errors) == 0, errors, warnings

    def normalize_content(self, data: Dict) -> Dict:
        """Normalize environment variable content to consistent format."""
        normalized = data.copy()

        # Normalize platform specification
        if "platform" in normalized:
            platform = normalized["platform"]
            if isinstance(platform, str):
                normalized["platform"] = [platform.lower()]
            elif isinstance(platform, list):
                normalized["platform"] = [
                    p.lower() if isinstance(p, str) else p for p in platform
                ]

        # Normalize scope
        if "scope" in normalized and isinstance(normalized["scope"], str):
            normalized["scope"] = normalized["scope"].lower()

        return normalized

    def process(self, content: str) -> ProcessingResult:
        """Process and validate environment variable content."""
        try:
            # Extract variables from content
            variables = self._extract_variables(content)

            # Prepare complete data for validation
            data = {
                "variables": variables,
                "scope": "user",  # Default scope
                "platform": "all",  # Default platform
            }

            # Try to extract additional metadata if content is YAML
            try:
                yaml_data = yaml.safe_load(content)
                if isinstance(yaml_data, dict):
                    data.update(
                        {
                            k: v
                            for k, v in yaml_data.items()
                            if k in self.optional_fields
                        }
                    )
            except yaml.YAMLError:
                pass

            # Validate the data
            is_valid, errors, warnings = self.validate(data)

            return ProcessingResult(
                content_type=ContentType.ENV_VAR,
                is_valid=is_valid,
                data=data if is_valid else None,
                errors=errors,
                warnings=warnings,
            )

        except Exception as e:
            return ProcessingResult(
                content_type=ContentType.ENV_VAR,
                is_valid=False,
                data=None,
                errors=[f"Error processing environment variables: {str(e)}"],
                warnings=[],
            )

    def generate_filename(self, data: Dict) -> str:
        """Generate filename for environment variable content."""
        # Use platform and scope in filename if specified
        parts = []

        platform = data.get("platform", "all")
        if isinstance(platform, list):
            platform = "_".join(sorted(platform))
        parts.append(platform)

        scope = data.get("scope", "user")
        parts.append(scope)

        # Add a hash of variables to ensure uniqueness
        var_names = "_".join(sorted(data["variables"].keys()))
        if len(var_names) > 30:
            import hashlib

            # Using SHA-256 for non-cryptographic purposes
            var_hash = hashlib.sha256(var_names.encode()).hexdigest()[:8]
            parts.append(var_hash)
        else:
            parts.append(var_names)

        return f"env_{'_'.join(parts)}.yaml"

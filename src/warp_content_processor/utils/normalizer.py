"""
Content normalization utilities for handling poorly formatted input.
Standardizes mixed YAML, Markdown, and plain text into consistent formats.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

import yaml

from .security import ContentSanitizer, secure_yaml_dump, secure_yaml_load

logger = logging.getLogger(__name__)


class ContentNormalizer:
    """Normalizes and standardizes content from various messy formats."""

    @staticmethod
    def normalize_yaml_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
        """
        Extract and normalize YAML frontmatter from Markdown-style content.

        Args:
            content: Raw content that may contain frontmatter

        Returns:
            Tuple[Optional[Dict], str]: (frontmatter_dict, remaining_content)
        """
        content = ContentSanitizer.sanitize_string(content)

        # First strip leading whitespace from each line to normalize indentation
        lines = content.split("\n")
        # Find minimum indentation (excluding empty lines)
        min_indent = float("inf")
        for line in lines:
            if line.strip():  # Skip empty lines
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)

        if min_indent != float("inf") and min_indent > 0:
            # Remove common leading whitespace
            normalized_lines = []
            for line in lines:
                if line.strip():  # For non-empty lines, remove common indent
                    normalized_lines.append(
                        line[min_indent:] if len(line) > min_indent else line
                    )
                else:  # Keep empty lines as-is
                    normalized_lines.append(line)
            content = "\n".join(normalized_lines)

        # Match YAML frontmatter patterns (after normalization, content starts with ---)
        frontmatter_patterns = [
            r"^---\s*\n(.*?)\n---\s*\n(.*)$",  # Standard frontmatter
            r"^---\s*\n(.*?)\n---\s*(.*)$",  # Without trailing newline
            r"^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n(.*)$",  # TOML-style markers
            r"^\s*---\s*\n(.*?)\n\s*---\s*\n(.*)$",  # With leading whitespace
<<<<<<< HEAD
            r"^\s*---\s*\n(.*?)\n\s*---\s*(.*)$",  # With leading whitespace, no trailing newline
        ]

        for pattern in frontmatter_patterns:
            match = re.match(pattern, content, re.DOTALL)
            if match:
=======
            # With leading whitespace, no trailing newline
            r"^\s*---\s*\n(.*?)\n\s*---\s*(.*)$",
        ]

        for pattern in frontmatter_patterns:
            if match := re.match(pattern, content, re.DOTALL):
>>>>>>> main
                yaml_content, remaining = match.groups()
                try:
                    frontmatter = secure_yaml_load(yaml_content)
                    return frontmatter, remaining.strip()
                except (yaml.YAMLError, Exception) as e:
                    logger.warning(f"Failed to parse frontmatter: {e}")
                    continue

        return None, content

    @staticmethod
    def normalize_messy_yaml(content: str) -> str:
        """
        Clean up and standardize messy YAML content.

        Args:
            content: Messy YAML content

        Returns:
            str: Normalized YAML content
        """
        content = ContentSanitizer.sanitize_string(content)

        # Fix common YAML formatting issues
        fixes = [
            # Fix missing spaces after colons
            (r"(\w):([^\s])", r"\1: \2"),
            # Fix missing spaces in lists
            (r"^(\s*)-([^\s])", r"\1- \2"),
            # Fix tabs to spaces
            (r"\t", "  "),
            # Fix Windows line endings
            (r"\r\n", "\n"),
            # Fix multiple consecutive blank lines
            (r"\n\s*\n\s*\n+", "\n\n"),
            # Fix trailing whitespace
            (r"[ \t]+$", ""),
        ]

        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        # Try to parse and re-dump to ensure valid YAML
        try:
            data = secure_yaml_load(content)
            if data is not None:
                content = secure_yaml_dump(data)
        except (yaml.YAMLError, Exception) as e:
            logger.warning(f"Could not normalize YAML structure: {e}")

        return content.strip()

    @staticmethod
    def extract_code_blocks(content: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from Markdown content.

        Args:
            content: Markdown content

        Returns:
            List[Dict[str, str]]: List of code blocks with language and content
        """
        content = ContentSanitizer.sanitize_string(content)

        code_blocks = []

        # Match fenced code blocks
        pattern = r"```(\w+)?\s*\n(.*?)\n```"
        matches = re.finditer(pattern, content, re.DOTALL)

        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2).strip()

            code_blocks.append({"language": language, "content": code})

        return code_blocks

    @staticmethod
    def normalize_workflow_content(content: str) -> Dict:
        """
        Normalize workflow content from various formats.

        Args:
            content: Raw workflow content

        Returns:
            Dict: Normalized workflow data
        """
        content = ContentSanitizer.sanitize_string(content)

        # Extract frontmatter if present
        frontmatter, remaining = ContentNormalizer.normalize_yaml_frontmatter(content)

        # Start with frontmatter or empty dict
<<<<<<< HEAD
        workflow = frontmatter if frontmatter else {}
=======
        workflow = frontmatter or {}
>>>>>>> main

        # Try to parse remaining content as YAML
        if remaining:
            try:
                yaml_data = secure_yaml_load(remaining)
                if isinstance(yaml_data, dict):
                    workflow.update(yaml_data)
                # Always try to extract additional info from text too
                text_data = ContentNormalizer._extract_workflow_from_text(remaining)
                # Add any fields not already present
                for key, value in text_data.items():
                    if key not in workflow:
                        workflow[key] = value
            except (yaml.YAMLError, Exception):
                # If not YAML, try to extract workflow info from text
                workflow.update(
                    ContentNormalizer._extract_workflow_from_text(remaining)
                )

        # Ensure required fields and normalize values
        workflow = ContentNormalizer._normalize_workflow_fields(workflow)

        return workflow

    @staticmethod
    def _extract_workflow_from_text(text: str) -> Dict:
        """Extract workflow information from plain text."""
        workflow = {}

        # Extract name from first line or heading
        lines = text.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            # Remove Markdown heading markers and comments
            first_line = re.sub(r"^#+\s*", "", first_line)
            first_line = re.sub(r"^#\s*", "", first_line)
            if first_line and not workflow.get("name"):
                workflow["name"] = first_line

        # Look for command patterns
        command_patterns = [
            r"command:\s*(.+)",
            r"cmd:\s*(.+)",
            r"run:\s*(.+)",
            r"execute:\s*(.+)",
        ]

        for pattern in command_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                workflow["command"] = match.group(1).strip()
                break

        # Look for description
        desc_patterns = [
            r"description:\s*(.+)",
            r"desc:\s*(.+)",
            r"about:\s*(.+)",
        ]

        for pattern in desc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                workflow["description"] = match.group(1).strip()
                break

        return workflow

    @staticmethod
    def _normalize_workflow_fields(workflow: Dict) -> Dict:
        """Normalize workflow field values."""
        normalized = {}

        # Normalize name
        if "name" in workflow:
            normalized["name"] = str(workflow["name"]).strip()

        # Normalize command
        if "command" in workflow:
            normalized["command"] = str(workflow["command"]).strip()

        # Normalize description
        if "description" in workflow:
            normalized["description"] = str(workflow["description"]).strip()

        # Normalize tags (ensure list of strings)
        if "tags" in workflow:
            tags = workflow["tags"]
            if isinstance(tags, str):
                # Split comma or space separated tags
                tags = re.split(r"[,\s]+", tags)
            if isinstance(tags, list):
                normalized["tags"] = [str(tag).strip().lower() for tag in tags if tag]

        # Normalize shells (ensure list of strings)
        if "shells" in workflow:
            shells = workflow["shells"]
            if isinstance(shells, str):
                shells = re.split(r"[,\s]+", shells)
            if isinstance(shells, list):
                normalized["shells"] = [
                    str(shell).strip().lower() for shell in shells if shell
                ]

        # Normalize arguments
        if "arguments" in workflow:
            args = workflow["arguments"]
            if isinstance(args, list):
                normalized_args = []
                for arg in args:
                    if isinstance(arg, dict):
                        normalized_arg = {}
                        if "name" in arg:
                            normalized_arg["name"] = str(arg["name"]).strip()
                        if "description" in arg:
                            normalized_arg["description"] = str(
                                arg["description"]
                            ).strip()
                        if "default_value" in arg:
                            normalized_arg["default_value"] = str(arg["default_value"])
                        if normalized_arg:
                            normalized_args.append(normalized_arg)
                normalized["arguments"] = normalized_args

        return normalized

    @staticmethod
    def normalize_prompt_content(content: str) -> Dict:
        """
        Normalize prompt content from various formats.

        Args:
            content: Raw prompt content

        Returns:
            Dict: Normalized prompt data
        """
        content = ContentSanitizer.sanitize_string(content)

        # Extract frontmatter if present
        frontmatter, remaining = ContentNormalizer.normalize_yaml_frontmatter(content)

        # Start with frontmatter or empty dict
<<<<<<< HEAD
        prompt = frontmatter if frontmatter else {}
=======
        prompt = frontmatter or {}
>>>>>>> main

        # If remaining content exists, try to extract prompt info
        if remaining:
            try:
                yaml_data = secure_yaml_load(remaining)
                if isinstance(yaml_data, dict):
                    prompt.update(yaml_data)
                # If remaining content is not parsed as YAML but contains prompt text
                if not prompt.get("prompt") and remaining.strip():
                    prompt["prompt"] = remaining.strip()
            except (yaml.YAMLError, Exception):
                # If not YAML, treat as prompt text
                if not prompt.get("prompt"):
                    prompt["prompt"] = remaining.strip()

        # Normalize prompt fields
        prompt = ContentNormalizer._normalize_prompt_fields(prompt)

        return prompt

    @staticmethod
    def _normalize_prompt_fields(prompt: Dict) -> Dict:
        """Normalize prompt field values."""
        normalized = {}

        # Normalize name
        if "name" in prompt:
            normalized["name"] = str(prompt["name"]).strip()

        # Normalize prompt text
        if "prompt" in prompt:
            normalized["prompt"] = str(prompt["prompt"]).strip()

        # Normalize description
        if "description" in prompt:
            normalized["description"] = str(prompt["description"]).strip()

        # Normalize arguments (same as workflow)
        if "arguments" in prompt:
            args = prompt["arguments"]
            if isinstance(args, list):
                normalized_args = []
                for arg in args:
                    if isinstance(arg, dict):
                        normalized_arg = {}
                        if "name" in arg:
                            normalized_arg["name"] = str(arg["name"]).strip()
                        if "description" in arg:
                            normalized_arg["description"] = str(
                                arg["description"]
                            ).strip()
                        if "default_value" in arg:
                            normalized_arg["default_value"] = str(arg["default_value"])
                        if normalized_arg:
                            normalized_args.append(normalized_arg)
                normalized["arguments"] = normalized_args

        # Normalize tags
        if "tags" in prompt:
            tags = prompt["tags"]
            if isinstance(tags, str):
                tags = re.split(r"[,\s]+", tags)
            if isinstance(tags, list):
                normalized["tags"] = [str(tag).strip().lower() for tag in tags if tag]

        return normalized

    @staticmethod
    def normalize_mixed_content(content: str) -> List[Tuple[str, Dict]]:
        """
        Normalize mixed content containing multiple document types.

        Args:
            content: Mixed content string

        Returns:
            List[Tuple[str, Dict]]: List of (content_type, normalized_data) pairs
        """
        content = ContentSanitizer.sanitize_string(content)
        documents = []

        # Split by document separators
        parts = re.split(r"^---\s*$", content, flags=re.MULTILINE)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Try to determine content type and normalize
            try:
                # First try as YAML
                yaml_data = secure_yaml_load(part)
                if isinstance(yaml_data, dict):
                    content_type = ContentNormalizer._detect_content_type(yaml_data)
                    if content_type == "workflow":
                        normalized = ContentNormalizer._normalize_workflow_fields(
                            yaml_data
                        )
                    elif content_type == "prompt":
                        normalized = ContentNormalizer._normalize_prompt_fields(
                            yaml_data
                        )
                    else:
                        normalized = yaml_data

                    documents.append((content_type, normalized))
                    continue
            except (yaml.YAMLError, Exception):
                pass

            # If not YAML, try to detect from text patterns
            content_type = ContentNormalizer._detect_text_content_type(part)

            if content_type == "workflow":
                normalized = ContentNormalizer.normalize_workflow_content(part)
                documents.append((content_type, normalized))
            elif content_type == "prompt":
                normalized = ContentNormalizer.normalize_prompt_content(part)
                documents.append((content_type, normalized))
            else:
                # Treat as generic content
                documents.append(("unknown", {"content": part}))

        return documents

    @staticmethod
    def _detect_content_type(data: Dict) -> str:
        """Detect content type from structured data."""
        # Check for workflow indicators
        if "command" in data or ("name" in data and "shells" in data):
            return "workflow"

        # Check for prompt indicators
        if "prompt" in data or ("name" in data and "arguments" in data):
            return "prompt"

        # Check for rule indicators
        if "guidelines" in data or ("title" in data and "description" in data):
            return "rule"

        # Check for environment variables
        if "variables" in data or "environment" in data:
            return "env_var"

        # Check for notebook indicators
<<<<<<< HEAD
        if "title" in data and ("tags" in data or "description" in data):
            return "notebook"

        return "unknown"
=======
        return "notebook" if "title" in data and "tags" in data else "unknown"
>>>>>>> main

    @staticmethod
    def _detect_text_content_type(text: str) -> str:
        """Detect content type from plain text patterns."""
        text_lower = text.lower()

        # Look for workflow patterns
        if re.search(r"(command|cmd|execute|run):\s*\S+", text_lower):
            return "workflow"

        # Look for prompt patterns
        if re.search(r"prompt:\s*\S+", text_lower) or "{{" in text:
            return "prompt"

        # Look for rule patterns
        if re.search(r"(guidelines?|rules?):\s*", text_lower):
            return "rule"

        # Look for environment variable patterns
        if re.search(r"(variables?|environment):\s*", text_lower):
            return "env_var"

        # Look for notebook patterns (markdown headers + code blocks)
        if re.search(r"^#+\s+", text, re.MULTILINE) and "```" in text:
            return "notebook"

        return "unknown"

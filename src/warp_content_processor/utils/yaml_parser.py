"""Enhanced YAML parsing utilities with robust error handling."""

import re
from typing import Any, Dict, List, Optional, Tuple

import yaml


class YAMLParsingResult:
    """Result of a YAML parsing operation."""

    def __init__(
        self,
        content: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        warnings: Optional[List[str]] = None,
        line_number: Optional[int] = None,
        column: Optional[int] = None,
    ):
        self.content = content
        self.error = error
        self.warnings = warnings or []
        self.line_number = line_number
        self.column = column

    @property
    def is_valid(self) -> bool:
        """Return whether the parsing was successful."""
        return self.content is not None and self.error is None


def parse_yaml_enhanced(content: str) -> YAMLParsingResult:
    """Parse YAML content with enhanced error handling and validation.

    Args:
        content: YAML content to parse

    Returns:
        YAMLParsingResult object containing:
        - Parsed content if successful
        - Detailed error information if parsing failed
        - Any warnings generated during parsing
        - Line and column numbers for errors when available
    """
    if not content or not content.strip():
        return YAMLParsingResult(error="Empty YAML content")

    warnings = []
    try:
        # Try to parse the YAML content
        parsed = yaml.safe_load(content)

        # Validate the parsed content
        if parsed is None:
            return YAMLParsingResult(error="YAML content is empty or null")
        if not isinstance(parsed, dict):
            return YAMLParsingResult(
                error=f"Expected dictionary, got {type(parsed).__name__}"
            )

        # Check for common issues that should generate warnings
        if len(parsed) == 0:
            warnings.append("Empty YAML dictionary")
        for key, value in parsed.items():
            if not isinstance(key, str):
                warnings.append(f"Non-string key found: {key}")
            if isinstance(value, str) and not value.strip():
                warnings.append(f"Empty string value for key: {key}")

        return YAMLParsingResult(content=parsed, warnings=warnings)

    except yaml.MarkedYAMLError as e:
        # Handle YAML errors with position information
        line = e.problem_mark.line + 1 if e.problem_mark else None
        col = e.problem_mark.column + 1 if e.problem_mark else None

        problem = str(e.problem) if e.problem else "Unknown error"
        context = str(e.context) if e.context else None

        error_msg = f"YAML error at line {line}, column {col}: {problem}"
        if context:
            error_msg += f" ({context})"

        return YAMLParsingResult(error=error_msg, line_number=line, column=col)

    except yaml.YAMLError as e:
        return YAMLParsingResult(error=f"YAML parsing error: {str(e)}")

    except Exception as e:
        return YAMLParsingResult(error=f"Unexpected error parsing YAML: {str(e)}")


def parse_yaml_documents(content: str) -> List[YAMLParsingResult]:
    """Parse multi-document YAML content.

    Args:
        content: YAML content that may contain multiple documents

    Returns:
        List of YAMLParsingResult objects, one for each document found
    """
    if not content or not content.strip():
        return [YAMLParsingResult(error="Empty YAML content")]

    # Split content by document separator
    parts = re.split(r"^---\s*$", content.strip(), flags=re.MULTILINE)
    results = []

    # Process each part
    for part in parts:
        part = part.strip()
        if not part:
            continue

        try:
            doc = yaml.safe_load(part)
            if doc is None:
                results.append(YAMLParsingResult(error="Empty document"))
            elif not isinstance(doc, dict):
                results.append(
                    YAMLParsingResult(
                        error=f"Document is not a dictionary: {type(doc).__name__}"
                    )
                )
            else:
                results.append(YAMLParsingResult(content=doc))
        except yaml.MarkedYAMLError as e:
            line = e.problem_mark.line + 1 if e.problem_mark else None
            col = e.problem_mark.column + 1 if e.problem_mark else None
            problem = str(e.problem) if e.problem else "Unknown error"
            context = str(e.context) if e.context else None
            error = f"YAML error at line {line}, column {col}: {problem}"
            if context:
                error += f" ({context})"
            results.append(YAMLParsingResult(error=error, line_number=line, column=col))
        except yaml.YAMLError as e:
            results.append(YAMLParsingResult(error=f"YAML parsing error: {str(e)}"))
        except Exception as e:
            results.append(
                YAMLParsingResult(error=f"Unexpected error parsing YAML: {str(e)}")
            )

    return results or [YAMLParsingResult(error="No documents found")]

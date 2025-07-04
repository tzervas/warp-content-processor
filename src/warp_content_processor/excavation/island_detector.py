"""
Schema Island Detector - Finds potential schema content within contaminated data.

Following SRP: Only responsible for identifying potential schema islands.
Following KISS: Simple pattern-based detection with confidence scoring.
Following DRY: Reuses existing content detection patterns.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from .artifacts import ContaminationType

class SchemaIslandDetector:
    """Schema island detector for finding valid content in contaminated data."""
    
    def __init__(self):
        """Initialize patterns for schema detection."""
        self.contamination_patterns = {
            ContaminationType.LOG_PREFIXES: re.compile(
                r"^\d{4}-\d{2}-\d{2}[\s\[]|^INFO|^DEBUG|^ERROR|^WARN", re.MULTILINE
            ),
        }

    def _clean_log_prefixes(self, cleaned: str, warnings: List[str]) -> str:
        """Clean log prefixes from text, using correct regex patterns."""
        lines = cleaned.split("\n")
        cleaned_lines = []
        removed_count = 0

        for line in lines:
            # Remove common log prefixes using correct patterns without escaped backslashes
            cleaned_line = re.sub(r"^\d{4}-\d{2}-\d{2}[\s\[].*?\]\s*", "", line)
            cleaned_line = re.sub(
                r"^(INFO|DEBUG|ERROR|WARN)\s*[:\-]\s*", "", cleaned_line
            )

            if cleaned_line != line:
                removed_count += 1

            if cleaned_line.strip():  # Keep non-empty lines
                cleaned_lines.append(cleaned_line)

        if removed_count > 0:
            warnings.append(f"Cleaned {removed_count} log prefix lines")

        return "\n".join(cleaned_lines)

    def _clean_content(
        self, content: str, contamination_types: Set[ContaminationType]
    ) -> Tuple[str, List[str]]:
        """Clean contaminated content and return warnings."""
        cleaned = content
        if not content.strip():
            return content, []
        warnings: List[str] = []

        if ContaminationType.LOG_PREFIXES in contamination_types:
            cleaned = self._clean_log_prefixes(cleaned, warnings)

        return cleaned, warnings

"""Base classes for content processors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ProcessingResult:
    """Results from content processing."""

    content_type: str
    is_valid: bool
    data: Optional[Dict]
    errors: List[str]
    warnings: List[str]


class SchemaProcessor(ABC):
    """Base class for schema processors."""

    def __init__(self) -> None:
        self.required_fields: Set[str] = set()
        self.optional_fields: Set[str] = set()

    @abstractmethod
    def validate(self, data: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate data against schema.

        Returns:
            Tuple[bool, List[str], List[str]]: (is_valid, errors, warnings)
        """

    @abstractmethod
    def process(self, content: str) -> ProcessingResult:
        """
        Process and validate content.

        Returns:
            ProcessingResult: Processing results including validation status
        """

    @abstractmethod
    def generate_filename(self, data: Dict) -> str:
        """Generate appropriate filename for the content."""

    @abstractmethod
    def normalize_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize content to a consistent format.
        This method must not modify the input dictionary.

        Args:
            data: Dictionary of content data to normalize

        Returns:
            Dict[str, Any]: New dictionary with normalized content

        Note:
            This method MUST NOT modify the input dictionary.
            Always return a new dictionary with normalized content.
        """
        return data.copy()  # Base implementation returns a shallow copy

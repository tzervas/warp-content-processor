"""Base classes for content processors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

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
    
    def __init__(self):
        self.required_fields: Set[str] = set()
        self.optional_fields: Set[str] = set()
    
    @abstractmethod
    def validate(self, data: Dict) -> Tuple[bool, List[str], List[str]]:
        """
        Validate data against schema.
        
        Returns:
            Tuple[bool, List[str], List[str]]: (is_valid, errors, warnings)
        """
        pass
    
    @abstractmethod
    def process(self, content: str) -> ProcessingResult:
        """
        Process and validate content.
        
        Returns:
            ProcessingResult: Processing results including validation status
        """
        pass
    
    @abstractmethod
    def generate_filename(self, data: Dict) -> str:
        """Generate appropriate filename for the content."""
        pass
        
    def normalize_content(self, data: Dict) -> Dict:
        """
        Normalize content to a consistent format.
        Override this method in derived classes to implement specific normalization.
        
        Args:
            data: Dictionary of data to normalize
        
        Returns:
            Dict: Normalized data
        """
        return data  # Default implementation returns unmodified data

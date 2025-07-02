"""Warp Terminal content processor package."""

__version__ = "0.1.0"

from .base_processor import ProcessingResult, SchemaProcessor
from .schema_processor import (
    ContentProcessor,
    ContentSplitter,
    SchemaDetector,
    ContentType,
)
from .workflow_processor import WorkflowProcessor, WorkflowValidator
from .processors import (
    PromptProcessor,
    NotebookProcessor,
    EnvVarProcessor,
    RuleProcessor,
)

__all__ = [
    # Base classes
    'ProcessingResult',
    'SchemaProcessor',
    
    # Core functionality
    'ContentProcessor',
    'ContentSplitter',
    'SchemaDetector',
    'ContentType',
    
    # Processors
    'WorkflowProcessor',
    'WorkflowValidator',
    'PromptProcessor',
    'NotebookProcessor',
    'EnvVarProcessor',
    'RuleProcessor',
]

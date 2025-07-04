"""Warp Terminal content processor package."""

__version__ = "0.1.0"

from .base_processor import ProcessingResult, SchemaProcessor
from .processors import (
    EnvVarProcessor,
    NotebookProcessor,
    PromptProcessor,
    RuleProcessor,
)
from .processors.schema_processor import (
    ContentProcessor,
    ContentSplitter,
    ContentType,
    ContentTypeDetector,
)
from .processors.workflow_processor import WorkflowProcessor, WorkflowValidator

__all__ = [
    # Base classes
    "ProcessingResult",
    "SchemaProcessor",
    # Core functionality
    "ContentProcessor",
    "ContentSplitter",
    "ContentTypeDetector",
    "ContentType",
    # Processors
    "WorkflowProcessor",
    "WorkflowValidator",
    "PromptProcessor",
    "NotebookProcessor",
    "EnvVarProcessor",
    "RuleProcessor",
]

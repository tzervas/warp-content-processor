"""
Excavation module for extracting schema data from contaminated content.

This module handles massive mixed content parsing with robust error recovery.
"""

from .archaeologist import ContentArchaeologist
from .artifacts import (
    ContaminationType,
    ContentType,
    ExcavationResult,
    ExtractionConfidence,
    ExtractionContext,
    SchemaArtifact,
)
from .island_detector import ContentIsland, SchemaIslandDetector

__all__ = [
    "ContentArchaeologist",
    "SchemaIslandDetector",
    "ContentIsland",
    "SchemaArtifact",
    "ExcavationResult",
    "ExtractionContext",
    "ExtractionConfidence",
    "ContaminationType",
    "ContentType",
]

"""Artifacts for content excavation."""

from enum import Enum, auto

class ContaminationType(Enum):
    """Types of content contamination."""

    BINARY_DATA = auto()
    LOG_PREFIXES = auto()
    CODE_FRAGMENTS = auto()
    RANDOM_TEXT = auto()
    ENCODING_ISSUES = auto()
    MALFORMED_STRUCTURE = auto()

"""
Simple, robust parsers for handling mangled content.

This module follows KISS, SRP, and DRY principles:
- KISS: Each parser has a single, simple purpose
- SRP: Clear separation of concerns (detection, splitting, parsing, cleaning)
- DRY: Shared utilities and common patterns
"""

from .base import ErrorTolerantParser, ParseResult, ParsingStrategy
from .common_patterns import CommonPatterns, MangledContentCleaner
from .content_detector import ContentDetector
from .document_splitter import DocumentSplitter

__all__ = [
    "ParseResult",
    "ParsingStrategy",
    "ErrorTolerantParser",
    "ContentDetector",
    "DocumentSplitter",
    "CommonPatterns",
    "MangledContentCleaner",
]

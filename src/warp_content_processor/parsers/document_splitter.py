"""
Document boundary detection and splitting.

Following SRP: This class has exactly one responsibility - split documents.
Following KISS: Simple, clear splitting logic with multiple fallback strategies.
"""

import logging
import re
from typing import List

from .base import ParseResult, SimpleParser
from .common_patterns import CommonPatterns

logger = logging.getLogger(__name__)


class DocumentSplitter(SimpleParser):
    """
    Simple document splitter that finds document boundaries.

    SRP: Only responsible for splitting documents, no type detection or validation.
    KISS: Clear, predictable splitting with multiple strategies.
    """

    def __init__(self):
        super().__init__()
        self.split_count = 0
        self.multi_document_count = 0

    @property
    def parser_name(self) -> str:
        return "DocumentSplitter"

    def split(self, content: str) -> List[str]:
        """
        Split content into individual documents.

        Args:
            content: Raw content that may contain multiple documents

        Returns:
            List[str]: List of document content strings (at least one)
        """
        self._record_attempt(True)  # Always succeeds
        self.split_count += 1

        if not content or not content.strip():
            return [content] if content else [""]

        # Try different splitting strategies in order of preference
        strategies = [
            self._split_by_yaml_separators,
            self._split_by_common_separators,
            self._split_by_content_blocks,
        ]

        for strategy in strategies:
            try:
                documents = strategy(content)
                if len(documents) > 1:
                    self.multi_document_count += 1
                    logger.debug(
                        f"Split into {len(documents)} documents using {strategy.__name__}"
                    )
                    return documents
            except Exception as e:
                logger.debug(f"Splitting strategy {strategy.__name__} failed: {e}")

        # If no splitting worked, return the whole content as one document
        logger.debug("No document separators found, treating as single document")
        return [content]

    def parse(self, content: str) -> ParseResult:
        """
        Parse content to split into documents (required by SimpleParser interface).

        Returns:
            ParseResult: Always successful, contains list of document strings
        """
        documents = self.split(content)

        return ParseResult.success_result(
            data={"documents": documents, "count": len(documents)},
            original_content=content,
        )

    def _split_by_yaml_separators(self, content: str) -> List[str]:
        """
        Split by YAML document separators (--- or +++).

        This is the most common and reliable splitting method.
        """
        # Try each separator pattern
        for separator_pattern in CommonPatterns.DOCUMENT_SEPARATORS:
            parts = re.split(separator_pattern, content, flags=re.MULTILINE)

            # Filter out empty parts and clean up
            documents = []
            for part in parts:
                if cleaned := part.strip():
                    documents.append(cleaned)

            # If we found multiple documents, return them
            if len(documents) > 1:
                return documents

        # No separators found
        return [content]

    def _split_by_common_separators(self, content: str) -> List[str]:
        """
        Split by other common document separators.

        Fallback for non-YAML content that uses other separators.
        """
        # Additional separator patterns for non-YAML content
        additional_separators = [
            r"^#{1,3}\s+[^\n]+\n",  # Markdown headers as separators
            r"^\*{3,}\s*$",  # Asterisk separators
            r"^_{3,}\s*$",  # Underscore separators
            r"^\s*\n\s*\n\s*\n+",  # Multiple blank lines
        ]

        for separator_pattern in additional_separators:
            parts = re.split(separator_pattern, content, flags=re.MULTILINE)

            documents = []
            for part in parts:
                cleaned = part.strip()
                if cleaned and len(cleaned) > 10:  # Minimum content length
                    documents.append(cleaned)

            if len(documents) > 1:
                return documents

        return [content]

    def _split_by_content_blocks(self, content: str) -> List[str]:
        """
        Split by detecting distinct content blocks.

        Last resort splitting for content without clear separators.
        """
        lines = content.split("\n")
        if len(lines) < 3:
            return [content]

        # Look for blocks separated by blank lines
        blocks = []
        current_block = []
        blank_line_count = 0

        for line in lines:
            if not line.strip():  # Blank line
                blank_line_count += 1
                if blank_line_count >= 2 and current_block:
                    # End of block
                    block_content = "\n".join(current_block).strip()
                    if block_content and len(block_content) > 20:  # Minimum block size
                        blocks.append(block_content)
                    current_block = []
                    blank_line_count = 0
            else:
                # Non-blank line
                if blank_line_count > 0:
                    current_block.append("")  # Add blank line to block
                current_block.append(line)
                blank_line_count = 0

        # Add final block
        if current_block:
            block_content = "\n".join(current_block).strip()
            if block_content:
                blocks.append(block_content)

        # Return blocks if we found multiple, otherwise original content
        return blocks if len(blocks) > 1 else [content]

    def detect_separator_type(self, content: str) -> str:
        """
        Detect what type of separator is used in the content.

        Useful for debugging and understanding document structure.

        Returns:
            str: Type of separator detected ('yaml', 'markdown', 'blank_lines', 'none')
        """
        # Check for YAML separators
        for pattern in CommonPatterns.DOCUMENT_SEPARATORS[:4]:  # First 4 are YAML-style
            if re.search(pattern, content, re.MULTILINE):
                return "yaml"

        # Check for Markdown headers
        if re.search(r"^#{1,3}\s+[^\n]+\n", content, re.MULTILINE):
            return "markdown"

        # Check for multiple blank lines
        if re.search(r"^\s*\n\s*\n\s*\n+", content, re.MULTILINE):
            return "blank_lines"

        return "none"

    def get_splitting_stats(self) -> dict:
        """
        Get statistics about splitting performance.

        Returns:
            dict: Statistics including split counts and success rates
        """
        multi_doc_rate = 0.0
        if self.split_count > 0:
            multi_doc_rate = self.multi_document_count / self.split_count

        return {
            "total_splits": self.split_count,
            "multi_document_splits": self.multi_document_count,
            "multi_document_rate": multi_doc_rate,
            "success_rate": self.get_success_rate(),
        }

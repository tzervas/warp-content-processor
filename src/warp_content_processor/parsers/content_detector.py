"""
Content type detection with confidence scoring.

Following SRP: This class has exactly one responsibility - detect content types.
Following KISS: Simple, clear detection logic with confidence scores.
"""

import logging
from typing import Tuple

from ..content_type import ContentType
from .base import ParseResult, SimpleParser
from .common_patterns import CommonPatterns

logger = logging.getLogger(__name__)


class ContentDetector(SimpleParser):
    """
    Simple content type detector.

    SRP: Only responsible for detecting content types, nothing else.
    KISS: Clear, predictable behavior with confidence scores.
    """

    def __init__(self, min_confidence: float = 0.3):
        """
        Initialize detector with minimum confidence threshold.

        Args:
            min_confidence: Minimum confidence score to consider a detection valid
        """
        super().__init__()
        self.min_confidence = min_confidence

    @property
    def parser_name(self) -> str:
        return "ContentDetector"

    def _compute_confidence_scores(self, content: str) -> dict:
        """Compute confidence scores for all content types."""
        all_scores = {}
        for content_type_str, patterns in CommonPatterns.CONTENT_TYPE_PATTERNS.items():
            try:
                content_type = ContentType(content_type_str)
                normalized = content.lower()

                score = 0
                for pattern in patterns:
                    import re

                    if re.search(pattern, normalized, re.MULTILINE | re.IGNORECASE):
                        score += 1

                # Normalize by number of patterns
                confidence = score / len(patterns) if patterns else 0.0
                all_scores[content_type] = confidence

            except ValueError:
                # Invalid content type, skip
                continue

        # Add unknown type
        all_scores[ContentType.UNKNOWN] = 0.0
        return all_scores

    def detect(self, content: str) -> Tuple[ContentType, float]:
        """Detect content type with confidence score."""
        if not content or not content.strip():
            return ContentType.UNKNOWN, 0.0

        try:
            # Normalize and analyze the content
            normalized = content.replace("：", ":").replace(
                "，", ","
            )  # Handle unicode punctuation
            scores = self._compute_confidence_scores(normalized)
            if not any(scores.values()):
                return ContentType.UNKNOWN, 0.0

            # Find type with highest confidence
            max_type = max(scores.items(), key=lambda x: x[1])
            content_type, confidence = max_type[0], max_type[1]

            # Adjust confidence based on overall structure
            if confidence > 0:
                if content_type == ContentType.WORKFLOW:
                    # Boost confidence for workflow markers
                    confidence = min(confidence * 1.5, 1.0)

                # Apply minimum confidence threshold
                if confidence >= self.min_confidence:
                    logger.debug(
                        f"Detected content type: {content_type.value} "
                        f"(confidence: {confidence:.2f})"
                    )
                    return content_type, confidence

        except Exception as e:
            logger.warning(f"Error during content detection: {e}")

        return ContentType.UNKNOWN, 0.0

    def parse(self, content: str) -> ParseResult:
        """
        Parse content to detect its type (required by SimpleParser interface).

        Returns:
            ParseResult: Always successful, contains (content_type, confidence) tuple
        """
        content_type, confidence = self.detect(content)

        return ParseResult.success_result(
            data={"content_type": content_type, "confidence": confidence},
            original_content=content,
        )

    def detect_multiple_types(self, content: str) -> dict:
        """
        Get confidence scores for all content types.

        Useful for debugging and understanding why a particular type was chosen.

        Returns:
            dict: Mapping of content_type -> confidence_score for all types
        """
        if not content or not content.strip():
            return dict.fromkeys(ContentType, 0.0)

        # Get all scores from common patterns
        all_scores = {}
        for content_type_str, patterns in CommonPatterns.CONTENT_TYPE_PATTERNS.items():
            try:
                content_type = ContentType(content_type_str)
                normalized = content.lower()

                score = 0
                for pattern in patterns:
                    import re

                    if re.search(pattern, normalized, re.MULTILINE | re.IGNORECASE):
                        score += 1

                # Normalize by number of patterns
                confidence = score / len(patterns) if patterns else 0.0
                all_scores[content_type] = confidence

            except ValueError:
                # Invalid content type, skip
                continue

        # Add unknown type
        all_scores[ContentType.UNKNOWN] = 0.0

        return all_scores

    def get_detection_stats(self) -> dict:
        """
        Get statistics about detection performance.

        Returns:
            dict: Statistics including success rate and detection counts
        """
        return {
            "total_detections": self.parse_count,
            "success_rate": self.get_success_rate(),
            "min_confidence_threshold": self.min_confidence,
        }

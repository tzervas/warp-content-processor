"""
Schema artifact definitions for content extraction.

Following SRP: Clear definitions of extracted content with confidence scoring.
Following KISS: Simple, clear data structures for extracted artifacts.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ContentType(str, Enum):
    """Content types for excavated schema data."""

    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    UNKNOWN = "unknown"


class ExtractionConfidence(Enum):
    """Confidence levels for extracted artifacts."""

    HIGH = "high"  # 90%+ confidence - clear, well-formed schema
    MEDIUM = "medium"  # 70-89% confidence - recognizable but may need cleanup
    LOW = "low"  # 50-69% confidence - partial or heavily damaged
    SUSPECT = "suspect"  # <50% confidence - might be false positive


class ContaminationType(Enum):
    """Types of contamination found around legitimate content."""

    BINARY_DATA = "binary_data"  # Binary data mixed in
    LOG_PREFIXES = "log_prefixes"  # Log file prefixes/suffixes
    CODE_FRAGMENTS = "code_fragments"  # Programming language artifacts
    RANDOM_TEXT = "random_text"  # Random/garbage text
    ENCODING_ISSUES = "encoding_issues"  # Character encoding problems
    MALFORMED_STRUCTURE = "malformed_structure"  # Broken schema structures


@dataclass(frozen=True)
class ExtractionContext:
    """Context information about where/how content was extracted."""

    source_type: str  # e.g., "log_file", "documentation", "code_comment"
    start_offset: int  # Character offset where extraction started
    end_offset: int  # Character offset where extraction ended
    contamination_types: Set[ContaminationType]
    extraction_method: str  # Which extractor found this content
    original_surrounding: Optional[str] = None  # Context around the extraction


@dataclass(frozen=True)
class SchemaArtifact:
    """A piece of legitimate schema content extracted from contaminated input."""

    # Core content
    content_type: ContentType
    raw_content: str  # Original extracted content
    cleaned_content: str  # Cleaned and normalized content
    parsed_data: Optional[Dict[str, Any]]  # Successfully parsed structure

    # Quality metrics
    confidence: ExtractionConfidence
    is_valid: bool  # Whether the content parses successfully
    extraction_context: ExtractionContext

    # Error information
    validation_errors: List[str]
    cleaning_warnings: List[str]

    @property
    def quality_score(self) -> float:
        """Calculate overall quality score (0.0 to 1.0)."""
        base_scores = {
            ExtractionConfidence.HIGH: 0.95,
            ExtractionConfidence.MEDIUM: 0.80,
            ExtractionConfidence.LOW: 0.65,
            ExtractionConfidence.SUSPECT: 0.35,
        }

        score = base_scores[self.confidence]

        # Adjust based on validation
        if not self.is_valid:
            score *= 0.5

        # Adjust based on contamination severity
        contamination_penalty = len(self.extraction_context.contamination_types) * 0.05
        score = max(0.0, score - contamination_penalty)

        return min(1.0, score)

    @property
    def is_high_quality(self) -> bool:
        """Check if this artifact meets high quality standards."""
        return (
            self.confidence in [ExtractionConfidence.HIGH, ExtractionConfidence.MEDIUM]
            and self.is_valid
            and len(self.validation_errors) == 0
            and self.quality_score >= 0.7
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert artifact to dictionary for serialization."""
        return {
            "content_type": self.content_type.value,
            "raw_content": self.raw_content,
            "cleaned_content": self.cleaned_content,
            "parsed_data": self.parsed_data,
            "confidence": self.confidence.value,
            "is_valid": self.is_valid,
            "quality_score": self.quality_score,
            "extraction_context": {
                "source_type": self.extraction_context.source_type,
                "start_offset": self.extraction_context.start_offset,
                "end_offset": self.extraction_context.end_offset,
                "contamination_types": [
                    ct.value for ct in self.extraction_context.contamination_types
                ],
                "extraction_method": self.extraction_context.extraction_method,
            },
            "validation_errors": self.validation_errors,
            "cleaning_warnings": self.cleaning_warnings,
        }


@dataclass(frozen=True)
class ExcavationResult:
    """Result of content excavation process."""

    artifacts: List[SchemaArtifact]
    total_content_size: int
    processing_time_ms: int
    extraction_stats: Dict[str, int]  # Stats by extractor method

    @property
    def high_quality_artifacts(self) -> List[SchemaArtifact]:
        """Get only high-quality artifacts."""
        return [a for a in self.artifacts if a.is_high_quality]

    @property
    def valid_artifacts(self) -> List[SchemaArtifact]:
        """Get all valid artifacts (regardless of confidence)."""
        return [a for a in self.artifacts if a.is_valid]

    @property
    def extraction_success_rate(self) -> float:
        """Calculate success rate of extraction."""
        if not self.artifacts:
            return 0.0
        return len(self.valid_artifacts) / len(self.artifacts)

    def get_artifacts_by_type(self, content_type: ContentType) -> List[SchemaArtifact]:
        """Get artifacts of a specific content type."""
        return [a for a in self.artifacts if a.content_type == content_type]

    def get_artifacts_by_confidence(
        self, min_confidence: ExtractionConfidence
    ) -> List[SchemaArtifact]:
        """Get artifacts with at least the specified confidence level."""
        confidence_order = [
            ExtractionConfidence.SUSPECT,
            ExtractionConfidence.LOW,
            ExtractionConfidence.MEDIUM,
            ExtractionConfidence.HIGH,
        ]

        min_level = confidence_order.index(min_confidence)
        return [
            a
            for a in self.artifacts
            if confidence_order.index(a.confidence) >= min_level
        ]

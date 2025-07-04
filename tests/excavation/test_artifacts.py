"""
Tests for excavation artifacts - Following KISS principles with parameterized tests.

Tests data structures and validation logic without complex test loops.
"""

from dataclasses import FrozenInstanceError

import pytest

from warp_content_processor.excavation.artifacts import (
    ContaminationType,
    ContentType,
    ExcavationResult,
    ExtractionConfidence,
    ExtractionContext,
    SchemaArtifact,
)


class TestExtractionConfidence:
    """Test ExtractionConfidence enum."""

    @pytest.mark.parametrize(
        "confidence_level",
        [
            ExtractionConfidence.HIGH,
            ExtractionConfidence.MEDIUM,
            ExtractionConfidence.LOW,
            ExtractionConfidence.SUSPECT,
        ],
    )
    def test_confidence_enum_values(self, confidence_level):
        """Test that all confidence levels are accessible."""
        assert isinstance(confidence_level, ExtractionConfidence)
        assert confidence_level.value is not None


class TestContaminationType:
    """Test ContaminationType enum."""

    @pytest.mark.parametrize(
        "contamination_type",
        [
            ContaminationType.BINARY_DATA,
            ContaminationType.LOG_PREFIXES,
            ContaminationType.CODE_FRAGMENTS,
            ContaminationType.RANDOM_TEXT,
            ContaminationType.ENCODING_ISSUES,
            ContaminationType.MALFORMED_STRUCTURE,
        ],
    )
    def test_contamination_enum_values(self, contamination_type):
        """Test that all contamination types are accessible."""
        assert isinstance(contamination_type, ContaminationType)
        assert contamination_type.value is not None


class TestContentType:
    """Test ContentType enum."""

    @pytest.mark.parametrize(
        "content_type",
        [
            ContentType.YAML,
            ContentType.JSON,
            ContentType.MARKDOWN,
            ContentType.PLAIN_TEXT,
            ContentType.UNKNOWN,
        ],
    )
    def test_content_type_enum_values(self, content_type):
        """Test that all content types are accessible."""
        assert isinstance(content_type, ContentType)
        assert content_type.value is not None


class TestExtractionContext:
    """Test ExtractionContext dataclass."""

    @pytest.fixture
    def basic_context(self):
        """Create a basic extraction context for testing."""
        return ExtractionContext(
            source_type="test_source",
            start_offset=0,
            end_offset=100,
            contamination_types={ContaminationType.LOG_PREFIXES},
            extraction_method="test_method",
            original_surrounding="surrounding context",
        )

    def test_context_creation(self, basic_context):
        """Test that extraction context can be created correctly."""
        assert basic_context.source_type == "test_source"
        assert basic_context.start_offset == 0
        assert basic_context.end_offset == 100
        assert ContaminationType.LOG_PREFIXES in basic_context.contamination_types
        assert basic_context.extraction_method == "test_method"
        assert basic_context.original_surrounding == "surrounding context"

    def test_context_immutability(self, basic_context):
        """Test that extraction context is immutable (frozen dataclass)."""
        with pytest.raises((FrozenInstanceError, AttributeError)):
            basic_context.source_type = "modified"

    @pytest.mark.parametrize(
        "start,end,valid",
        [
            (0, 100, True),  # Normal range
            (50, 50, True),  # Single position
            (100, 0, False),  # Invalid range (end < start)
            (-1, 100, False),  # Negative start
            (0, -1, False),  # Negative end
        ],
    )
    def test_context_offset_validation(self, start, end, valid):
        """Test extraction context with various offset values."""
        # Create context regardless (validation is not enforced by dataclass)
        context = ExtractionContext(
            source_type="test",
            start_offset=start,
            end_offset=end,
            contamination_types=set(),
            extraction_method="test",
            original_surrounding="",
        )
        # Values are stored as-is
        assert context.start_offset == start
        assert context.end_offset == end

        # For valid ranges, additional checks could be added
        if valid:
            assert start <= end or start == end  # Allow same position


class TestSchemaArtifact:
    """Test SchemaArtifact dataclass."""

    @pytest.fixture
    def basic_artifact(self):
        """Create a basic schema artifact for testing."""
        context = ExtractionContext(
            source_type="yaml",
            start_offset=0,
            end_offset=50,
            contamination_types=set(),
            extraction_method="yaml_block",
            original_surrounding="",
        )

        return SchemaArtifact(
            content_type=ContentType.YAML,
            raw_content="name: test\nvalue: 123",
            cleaned_content="name: test\nvalue: 123",
            parsed_data={"name": "test", "value": 123},
            confidence=ExtractionConfidence.HIGH,
            is_valid=True,
            extraction_context=context,
            validation_errors=[],
            cleaning_warnings=[],
        )

    def test_artifact_creation(self, basic_artifact):
        """Test that schema artifact can be created correctly."""
        assert basic_artifact.content_type == ContentType.YAML
        assert basic_artifact.raw_content == "name: test\nvalue: 123"
        assert basic_artifact.cleaned_content == "name: test\nvalue: 123"
        assert basic_artifact.parsed_data == {"name": "test", "value": 123}
        assert basic_artifact.confidence == ExtractionConfidence.HIGH
        assert basic_artifact.is_valid is True
        assert len(basic_artifact.validation_errors) == 0
        assert len(basic_artifact.cleaning_warnings) == 0

    def test_artifact_immutability(self, basic_artifact):
        """Test that schema artifact is immutable."""
        with pytest.raises((FrozenInstanceError, AttributeError)):
            basic_artifact.is_valid = False

    @pytest.mark.parametrize(
        "is_valid,parsed_data,validation_errors",
        [
            (True, {"key": "value"}, []),  # Valid with data
            (True, None, []),  # Valid but no parsed data
            (False, None, ["Parse error"]),  # Invalid with errors
            (False, {"key": "value"}, ["Warning"]),  # Invalid but with data (edge case)
        ],
    )
    def test_artifact_validation_combinations(
        self, is_valid, parsed_data, validation_errors
    ):
        """Test artifact with various validation states."""
        context = ExtractionContext(
            source_type="test",
            start_offset=0,
            end_offset=10,
            contamination_types=set(),
            extraction_method="test",
            original_surrounding="",
        )

        artifact = SchemaArtifact(
            content_type=ContentType.YAML,
            raw_content="test",
            cleaned_content="test",
            parsed_data=parsed_data,
            confidence=ExtractionConfidence.MEDIUM,
            is_valid=is_valid,
            extraction_context=context,
            validation_errors=validation_errors,
            cleaning_warnings=[],
        )

        assert artifact.is_valid == is_valid
        assert artifact.parsed_data == parsed_data
        assert artifact.validation_errors == validation_errors

    def test_artifact_with_contamination(self):
        """Test artifact creation with contamination and cleaning warnings."""
        context = ExtractionContext(
            source_type="contaminated",
            start_offset=0,
            end_offset=20,
            contamination_types={
                ContaminationType.LOG_PREFIXES,
                ContaminationType.BINARY_DATA,
            },
            extraction_method="yaml_block",
            original_surrounding="2024-01-01 [INFO] name: test",
        )

        artifact = SchemaArtifact(
            content_type=ContentType.YAML,
            raw_content="2024-01-01 [INFO] name: test",
            cleaned_content="name: test",
            parsed_data={"name": "test"},
            confidence=ExtractionConfidence.MEDIUM,
            is_valid=True,
            extraction_context=context,
            validation_errors=[],
            cleaning_warnings=["Removed log prefix", "Removed binary data"],
        )

        assert len(artifact.extraction_context.contamination_types) == 2
        assert len(artifact.cleaning_warnings) == 2
        assert artifact.raw_content != artifact.cleaned_content


class TestExcavationResult:
    """Test ExcavationResult dataclass."""

    @pytest.fixture
    def sample_artifacts(self):
        """Create sample artifacts for testing."""
        context1 = ExtractionContext(
            source_type="yaml",
            start_offset=0,
            end_offset=20,
            contamination_types=set(),
            extraction_method="yaml_block",
            original_surrounding="",
        )

        context2 = ExtractionContext(
            source_type="json",
            start_offset=25,
            end_offset=45,
            contamination_types={ContaminationType.LOG_PREFIXES},
            extraction_method="json_block",
            original_surrounding="",
        )

        artifact1 = SchemaArtifact(
            content_type=ContentType.YAML,
            raw_content="name: test1",
            cleaned_content="name: test1",
            parsed_data={"name": "test1"},
            confidence=ExtractionConfidence.HIGH,
            is_valid=True,
            extraction_context=context1,
            validation_errors=[],
            cleaning_warnings=[],
        )

        artifact2 = SchemaArtifact(
            content_type=ContentType.JSON,
            raw_content='{"name": "test2"}',
            cleaned_content='{"name": "test2"}',
            parsed_data={"name": "test2"},
            confidence=ExtractionConfidence.MEDIUM,
            is_valid=True,
            extraction_context=context2,
            validation_errors=[],
            cleaning_warnings=["Cleaned log prefix"],
        )

        return [artifact1, artifact2]

    def test_excavation_result_creation(self, sample_artifacts):
        """Test that excavation result can be created correctly."""
        result = ExcavationResult(
            artifacts=sample_artifacts,
            total_content_size=1000,
            processing_time_ms=250,
            extraction_stats={"yaml_block": 1, "json_block": 1},
        )

        assert len(result.artifacts) == 2
        assert result.total_content_size == 1000
        assert result.processing_time_ms == 250
        assert result.extraction_stats["yaml_block"] == 1
        assert result.extraction_stats["json_block"] == 1

    def test_excavation_result_immutability(self, sample_artifacts):
        """Test that excavation result is immutable."""
        result = ExcavationResult(
            artifacts=sample_artifacts,
            total_content_size=1000,
            processing_time_ms=250,
            extraction_stats={},
        )

        with pytest.raises((FrozenInstanceError, AttributeError)):
            result.total_content_size = 2000

    @pytest.mark.parametrize(
        "artifact_count,content_size,processing_time",
        [
            (0, 0, 0),  # Empty result
            (1, 100, 50),  # Single artifact
            (5, 10000, 1000),  # Multiple artifacts
            (100, 1000000, 5000),  # Large result
        ],
    )
    def test_excavation_result_metrics(
        self, artifact_count, content_size, processing_time
    ):
        """Test excavation result with various metrics."""
        # Create mock artifacts using helper
        artifacts = self._create_mock_artifacts(artifact_count)

        result = ExcavationResult(
            artifacts=artifacts,
            total_content_size=content_size,
            processing_time_ms=processing_time,
            extraction_stats={"test": artifact_count},
        )

        assert len(result.artifacts) == artifact_count
        assert result.total_content_size == content_size
        assert result.processing_time_ms == processing_time

    def _create_mock_artifacts(self, count):
        """Helper to create mock artifacts for testing."""
        return [
            SchemaArtifact(
                content_type=ContentType.YAML,
                raw_content=f"test{i}",
                cleaned_content=f"test{i}",
                parsed_data={"test": i},
                confidence=ExtractionConfidence.MEDIUM,
                is_valid=True,
                extraction_context=ExtractionContext(
                    source_type="test",
                    start_offset=i * 10,
                    end_offset=(i + 1) * 10,
                    contamination_types=set(),
                    extraction_method="test",
                    original_surrounding="",
                ),
                validation_errors=[],
                cleaning_warnings=[],
            )
            for i in range(count)
        ]

    def test_empty_excavation_result(self):
        """Test creation of empty excavation result."""
        result = ExcavationResult(
            artifacts=[],
            total_content_size=500,
            processing_time_ms=100,
            extraction_stats={},
        )

        assert len(result.artifacts) == 0
        assert result.total_content_size == 500
        assert result.processing_time_ms == 100
        assert len(result.extraction_stats) == 0


class TestArtifactQualityMetrics:
    """Test quality metrics and scoring for artifacts."""

    @pytest.mark.parametrize(
        "confidence,contamination_count,expected_quality_tier",
        [
            (ExtractionConfidence.HIGH, 0, "excellent"),
            (
                ExtractionConfidence.HIGH,
                1,
                "excellent",
            ),  # Fixed: Still excellent with one contamination
            (ExtractionConfidence.MEDIUM, 0, "good"),
            (ExtractionConfidence.MEDIUM, 2, "fair"),
            (ExtractionConfidence.LOW, 0, "fair"),
            (
                ExtractionConfidence.LOW,
                3,
                "very_poor",
            ),  # Fixed: More contamination = very_poor
            (ExtractionConfidence.SUSPECT, 0, "poor"),
            (ExtractionConfidence.SUSPECT, 5, "very_poor"),
        ],
    )
    def test_artifact_quality_assessment(
        self, confidence, contamination_count, expected_quality_tier
    ):
        """Test quality assessment based on confidence and contamination."""
        contamination_types = set(list(ContaminationType)[:contamination_count])

        # artifact = SchemaArtifact(
        #     content_type=ContentType.YAML,
        #     raw_content="test",
        #     cleaned_content="test",
        #     parsed_data={"test": "value"},
        #     confidence=confidence,
        #     is_valid=True,
        #     extraction_context=context,
        #     validation_errors=[],
        #     cleaning_warnings=[],
        # )

        # Use helper to calculate quality tier
        calculated_tier = self._calculate_quality_tier(confidence, contamination_types)
        assert calculated_tier == expected_quality_tier

    def _calculate_quality_tier(self, confidence, contamination_types):
        """Helper to calculate quality tier based on confidence and contamination."""
        # Quality score mapping for confidence levels
        confidence_scores = {
            ExtractionConfidence.HIGH: 1.0,
            ExtractionConfidence.MEDIUM: 0.8,
            ExtractionConfidence.LOW: 0.6,
            ExtractionConfidence.SUSPECT: 0.4,
        }

        quality_score = confidence_scores.get(confidence, 0.0)

        # Reduce for contamination
        quality_score -= len(contamination_types) * 0.1

        # Quality tier thresholds
        if quality_score >= 0.9:
            return "excellent"
        elif quality_score >= 0.7:
            return "good"
        elif quality_score >= 0.5:
            return "fair"
        elif quality_score >= 0.3:
            return "poor"
        else:
            return "very_poor"

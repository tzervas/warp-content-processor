"""
Tests for ContentArchaeologist - Following KISS principles with parameterized tests.

No loops in tests - using parameterization and fixtures for clean test logic.
"""

from unittest.mock import Mock, patch

import pytest

from warp_content_processor.excavation.archaeologist import ContentArchaeologist
from warp_content_processor.excavation.artifacts import (
    ExcavationResult,
    ExtractionConfidence,
    SchemaArtifact,
)
from warp_content_processor.utils.security import SecurityValidationError


class TestContentArchaeologistInitialization:
    """Test archaeologist initialization with different configurations."""

    @pytest.mark.parametrize(
        "max_size,timeout,expected_max_size,expected_timeout,expected_extractions",
        [
            (1024, 30, 1024, 30, 0),  # Small limits
            (100 * 1024 * 1024, 300, 100 * 1024 * 1024, 300, 0),  # Default limits
            (1000 * 1024 * 1024, 600, 1000 * 1024 * 1024, 600, 0),  # Large limits
            (0, 300, 0, 300, 0),  # Invalid size (still initializes)
            (1024, 0, 1024, 0, 0),  # Invalid timeout (still initializes)
        ],
    )
    def test_initialization_parameters(self, max_size, timeout, expected_max_size, expected_timeout, expected_extractions):
        """Test archaeologist initialization with various parameter combinations."""
        archaeologist = ContentArchaeologist(max_size, timeout)
        assert archaeologist.max_content_size == expected_max_size
        assert archaeologist.extraction_timeout == expected_timeout
        assert archaeologist.total_extractions == expected_extractions
        assert isinstance(archaeologist, ContentArchaeologist)


class TestContentArchaeologistExcavation:
    """Test core excavation functionality."""

    @pytest.fixture
    def archaeologist(self):
        """Create a standard archaeologist for testing."""
        return ContentArchaeologist(max_content_size=1024 * 1024, extraction_timeout=60)

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch(
            "warp_content_processor.excavation.archaeologist.ContentDetector"
        ) as mock_detector, patch(
            "warp_content_processor.excavation.archaeologist.SchemaIslandDetector"
        ) as mock_island, patch(
            "warp_content_processor.excavation.archaeologist.create_yaml_parser"
        ) as mock_parser:
            # Setup mock returns
            mock_detector.return_value.detect.return_value = ("yaml", 0.9)
            mock_island.return_value.find_islands.return_value = []
            mock_parser.return_value.parse.return_value = Mock(
                success=True, data={"key": "value"}, error_message=None
            )

            yield {
                "detector": mock_detector,
                "island": mock_island,
                "parser": mock_parser,
            }

    @pytest.mark.parametrize(
        "content,source_hint,expected_artifact_count",
        [
            ("", None, 0),  # Empty content
            ("   ", None, 0),  # Whitespace only
            ("name: test\nvalue: 123", "yaml", 1),  # Valid YAML
            ("random text without structure", None, 0),  # No structure
            ("name: test\n---\nother: data", "yaml", 2),  # Multiple sections
        ],
    )
    def test_excavation_basic_scenarios(
        self,
        archaeologist,
        mock_dependencies,
        content,
        source_hint,
        expected_artifact_count,
    ):
        """Test excavation with basic content scenarios."""
        # Setup mock island detector to return appropriate islands
        if expected_artifact_count > 0:
            mock_island = Mock()
            mock_island.content = content
            mock_island.raw_content = content
            mock_island.start_offset = 0
            mock_island.end_offset = len(content)
            mock_island.quality_score = 0.8
            mock_island.source_type = source_hint or "unknown"
            mock_island.extraction_method = "yaml_block"
            mock_island.contamination_types = set()
            mock_island.cleaning_warnings = []
            mock_island.surrounding_context = content

            mock_dependencies["island"].return_value.find_islands.return_value = [
                mock_island
            ] * expected_artifact_count

        result = archaeologist.excavate(content, source_hint)

        assert isinstance(result, ExcavationResult)
        assert len(result.artifacts) == expected_artifact_count
        assert result.total_content_size == len(content)
        assert result.processing_time_ms >= 0


class TestSecurityValidation:
    """Test security validation during excavation."""

    @pytest.fixture
    def archaeologist(self):
        """Create archaeologist with small limits for security testing."""
        return ContentArchaeologist(max_content_size=100, extraction_timeout=5)

    @pytest.mark.parametrize(
        "dangerous_content,expected_artifacts,expected_stats,should_patch_sanitizer",
        [
            ("<script>alert('xss')</script>", 0, {}, True),  # XSS attempt
            ("javascript:void(0)", 0, {}, True),  # JavaScript URL
            ("normal yaml content", None, None, False),  # Safe content (variable results)
            ("name: <script>test</script>", 0, {}, True),  # Embedded script
            ("just some text", None, None, False),  # Plain text (variable results)
        ],
    )
    def test_security_validation(self, archaeologist, dangerous_content, expected_artifacts, expected_stats, should_patch_sanitizer):
        """Test security validation blocks dangerous content."""
        if should_patch_sanitizer:
            with patch(
                "warp_content_processor.utils.security.ContentSanitizer.sanitize_string"
            ) as mock_sanitize:
                mock_sanitize.side_effect = SecurityValidationError(
                    "Dangerous content detected"
                )

                result = archaeologist.excavate(dangerous_content)

                # Should return empty result when security validation fails
                assert len(result.artifacts) == expected_artifacts
                assert result.extraction_stats == expected_stats
        else:
            # Safe content should process normally
            result = archaeologist.excavate(dangerous_content)
            assert isinstance(result, ExcavationResult)

    def test_content_size_limit(self, archaeologist):
        """Test content size limits are enforced."""
        oversized_content = "x" * 200  # Exceeds 100 byte limit

        result = archaeologist.excavate(oversized_content)

        # Should truncate content and continue processing
        assert isinstance(result, ExcavationResult)
        assert result.total_content_size == 200  # Original size preserved in stats

    def test_extraction_timeout(self, archaeologist):
        """Test extraction timeout is enforced."""
        with patch("time.time") as mock_time:
            # Simulate timeout condition - need more values for all time.time() calls
            mock_time.side_effect = [
                0,
                0,
                10,
                10,
            ]  # Start at 0, check multiple times, then timeout

            result = archaeologist.excavate("name: test")

            # Should handle timeout gracefully
            assert isinstance(result, ExcavationResult)


class TestExtractionStatistics:
    """Test extraction statistics tracking."""

    @pytest.fixture
    def archaeologist(self):
        return ContentArchaeologist()

    def test_statistics_tracking(self, archaeologist):
        """Test that statistics are tracked correctly."""
        initial_stats = archaeologist.get_extraction_statistics()

        assert initial_stats["total_extractions"] == 0
        assert initial_stats["successful_extractions"] == 0
        assert initial_stats["success_rate"] == 0.0

        # Perform some extractions
        archaeologist.excavate("name: test")
        archaeologist.excavate("invalid content")

        updated_stats = archaeologist.get_extraction_statistics()
        assert updated_stats["total_extractions"] == 2

    def test_statistics_reset(self, archaeologist):
        """Test statistics can be reset."""
        archaeologist.excavate("name: test")
        archaeologist.reset_statistics()

        stats = archaeologist.get_extraction_statistics()
        assert stats["total_extractions"] == 0
        assert stats["successful_extractions"] == 0


class TestArtifactExtraction:
    """Test artifact extraction from islands."""

    @pytest.fixture
    def archaeologist(self):
        return ContentArchaeologist()

    @pytest.fixture
    def mock_island(self):
        """Create a mock content island."""
        island = Mock()
        island.content = "name: test\nvalue: 123"
        island.raw_content = "name: test\nvalue: 123"
        island.start_offset = 0
        island.end_offset = 17
        island.quality_score = 0.8
        island.source_type = "yaml"
        island.extraction_method = "yaml_block"
        island.contamination_types = set()
        island.cleaning_warnings = []
        island.surrounding_context = "name: test\nvalue: 123"
        return island

    @pytest.mark.parametrize(
        "parse_success,expected_valid",
        [
            (True, True),  # Successful parsing
            (False, False),  # Failed parsing
        ],
    )
    def test_artifact_extraction_from_island(
        self, archaeologist, mock_island, parse_success, expected_valid
    ):
        """Test artifact extraction with different parsing outcomes."""
        with patch.object(
            archaeologist, "content_detector"
        ) as mock_detector, patch.object(archaeologist, "yaml_parser") as mock_parser:
            # Setup mocks
            mock_detector.detect.return_value = ("yaml", 0.9)

            parse_result = Mock()
            parse_result.success = parse_success
            parse_result.data = (
                {"name": "test", "value": 123} if parse_success else None
            )
            parse_result.error_message = None if parse_success else "Parse error"
            mock_parser.parse.return_value = parse_result

            # Extract artifact
            artifact = archaeologist._extract_artifact_from_island(mock_island)

            assert artifact is not None
            assert isinstance(artifact, SchemaArtifact)
            assert artifact.is_valid == expected_valid

            if expected_valid:
                assert artifact.parsed_data is not None
                assert len(artifact.validation_errors) == 0
            else:
                assert artifact.parsed_data is None
                assert len(artifact.validation_errors) > 0


class TestConfidenceCalculation:
    """Test extraction confidence calculation."""

    @pytest.fixture
    def archaeologist(self):
        return ContentArchaeologist()

    @pytest.mark.parametrize(
        "island_quality,detection_confidence,contamination_count,expected_confidence",
        [
            (0.9, 0.9, 0, ExtractionConfidence.HIGH),  # High quality, no contamination
            (0.7, 0.7, 0, ExtractionConfidence.MEDIUM),  # Medium quality
            (0.5, 0.5, 1, ExtractionConfidence.LOW),  # Lower quality with contamination
            (
                0.3,
                0.3,
                2,
                ExtractionConfidence.SUSPECT,
            ),  # Poor quality, multiple contaminations
            (0.0, 0.0, 3, ExtractionConfidence.SUSPECT),  # Very poor quality
        ],
    )
    def test_confidence_calculation(
        self,
        archaeologist,
        island_quality,
        detection_confidence,
        contamination_count,
        expected_confidence,
    ):
        """Test confidence calculation with various quality metrics."""
        # Create mock island with specified quality
        mock_island = Mock()
        mock_island.quality_score = island_quality
        mock_island.contamination_types = set(
            range(contamination_count)
        )  # Mock contamination types

        confidence = archaeologist._calculate_extraction_confidence(
            mock_island, detection_confidence
        )

        assert confidence == expected_confidence


class TestExcavationResultStructure:
    """Test excavation result data structure."""

    def test_excavation_result_completeness(self):
        """Test that excavation results contain all required fields."""
        archaeologist = ContentArchaeologist()
        result = archaeologist.excavate("name: test")

        # Check all required fields are present
        assert hasattr(result, "artifacts")
        assert hasattr(result, "total_content_size")
        assert hasattr(result, "processing_time_ms")
        assert hasattr(result, "extraction_stats")

        # Check types
        assert isinstance(result.artifacts, list)
        assert isinstance(result.total_content_size, int)
        assert isinstance(result.processing_time_ms, int)
        assert isinstance(result.extraction_stats, dict)

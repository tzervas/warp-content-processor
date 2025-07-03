"""Test suite for schema island detector."""

import pytest

from warp_content_processor.excavation.island_detector import SchemaIslandDetector
from warp_content_processor.excavation.artifacts import ContaminationType

class TestContentCleaning:
    """Test content cleaning with various contamination types."""

    @pytest.fixture
    def detector(self):
        """Create a SchemaIslandDetector instance."""
        return SchemaIslandDetector()

    @pytest.mark.parametrize(
        "contaminated_content,expected_cleaned",
        [
            ("name: test", "name: test"),  # No cleaning needed
            ("2024-01-01 [INFO] name: test", "name: test"),  # Log prefix removal
            (
                "INFO: name: test\nDEBUG: value: 123",
                "name: test\nvalue: 123",
            ),  # Multiple log lines
            ("name: test\x00\x01removed", "name: testremoved"),  # Binary removal
            (
                "name: test\n\n\n\nvalue: 123",
                "name: test\n\n\nvalue: 123",
            ),  # Only collapse 5+ newlines
        ],
    )
    def test_content_cleaning(self, detector, contaminated_content, expected_cleaned):
        """Test content cleaning with various contamination types."""
        contamination_types = set()

        # Detect contamination types using helper method
        contamination_types = self._detect_contamination_types(
            detector, contaminated_content
        )

        cleaned_content, warnings = detector._clean_content(
            contaminated_content, contamination_types
        )

        # Check cleaning result
        assert cleaned_content.strip() == expected_cleaned.strip()

    def _detect_contamination_types(
        self, detector: SchemaIslandDetector, content: str
    ) -> Set[ContaminationType]:
        """Helper to detect contamination types in content."""
        types = set()
        for ctype, pattern in detector.contamination_patterns.items():
            if pattern.search(content):
                types.add(ctype)
        return types

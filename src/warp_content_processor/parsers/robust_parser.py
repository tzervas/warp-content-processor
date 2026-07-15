"""
Robust parser implementation with strong error handling.

Following KISS principles with single-purpose components.
Following SRP with clear separation of responsibilities.
Following DRY by reusing existing parsing infrastructure.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import ParseResult, ParsingStrategy
from .common_patterns import MangledContentCleaner
from .yaml_strategies import CleanedYAMLStrategy, MangledYAMLStrategy, StandardYAMLStrategy

logger = logging.getLogger(__name__)


class RobustParser:
    """
    Robust parser that gracefully handles malformed content.

    Uses multiple strategies in order of decreasing strictness.
    """

    def __init__(self):
        """Initialize with standard parsing strategies."""
        self.strategies: List[ParsingStrategy] = [
            StandardYAMLStrategy(),
            CleanedYAMLStrategy(),
            MangledYAMLStrategy(),
        ]
        self.cleaner = MangledContentCleaner()

    def parse_with_fallbacks(self, content: str) -> Dict[str, Any]:
        """
        Parse content with graceful fallback to less strict strategies.

        Args:
            content: Content to parse

        Returns:
            Dict with parsing results including success/failure status
        """
        if not content:
            return {"success": False, "error": "Empty content"}

        # First pass - try standard parsing strategies
        last_error = None
        success = False
        errors = []

        # Clean content first
        try:
            content = self.cleaner.clean_content(content)
        except Exception as e:
            logger.warning("Error cleaning content: %s", str(e))
            errors.append(f"Content cleaning failed: {str(e)}")

        # Try each strategy
        for strategy in self.strategies:
            try:
                result = strategy.attempt_parse(content)
                if result.success:
                    success = True
                    return {
                        "success": True,
                        "data": result.data,
                        "strategy": strategy.strategy_name,
                    }
                else:
                    last_error = result.error_message
                    errors.append(f"{strategy.strategy_name}: {last_error}")
            except Exception as e:
                logger.warning(
                    "Error with strategy %s: %s", strategy.strategy_name, str(e)
                )
                errors.append(f"{strategy.strategy_name} failed: {str(e)}")

        # Return failure info if nothing worked
        return {
            "success": False,
            "errors": errors,
            "last_error": last_error,
            "strategies_attempted": len(self.strategies),
        }

    def get_parsing_stats(self) -> Dict[str, Any]:
        """Get statistics from parsing attempts."""
        stats = {"total_attempts": 0, "successful_parses": 0}
        for strategy in self.strategies:
            try:
                # Only count if strategy has stats
                if hasattr(strategy, "get_stats"):
                    strategy_stats = strategy.get_stats()
                    stats["total_attempts"] += strategy_stats.get(
                        "total_attempts", 0
                    )
                    stats["successful_parses"] += strategy_stats.get(
                        "successful_parses", 0
                    )
            except Exception as e:
                logger.warning("Error getting stats for %s: %s", strategy, str(e))
        return stats

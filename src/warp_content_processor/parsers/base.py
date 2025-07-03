"""
Base classes for robust content parsing.

Following KISS principle: Simple, predictable interfaces with clear success/failure semantics.
Following SRP principle: Each class has exactly one responsibility.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Simple result container for parsing operations."""

    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    original_content: Optional[str] = None

    @classmethod
    def success_result(cls, data: Any, original_content: str = None) -> "ParseResult":
        """Create a successful parsing result."""
        return cls(success=True, data=data, original_content=original_content)

    @classmethod
    def failure_result(
        cls, error_message: str, original_content: str = None
    ) -> "ParseResult":
        """Create a failed parsing result."""
        return cls(
            success=False,
            error_message=error_message,
            original_content=original_content,
        )


class ParsingStrategy(ABC):
    """
    Abstract base for parsing strategies.

    SRP: Each strategy handles exactly one parsing approach.
    KISS: Single method with clear success/failure result.
    """

    @abstractmethod
    def attempt_parse(self, content: str) -> ParseResult:
        """
        Attempt to parse content using this strategy.

        Args:
            content: Raw content string to parse

        Returns:
            ParseResult: Clear success/failure with data or error message
        """
        pass

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Name of this parsing strategy for logging."""
        pass


class ErrorTolerantParser:
    """
    KISS: Try parsing strategies in order until one succeeds.

    This is the core of our robust parsing - we try increasingly tolerant
    strategies until we either succeed or exhaust all options.
    """

    def __init__(self, strategies: List[ParsingStrategy]):
        """
        Initialize with a list of strategies to try in order.

        Args:
            strategies: List of strategies, ordered from fastest/strictest to slowest/most tolerant
        """
        if not strategies:
            raise ValueError("At least one parsing strategy is required")

        self.strategies = strategies
        self.stats = {
            "total_attempts": 0,
            "successful_parses": 0,
            "strategy_successes": {
                strategy.strategy_name: 0 for strategy in strategies
            },
        }

    def parse(self, content: str) -> ParseResult:
        """
        Parse content using the first successful strategy.

        Args:
            content: Raw content to parse

        Returns:
            ParseResult: Result from first successful strategy, or failure if all strategies fail
        """
        self.stats["total_attempts"] += 1

        if not content or not content.strip():
            return ParseResult.failure_result(
                "Empty or whitespace-only content", content
            )

        # Try each strategy in order
        last_error = None
        for strategy in self.strategies:
            try:
                result = strategy.attempt_parse(content)
                if result.success:
                    self.stats["successful_parses"] += 1
                    self.stats["strategy_successes"][strategy.strategy_name] += 1
                    logger.debug(
                        f"Successfully parsed using strategy: {strategy.strategy_name}"
                    )
                    return result
                else:
                    last_error = result.error_message
                    logger.debug(
                        f"Strategy {strategy.strategy_name} failed: {result.error_message}"
                    )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Strategy {strategy.strategy_name} raised exception: {e}"
                )

        # All strategies failed
        error_msg = f"All parsing strategies failed. Last error: {last_error}"
        logger.warning(error_msg)
        return ParseResult.failure_result(error_msg, content)

    def get_stats(self) -> dict:
        """Get parsing statistics for monitoring and debugging."""
        return self.stats.copy()


class SimpleParser(ABC):
    """
    Base class for simple, single-purpose parsers.

    SRP: Each parser handles exactly one content type or parsing concern.
    KISS: Minimal interface with clear, predictable behavior.
    """

    def __init__(self):
        self.parse_count = 0
        self.success_count = 0

    @abstractmethod
    def parse(self, content: str) -> ParseResult:
        """
        Parse the given content.

        Args:
            content: Raw content string

        Returns:
            ParseResult: Parsing result with success/failure and data/error
        """
        pass

    @property
    @abstractmethod
    def parser_name(self) -> str:
        """Name of this parser for logging and debugging."""
        pass

    def _record_attempt(self, success: bool):
        """Record parsing attempt for statistics."""
        self.parse_count += 1
        if success:
            self.success_count += 1

    def get_success_rate(self) -> float:
        """Get success rate for monitoring."""
        if self.parse_count == 0:
            return 0.0
        return self.success_count / self.parse_count

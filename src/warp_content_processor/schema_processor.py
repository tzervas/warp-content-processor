"""
Schema detection and processing for Warp Terminal content types.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Union

import yaml

from .base_processor import ProcessingResult, SchemaProcessor
from .content_type import ContentType
from .processor_factory import ProcessorFactory

logger = logging.getLogger(__name__)


# Regular expression patterns for content detection
CONTENT_PATTERNS = {
    "workflow": [
        r"name:\s*.+\s*command:\s*.+",  # Basic workflow pattern
        r"shells:\s*\[.*\]|shells:\s*-\s*\w+",  # Shell specifications
    ],
    "prompt": [
        r"name:\s*.+\s*prompt:\s*.+",  # Basic prompt pattern
        r"completion:\s*|response:\s*",  # Common prompt fields
    ],
    "notebook": [
        r"---[\s\S]*?title:[\s\S]*?---",  # Markdown front matter with title
        r"```[^`]*```",  # Code blocks
        r"^\s*#\s+",  # Markdown headers
    ],
    "env_var": [
        r"environment:\s*|env:\s*|variables:\s*",
        r"export\s+\w+=.*|\w+=.*",
    ],
    "rule": [
        r"title:\s*.+\s*description:\s*.+\s*guidelines?:\s*",
        r"standards?:\s*|rules?:\s*",
    ],
}


class ContentTypeDetector:
    """Detects content type from input."""

    @classmethod
    def detect_type(cls, content: str) -> str:
        """
        Detect the content type from input text.
        Uses pattern matching and heuristics to determine the most likely type.

        Args:
            content: String content to analyze

        Returns:
            str: Detected content type (from ContentType class)
        """
        if not content or content.isspace():
            return ContentType.UNKNOWN

        scores = {ContentType(ctype): 0 for ctype in CONTENT_PATTERNS}

        # Check each type's patterns
        for content_type_str, patterns in CONTENT_PATTERNS.items():
            content_type = ContentType(content_type_str)
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    scores[content_type] += 1

        # Get type with highest score
        if scores and max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]

        return ContentType.UNKNOWN


class ContentSplitter:
    """Splits combined content into individual documents."""

    # Patterns for document boundaries
    DOCUMENT_PATTERNS = {
        ContentType.WORKFLOW: r"(?:^|\n)---\s*(?:workflow|name):\s*.*?(?=\n---|\Z)",
        ContentType.PROMPT: r"(?:^|\n)---\s*(?:prompt|name):\s*.*?(?=\n---|\Z)",
        ContentType.NOTEBOOK: r"(?:^|\n)---\s*title:\s*.*?(?=\n---|\Z)",
        ContentType.ENV_VAR: (
            r"(?:^|\n)(?:environment|variables):\s*.*?(?=\n(?:environment|variables)|\Z)"
        ),
        ContentType.RULE: r"(?:^|\n)---\s*(?:rule|title):\s*.*?(?=\n---|\Z)",
    }

    @classmethod
    def split_content(cls, content: str) -> List[Tuple[str, str]]:
        """
        Split content into individual documents and detect their types.

        Returns:
            List[Tuple[str, str]]: List of (content_type, document_content) pairs
        """
        documents = []

        # First try to split by YAML documents with explicit separators
        sections = re.split(r'^---\s*$', content, flags=re.MULTILINE)
        
        # Filter out empty sections and process each non-empty one
        for section in sections:
            section = section.strip()
            if not section:
                continue

            try:
                # Try to parse as YAML first
                doc = yaml.safe_load(section)
                if doc and isinstance(doc, dict):
                    doc_content = yaml.dump(doc)
                    doc_type = ContentTypeDetector.detect_type(doc_content)
                    documents.append((doc_type, doc_content))
                    continue
            except yaml.YAMLError:
                pass

            # If not valid YAML, detect type from content patterns
            doc_type = ContentTypeDetector.detect_type(section)
            documents.append((doc_type, section))

        return documents


class ContentProcessor:
    """Main processor for all content types."""

    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.processors: Dict[ContentType, SchemaProcessor] = {
            content_type: ProcessorFactory.create_processor(
                content_type, self.output_dir
            )
            for content_type in ContentType
            if content_type != ContentType.UNKNOWN
        }

        # Create output directories
        for content_type in self.processors.keys():
            (self.output_dir / str(content_type)).mkdir(parents=True, exist_ok=True)

    def process_file(self, file_path: Union[str, Path]) -> List[ProcessingResult]:
        """
        Process a single file that may contain multiple content types.

        Returns:
            List[ProcessingResult]: Results for each processed document
        """
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            documents = ContentSplitter.split_content(content)
            results = []

            for doc_type_str, doc_content in documents:
                try:
                    doc_type = ContentType(doc_type_str)
                    if doc_type in self.processors:
                        processor = self.processors[doc_type]
                        result = processor.process(doc_content)

                        if result.is_valid and result.data is not None:
                            # Generate filename and save
                            filename = processor.generate_filename(result.data)
                            output_path = self.output_dir / doc_type / filename

                            # Ensure unique filename
                            counter = 1
                            while output_path.exists():
                                base_name = filename.rsplit(".", 1)[0]
                                ext = filename.rsplit(".", 1)[1]
                                output_path = (
                                    self.output_dir
                                    / doc_type
                                    / f"{base_name}_{counter}.{ext}"
                                )
                                counter += 1

                            output_path.write_text(doc_content)
                            logger.info("Saved %s content to %s", doc_type, output_path)

                        results.append(result)
                except ValueError:
                    logger.warning("Unknown content type in %s", file_path)
                    results.append(
                        ProcessingResult(
                            content_type=ContentType.UNKNOWN,
                            is_valid=False,
                            data=None,
                            errors=["Unknown content type"],
                            warnings=[],
                        )
                    )

            return results

        except Exception as e:
            logger.error("Error processing %s: %s", file_path, str(e))
            return [
                ProcessingResult(
                    content_type=ContentType.UNKNOWN,
                    is_valid=False,
                    data=None,
                    errors=[str(e)],
                    warnings=[],
                )
            ]

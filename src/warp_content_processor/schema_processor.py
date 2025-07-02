"""
Schema detection and processing for Warp Terminal content types.
"""

import logging
import re
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import yaml

from .base_processor import ProcessingResult

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Enumeration of supported content types."""

    WORKFLOW = "workflow"
    PROMPT = "prompt"
    NOTEBOOK = "notebook"
    ENV_VAR = "env_var"
    RULE = "rule"
    UNKNOWN = "unknown"

    # Regular expression patterns for content detection
    PATTERNS = {
        ContentType.WORKFLOW: [
            r"name:\s*.+\s*command:\s*.+",  # Basic workflow pattern
            r"shells:\s*\[.*\]|shells:\s*-\s*\w+",  # Shell specifications
        ],
        ContentType.PROMPT: [
            r"name:\s*.+\s*prompt:\s*.+",  # Basic prompt pattern
            r"completion:\s*|response:\s*",  # Common prompt fields
        ],
        ContentType.NOTEBOOK: [
            r"---\s*title:\s*.+\s*---",  # Markdown front matter
            r"#\s+.*\n.*```.*```",  # Markdown with code blocks
        ],
        ContentType.ENV_VAR: [
            r"environment:\s*|env:\s*|variables:\s*",
            r"export\s+\w+=.*|\w+=.*",
        ],
        ContentType.RULE: [
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

        scores = {ctype: 0 for ctype in ContentType.PATTERNS.keys()}

        # Check each type's patterns
        for content_type, patterns in ContentType.PATTERNS.items():
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
        ContentType.ENV_VAR: r"(?:^|\n)(?:environment|variables):\s*.*?(?=\n(?:environment|variables)|\Z)",
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

        # First try to split by YAML documents
        try:
            yaml_docs = list(yaml.safe_load_all(content))
            if len(yaml_docs) > 1:
                for doc in yaml_docs:
                    if doc:  # Skip empty documents
                        doc_content = yaml.dump(doc)
                        doc_type = ContentTypeDetector.detect_type(doc_content)
                        documents.append((doc_type, doc_content))
                return documents
        except yaml.YAMLError:
            pass

        # If YAML splitting fails, try pattern-based splitting
        current_pos = 0
        content_length = len(content)

        while current_pos < content_length:
            # Try to find the next document boundary
            next_doc_start = content_length
            detected_type = None

            for content_type, pattern in cls.DOCUMENT_PATTERNS.items():
                match = re.search(
                    pattern, content[current_pos:], re.MULTILINE | re.DOTALL
                )
                if match and match.start() + current_pos < next_doc_start:
                    next_doc_start = match.start() + current_pos
                    detected_type = content_type

            if detected_type:
                # Extract document content
                doc_content = content[current_pos:next_doc_start].strip()
                if doc_content:  # Don't add empty documents
                    doc_type = ContentTypeDetector.detect_type(doc_content)
                    documents.append((doc_type, doc_content))
                current_pos = next_doc_start
            else:
                # No more boundaries found, add remaining content if any
                remaining = content[current_pos:].strip()
                if remaining:
                    doc_type = ContentTypeDetector.detect_type(remaining)
                    documents.append((doc_type, remaining))
                break

        return documents


class ContentProcessor:
    """Main processor for all content types."""

    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.processors = {
            ContentType.WORKFLOW: WorkflowProcessor(self.output_dir),
            ContentType.PROMPT: PromptProcessor(),
            ContentType.NOTEBOOK: NotebookProcessor(),
            ContentType.ENV_VAR: EnvVarProcessor(),
            ContentType.RULE: RuleProcessor(),
        }

        # Create output directories
        for content_type in ContentType.__dict__.values():
            if isinstance(content_type, str) and content_type != "UNKNOWN":
                (self.output_dir / content_type).mkdir(parents=True, exist_ok=True)

    def process_file(self, file_path: Union[str, Path]) -> List[ProcessingResult]:
        """
        Process a single file that may contain multiple content types.

        Returns:
            List[ProcessingResult]: Results for each processed document
        """
        try:
            content = Path(file_path).read_text()
            documents = ContentSplitter.split_content(content)
            results = []

            for doc_type, doc_content in documents:
                if doc_type in self.processors:
                    processor = self.processors[doc_type]
                    result = processor.process(doc_content)

                    if result.is_valid:
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
                else:
                    logger.warning("Unknown content type in %s", file_path)
                    results.append(
                        ProcessingResult(
                            content_type=ContentType.UNKNOWN,
                            is_valid=False,
                            data=None,
                            errors=[f"Unknown content type"],
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

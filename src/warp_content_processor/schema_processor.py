"""
Schema detection and processing for Warp Terminal content types.
Includes security validation and content normalization.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple, Union

import yaml

from .base_processor import ProcessingResult, SchemaProcessor
from .content_type import ContentType
from .processor_factory import ProcessorFactory
from .utils.security import (
    ContentSanitizer, 
    SecurityValidationError, 
    secure_yaml_load, 
    secure_yaml_dump
)
from .utils.normalizer import ContentNormalizer

logger = logging.getLogger(__name__)


# Regular expression patterns for content detection
CONTENT_PATTERNS = {
    "workflow": [
        r"name:\s*.+command:\s*",  # Basic workflow pattern
        r"shells:\s*[\[\-]",  # Shell specifications
        r"command:\s*.+",  # Command field
    ],
    "prompt": [
        r"name:\s*.+prompt:\s*",  # Basic prompt pattern
        r"prompt:\s*.+\{\{.*\}\}",  # Prompt with template variables
        r"arguments:\s*\-\s*name:",  # Prompt arguments
    ],
    "notebook": [
        r"title:\s*.+description:\s*.+tags:\s*\n\s*\-",  # Notebook with title/desc/tags
        r"```[^`]*```",  # Code blocks
        r"^\s*##?\s+[^\n]*\n\s*\n.*```",  # Markdown headers with code blocks
    ],
    "env_var": [
        r"variables:\s*\n\s+\w+:",  # Variables block
        r"environment:\s*\n",  # Environment block
        r"scope:\s*user",  # Scope indicator
    ],
    "rule": [
        r"title:\s*.+description:\s*.+guidelines:\s*\-",  # Rule with guidelines
        r"category:\s*\w+",  # Category field
        r"guidelines:\s*\n\s*\-",  # Guidelines list
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
    """Splits combined content into individual documents with security validation."""

    @classmethod
    def split_content(cls, content: str) -> List[Tuple[str, str]]:
        """
        Split content into individual documents and detect their types.
        Includes security validation and content normalization.

        Returns:
            List[Tuple[str, str]]: List of (content_type, document_content) pairs
        """
        try:
            # Validate and sanitize input
            content = ContentSanitizer.validate_content(content)
        except SecurityValidationError as e:
            logger.error(f"Security validation failed: {e}")
            return []
        
        documents = []

        # First try simple document separation before normalization
        try:
            simple_docs = cls._simple_split_content(content)
            if len(simple_docs) > 1:
                # Multiple documents found, use simple splitting
                return simple_docs
        except Exception as e:
            logger.warning(f"Simple splitting failed: {e}")
        
        # Use the enhanced normalizer for single document or complex parsing
        try:
            normalized_docs = ContentNormalizer.normalize_mixed_content(content)
            for content_type, normalized_data in normalized_docs:
                if content_type != 'unknown':
                    # Convert back to string format for processing
                    try:
                        doc_content = secure_yaml_dump(normalized_data)
                        documents.append((ContentType(content_type), doc_content))
                    except Exception as e:
                        logger.warning(f"Failed to serialize {content_type}: {e}")
                        # Fall back to raw content
                        if 'content' in normalized_data:
                            documents.append((ContentType.UNKNOWN, normalized_data['content']))
                else:
                    # Handle unknown content types
                    if isinstance(normalized_data, dict) and 'content' in normalized_data:
                        doc_type = ContentTypeDetector.detect_type(normalized_data['content'])
                        documents.append((doc_type, normalized_data['content']))
            
            if documents:
                return documents
        except Exception as e:
            logger.warning(f"Normalization failed, falling back to simple splitting: {e}")

        # Fallback to simple splitting if normalization fails
        return cls._simple_split_content(content)
    
    @classmethod
    def _simple_split_content(cls, content: str) -> List[Tuple[str, str]]:
        """Simple content splitting as fallback."""
        documents = []
        
        # First try to split by YAML documents
        try:
            yaml_docs = list(yaml.safe_load_all(content))
            if len(yaml_docs) > 1:
                for doc in yaml_docs:
                    if doc:  # Skip empty documents
                        try:
                            doc_content = secure_yaml_dump(doc)
                            doc_type = ContentTypeDetector.detect_type(doc_content)
                            documents.append((doc_type, doc_content))
                        except Exception as e:
                            logger.warning(f"Failed to process YAML document: {e}")
                return documents
        except yaml.YAMLError:
            pass

        # If YAML splitting fails, split by YAML document separators (with possible indentation)
        parts = re.split(r'^\s*---\s*$', content, flags=re.MULTILINE)
        
        for part in parts:
            part = part.strip()
            if part:  # Skip empty parts
                try:
                    part = ContentSanitizer.sanitize_string(part)
                    doc_type = ContentTypeDetector.detect_type(part)
                    documents.append((doc_type, part))
                except SecurityValidationError as e:
                    logger.warning(f"Part failed security validation: {e}")

        # If no documents found, treat entire content as single document
        if not documents:
            try:
                content = ContentSanitizer.sanitize_string(content)
                doc_type = ContentTypeDetector.detect_type(content)
                documents.append((doc_type, content))
            except SecurityValidationError as e:
                logger.error(f"Content failed security validation: {e}")

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
            (self.output_dir / content_type.value).mkdir(parents=True, exist_ok=True)

    def process_file(self, file_path: Union[str, Path]) -> List[ProcessingResult]:
        """
        Process a single file that may contain multiple content types.
        Includes security validation for file paths and content.

        Returns:
            List[ProcessingResult]: Results for each processed document
        """
        try:
            # Validate file path for security
            validated_path = ContentSanitizer.validate_file_path(file_path)
            
            # Read and validate content
            content = validated_path.read_text(encoding="utf-8")
            content = ContentSanitizer.validate_content(content)
            
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
                            output_path = self.output_dir / doc_type.value / filename

                            # Ensure unique filename
                            counter = 1
                            while output_path.exists():
                                base_name = filename.rsplit(".", 1)[0]
                                ext = filename.rsplit(".", 1)[1]
                                output_path = (
                                    self.output_dir
                                    / doc_type.value
                                    / f"{base_name}_{counter}.{ext}"
                                )
                                counter += 1

                            # Save the processed and normalized data instead of raw content
                            try:
                                processed_content = secure_yaml_dump(result.data)
                                output_path.write_text(processed_content)
                                logger.info("Saved %s content to %s", doc_type, output_path)
                            except Exception as save_error:
                                logger.error("Failed to save %s to %s: %s", doc_type, output_path, save_error)
                                # Fall back to original content if serialization fails
                                output_path.write_text(doc_content)
                                logger.info("Saved %s content to %s (fallback)", doc_type, output_path)

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

#!/usr/bin/env python3

"""
Main script for processing Warp Terminal content files.
Handles validation, splitting, and organization of various content types.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Union

from warp_content_processor.base_processor import ProcessingResult

from .processors.schema_processor import ContentProcessor


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("workflow_processing.log"),
        ],
    )


def process_directory(
    source_dir: Union[str, Path], output_dir: Union[str, Path]
) -> Dict[str, List[ProcessingResult]]:
    """Process all files in a directory and its subdirectories."""
    processor = ContentProcessor(output_dir)
    results: Dict[str, List[ProcessingResult]] = {}

    # Process all yaml, yml, and md files
    for ext in ["*.yaml", "*.yml", "*.md"]:
        for file_path in Path(source_dir).rglob(ext):
            file_results = processor.process_file(file_path)
            for result in file_results:
                if result.content_type not in results:
                    results[result.content_type] = []
                results[result.content_type].append(result)

    return results


def main() -> None:
    """Main entry point for content processing."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Define paths relative to the project root
        project_root = Path(__file__).parent.parent
        source_dir = project_root / "imports"
        output_dir = project_root / "output"

        # Process all content
        results = process_directory(source_dir, output_dir)

        # Report results by content type
        for content_type, type_results in results.items():
            valid_count = sum(1 for r in type_results if r.is_valid)
            total_count = len(type_results)
            logger.info(
                f"{content_type}: Processed {total_count} files, {valid_count} valid"
            )

            # Report errors and warnings
            for result in type_results:
                if result.errors:
                    logger.error(f"{content_type} errors: {result.errors}")
                if result.warnings:
                    logger.warning(f"{content_type} warnings: {result.warnings}")

    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

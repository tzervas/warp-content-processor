"""Factory for creating content processors."""

from pathlib import Path
from typing import Dict, Type, Union

from .base_processor import SchemaProcessor
from .processors.env_var_processor import EnvVarProcessor
from .processors.notebook_processor import NotebookProcessor
from .processors.prompt_processor import PromptProcessor
from .processors.rule_processor import RuleProcessor
from .schema_processor import ContentType
from .workflow_processor import WorkflowProcessor


class ProcessorFactory:
    """Factory for creating content processors."""

    _processors: Dict[ContentType, Type[SchemaProcessor]] = {
        ContentType.WORKFLOW: WorkflowProcessor,
        ContentType.PROMPT: PromptProcessor,
        ContentType.NOTEBOOK: NotebookProcessor,
        ContentType.ENV_VAR: EnvVarProcessor,
        ContentType.RULE: RuleProcessor,
    }

    @classmethod
    def create_processor(
        cls, content_type: ContentType, output_dir: Union[str, Path] = None
    ) -> SchemaProcessor:
        """Create a processor instance for the given content type."""
        processor_class = cls._processors.get(content_type)
        if not processor_class:
            raise ValueError(f"No processor available for content type: {content_type}")

        if output_dir is not None:
            return processor_class(Path(output_dir))
        return processor_class()

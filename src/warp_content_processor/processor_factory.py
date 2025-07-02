"""Factory for creating content processors."""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from .base_processor import SchemaProcessor
from .content_type import ContentType


class ProcessorFactory:
    """Factory for creating content processors."""

    _processor_imports = {
        "workflow": ("workflow_processor", "WorkflowProcessor"),
        "prompt": ("processors.prompt_processor", "PromptProcessor"),
        "notebook": ("processors.notebook_processor", "NotebookProcessor"),
        "env_var": ("processors.env_var_processor", "EnvVarProcessor"),
        "rule": ("processors.rule_processor", "RuleProcessor"),
    }

    _processors: Dict[str, Any] = {}

    @classmethod
    def _get_processor_class(cls, content_type_str: str) -> Optional[Any]:
        """Lazy load processor class to avoid circular imports."""
        if content_type_str not in cls._processors:
            if content_type_str == "workflow":
                from .workflow_processor import WorkflowProcessor

                cls._processors[content_type_str] = WorkflowProcessor
            elif content_type_str == "prompt":
                from .processors.prompt_processor import PromptProcessor

                cls._processors[content_type_str] = PromptProcessor
            elif content_type_str == "notebook":
                from .processors.notebook_processor import NotebookProcessor

                cls._processors[content_type_str] = NotebookProcessor
            elif content_type_str == "env_var":
                from .processors.env_var_processor import EnvVarProcessor

                cls._processors[content_type_str] = EnvVarProcessor
            elif content_type_str == "rule":
                from .processors.rule_processor import RuleProcessor

                cls._processors[content_type_str] = RuleProcessor
            else:
                return None

        return cls._processors[content_type_str]

    @classmethod
    def create_processor(
        cls, content_type: ContentType, output_dir: Union[str, Path]
    ) -> SchemaProcessor:
        """Create a processor instance for the given content type."""
        processor_class = cls._get_processor_class(str(content_type))
        if not processor_class:
            raise ValueError(f"No processor available for content type: {content_type}")

        processor: SchemaProcessor = processor_class(Path(output_dir))
        return processor

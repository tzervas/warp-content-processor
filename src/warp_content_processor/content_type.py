"""Content type definitions."""

from enum import Enum


class ContentType(str, Enum):
    """Enumeration of supported content types."""

    WORKFLOW = "workflow"
    PROMPT = "prompt"
    NOTEBOOK = "notebook"
    ENV_VAR = "env_var"
    RULE = "rule"
    UNKNOWN = "unknown"

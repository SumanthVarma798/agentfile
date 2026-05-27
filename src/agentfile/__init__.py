"""Agentfile: a portable, declarative format for AI agent setups."""

from agentfile.errors import (
    AgentfileError,
    SchemaValidationError,
    SecretLeakError,
)
from agentfile.errors import (
    ReferenceError as AgentfileReferenceError,
)
from agentfile.loader import load_agentfile
from agentfile.review import compare_files, compare_manifests, review_file, review_manifest
from agentfile.validator import ValidationResult, validate, validate_file

__version__ = "0.2.0"
__all__ = [
    "AgentfileError",
    "AgentfileReferenceError",
    "SchemaValidationError",
    "SecretLeakError",
    "ValidationResult",
    "compare_files",
    "compare_manifests",
    "load_agentfile",
    "review_file",
    "review_manifest",
    "validate",
    "validate_file",
]

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
from agentfile.validator import ValidationResult, validate, validate_file

__version__ = "0.2.0"
__all__ = [
    "AgentfileError",
    "AgentfileReferenceError",
    "SchemaValidationError",
    "SecretLeakError",
    "ValidationResult",
    "load_agentfile",
    "validate",
    "validate_file",
]

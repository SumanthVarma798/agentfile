"""Exception hierarchy for Agentfile errors."""

from __future__ import annotations


class AgentfileError(Exception):
    """Base class for all Agentfile errors."""


class SchemaValidationError(AgentfileError):
    """Raised when an Agentfile fails JSON Schema validation.

    Attributes:
        errors: List of human-readable error messages, one per violation.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        message = f"Schema validation failed with {len(errors)} error(s):\n  - " + "\n  - ".join(
            errors
        )
        super().__init__(message)


class ReferenceError(AgentfileError):
    """Raised when a referenced file (e.g. system_prompt.file) cannot be resolved."""


class SecretLeakError(AgentfileError):
    """Raised when a value in the Agentfile looks like a real credential."""

    def __init__(self, field: str, pattern: str) -> None:
        self.field = field
        self.pattern = pattern
        super().__init__(
            f"Possible secret detected in field '{field}' (matched pattern: {pattern}). "
            f"Credentials must be referenced via env vars, not embedded."
        )

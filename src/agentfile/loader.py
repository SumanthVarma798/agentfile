"""Load Agentfiles from disk or strings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from agentfile.errors import AgentfileError


def load_agentfile(path: str | Path) -> dict[str, Any]:
    """Load an Agentfile from a path. Supports .yaml, .yml, and .json.

    Args:
        path: Path to the Agentfile.

    Returns:
        The parsed manifest as a dict.

    Raises:
        AgentfileError: If the file cannot be read or parsed.
    """
    p = Path(path)
    if not p.exists():
        raise AgentfileError(f"Agentfile not found: {p}")
    if not p.is_file():
        raise AgentfileError(f"Path is not a file: {p}")

    text = p.read_text(encoding="utf-8")

    # Default to YAML for .yaml, .yml, or anything else (Agentfile, agent.yml, etc.)
    suffix = p.suffix.lower()
    try:
        data = json.loads(text) if suffix == ".json" else yaml.safe_load(text)
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise AgentfileError(f"Failed to parse {p}: {e}") from e

    if not isinstance(data, dict):
        raise AgentfileError(f"Agentfile must be a mapping at top level, got {type(data).__name__}")

    return data


def load_agentfile_from_string(text: str, format: str = "yaml") -> dict[str, Any]:
    """Load an Agentfile from a string.

    Args:
        text: The Agentfile content.
        format: Either 'yaml' or 'json'.

    Returns:
        The parsed manifest as a dict.
    """
    try:
        if format == "json":
            data = json.loads(text)
        elif format == "yaml":
            data = yaml.safe_load(text)
        else:
            raise AgentfileError(f"Unknown format: {format}")
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise AgentfileError(f"Failed to parse Agentfile: {e}") from e

    if not isinstance(data, dict):
        raise AgentfileError(f"Agentfile must be a mapping at top level, got {type(data).__name__}")

    return data

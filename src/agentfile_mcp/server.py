"""Agentfile MCP server.

Exposes Agentfile authoring and validation tools via the Model Context Protocol.
Connect with: agentfile-mcp  (stdio transport, default)
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP

from agentfile.validator import get_schema, validate, validate_file

mcp = FastMCP("agentfile")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
_SPEC_PATH = Path(__file__).resolve().parents[2] / "SPEC.md"

_EXAMPLE_META: list[dict[str, str]] = [
    {
        "name": "research-agent",
        "path": str(_EXAMPLES_DIR / "research-agent" / "agent.yaml"),
        "description": "Web-research agent that synthesises findings into Markdown briefs.",
    },
    {
        "name": "data-pipeline",
        "path": str(_EXAMPLES_DIR / "data-pipeline" / "agent.yaml"),
        "description": "FHIR bulk-data pipeline agent with custom MCP servers and Chroma memory.",
    },
    {
        "name": "coding-helper",
        "path": str(_EXAMPLES_DIR / "coding-helper" / "agent.yaml"),
        "description": "Minimal coding assistant — smallest valid Agentfile.",
    },
]


def _example_by_name(name: str) -> dict[str, str] | None:
    return next((e for e in _EXAMPLE_META if e["name"] == name), None)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def validate_agentfile(path: str, strict: bool = False) -> dict[str, Any]:
    """Validate an Agentfile at the given path.

    Args:
        path: Absolute or relative path to an agent.yaml / Agentfile.yaml.
        strict: If True, warnings are promoted to errors.

    Returns:
        dict with keys: valid (bool), errors (list[str]), warnings (list[str]).
    """
    result = validate_file(path, strict=strict)
    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@mcp.tool()
def show_agentfile(path: str) -> dict[str, Any]:
    """Parse and summarise an Agentfile.

    Args:
        path: Path to the Agentfile.

    Returns:
        dict with keys: manifest (the parsed dict) and summary (human-readable string).
    """
    result = validate_file(path)
    manifest = result.manifest or {}
    meta = manifest.get("metadata", {})
    spec = manifest.get("spec", {})
    model = spec.get("model", {})
    tools = spec.get("tools") or []
    tool_names = [t.get("mcp", "?") for t in tools if isinstance(t, dict)]

    sp = spec.get("system_prompt")
    sp_summary = (
        f"[inline] {str(sp).strip().splitlines()[0][:80]}"
        if isinstance(sp, str)
        else f"[file] {sp.get('file')}"
        if isinstance(sp, dict)
        else "?"
    )

    env = spec.get("env", {}) or {}
    req_env = ", ".join(env.get("required") or []) or "none"

    summary_lines = [
        f"name:         {meta.get('name', '?')} v{meta.get('version', '?')}",
        f"description:  {meta.get('description', '(none)')}",
        f"model:        {model.get('provider', '?')}:{model.get('name', '?')}",
        f"system_prompt:{sp_summary}",
        f"tools ({len(tools)}):   {', '.join(tool_names) or 'none'}",
        f"env required: {req_env}",
    ]

    if mem := spec.get("memory"):
        summary_lines.append(f"memory:       {mem.get('type', '?')}")

    return {
        "manifest": manifest,
        "summary": "\n".join(summary_lines),
    }


@mcp.tool()
def get_agentfile_schema() -> dict[str, Any]:
    """Return the Agentfile v1 JSON Schema."""
    return get_schema()


@mcp.tool()
def list_examples() -> list[dict[str, str]]:
    """Return metadata for the 3 bundled Agentfile examples.

    Returns:
        List of dicts with keys: name, path, description.
    """
    return _EXAMPLE_META


@mcp.tool()
def read_example(name: str) -> str:
    """Return the raw YAML of a bundled example.

    Args:
        name: One of 'research-agent', 'data-pipeline', 'coding-helper'.

    Returns:
        YAML string of the example Agentfile.
    """
    meta = _example_by_name(name)
    if meta is None:
        known = [e["name"] for e in _EXAMPLE_META]
        raise ValueError(f"Unknown example '{name}'. Known examples: {known}")
    return Path(meta["path"]).read_text(encoding="utf-8")


@mcp.tool()
def scaffold(
    name: str,
    description: str = "",
    model_provider: str = "anthropic",
    model_name: str = "claude-sonnet-4-5",
    tools: list[str] | None = None,
    system_prompt_intent: str = "",
) -> str:
    """Generate a starter Agentfile YAML that passes validation.

    Args:
        name: Kebab-case agent name (e.g. 'my-research-agent').
        description: One-line description of what the agent does.
        model_provider: One of anthropic, openai, google, bedrock, azure, local, custom.
        model_name: Provider-specific model identifier.
        tools: List of MCP tool identifiers (e.g. ['builtin/web_search', 'https://…/mcp']).
        system_prompt_intent: Plain-English description of the agent's purpose — used to
            write a sensible inline system prompt scaffold.

    Returns:
        YAML string of a valid Agentfile.
    """
    # Validate name pattern early for a better error message.
    import re

    if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", name):
        raise ValueError(
            f"name '{name}' is invalid. Use kebab-case: lowercase letters, digits, hyphens. "
            "Must start and end with a letter or digit."
        )

    tool_list: list[dict[str, str]] = []
    for t in tools or []:
        tool_list.append({"mcp": t})

    intent = system_prompt_intent.strip() or f"You are {name}, a helpful AI assistant."
    system_prompt = textwrap.dedent(f"""\
        {intent}

        Always be concise and accurate.
        Never embed credentials or sensitive data in responses.
    """)

    manifest: dict[str, Any] = {
        "apiVersion": "agentfile/v1",
        "kind": "Agent",
        "metadata": {
            "name": name,
            "version": "0.1.0",
            **({"description": description} if description else {}),
        },
        "spec": {
            "model": {
                "provider": model_provider,
                "name": model_name,
            },
            "system_prompt": system_prompt,
            **({"tools": tool_list} if tool_list else {}),
            "env": {
                "required": ["ANTHROPIC_API_KEY"],
            },
        },
    }

    result = validate(manifest)
    if not result.valid:
        # Should only happen if caller passes a bad model_provider; surface clearly.
        raise ValueError(f"Scaffolded manifest is invalid: {result.errors}")

    return yaml.dump(manifest, sort_keys=False, allow_unicode=True)


@mcp.tool()
def lint_inline(yaml_text: str, strict: bool = False) -> dict[str, Any]:
    """Validate a YAML string with no file on disk.

    Useful when the manifest is already in agent context (e.g. pasted by the user).
    File-reference checks (system_prompt.file) are skipped since there is no base directory.

    Args:
        yaml_text: Raw YAML or JSON string of an Agentfile manifest.
        strict: If True, warnings are promoted to errors.

    Returns:
        dict with keys: valid (bool), errors (list[str]), warnings (list[str]).
    """
    import yaml as _yaml

    try:
        manifest = _yaml.safe_load(yaml_text)
    except _yaml.YAMLError as exc:
        return {"valid": False, "errors": [f"YAML parse error: {exc}"], "warnings": []}

    if not isinstance(manifest, dict):
        return {
            "valid": False,
            "errors": ["Top-level document must be a YAML mapping (dict)."],
            "warnings": [],
        }

    result = validate(manifest, base_dir=None, strict=strict)
    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("agentfile://spec")
def spec_resource() -> str:
    """Full text of SPEC.md — the authoritative Agentfile v1 specification."""
    return _SPEC_PATH.read_text(encoding="utf-8")


@mcp.resource("agentfile://schema")
def schema_resource() -> str:
    """Agentfile v1 JSON Schema as a JSON string."""
    return json.dumps(get_schema(), indent=2)


@mcp.resource("agentfile://examples/{name}")
def example_resource(name: str) -> str:
    """Raw YAML of a bundled example Agentfile.

    Available names: research-agent, data-pipeline, coding-helper.
    """
    meta = _example_by_name(name)
    if meta is None:
        known = [e["name"] for e in _EXAMPLE_META]
        raise ValueError(f"Unknown example '{name}'. Known: {known}")
    return Path(meta["path"]).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the Agentfile MCP server (stdio transport)."""
    mcp.run()


if __name__ == "__main__":
    main()

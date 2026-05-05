"""Validate Agentfiles against the v1 spec."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaError

from agentfile.errors import SchemaValidationError
from agentfile.loader import load_agentfile

# Heuristic patterns for common credential formats. Used for warnings, not hard failures
# (except when explicitly invoked with strict=True via the CLI).
SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "anthropic-api-key": re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}"),
    "openai-api-key": re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    "github-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "google-api-key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "slack-token": re.compile(r"xox[bpoa]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{20,}"),
    "private-key-block": re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
}

# Builtin tool names recognized by the reference validator. Unknown values are warned, not rejected.
KNOWN_BUILTINS = {
    "filesystem",
    "web_search",
    "web_fetch",
    "shell",
    "code_interpreter",
    "memory",
}


@dataclass
class ValidationResult:
    """Outcome of validating an Agentfile.

    Attributes:
        valid: True if no errors. Warnings do not invalidate.
        errors: Hard validation failures.
        warnings: Soft issues (unknown builtins, possible secrets, etc.).
        manifest: The parsed manifest (may be partial if loading failed).
    """

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    manifest: dict[str, Any] | None = None

    def raise_if_invalid(self) -> None:
        """Raise SchemaValidationError if validation failed."""
        if not self.valid:
            raise SchemaValidationError(self.errors)


def _load_schema() -> dict[str, Any]:
    """Load the bundled JSON Schema."""
    # Try the installed location first (when packaged), fall back to repo layout.
    try:
        schema_text = (
            resources.files("agentfile") / "_schema" / "agentfile.v1.schema.json"
        ).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        # Repo layout: schema lives in <repo>/schema/
        repo_schema = Path(__file__).resolve().parents[2] / "schema" / "agentfile.v1.schema.json"
        schema_text = repo_schema.read_text(encoding="utf-8")
    return json.loads(schema_text)


_SCHEMA: dict[str, Any] | None = None


def get_schema() -> dict[str, Any]:
    """Return the JSON Schema for Agentfile v1 (cached)."""
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = _load_schema()
    return _SCHEMA


def _format_jsonschema_error(err: JsonSchemaError) -> str:
    """Format a jsonschema error into a friendly single-line message."""
    location = ".".join(str(p) for p in err.absolute_path) if err.absolute_path else "<root>"
    return f"{location}: {err.message}"


def _walk_strings(obj: Any, path: str = "") -> list[tuple[str, str]]:
    """Walk a nested structure yielding (json-path, string-value) for every string leaf."""
    out: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(_walk_strings(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_walk_strings(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        out.append((path or "<root>", obj))
    return out


def _check_secrets(manifest: dict[str, Any]) -> list[str]:
    """Scan all string values for things that look like credentials. Returns warning strings."""
    warnings: list[str] = []
    for path, value in _walk_strings(manifest):
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(value):
                warnings.append(
                    f"{path}: looks like a {name} (matched pattern). "
                    f"Credentials must be passed via env vars, not embedded."
                )
                break
    return warnings


def _check_references(manifest: dict[str, Any], base_dir: Path | None) -> list[str]:
    """Verify file references (system_prompt.file, memory.config.file) exist relative to base_dir.

    If base_dir is None, file references are skipped (e.g. when validating from a string).
    Returns a list of error strings.
    """
    errors: list[str] = []
    if base_dir is None:
        return errors

    spec = manifest.get("spec", {})

    # system_prompt.file
    sp = spec.get("system_prompt")
    if isinstance(sp, dict) and "file" in sp:
        rel = sp["file"]
        if _escapes_dir(rel):
            errors.append(f"spec.system_prompt.file: path '{rel}' escapes the Agentfile directory")
        else:
            target = (base_dir / rel).resolve()
            if not target.exists():
                errors.append(f"spec.system_prompt.file: '{rel}' not found relative to Agentfile")
            elif not target.is_file():
                errors.append(f"spec.system_prompt.file: '{rel}' is not a regular file")

    # memory.config.file
    mem = spec.get("memory")
    if isinstance(mem, dict):
        cfg = mem.get("config")
        if isinstance(cfg, dict) and "file" in cfg:
            rel = cfg["file"]
            if _escapes_dir(rel):
                errors.append(
                    f"spec.memory.config.file: path '{rel}' escapes the Agentfile directory"
                )
            else:
                target = (base_dir / rel).resolve()
                if not target.exists():
                    errors.append(
                        f"spec.memory.config.file: '{rel}' not found relative to Agentfile"
                    )

    return errors


def _escapes_dir(rel_path: str) -> bool:
    """Check if a relative path tries to escape its base via .. components."""
    parts = Path(rel_path).parts
    return ".." in parts or rel_path.startswith("/")


def _check_builtins(manifest: dict[str, Any]) -> list[str]:
    """Warn on unrecognized builtin/* tool names."""
    warnings: list[str] = []
    spec = manifest.get("spec", {})
    tools = spec.get("tools") or []
    for i, t in enumerate(tools):
        if not isinstance(t, dict):
            continue
        mcp = t.get("mcp", "")
        if isinstance(mcp, str) and mcp.startswith("builtin/"):
            name = mcp.removeprefix("builtin/")
            if name not in KNOWN_BUILTINS:
                warnings.append(
                    f"spec.tools[{i}].mcp: 'builtin/{name}' is not in the reference set "
                    f"({sorted(KNOWN_BUILTINS)}). Runtimes may not recognize it."
                )
    return warnings


def _check_custom_endpoint(manifest: dict[str, Any]) -> list[str]:
    """If provider is 'custom', endpoint must be present."""
    errors: list[str] = []
    model = manifest.get("spec", {}).get("model", {})
    if model.get("provider") == "custom" and "endpoint" not in model:
        errors.append("spec.model: when provider is 'custom', 'endpoint' is required")
    return errors


def _check_auth_env(manifest: dict[str, Any]) -> list[str]:
    """If a tool uses bearer auth, an env var name should be provided."""
    warnings: list[str] = []
    tools = manifest.get("spec", {}).get("tools") or []
    for i, t in enumerate(tools):
        if not isinstance(t, dict):
            continue
        auth = t.get("auth")
        if isinstance(auth, dict) and auth.get("type") == "bearer" and not auth.get("env"):
            warnings.append(
                f"spec.tools[{i}].auth: bearer auth declared without 'env' field; "
                f"runtimes won't know which env var holds the credential"
            )
    return warnings


def validate(
    manifest: dict[str, Any],
    *,
    base_dir: Path | str | None = None,
    strict: bool = False,
) -> ValidationResult:
    """Validate a parsed Agentfile manifest.

    Args:
        manifest: The parsed Agentfile (a dict).
        base_dir: Directory the Agentfile was loaded from, used to resolve file references.
                  If None, file-existence checks are skipped.
        strict: If True, warnings are promoted to errors.

    Returns:
        A ValidationResult.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Schema validation
    schema = get_schema()
    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path))
    for e in schema_errors:
        errors.append(_format_jsonschema_error(e))

    # If schema fails, we still run the other checks for better feedback,
    # but they may produce noise on a malformed manifest.
    base = Path(base_dir) if base_dir is not None else None

    # 2. Custom semantic checks (only meaningful if structure is roughly right)
    errors.extend(_check_custom_endpoint(manifest))
    errors.extend(_check_references(manifest, base))

    # 3. Soft warnings
    warnings.extend(_check_secrets(manifest))
    warnings.extend(_check_builtins(manifest))
    warnings.extend(_check_auth_env(manifest))

    if strict:
        errors.extend(warnings)
        warnings = []

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        manifest=manifest,
    )


def validate_file(path: str | Path, *, strict: bool = False) -> ValidationResult:
    """Load and validate an Agentfile at a given path.

    Args:
        path: Path to the Agentfile.
        strict: If True, warnings are promoted to errors.

    Returns:
        A ValidationResult.
    """
    p = Path(path).resolve()
    manifest = load_agentfile(p)
    return validate(manifest, base_dir=p.parent, strict=strict)

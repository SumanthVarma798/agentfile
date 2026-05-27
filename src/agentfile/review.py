"""Review helpers for team-shareable Agentfiles."""

from __future__ import annotations

import hashlib
import ipaddress
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from agentfile.loader import load_agentfile
from agentfile.validator import SECRET_PATTERNS, validate

Issue = dict[str, str]
Change = dict[str, Any]

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_INTERNAL_SUFFIXES = (".corp", ".internal", ".lan", ".local")


def review_file(path: str | Path, *, strict: bool = False) -> dict[str, Any]:
    """Review an Agentfile for team-shareability issues.

    Args:
        path: Path to an Agentfile.
        strict: If True, validator warnings are promoted to validation errors.

    Returns:
        Structured review result with validation status, issues, and summary.
    """
    p = Path(path).resolve()
    manifest = load_agentfile(p)
    return review_manifest(manifest, base_dir=p.parent, strict=strict)


def review_manifest(
    manifest: dict[str, Any],
    *,
    base_dir: Path | str | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Review a parsed Agentfile for portability and reviewability issues."""
    base = Path(base_dir) if base_dir is not None else None
    validation = validate(manifest, base_dir=base, strict=strict)
    issues: list[Issue] = []

    for error in validation.errors:
        issues.append(_issue("error", "<validation>", error, "Fix the validation error."))
    for warning in validation.warnings:
        issues.append(_issue("warning", "<validation>", warning, "Review before sharing."))

    issues.extend(_check_metadata(manifest))
    issues.extend(_check_tool_declarations(manifest))
    issues.extend(_check_permissions(manifest))
    issues.extend(_check_env_declarations(manifest))

    counts = _issue_counts(issues)
    return {
        "shareable": counts["error"] == 0 and counts["warning"] == 0,
        "valid": validation.valid,
        "errors": validation.errors,
        "warnings": validation.warnings,
        "issue_counts": counts,
        "issues": issues,
        "summary": _review_summary(counts),
    }


def compare_files(base_path: str | Path, head_path: str | Path) -> dict[str, Any]:
    """Compare two Agentfiles and return review-friendly changes.

    Args:
        base_path: Path to the older/base Agentfile.
        head_path: Path to the newer/head Agentfile.

    Returns:
        Structured change summary that avoids echoing secret-like values.
    """
    base = Path(base_path).resolve()
    head = Path(head_path).resolve()
    base_manifest = load_agentfile(base)
    head_manifest = load_agentfile(head)
    base_validation = validate(base_manifest, base_dir=base.parent)
    head_validation = validate(head_manifest, base_dir=head.parent)
    changes = compare_manifests(base_manifest, head_manifest)

    return {
        "changed": len(changes) > 0,
        "base_valid": base_validation.valid,
        "head_valid": head_validation.valid,
        "base_errors": base_validation.errors,
        "head_errors": head_validation.errors,
        "change_count": len(changes),
        "changes": changes,
        "summary": _change_summary(changes),
    }


def compare_manifests(
    base_manifest: dict[str, Any],
    head_manifest: dict[str, Any],
) -> list[Change]:
    """Compare two parsed Agentfiles and return a stable list of changes."""
    changes: list[Change] = []

    _compare_value(changes, base_manifest, head_manifest, "metadata.name", "low")
    _compare_value(changes, base_manifest, head_manifest, "metadata.version", "medium")
    _compare_value(changes, base_manifest, head_manifest, "metadata.description", "low")
    _compare_list(changes, base_manifest, head_manifest, "metadata.tags", "low")
    _compare_value(changes, base_manifest, head_manifest, "spec.model.provider", "high")
    _compare_value(changes, base_manifest, head_manifest, "spec.model.name", "high")
    _compare_value(changes, base_manifest, head_manifest, "spec.model.endpoint", "high")
    _compare_value(changes, base_manifest, head_manifest, "spec.model.params", "medium")
    _compare_prompt(changes, base_manifest, head_manifest)
    _compare_tools(changes, base_manifest, head_manifest)
    _compare_value(changes, base_manifest, head_manifest, "spec.memory", "medium")
    _compare_value(changes, base_manifest, head_manifest, "spec.permissions", "high")
    _compare_list(changes, base_manifest, head_manifest, "spec.env.required", "medium")
    _compare_list(changes, base_manifest, head_manifest, "spec.env.optional", "low")
    _compare_value(changes, base_manifest, head_manifest, "spec.params", "medium")

    return changes


def _issue(severity: str, path: str, message: str, recommendation: str) -> Issue:
    return {
        "severity": severity,
        "path": path,
        "message": message,
        "recommendation": recommendation,
    }


def _issue_counts(issues: list[Issue]) -> dict[str, int]:
    return {
        "error": sum(1 for issue in issues if issue["severity"] == "error"),
        "warning": sum(1 for issue in issues if issue["severity"] == "warning"),
        "info": sum(1 for issue in issues if issue["severity"] == "info"),
    }


def _review_summary(counts: dict[str, int]) -> str:
    if counts["error"] == 0 and counts["warning"] == 0 and counts["info"] == 0:
        return "No shareability issues found."

    parts = []
    if counts["error"]:
        parts.append(f"{counts['error']} error(s)")
    if counts["warning"]:
        parts.append(f"{counts['warning']} warning(s)")
    if counts["info"]:
        parts.append(f"{counts['info']} info note(s)")
    return "Shareability review found " + ", ".join(parts) + "."


def _check_metadata(manifest: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    metadata = manifest.get("metadata")
    if not isinstance(metadata, dict):
        return issues

    if not metadata.get("description"):
        issues.append(
            _issue(
                "info",
                "metadata.description",
                "No description is present.",
                "Add a short purpose statement so reviewers know what this agent is for.",
            )
        )
    if not metadata.get("license"):
        issues.append(
            _issue(
                "info",
                "metadata.license",
                "No license is present.",
                "Add an SPDX license identifier when publishing or sharing outside one repository.",
            )
        )
    return issues


def _check_tool_declarations(manifest: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    spec = manifest.get("spec")
    if not isinstance(spec, dict):
        return issues

    required_env, optional_env = _env_sets(spec)
    declared_network_hosts = _network_allowlist_hosts(spec)
    tools = spec.get("tools") or []
    if not isinstance(tools, list):
        return issues

    for index, tool in enumerate(tools):
        if not isinstance(tool, dict):
            continue

        mcp_value = tool.get("mcp")
        mcp_path = f"spec.tools[{index}].mcp"
        if not isinstance(mcp_value, str):
            continue

        host = _remote_host(mcp_value)
        if host is None and not mcp_value.startswith("builtin/"):
            issues.append(
                _issue(
                    "warning",
                    mcp_path,
                    "Tool reference is neither a builtin shorthand nor an HTTP(S) MCP URL.",
                    "Use builtin/<name> or a fully-qualified MCP server URL.",
                )
            )
        if host is not None:
            issues.extend(_host_shareability_issues(host, mcp_path))
            if declared_network_hosts is not None and host not in declared_network_hosts:
                issues.append(
                    _issue(
                        "warning",
                        mcp_path,
                        f"Host '{host}' is not present in permissions.network.hosts.",
                        "Add the host to the network allowlist or change the permission mode.",
                    )
                )

        auth = tool.get("auth")
        if isinstance(auth, dict) and auth.get("type") == "bearer":
            env_name = auth.get("env")
            if isinstance(env_name, str) and env_name not in required_env:
                severity = "warning" if env_name not in optional_env else "info"
                issues.append(
                    _issue(
                        severity,
                        f"spec.tools[{index}].auth.env",
                        f"Bearer token env '{env_name}' is not listed as required.",
                        "Add it to spec.env.required so teammates get a complete setup contract.",
                    )
                )
    return issues


def _check_permissions(manifest: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    spec = manifest.get("spec")
    if not isinstance(spec, dict):
        return issues

    permissions = spec.get("permissions")
    if not isinstance(permissions, dict):
        return issues

    network = permissions.get("network")
    if isinstance(network, dict) and network.get("mode") == "open":
        issues.append(
            _issue(
                "info",
                "spec.permissions.network.mode",
                "Network permission mode is open.",
                "Use allowlist mode when this agent only needs known hosts.",
            )
        )

    filesystem = permissions.get("filesystem")
    if isinstance(filesystem, dict):
        if filesystem.get("mode") == "read-write":
            issues.append(
                _issue(
                    "info",
                    "spec.permissions.filesystem.mode",
                    "Filesystem permission mode is read-write.",
                    "Confirm this write scope is intentional before sharing.",
                )
            )
        paths = filesystem.get("paths") or []
        if isinstance(paths, list):
            for index, rel_path in enumerate(paths):
                if isinstance(rel_path, str) and not _is_portable_relative_path(rel_path):
                    issues.append(
                        _issue(
                            "warning",
                            f"spec.permissions.filesystem.paths[{index}]",
                            f"Path '{rel_path}' is not portable across machines.",
                            "Use a relative path inside the agent project.",
                        )
                    )
    return issues


def _check_env_declarations(manifest: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    env = manifest.get("spec", {}).get("env") if isinstance(manifest.get("spec"), dict) else None
    if not isinstance(env, dict):
        return issues

    for field_name in ("required", "optional"):
        values = env.get(field_name) or []
        if not isinstance(values, list):
            continue
        seen: set[str] = set()
        for index, value in enumerate(values):
            if not isinstance(value, str):
                continue
            path = f"spec.env.{field_name}[{index}]"
            if "=" in value:
                issues.append(
                    _issue(
                        "warning",
                        path,
                        "Environment declaration appears to include an assignment.",
                        "List only the variable name; values belong outside the Agentfile.",
                    )
                )
            if value in seen:
                issues.append(
                    _issue(
                        "info",
                        path,
                        f"Environment variable '{value}' is declared more than once.",
                        "Remove duplicate env entries to reduce review noise.",
                    )
                )
            seen.add(value)
    return issues


def _env_sets(spec: dict[str, Any]) -> tuple[set[str], set[str]]:
    env = spec.get("env") or {}
    if not isinstance(env, dict):
        return set(), set()
    required = {item for item in env.get("required") or [] if isinstance(item, str)}
    optional = {item for item in env.get("optional") or [] if isinstance(item, str)}
    return required, optional


def _network_allowlist_hosts(spec: dict[str, Any]) -> set[str] | None:
    permissions = spec.get("permissions") or {}
    if not isinstance(permissions, dict):
        return None
    network = permissions.get("network") or {}
    if not isinstance(network, dict) or network.get("mode") != "allowlist":
        return None
    hosts = network.get("hosts") or []
    if not isinstance(hosts, list):
        return set()
    return {_normalize_host(str(host)) for host in hosts}


def _remote_host(mcp_value: str) -> str | None:
    parsed = urlparse(mcp_value)
    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.hostname is None:
        return None
    return _normalize_host(parsed.hostname)


def _normalize_host(host: str) -> str:
    return host.strip().strip("[]").lower()


def _host_shareability_issues(host: str, path: str) -> list[Issue]:
    host_type = _host_type(host)
    if host_type is None:
        return []
    return [
        _issue(
            "warning",
            path,
            f"Tool endpoint uses a {host_type} host ('{host}').",
            "Use a reachable shared endpoint or document the local tunnel/setup outside the Agentfile.",
        )
    ]


def _host_type(host: str) -> str | None:
    normalized = _normalize_host(host)
    if normalized in _LOCAL_HOSTS or normalized.endswith(_INTERNAL_SUFFIXES):
        return "local/private"
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return None
    if address.is_loopback or address.is_private or address.is_link_local:
        return "local/private"
    return None


def _is_portable_relative_path(path: str) -> bool:
    parts = Path(path).parts
    return not (path.startswith("/") or path.startswith("~") or ".." in parts)


def _compare_value(
    changes: list[Change],
    base_manifest: dict[str, Any],
    head_manifest: dict[str, Any],
    path: str,
    risk: str,
) -> None:
    before = _get_path(base_manifest, path)
    after = _get_path(head_manifest, path)
    if before == after:
        return
    changes.append(
        {
            "path": path,
            "kind": _change_kind(before, after),
            "risk": risk,
            "before": _safe_value(before),
            "after": _safe_value(after),
        }
    )


def _compare_list(
    changes: list[Change],
    base_manifest: dict[str, Any],
    head_manifest: dict[str, Any],
    path: str,
    risk: str,
) -> None:
    before = _as_string_set(_get_path(base_manifest, path))
    after = _as_string_set(_get_path(head_manifest, path))
    added = sorted(after - before)
    removed = sorted(before - after)
    if not added and not removed:
        return
    changes.append(
        {
            "path": path,
            "kind": "list_changed",
            "risk": risk,
            "added": added,
            "removed": removed,
        }
    )


def _compare_prompt(
    changes: list[Change],
    base_manifest: dict[str, Any],
    head_manifest: dict[str, Any],
) -> None:
    before = _prompt_summary(_get_path(base_manifest, "spec.system_prompt"))
    after = _prompt_summary(_get_path(head_manifest, "spec.system_prompt"))
    if before == after:
        return
    changes.append(
        {
            "path": "spec.system_prompt",
            "kind": _change_kind(before, after),
            "risk": "high",
            "before": before,
            "after": after,
        }
    )


def _compare_tools(
    changes: list[Change],
    base_manifest: dict[str, Any],
    head_manifest: dict[str, Any],
) -> None:
    before_tools = _tool_map(_get_path(base_manifest, "spec.tools"))
    after_tools = _tool_map(_get_path(head_manifest, "spec.tools"))
    before_keys = set(before_tools)
    after_keys = set(after_tools)

    for key in sorted(after_keys - before_keys):
        changes.append(
            {
                "path": "spec.tools",
                "kind": "added",
                "risk": "high",
                "tool": key,
                "after": _safe_value(after_tools[key]),
            }
        )
    for key in sorted(before_keys - after_keys):
        changes.append(
            {
                "path": "spec.tools",
                "kind": "removed",
                "risk": "high",
                "tool": key,
                "before": _safe_value(before_tools[key]),
            }
        )
    for key in sorted(before_keys & after_keys):
        if before_tools[key] == after_tools[key]:
            continue
        changes.append(
            {
                "path": f"spec.tools[{key}]",
                "kind": "modified",
                "risk": "high",
                "before": _safe_value(before_tools[key]),
                "after": _safe_value(after_tools[key]),
            }
        )


def _get_path(manifest: dict[str, Any], dotted_path: str) -> Any:
    current: Any = manifest
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _change_kind(before: Any, after: Any) -> str:
    if before is None:
        return "added"
    if after is None:
        return "removed"
    return "modified"


def _as_string_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item for item in value if isinstance(item, str)}


def _tool_map(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        return {}
    tools: dict[str, dict[str, Any]] = {}
    for index, tool in enumerate(value):
        if not isinstance(tool, dict):
            continue
        key = tool.get("mcp")
        tools[str(key) if isinstance(key, str) else f"<tool-{index}>"] = tool
    return tools


def _prompt_summary(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return {
            "type": "inline",
            "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
            "line_count": len(value.splitlines()) or 1,
        }
    if isinstance(value, dict):
        return {"type": "file", "file": _safe_value(value.get("file"))}
    return {"type": type(value).__name__}


def _safe_value(value: Any) -> Any:
    if isinstance(value, str):
        if _looks_secret(value):
            return "<redacted>"
        return value if len(value) <= 160 else value[:157] + "..."
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in value.items()}
    return value


def _looks_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_PATTERNS.values())


def _change_summary(changes: list[Change]) -> str:
    if not changes:
        return "No Agentfile changes detected."
    risk_counts = {
        "high": sum(1 for change in changes if change["risk"] == "high"),
        "medium": sum(1 for change in changes if change["risk"] == "medium"),
        "low": sum(1 for change in changes if change["risk"] == "low"),
    }
    parts = [f"{len(changes)} change(s)"]
    parts.extend(f"{count} {risk} risk" for risk, count in risk_counts.items() if count)
    return "Agentfile comparison found " + ", ".join(parts) + "."

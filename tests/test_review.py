"""Tests for team-shareability review helpers."""

from __future__ import annotations

from pathlib import Path

from agentfile.review import compare_files, review_file, review_manifest


def test_review_passes_for_shareable_manifest(tmp_path: Path) -> None:
    manifest = {
        "apiVersion": "agentfile/v1",
        "kind": "Agent",
        "metadata": {
            "name": "shareable-agent",
            "version": "0.1.0",
            "description": "A portable example agent.",
            "license": "MIT",
        },
        "spec": {
            "model": {"provider": "anthropic", "name": "claude-sonnet-4-5"},
            "system_prompt": "You help teammates work through project tasks.",
            "tools": [
                {
                    "mcp": "https://tools.example.com/mcp",
                    "auth": {"type": "bearer", "env": "TOOLS_TOKEN"},
                }
            ],
            "permissions": {
                "network": {"mode": "allowlist", "hosts": ["tools.example.com"]},
                "filesystem": {"mode": "read-only", "paths": ["./prompts"]},
            },
            "env": {"required": ["TOOLS_TOKEN"]},
        },
    }

    result = review_manifest(manifest, base_dir=tmp_path)

    assert result["shareable"] is True
    assert result["issue_counts"]["warning"] == 0
    assert result["summary"] == "No shareability issues found."


def test_review_flags_local_endpoint_and_incomplete_env_contract(tmp_path: Path) -> None:
    agentfile = tmp_path / "agent.yaml"
    agentfile.write_text(
        """\
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: local-agent
  version: 0.1.0
  description: Demonstrates a local MCP endpoint.
  license: MIT
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt: You help with local work.
  tools:
    - mcp: http://localhost:8080/mcp
      auth:
        type: bearer
        env: LOCAL_TOKEN
  permissions:
    network:
      mode: allowlist
      hosts: [shared.example.com]
    filesystem:
      mode: read-only
      paths: [/Users/alice/project]
  env:
    required: []
""",
        encoding="utf-8",
    )

    result = review_file(agentfile)
    messages = " ".join(issue["message"] for issue in result["issues"])

    assert result["shareable"] is False
    assert "local/private host" in messages
    assert "not listed as required" in messages
    assert "not portable" in messages


def test_compare_files_reports_review_friendly_changes(tmp_path: Path) -> None:
    base = tmp_path / "base.yaml"
    head = tmp_path / "head.yaml"
    base.write_text(
        """\
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: compare-agent
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt: You are concise.
  tools:
    - mcp: builtin/web_search
  env:
    required: [ANTHROPIC_API_KEY]
""",
        encoding="utf-8",
    )
    head.write_text(
        """\
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: compare-agent
  version: 0.2.0
spec:
  model:
    provider: openai
    name: gpt-4o
  system_prompt: "sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
  tools:
    - mcp: builtin/web_search
    - mcp: https://tools.example.com/mcp
      auth:
        type: bearer
        env: TOOLS_TOKEN
  env:
    required: [OPENAI_API_KEY, TOOLS_TOKEN]
""",
        encoding="utf-8",
    )

    result = compare_files(base, head)
    paths = {change["path"] for change in result["changes"]}
    prompt_change = next(
        change for change in result["changes"] if change["path"] == "spec.system_prompt"
    )

    assert result["changed"] is True
    assert "spec.model.provider" in paths
    assert "spec.tools" in paths
    assert "spec.env.required" in paths
    assert prompt_change["before"]["type"] == "inline"
    assert "sk-ant" not in str(prompt_change)

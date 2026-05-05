"""Tests for the validator."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentfile import (
    SchemaValidationError,
    validate,
    validate_file,
)
from agentfile.validator import get_schema

FIXTURES = Path(__file__).parent / "fixtures"


class TestSchemaLoading:
    def test_schema_loads(self) -> None:
        schema = get_schema()
        assert schema["title"] == "Agentfile v1"
        assert "apiVersion" in schema["properties"]


class TestValidMinimal:
    def test_valid_minimal_passes(self) -> None:
        result = validate_file(FIXTURES / "valid_minimal.yaml")
        assert result.valid, f"Expected valid, got errors: {result.errors}"
        assert result.errors == []

    def test_valid_minimal_no_warnings(self) -> None:
        result = validate_file(FIXTURES / "valid_minimal.yaml")
        # Minimal file has no builtins, no auth, no secrets
        assert result.warnings == []


class TestValidFull:
    def test_valid_full_passes(self) -> None:
        result = validate_file(FIXTURES / "valid_full.yaml")
        assert result.valid, f"Expected valid, got errors: {result.errors}"

    def test_valid_full_has_manifest(self) -> None:
        result = validate_file(FIXTURES / "valid_full.yaml")
        assert result.manifest is not None
        assert result.manifest["metadata"]["name"] == "test-full"


class TestInvalidStructure:
    def test_missing_spec_fails(self) -> None:
        result = validate_file(FIXTURES / "invalid_missing_spec.yaml")
        assert not result.valid
        assert any("spec" in e for e in result.errors)

    def test_bad_metadata_fails(self) -> None:
        result = validate_file(FIXTURES / "invalid_metadata.yaml")
        assert not result.valid
        # both name pattern and version pattern should fail
        joined = " ".join(result.errors)
        assert "name" in joined
        assert "version" in joined

    def test_custom_provider_without_endpoint_fails(self) -> None:
        result = validate_file(FIXTURES / "invalid_custom_no_endpoint.yaml")
        assert not result.valid
        assert any("endpoint" in e for e in result.errors)


class TestSecretDetection:
    def test_leaked_secret_warns(self) -> None:
        result = validate_file(FIXTURES / "warns_secret.yaml")
        assert result.valid  # not a hard error by default
        assert len(result.warnings) >= 1
        assert any("anthropic-api-key" in w for w in result.warnings)

    def test_strict_mode_promotes_secret_warning(self) -> None:
        result = validate_file(FIXTURES / "warns_secret.yaml", strict=True)
        assert not result.valid
        assert any("anthropic-api-key" in e for e in result.errors)


class TestFileReferences:
    def test_missing_prompt_file_fails(self, tmp_path: Path) -> None:
        agentfile = tmp_path / "agent.yaml"
        agentfile.write_text(
            """
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: test
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt:
    file: ./does-not-exist.md
""".strip()
        )
        result = validate_file(agentfile)
        assert not result.valid
        assert any("does-not-exist.md" in e for e in result.errors)

    def test_existing_prompt_file_passes(self, tmp_path: Path) -> None:
        prompt = tmp_path / "system.md"
        prompt.write_text("Hello.")
        agentfile = tmp_path / "agent.yaml"
        agentfile.write_text(
            """
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: test
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt:
    file: ./system.md
""".strip()
        )
        result = validate_file(agentfile)
        assert result.valid, result.errors

    def test_path_escape_rejected(self, tmp_path: Path) -> None:
        agentfile = tmp_path / "agent.yaml"
        agentfile.write_text(
            """
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: test
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt:
    file: ../escape.md
""".strip()
        )
        result = validate_file(agentfile)
        assert not result.valid
        assert any("escape" in e.lower() for e in result.errors)


class TestBuiltins:
    def test_known_builtin_no_warning(self, tmp_path: Path) -> None:
        manifest = {
            "apiVersion": "agentfile/v1",
            "kind": "Agent",
            "metadata": {"name": "test-agent", "version": "0.1.0"},
            "spec": {
                "model": {"provider": "anthropic", "name": "claude-sonnet-4-5"},
                "system_prompt": "x",
                "tools": [{"mcp": "builtin/web_search"}],
            },
        }
        result = validate(manifest)
        assert result.valid
        assert not any("builtin" in w for w in result.warnings)

    def test_unknown_builtin_warns(self) -> None:
        manifest = {
            "apiVersion": "agentfile/v1",
            "kind": "Agent",
            "metadata": {"name": "test-agent", "version": "0.1.0"},
            "spec": {
                "model": {"provider": "anthropic", "name": "claude-sonnet-4-5"},
                "system_prompt": "x",
                "tools": [{"mcp": "builtin/teleport"}],
            },
        }
        result = validate(manifest)
        assert result.valid
        assert any("builtin/teleport" in w for w in result.warnings)


class TestAuthEnv:
    def test_bearer_without_env_warns(self) -> None:
        manifest = {
            "apiVersion": "agentfile/v1",
            "kind": "Agent",
            "metadata": {"name": "test-agent", "version": "0.1.0"},
            "spec": {
                "model": {"provider": "anthropic", "name": "claude-sonnet-4-5"},
                "system_prompt": "x",
                "tools": [{"mcp": "https://example.com/mcp", "auth": {"type": "bearer"}}],
            },
        }
        result = validate(manifest)
        assert result.valid
        assert any("env" in w for w in result.warnings)


class TestRaiseIfInvalid:
    def test_raises_on_invalid(self) -> None:
        result = validate_file(FIXTURES / "invalid_missing_spec.yaml")
        with pytest.raises(SchemaValidationError):
            result.raise_if_invalid()

    def test_does_not_raise_on_valid(self) -> None:
        result = validate_file(FIXTURES / "valid_minimal.yaml")
        result.raise_if_invalid()  # should not raise


class TestExamples:
    """Every shipped example must validate."""

    @pytest.mark.parametrize(
        "example",
        [
            "research-agent",
            "data-pipeline",
            "coding-helper",
        ],
    )
    def test_example_validates(self, example: str) -> None:
        path = Path(__file__).parents[1] / "examples" / example / "agent.yaml"
        result = validate_file(path)
        assert result.valid, f"{example} failed: {result.errors}"

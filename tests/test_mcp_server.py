"""Tests for the Agentfile MCP server tools.

Tools decorated with @mcp.tool() are plain callables — we call them directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agentfile_mcp.server import (
    get_agentfile_schema,
    lint_inline,
    list_examples,
    read_example,
    scaffold,
    show_agentfile,
    validate_agentfile,
)

EXAMPLES_DIR = Path(__file__).parents[1] / "examples"
FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# validate_agentfile
# ---------------------------------------------------------------------------


class TestValidateTool:
    def test_valid_file_returns_valid(self) -> None:
        path = str(EXAMPLES_DIR / "research-agent" / "agent.yaml")
        result = validate_agentfile(path)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_file_returns_errors(self) -> None:
        path = str(FIXTURES / "invalid_missing_spec.yaml")
        result = validate_agentfile(path)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_strict_promotes_warnings(self, tmp_path: Path) -> None:
        # coding-helper has no warnings, use a file that has a secret
        agentfile = tmp_path / "agent.yaml"
        agentfile.write_text(
            "apiVersion: agentfile/v1\n"
            "kind: Agent\n"
            "metadata:\n"
            "  name: leak-agent\n"
            "  version: 0.1.0\n"
            "spec:\n"
            "  model:\n"
            "    provider: anthropic\n"
            "    name: claude-sonnet-4-5\n"
            "  system_prompt: 'sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'\n"
            "  env:\n"
            "    required: [ANTHROPIC_API_KEY]\n"
        )
        normal = validate_agentfile(str(agentfile), strict=False)
        assert normal["valid"] is True
        assert len(normal["warnings"]) >= 1

        strict = validate_agentfile(str(agentfile), strict=True)
        assert strict["valid"] is False

    def test_result_has_expected_keys(self) -> None:
        path = str(EXAMPLES_DIR / "coding-helper" / "agent.yaml")
        result = validate_agentfile(path)
        assert set(result.keys()) == {"valid", "errors", "warnings"}


# ---------------------------------------------------------------------------
# show_agentfile
# ---------------------------------------------------------------------------


class TestShowTool:
    def test_show_returns_manifest_and_summary(self) -> None:
        path = str(EXAMPLES_DIR / "coding-helper" / "agent.yaml")
        result = show_agentfile(path)
        assert "manifest" in result
        assert "summary" in result

    def test_show_manifest_has_correct_name(self) -> None:
        path = str(EXAMPLES_DIR / "coding-helper" / "agent.yaml")
        result = show_agentfile(path)
        assert result["manifest"]["metadata"]["name"] == "coding-helper"

    def test_show_summary_contains_model(self) -> None:
        path = str(EXAMPLES_DIR / "research-agent" / "agent.yaml")
        result = show_agentfile(path)
        assert "anthropic" in result["summary"]


# ---------------------------------------------------------------------------
# get_agentfile_schema
# ---------------------------------------------------------------------------


class TestSchemaTool:
    def test_schema_is_dict(self) -> None:
        schema = get_agentfile_schema()
        assert isinstance(schema, dict)

    def test_schema_has_title(self) -> None:
        schema = get_agentfile_schema()
        assert schema.get("title") == "Agentfile v1"


# ---------------------------------------------------------------------------
# list_examples
# ---------------------------------------------------------------------------


class TestListExamplesTool:
    def test_returns_three_examples(self) -> None:
        examples = list_examples()
        assert len(examples) == 3

    def test_each_has_required_keys(self) -> None:
        for ex in list_examples():
            assert "name" in ex
            assert "path" in ex
            assert "description" in ex


# ---------------------------------------------------------------------------
# read_example
# ---------------------------------------------------------------------------


class TestReadExampleTool:
    def test_read_known_example(self) -> None:
        text = read_example("research-agent")
        assert "research-agent" in text
        assert "apiVersion" in text

    def test_unknown_example_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown example"):
            read_example("nonexistent-agent")

    def test_returned_yaml_is_valid(self) -> None:
        for name in ("research-agent", "data-pipeline", "coding-helper"):
            text = read_example(name)
            parsed = yaml.safe_load(text)
            assert parsed["apiVersion"] == "agentfile/v1"


# ---------------------------------------------------------------------------
# scaffold
# ---------------------------------------------------------------------------


class TestScaffoldTool:
    def test_minimal_scaffold_is_valid_yaml(self) -> None:
        text = scaffold("my-agent")
        parsed = yaml.safe_load(text)
        assert parsed["metadata"]["name"] == "my-agent"

    def test_scaffold_passes_validation(self) -> None:
        text = scaffold("test-agent", description="A test agent")
        from agentfile_mcp.server import lint_inline

        result = lint_inline(text)
        assert result["valid"] is True, result["errors"]

    def test_scaffold_includes_anthropic_key_env(self) -> None:
        text = scaffold("key-agent")
        parsed = yaml.safe_load(text)
        assert "ANTHROPIC_API_KEY" in parsed["spec"]["env"]["required"]

    def test_scaffold_with_tools(self) -> None:
        text = scaffold("search-agent", tools=["builtin/web_search", "builtin/web_fetch"])
        parsed = yaml.safe_load(text)
        tools = [t["mcp"] for t in parsed["spec"]["tools"]]
        assert "builtin/web_search" in tools
        assert "builtin/web_fetch" in tools

    def test_scaffold_with_system_prompt_intent(self) -> None:
        text = scaffold("intent-agent", system_prompt_intent="You help with code reviews.")
        assert "code reviews" in text

    def test_scaffold_invalid_name_raises(self) -> None:
        with pytest.raises(ValueError, match="invalid"):
            scaffold("BadName")

    def test_scaffold_custom_model(self) -> None:
        text = scaffold("gpt-agent", model_provider="openai", model_name="gpt-4o")
        parsed = yaml.safe_load(text)
        assert parsed["spec"]["model"]["provider"] == "openai"
        assert parsed["spec"]["model"]["name"] == "gpt-4o"


# ---------------------------------------------------------------------------
# lint_inline
# ---------------------------------------------------------------------------


class TestLintInlineTool:
    def test_valid_yaml_passes(self) -> None:
        yaml_text = """\
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: inline-agent
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt: You are helpful.
  env:
    required: [ANTHROPIC_API_KEY]
"""
        result = lint_inline(yaml_text)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_yaml_structure_fails(self) -> None:
        result = lint_inline("apiVersion: agentfile/v1\nkind: Agent\n")
        assert result["valid"] is False

    def test_bad_yaml_parse_error(self) -> None:
        result = lint_inline("{ not: valid: yaml: }")
        assert result["valid"] is False
        assert any("YAML" in e or "parse" in e.lower() for e in result["errors"])

    def test_strict_mode(self) -> None:
        yaml_text = """\
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: secret-agent
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt: 'sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
  env:
    required: [ANTHROPIC_API_KEY]
"""
        normal = lint_inline(yaml_text, strict=False)
        assert normal["valid"] is True

        strict = lint_inline(yaml_text, strict=True)
        assert strict["valid"] is False

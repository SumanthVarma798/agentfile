"""Tests for the loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentfile import load_agentfile
from agentfile.errors import AgentfileError
from agentfile.loader import load_agentfile_from_string


class TestLoadFromFile:
    def test_loads_yaml(self, tmp_path: Path) -> None:
        f = tmp_path / "agent.yaml"
        f.write_text("apiVersion: agentfile/v1\nkind: Agent\n")
        data = load_agentfile(f)
        assert data["apiVersion"] == "agentfile/v1"

    def test_loads_json(self, tmp_path: Path) -> None:
        f = tmp_path / "agent.json"
        f.write_text('{"apiVersion": "agentfile/v1", "kind": "Agent"}')
        data = load_agentfile(f)
        assert data["kind"] == "Agent"

    def test_missing_file_raises(self) -> None:
        with pytest.raises(AgentfileError, match="not found"):
            load_agentfile("/nonexistent/agent.yaml")

    def test_invalid_yaml_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.yaml"
        f.write_text("key: value\n  bad: indentation\n broken")
        with pytest.raises(AgentfileError, match="Failed to parse"):
            load_agentfile(f)

    def test_top_level_must_be_mapping(self, tmp_path: Path) -> None:
        f = tmp_path / "list.yaml"
        f.write_text("- one\n- two\n")
        with pytest.raises(AgentfileError, match="must be a mapping"):
            load_agentfile(f)


class TestLoadFromString:
    def test_yaml_string(self) -> None:
        data = load_agentfile_from_string("foo: bar\n")
        assert data["foo"] == "bar"

    def test_json_string(self) -> None:
        data = load_agentfile_from_string('{"foo": "bar"}', format="json")
        assert data["foo"] == "bar"

    def test_unknown_format_raises(self) -> None:
        with pytest.raises(AgentfileError, match="Unknown format"):
            load_agentfile_from_string("foo: bar", format="toml")

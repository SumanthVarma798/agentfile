"""Tests for the CLI."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from agentfile.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
EXAMPLES = Path(__file__).parents[1] / "examples"


class TestValidateCommand:
    def test_valid_file_exit_zero(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(FIXTURES / "valid_minimal.yaml")])
        assert result.exit_code == 0

    def test_invalid_file_exit_one(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(FIXTURES / "invalid_missing_spec.yaml")])
        assert result.exit_code == 1

    def test_validates_examples_directory(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(EXAMPLES)])
        assert result.exit_code == 0, result.output

    def test_strict_mode(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "--strict", str(FIXTURES / "warns_secret.yaml")])
        assert result.exit_code == 1


class TestShowCommand:
    def test_show_summary(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["show", str(FIXTURES / "valid_full.yaml")])
        assert result.exit_code == 0
        assert "test-full" in result.output

    def test_show_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main, ["show", "--format", "json", str(FIXTURES / "valid_minimal.yaml")]
        )
        assert result.exit_code == 0
        assert "agentfile/v1" in result.output


class TestSchemaCommand:
    def test_schema_outputs_json(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["schema"])
        assert result.exit_code == 0
        assert "Agentfile v1" in result.output


class TestVersion:
    def test_version_flag(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "agent" in result.output.lower()

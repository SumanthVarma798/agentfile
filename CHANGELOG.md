# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versions follow [SemVer](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-05-05

### Changed (philosophy)
- **Agentic-first pivot.** Agentfile is now primarily accessed through an MCP server. The CLI remains fully supported for CI/scripts but is no longer the primary UX.
- README rewritten around agent-paste-prompt UX; CLI section demoted to "CI / scripting path".

### Added
- `agentfile-mcp` package (`src/agentfile_mcp/`): FastMCP server exposing 7 tools (`validate_agentfile`, `show_agentfile`, `get_agentfile_schema`, `list_examples`, `read_example`, `scaffold`, `lint_inline`) and 3 resources (`agentfile://spec`, `agentfile://schema`, `agentfile://examples/{name}`).
- `[project.optional-dependencies] mcp = ["mcp>=1.0"]` — install with `pip install "agentfile[mcp]"`.
- `agentfile-mcp` entrypoint (stdio transport, connect with `uvx agentfile-mcp`).
- `skills/agentfile/SKILL.md` — Claude skill for authoring and operating on Agentfiles inside any MCP-capable agent.
- `skills/agentfile/references/` — authoring guide, debugging reference, schema quick-ref.
- 25 new tests in `tests/test_mcp_server.py` (62 total across all suites).
- SPEC §14 "Consumers" — documents library/CLI and MCP server consumption modes.
- Roadmap updated through v1.0.

### Unchanged
- `agentfile/v1` spec — no breaking changes.
- Existing CLI commands (`agent validate`, `agent show`, `agent schema`).
- Python API (`validate()`, `validate_file()`, `load_agentfile()`).

## [0.1.0] - 2026-05-05

### Added
- Initial release of the `agentfile/v1` spec.
- JSON Schema for machine validation (`schema/agentfile.v1.schema.json`).
- Python validator with `validate()`, `validate_file()`, and `ValidationResult`.
- CLI: `agent validate`, `agent show`, `agent schema`, `--version`.
- Heuristic secret detection (Anthropic, OpenAI, GitHub, AWS, Slack, Google API keys, private key blocks).
- Builtin tool name awareness (warns on unknown `builtin/*` references).
- File reference resolution for `system_prompt.file` and `memory.config.file`.
- Three example Agentfiles: research-agent, data-pipeline, coding-helper.
- CI pipeline: lint, type-check, tests on Python 3.10, 3.11, 3.12.

[Unreleased]: https://github.com/SumanthVarma798/agentfile/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/SumanthVarma798/agentfile/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/SumanthVarma798/agentfile/releases/tag/v0.1.0

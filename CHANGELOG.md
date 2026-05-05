# Changelog

All notable changes to this project are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versions follow [SemVer](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/SumanthVarma798/agentfile/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/SumanthVarma798/agentfile/releases/tag/v0.1.0

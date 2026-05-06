## v0.2.0: agentic-first pivot — MCP server, Claude skill, agentic README

### Motivation

v0.1 proved the format works. v0.2 makes it *ergonomic* inside the places developers already live: Claude Code, Claude Desktop, Cursor, and any MCP-capable agent IDE.

The insight: Agentfile is most useful when it meets users where they write agents — inside an agent. An MCP server means zero integration friction: `claude mcp add agentfile -- uvx agentfile-mcp`, and from that point on your agent can author, validate, scaffold, and inspect Agentfiles natively. No terminal required for the happy path.

The CLI isn't going away — it's the right tool for CI pipelines and scripts. It's just no longer the primary UX.

---

### What changed

**New: `agentfile-mcp` package (`src/agentfile_mcp/`)**
- FastMCP server built on the official Python MCP SDK (`mcp>=1.0`)
- 7 tools: `validate_agentfile`, `show_agentfile`, `get_agentfile_schema`, `list_examples`, `read_example`, `scaffold`, `lint_inline`
- 3 resources: `agentfile://spec`, `agentfile://schema`, `agentfile://examples/{name}`
- Entrypoint: `agentfile-mcp` (stdio transport — `uvx agentfile-mcp`)
- All validation is delegated to `validate()` / `validate_file()` from the core package — zero duplication

**New: Claude skill (`skills/agentfile/SKILL.md`)**
- Teaches Claude when to invoke MCP tools vs. answer from memory
- Authoring, validation, and inspection workflows with worked examples
- Reference material in `skills/agentfile/references/` (authoring, debugging, schema-quick-ref)

**Rewritten: `README.md`**
- Lead with a single agent-paste prompt ("try it in 10 seconds")
- Primary path is MCP installation; CLI section demoted to "CI / scripting"
- 5 example prompts users can copy
- Comparison table now includes "MCP-native access" row
- Roadmap updated through v1.0

**Updated: `SPEC.md`**
- §14 "Consumers" — documents library/CLI and MCP server modes; asserts MCP servers are first-class runtimes

**Updated: `CHANGELOG.md`**
- v0.2.0 entry; v0.1.0 untouched

**Updated: `pyproject.toml`**
- `version = "0.2.0"`
- `[project.optional-dependencies] mcp = ["mcp>=1.0"]`
- `agentfile-mcp` script entrypoint
- Wheel target now includes `src/agentfile_mcp`

**Updated: `.github/workflows/ci.yml`**
- `pip install -e ".[dev,mcp]"` so MCP tests run in CI

**New: `tests/test_mcp_server.py`**
- 25 tests across all 7 tools (happy path + error path for validate, show, scaffold, lint_inline)

---

### What didn't change

- `agentfile/v1` spec — no breaking changes to the format
- Existing CLI commands (`agent validate`, `agent show`, `agent schema`) — unchanged
- Public Python API (`validate()`, `validate_file()`, `load_agentfile()`) — unchanged
- All 37 original tests — still pass

**Breaking changes: none.**

---

### Test results

```
62 passed in 0.20s
ruff: all checks passed
agent validate examples: all 3 valid
```

---

### Screencast TODO

- [ ] Record: `claude mcp add agentfile -- uvx agentfile-mcp` → paste scaffold prompt → validate
- [ ] Upload to repo or link from README

---

### Reviewer notes

- The `scaffold()` tool validates its output before returning — if the generated YAML ever fails validation it raises `ValueError`. This makes the tool self-testing.
- `lint_inline()` skips file-reference checks (no base dir on disk). This is intentional and documented in the docstring.
- The `agentfile://examples/{name}` resource uses a URI template — confirmed working with FastMCP 1.x.
- SKILL.md is 3.8KB (limit 4KB). References live in `references/` to keep the main skill file scannable.

<div align="center">

# Agentfile

**A portable, declarative format for sharing AI agent setups.**

*Like Dockerfile, but for agents.*

[![CI](https://github.com/SumanthVarma798/agentfile/actions/workflows/ci.yml/badge.svg)](https://github.com/SumanthVarma798/agentfile/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/agentfile.svg)](https://pypi.org/project/agentfile/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Spec: v1](https://img.shields.io/badge/spec-v1%20draft-orange.svg)](./SPEC.md)

[**Spec**](./SPEC.md) · [**Motivation**](./MOTIVATION.md) · [**Examples**](./examples) · [**Contributing**](./CONTRIBUTING.md)

</div>

---

## Try it in 10 seconds

Connect the MCP server (see [Use it with your agent](#use-it-with-your-agent)), then paste this into Claude Code, Claude Desktop, or Cursor:

> **"Scaffold an Agentfile for a research agent that uses web search and writes Markdown briefs. Save it to ./agent.yaml and validate it."**

Your agent will call `scaffold()`, write the file, and call `validate_agentfile()` to confirm it passes — all without touching a terminal.

---

## What is this?

Sharing an agent today: *"clone this, copy these env vars, edit the hardcoded prompt on line 47, install our internal MCP server, hope it works."*

Sharing an agent with Agentfile:

```yaml
# agent.yaml
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: research-agent
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
    params: { temperature: 0.4 }
  system_prompt:
    file: ./prompts/system.md
  tools:
    - mcp: builtin/web_search
    - mcp: https://internal-kb.corp/mcp
      auth: { type: bearer, env: KB_TOKEN }
  permissions:
    network: { mode: allowlist, hosts: [api.anthropic.com, internal-kb.corp] }
  env:
    required: [ANTHROPIC_API_KEY, KB_TOKEN]
```

One file. Diffable. Reviewable. Secret-free. Runs anywhere a compliant runtime exists.

---

## Use it with your agent

Agentfile ships an MCP server that exposes authoring and validation tools natively. This is the primary way to use it.

### Claude Code / Claude Desktop

```bash
# Install the MCP server and register it (one command):
claude mcp add agentfile -- uvx agentfile-mcp
# or with pipx:
claude mcp add agentfile -- pipx run agentfile-mcp
```

After connecting, Claude sees these tools: `scaffold`, `validate_agentfile`, `lint_inline`, `show_agentfile`, `read_example`, `list_examples`, `get_agentfile_schema`.

### Cursor / Continue / Cline

Add to your MCP client config (e.g. `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "agentfile": {
      "command": "uvx",
      "args": ["agentfile-mcp"]
    }
  }
}
```

### Bring your own MCP client

`agentfile-mcp` speaks stdio MCP (Model Context Protocol). Any client that supports MCP stdio transport can connect to it. The server exposes 7 tools and 3 resources over the `agentfile://` URI scheme. See [SPEC.md §14](./SPEC.md#14-consumers) for the full consumer protocol.

---

## What to say to your agent

Once the MCP server is connected, you can talk to your agent naturally:

- **"Author an Agentfile for an agent that monitors our Postgres database and answers questions about query performance."**
- **"Validate ./agent.yaml and explain any failures in plain English."**
- **"What does the `data-pipeline` example demonstrate? Walk me through it."**
- **"Convert this LangChain config into an Agentfile — here's the code: ..."**
- **"Why does this Agentfile fail strict mode? Here's the YAML: ..."**
- **"List the bundled examples and show me the simplest one."**

---

## CI / scripting (CLI path)

For pipelines without an agent in the loop, use the CLI directly:

```bash
pip install agentfile

# Validate one file or an entire examples directory
agent validate ./agent.yaml
agent validate examples          # recurses one level

# Strict mode (warnings become errors — use in CI to catch secret leaks)
agent validate --strict ./agent.yaml

# Inspect a manifest
agent show examples/research-agent/agent.yaml

# Dump the JSON Schema
agent schema --pretty
```

**GitHub Actions example:**

```yaml
- name: Validate Agentfiles
  run: |
    pip install agentfile
    agent validate --strict ./agent.yaml
```

---

## How it compares

| | **Agentfile** | OpenAI Custom GPTs | LangGraph configs | CrewAI YAML |
|---|---|---|---|---|
| Portable across runtimes | ✅ | ❌ (locked to OpenAI) | ❌ (LangGraph only) | ❌ (CrewAI only) |
| Lives in version control | ✅ | ❌ | ✅ | ✅ |
| Standardized tool layer | ✅ MCP | ✅ Actions | ❌ Framework-specific | ❌ Framework-specific |
| Model-agnostic | ✅ | ❌ | ✅ | ✅ |
| Secret-free by design | ✅ | n/a | ❌ | ❌ |
| MCP-native access | ✅ | ❌ | ❌ | ❌ |
| Has a registry | 🔜 v0.5 | ✅ | ❌ | ❌ |

---

## Roadmap

| Version | What | Status |
|---|---|---|
| **v0.1** | Spec + validator + CLI | ✅ shipped |
| **v0.2** | MCP server + Claude skill + agentic README | ✅ this release |
| **v0.3** | Reference runner as MCP `run_agentfile` tool | planned |
| **v0.4** | TypeScript port (validator + MCP server) | planned |
| **v0.5** | `pack` / `publish` / `install` + registry | planned |
| **v1.0** | Signing, stability, ecosystem | planned |

---

## Install from source

```bash
git clone https://github.com/SumanthVarma798/agentfile.git
cd agentfile
pip install -e ".[dev,mcp]"
pytest
agent validate examples
```

---

## FAQ

**Q: Why MCP-first?**
MCP is now the standard protocol for agent tool access — every major agent IDE and runtime supports it. Shipping an MCP server means zero integration work: connect once, use everywhere. The CLI is still there for scripts and CI; it just isn't the primary UX anymore.

**Q: Do I still need the CLI?**
For CI pipelines, Git hooks, and scripts — yes. For authoring and day-to-day use inside an agent environment — no. The MCP server does everything the CLI does and more.

**Q: Is the skill Claude-only?**
The `skills/agentfile/SKILL.md` file follows a convention Claude Code understands. The underlying MCP server is protocol-standard and works with any MCP-capable client (Cursor, Continue, Cline, etc.). A skill file for other clients can be added in v0.3.

**Q: Is this a framework?**
No. It's *config* — a manifest format. Use LangGraph, CrewAI, or the raw Anthropic SDK as your runtime.

**Q: Why not just use Docker?**
Docker captures the *environment*. Agentfile captures the *agent definition*. They compose.

**Q: How is this different from MCP?**
MCP is the protocol for *tools*. Agentfile is the manifest for an *agent* that uses MCP tools.

**Q: Is the spec stable?**
`agentfile/v1` is a *draft*. Backwards-compatible additions are allowed; breaking changes bump to v2.

---

## Contributing

Code changes via PRs; spec changes via [RFCs](./CONTRIBUTING.md#rfc-process).

The most valuable thing right now: **try it on a real agent** and open a [Discussion](https://github.com/SumanthVarma798/agentfile/discussions) when the spec falls short.

---

## License

[MIT](./LICENSE) — use it, fork it, ship it.

---

<div align="center">

Built by [@SumanthVarma798](https://github.com/SumanthVarma798) and the community.
The agent ecosystem deserves better than copy-paste.

</div>

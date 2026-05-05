# Agentfile

> A portable, declarative format for sharing AI agent setups.

[![CI](https://github.com/YOUR-USERNAME/agentfile/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USERNAME/agentfile/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Agentfile is to AI agents what Dockerfile is to applications.**

A single declarative manifest that captures everything needed to instantiate, share, and reproduce an agent — model, prompt, tools, memory, and permissions — minus the secrets and the model weights.

```yaml
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: research-agent
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt:
    file: ./prompts/system.md
  tools:
    - mcp: builtin/web_search
    - mcp: https://github-mcp.example.com/mcp
  permissions:
    network:
      mode: allowlist
      hosts: [api.anthropic.com, github-mcp.example.com]
```

## Why this exists

Today, sharing an agent setup with a teammate looks like: "clone this repo, copy these env vars, edit this hardcoded prompt, install these MCP servers, hope it works." There's no JAR, no Dockerfile, no `package.json` for agents.

This project is the first step toward fixing that. Read the [full motivation](./MOTIVATION.md) or the [spec](./SPEC.md).

## What's in v0

- ✅ The **spec** (`SPEC.md`) — a precise, versioned format definition
- ✅ A **JSON Schema** for machine validation
- ✅ A **Python validator + CLI** (`agent validate`, `agent show`)
- ✅ Three **example Agentfiles** demonstrating real patterns
- 🔜 A reference runtime (`agent run`) — coming in v0.2
- 🔜 A package registry — coming after the spec stabilizes

## Install

```bash
pip install agentfile
```

Or from source:

```bash
git clone https://github.com/YOUR-USERNAME/agentfile.git
cd agentfile
pip install -e .
```

## Quickstart

Validate an Agentfile:

```bash
agent validate examples/research-agent/agent.yaml
```

Pretty-print the parsed manifest:

```bash
agent show examples/research-agent/agent.yaml
```

Print the JSON Schema:

```bash
agent schema
```

## Writing your first Agentfile

Create `agent.yaml`:

```yaml
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: my-first-agent
  version: 0.1.0
  description: A minimal example
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
    params:
      temperature: 0.3
  system_prompt: |
    You are a helpful coding assistant.
    Respond concisely.
  tools:
    - mcp: builtin/filesystem
```

Validate it:

```bash
agent validate agent.yaml
# ✓ agent.yaml is valid
```

## Project goals

1. **Portability** — same Agentfile, any compliant runtime
2. **Reviewability** — prompts and tool configs are first-class artifacts in version control, diffable in PRs
3. **Composability** — tools and memory are declared, not hardcoded
4. **Secret-free** — credentials are referenced via env, never embedded

## Non-goals (for v1)

- Replacing agent frameworks like LangGraph or CrewAI — Agentfile is *config*, not a framework
- Bundling model weights — the spec references models, doesn't ship them
- Solving observability, evals, or deployment — those are separate concerns

## Roadmap

- **v0.1** ✅ Spec + validator + CLI
- **v0.2** Reference Python runner (`agent run`)
- **v0.3** TypeScript validator + runner
- **v0.4** `agent pack` / `agent publish` — packaging primitives
- **v1.0** Stable spec, registry protocol, security signing

## Contributing

This is a community project. Spec changes happen via [RFCs](./CONTRIBUTING.md#rfc-process); code changes via PRs. See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

[MIT](./LICENSE) — use it freely, fork it, ship it.

---

*Built with the Claude community. The agent ecosystem deserves better than copy-paste.*

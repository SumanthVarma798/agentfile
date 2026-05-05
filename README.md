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

## The pitch

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

## Quickstart

```bash
pip install agentfile
agent validate ./agent.yaml
```

That's it. You now have a validated agent manifest you can check into git, share with your team, or publish.

## Demo

```bash
$ agent show examples/research-agent/agent.yaml
```

```
╭───────────────── examples/research-agent/agent.yaml ─────────────────╮
│ research-agent v0.1.0                                                │
│ A web-research agent that synthesizes findings into briefs.          │
╰──────────────────────────────────────────────────────────────────────╯
apiVersion      agentfile/v1
kind            Agent
model           anthropic:claude-sonnet-4-5
params          temperature=0.4, max_tokens=4096
system_prompt   [file] ./prompts/system.md
tools (2)       builtin/web_search, builtin/web_fetch
permissions     network:allowlist, filesystem:read-only
env (required)  ANTHROPIC_API_KEY
env (optional)  OTEL_EXPORTER_OTLP_ENDPOINT
```

```bash
$ agent validate examples
✓ examples/research-agent/agent.yaml
✓ examples/data-pipeline/agent.yaml
✓ examples/coding-helper/agent.yaml

All 3 Agentfile(s) valid.
```

Validation catches secret leaks too:

```bash
$ agent validate leaky-agent.yaml
✓ (with warnings) leaky-agent.yaml
  warning: spec.system_prompt: looks like a anthropic-api-key (matched pattern).
           Credentials must be passed via env vars, not embedded.
```

## Why this exists

Three things changed in the last year:

1. **MCP stabilized.** Tools can now be addressed by URL across runtimes.
2. **System prompts got long enough to be code.** Treating them as version-controlled artifacts is now obviously correct.
3. **Enterprise teams hit the wall.** Once you have 30 agents in production, "how do we share these reliably" stops being a hobby question.

The agent ecosystem has standardized parts — model APIs, tool protocols, frameworks. What's missing is a layer *above* the framework: a portable description of what an agent **is**, independent of how you run it.

That layer is what Dockerfile is for apps. That's what Agentfile is trying to be for agents.

→ Read the [longer motivation](./MOTIVATION.md) for the full argument.

## How it compares

| | **Agentfile** | OpenAI Custom GPTs | LangGraph configs | CrewAI YAML |
|---|---|---|---|---|
| Portable across runtimes | ✅ | ❌ (locked to OpenAI) | ❌ (LangGraph only) | ❌ (CrewAI only) |
| Lives in version control | ✅ | ❌ | ✅ | ✅ |
| Standardized tool layer | ✅ MCP | ✅ Actions | ❌ Framework-specific | ❌ Framework-specific |
| Model-agnostic | ✅ | ❌ | ✅ | ✅ |
| Secret-free by design | ✅ | n/a | ❌ | ❌ |
| Has a registry | 🔜 v0.4 | ✅ | ❌ | ❌ |

## What's in v0.1

- ✅ The **spec** ([`SPEC.md`](./SPEC.md)) — precise, versioned format definition
- ✅ A **JSON Schema** for machine validation
- ✅ **Python validator + CLI** — `agent validate`, `agent show`, `agent schema`
- ✅ **Heuristic secret detection** — catches leaked API keys before they hit Git
- ✅ **File reference resolution** — system prompts and memory configs as separate files
- ✅ Three working **examples** demonstrating real patterns
- ✅ 37 tests, ruff-clean, CI on Python 3.10/3.11/3.12

## Roadmap

| Version | What | Why |
|---|---|---|
| **v0.1** ✅ | Spec + validator + CLI | Lock the format. Make it usable. |
| **v0.2** | Reference Python runner (`agent run`) | Battle-test the spec end-to-end. |
| **v0.3** | TypeScript validator + runner | Ecosystem reach. |
| **v0.4** | `agent pack` / `agent publish` | Packaging primitives for sharing. |
| **v1.0** | Stable spec, registry protocol, signing | Production-grade. |

## Install from source

```bash
git clone https://github.com/SumanthVarma798/agentfile.git
cd agentfile
pip install -e ".[dev]"
pytest
```

## Writing your first Agentfile

```yaml
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: my-first-agent
  version: 0.1.0
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt: |
    You are a precise coding assistant.
    Be concise, never invent APIs.
  tools:
    - mcp: builtin/filesystem
  env:
    required: [ANTHROPIC_API_KEY]
```

Save it as `agent.yaml`, then:

```bash
agent validate agent.yaml
# ✓ agent.yaml
```

You're shipping a versioned, reviewable agent.

## FAQ

**Q: Is this a framework?**
No. It's *config* — a manifest format. Use LangGraph, CrewAI, or the raw Anthropic SDK as your runtime.

**Q: Why not just use Docker?**
Docker captures the *environment*. Agentfile captures the *agent definition*. They compose: a Docker image can ship a runtime that consumes Agentfiles.

**Q: How is this different from MCP?**
MCP is the protocol for *tools*. Agentfile is the manifest for an *agent* that uses MCP tools. Different layers.

**Q: Can the same Agentfile run on different model providers?**
The format supports it (`provider: anthropic | openai | google | ...`), but behavior won't be identical across providers. The format is portable; semantics aren't fully portable yet — that's an open problem the whole field shares.

**Q: Why "advisory" permissions in v1?**
Because runtime enforcement is a separate hard problem. v1 establishes the *vocabulary*; v2 will define enforcement semantics. We didn't want to ship a half-enforced security model that gives false confidence.

**Q: Is the spec stable?**
v1 is a *draft*. Within v1, only backwards-compatible additions happen. Breaking changes go to v2.

## Goals & non-goals

**Goals**
- Portability — same Agentfile, any compliant runtime
- Reviewability — prompts and configs diffable in PRs
- Composability — tools and memory declared, not hardcoded
- Secret-free — credentials referenced via env, never embedded

**Non-goals**
- Replacing agent frameworks
- Bundling model weights
- Solving observability, evals, or deployment

## Contributing

This is a community project. Code changes via PRs; spec changes via [RFCs](./CONTRIBUTING.md#rfc-process).

The most valuable thing you can do right now: **try it on a real agent you're building** and tell me where the spec falls short. Open a [Discussion](https://github.com/SumanthVarma798/agentfile/discussions) — that feedback shapes v0.2.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for setup.

## License

[MIT](./LICENSE) — use it, fork it, ship it.

---

<div align="center">

Built by [@SumanthVarma798](https://github.com/SumanthVarma798) and the community.
The agent ecosystem deserves better than copy-paste.

</div>

# Why Agentfile?

> Or: *"a JAR file for agents"*

## The problem

Sharing an AI agent setup with a teammate today looks like this:

> "OK, so clone this repo. Then copy `.env.example` to `.env`. Then export these other env vars I forgot to put in there. Then `pip install -r requirements.txt`. Then edit line 47 of `agent.py` where the system prompt is hardcoded — change the temperature too. Oh and you need our internal MCP server running on port 8080. Did you install that? Here's a Slack DM with the install instructions from last quarter."

There is no shippable artifact. No standard manifest. No `package.json`, no `Dockerfile`, no JAR. The agent's "code" is split across a dozen places, half of which are in someone's head.

## What we have today

The agent ecosystem has standardized parts:

- **Tool interfaces** — MCP is finally stabilizing here.
- **LLM APIs** — Anthropic, OpenAI, Google APIs are well-defined.
- **Frameworks** — LangGraph, CrewAI, AutoGen each have their own agent shape.

What's missing is a **layer above the framework** — a portable, declarative description of *what an agent is*, independent of how you run it.

## The Dockerfile parallel

Before Docker:
- "Install Postgres 9.x. Then this Python version. Then these system libs. Then run this script."

After Docker:
- `docker run myapp:latest`

The Dockerfile didn't replace OS packaging, language runtimes, or compilers. It composed them into a portable manifest. **Agentfile is trying to do the same thing for agents.**

## What an Agentfile captures

| Layer | Mechanism |
|---|---|
| Model | Provider + name + params (no weights bundled) |
| Behavior | System prompt (inline or file reference) |
| Capability | List of MCP servers and builtins |
| Memory | Backend type + config |
| Boundaries | Permission declarations (network, filesystem) |
| Dependencies | Required and optional env vars |

What it deliberately does *not* capture:
- Model weights (referenced, not embedded)
- Secrets (referenced via env, never inlined)
- Runtime telemetry, deployment, observability (separate concerns)
- The framework you use (Agentfile is config, not code)

## Why now

Three things changed in the last 12 months that make this viable:

1. **MCP went from idea to widely-adopted protocol.** Tools can now be addressed by URL across implementations.
2. **System prompts got long enough to be code.** Treating them as source files in version control is now obviously correct.
3. **Enterprise adoption forced the question.** Once your team has 30 agents in production, "how do we share these" becomes existential.

## The hard parts (acknowledged)

- **Reproducibility is partial.** The same Agentfile + the same model name does *not* guarantee the same behavior — model versions drift. We'll address this in v0.2 with stronger version pinning.
- **Permissions are advisory in v1.** A runtime is supposed to honor `permissions.network.mode: allowlist`, but nothing forces it to. v2 will define enforcement.
- **No registry yet.** You can share Agentfiles via Git today, but there's no `pip install agent/research-agent`. That comes after the spec stabilizes.

## What this is not

- It is not a framework. Use LangGraph or CrewAI under the hood if you want.
- It is not a deployment system. Use Kubernetes, Modal, or a container runtime.
- It is not an evaluation harness. Use Inspect, Promptfoo, or your own.
- It is not a competitor to MCP — it *uses* MCP as the tool layer.

It is a small, opinionated, declarative format. That's the entire point.

## How to engage

Read [SPEC.md](./SPEC.md). Try the examples. If something is wrong or missing, open a Discussion. Spec changes go through [RFCs](./CONTRIBUTING.md#rfc-process).

This is a community project. The format only matters if people actually use it.

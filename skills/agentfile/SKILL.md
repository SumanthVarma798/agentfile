---
name: agentfile
description: Author, validate, inspect, and operate on Agentfile manifests — the portable declarative format for AI agents. Triggers on mentions of "Agentfile", "agent.yaml", "MCP agent config", "share my agent setup", or any request to define, scaffold, or debug an agent definition.
---

## What is an Agentfile?

A declarative manifest (`agent.yaml`) fully describing an AI agent: model, system prompt, tools, memory, env, and permissions. Portable (any compliant runtime), secret-free (env-var references only), and diffable in git.

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
  system_prompt: You research topics and write Markdown briefs.
  tools:
    - mcp: builtin/web_search
  env:
    required: [ANTHROPIC_API_KEY]
```

Fetch `agentfile://spec` for the authoritative reference when uncertain.

## When to use MCP tools vs. memory

| Situation | Tool |
|---|---|
| Scaffold / create | `scaffold()` |
| Validate inline YAML | `lint_inline()` |
| Validate file on disk | `validate_agentfile()` |
| Inspect a file | `show_agentfile()` |
| Read bundled example | `read_example()` |
| Fetch schema | `get_agentfile_schema()` |
| Conceptual question | Answer from knowledge |

## Authoring workflow

Ask the user: name (kebab-case), purpose, model (default: anthropic/claude-sonnet-4-5), tools, and env secrets. Then:

1. Call `scaffold(name, description, model_provider, model_name, tools, system_prompt_intent)`
2. Call `lint_inline(yaml_text=<result>)` to confirm `valid=True`
3. Present the YAML; offer to save as `./agent.yaml`

**Example — scaffold a research agent**
```
User: Create an Agentfile for a web research agent.
→ scaffold(name="research-agent", tools=["builtin/web_search","builtin/web_fetch"],
           system_prompt_intent="You research topics and write Markdown briefs.")
→ lint_inline(yaml_text=<result>)  # confirm valid
→ Present YAML to user
```

## Validation workflow

1. `lint_inline(yaml_text=...)` for pasted content, `validate_agentfile(path=...)` for files
2. Explain each error in plain language — don't echo raw messages
3. Surface warnings as advice (possible secrets, unknown builtins), not blockers
4. Offer to fix and re-validate

**Example — broken Agentfile**
```
User: (pastes YAML missing spec.model)
→ lint_inline(yaml_text=<content>)
→ errors: ["spec: 'model' is a required property"]
→ Explain: "The spec.model block is missing. Add provider and name."
→ Show corrected snippet, offer full fixed file
```

## Inspection workflow

1. `read_example(name=...)` for bundled examples, `show_agentfile(path=...)` for files
2. Summarise purpose, model, tools, and permissions in 3–5 sentences

**Example — what does the data-pipeline example do?**
```
User: What does the data-pipeline example do?
→ show_agentfile(path="examples/data-pipeline/agent.yaml")
→ Summarise: "The fhir-pipeline-agent monitors a FHIR bulk-data pipeline using
   two custom MCP servers (FHIR + OCI Streaming) and Chroma memory for run history."
```

## Common pitfalls

- **Leaked secrets** — literal `sk-`, `ghp_`, `AIza`, PEM blocks warn/fail strict. Use `env.required`.
- **Missing prompt files** — `system_prompt: {file: ./prompts/system.md}` fails if file absent.
- **Bad SemVer** — `version: 1.0` invalid; use `1.0.0`.
- **Custom provider** — `provider: custom` requires an `endpoint` field.
- **Path escape** — `../` references are rejected by the validator.

## Reference material

- `skills/agentfile/references/authoring.md` — field-by-field authoring guide
- `skills/agentfile/references/debugging.md` — error message reference
- `skills/agentfile/references/schema-quick-ref.md` — schema at a glance

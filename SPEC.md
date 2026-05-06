# Agentfile Specification — v1

**Status:** Draft
**Version:** `agentfile/v1`
**Last updated:** 2026-05-05

---

## 1. Overview

An **Agentfile** is a declarative manifest that specifies the configuration of an AI agent: its model, prompt, tools, memory, and runtime permissions. It is designed to be portable across runtimes, reviewable in version control, and free of embedded secrets.

Agentfiles are typically named `agent.yaml` or `Agentfile.yaml`. Both YAML and JSON encodings are valid.

## 2. Design principles

1. **Declarative.** An Agentfile describes *what* the agent is, not *how* to run it.
2. **Portable.** Any compliant runtime can instantiate any valid Agentfile.
3. **Secret-free.** Credentials are referenced via environment variables; they MUST NOT appear in the file.
4. **Reviewable.** Prompts and configs live alongside source and are diffable in pull requests.
5. **Conservative.** v1 specifies only what is well-understood today. Extensions are explicit.

## 3. Top-level structure

```yaml
apiVersion: agentfile/v1   # required
kind: Agent                # required
metadata: { ... }          # required
spec: { ... }              # required
```

### 3.1 `apiVersion`

String. MUST equal `agentfile/v1` for this version of the spec. Future major versions will increment.

### 3.2 `kind`

String. MUST equal `Agent` in v1. Reserved for future kinds (`AgentBundle`, `AgentChain`, etc.).

### 3.3 `metadata`

| Field         | Type            | Required | Description |
|---------------|-----------------|----------|-------------|
| `name`        | string          | yes      | Kebab-case identifier. Pattern: `^[a-z][a-z0-9-]*[a-z0-9]$` |
| `version`     | string (semver) | yes      | SemVer 2.0.0 string, e.g. `0.1.0` |
| `description` | string          | no       | Single-line summary |
| `authors`     | list[string]    | no       | Free-form author identifiers |
| `license`     | string          | no       | SPDX identifier, e.g. `MIT` |
| `tags`        | list[string]    | no       | Discoverability tags |
| `homepage`    | string (URL)    | no       | Project URL |

### 3.4 `spec`

| Field           | Type    | Required | Description |
|-----------------|---------|----------|-------------|
| `model`         | object  | yes      | See §4 |
| `system_prompt` | string OR `{ file: path }` | yes | See §5 |
| `tools`         | list    | no       | See §6 |
| `memory`        | object  | no       | See §7 |
| `permissions`   | object  | no       | See §8 |
| `env`           | object  | no       | See §9 |
| `params`        | object  | no       | Free-form key/value passed to runtime |

## 4. `spec.model`

Specifies the language model.

| Field      | Type   | Required | Description |
|------------|--------|----------|-------------|
| `provider` | string (enum) | yes | One of: `anthropic`, `openai`, `google`, `bedrock`, `azure`, `local`, `custom` |
| `name`     | string | yes | Provider-specific model identifier (e.g. `claude-sonnet-4-5`) |
| `params`   | object | no  | Provider-passthrough params (`temperature`, `top_p`, `max_tokens`, etc.) |

When `provider: custom`, an additional `endpoint` field MAY be specified.

```yaml
model:
  provider: anthropic
  name: claude-sonnet-4-5
  params:
    temperature: 0.3
    max_tokens: 4096
```

## 5. `spec.system_prompt`

The system prompt may be expressed in two forms:

**Inline:**
```yaml
system_prompt: |
  You are a helpful assistant.
```

**File reference:**
```yaml
system_prompt:
  file: ./prompts/system.md
```

Paths are relative to the Agentfile. Validators MUST verify the referenced file exists; runners MUST read it at instantiation time.

## 6. `spec.tools`

A list of tool declarations. Each entry has exactly one of these forms:

**MCP server (URL):**
```yaml
- mcp: https://example.com/mcp
  auth:
    type: bearer
    env: GITHUB_TOKEN
```

**Builtin shorthand:**
```yaml
- mcp: builtin/web_search
- mcp: builtin/filesystem
```

**Auth block** (optional):

| Field   | Type   | Description |
|---------|--------|-------------|
| `type`  | enum   | `bearer`, `oauth`, `none` |
| `env`   | string | Name of env var holding the credential (for `bearer`) |

The actual list of recognized `builtin/*` tools is runtime-defined; validators MAY warn on unrecognized names but MUST NOT reject them.

## 7. `spec.memory`

Optional memory backend declaration.

| Field    | Type   | Required | Description |
|----------|--------|----------|-------------|
| `type`   | enum   | yes      | `none`, `chroma`, `pinecone`, `weaviate`, `sqlite`, `redis`, `custom` |
| `config` | object OR `{ file: path }` | no | Backend-specific config |

```yaml
memory:
  type: chroma
  config:
    collection: agent-memory
    embedding_model: all-MiniLM-L6-v2
```

## 8. `spec.permissions`

Declarative permission boundaries. v1 treats these as **advisory**: runtimes SHOULD enforce them but MAY ignore them. v2 will define enforcement semantics more strictly.

```yaml
permissions:
  network:
    mode: allowlist        # allowlist | denylist | open
    hosts: [api.anthropic.com, github.com]
  filesystem:
    mode: read-only        # read-only | read-write | none
    paths: [./data, ./prompts]
```

## 9. `spec.env`

Declares environment variables the agent depends on. Validators MUST NOT read env values; this section is purely declarative.

```yaml
env:
  required: [ANTHROPIC_API_KEY]
  optional: [OTEL_EXPORTER_ENDPOINT]
```

Runners SHOULD verify all `required` vars are present before starting and fail fast otherwise.

## 10. Validation rules

A valid Agentfile MUST:

1. Match the JSON Schema (`schema/agentfile.v1.schema.json`)
2. Have `apiVersion: agentfile/v1` and `kind: Agent`
3. Have a `metadata.name` matching `^[a-z][a-z0-9-]*[a-z0-9]$`
4. Have a `metadata.version` parseable as SemVer 2.0.0
5. Have either an inline `system_prompt` or a `system_prompt.file` that exists relative to the Agentfile

A valid Agentfile MUST NOT:

1. Contain literal credentials in any string field (validators SHOULD heuristically warn on `sk-`, `ghp_`, etc.)
2. Reference `system_prompt.file` paths that escape the Agentfile's directory (no `../`)

## 11. Compatibility & versioning

- `agentfile/v1` is stable and will not change incompatibly.
- Backward-compatible additions (new optional fields) MAY be made to v1.
- Breaking changes will increment to `agentfile/v2` with a documented migration.

## 12. File layout convention

A typical agent project:

```
my-agent/
├── agent.yaml              # the Agentfile
├── prompts/
│   └── system.md
├── memory.yaml             # optional, referenced from agent.yaml
└── README.md
```

## 14. Consumers

An Agentfile can be consumed in two complementary modes:

### 14.1 Library / CLI

The reference Python package (`agentfile`) exposes `validate()`, `validate_file()`, and `load_agentfile()` as a public API. The `agent` CLI wraps these for interactive use and CI pipelines:

```bash
agent validate ./agent.yaml    # exit 0 if valid, 1 if not
agent show ./agent.yaml        # human-readable summary
agent schema                   # dump JSON Schema
```

This mode is appropriate for CI/CD pipelines, Git hooks, and any workflow where an agent framework is not in the loop.

### 14.2 MCP server (first-class runtime)

The `agentfile-mcp` package wraps the same library functions as an MCP server, making Agentfile tools available natively inside any MCP-capable agent environment (Claude Code, Claude Desktop, Cursor, Continue, Cline, etc.).

The server exposes:
- **Tools:** `validate_agentfile`, `show_agentfile`, `get_agentfile_schema`, `list_examples`, `read_example`, `scaffold`, `lint_inline`
- **Resources:** `agentfile://spec`, `agentfile://schema`, `agentfile://examples/{name}`

MCP servers are first-class consumers of the spec. The validation logic is shared: `agentfile-mcp` calls `validate()` / `validate_file()` directly and never duplicates validation rules. Any future change to the validation spec is automatically reflected in both modes.

Connect via: `uvx agentfile-mcp` (stdio transport).

---

## 13. Open questions (v1.x roadmap)

- Bundling: how is a multi-file Agentfile packaged for transport? (`agent pack` will define this in v0.4)
- Signing: how do we prove provenance of an Agentfile?
- Composition: how do agents reference other agents as sub-agents?

These are deferred to future revisions. Discussion happens in the [RFC tracker](https://github.com/SumanthVarma798/agentfile/discussions).

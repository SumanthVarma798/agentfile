# Authoring Agentfiles — field reference

## metadata

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Kebab-case: `^[a-z][a-z0-9-]*[a-z0-9]$` |
| `version` | string | yes | SemVer 2.0.0 — must be `x.y.z` |
| `description` | string | no | Single-line summary |
| `authors` | list[string] | no | Free-form |
| `license` | string | no | SPDX identifier, e.g. `MIT` |
| `tags` | list[string] | no | Discoverability |
| `homepage` | string (URL) | no | |

## spec.model

| Field | Type | Required | Notes |
|---|---|---|---|
| `provider` | enum | yes | `anthropic`, `openai`, `google`, `bedrock`, `azure`, `local`, `custom` |
| `name` | string | yes | Provider model ID, e.g. `claude-sonnet-4-5` |
| `params` | object | no | `temperature`, `max_tokens`, `top_p`, etc. |
| `endpoint` | string | if custom | Required when `provider: custom` |

## spec.system_prompt

Either inline or file reference:

```yaml
system_prompt: |
  You are a helpful assistant.

# OR
system_prompt:
  file: ./prompts/system.md
```

File paths are relative to the Agentfile. `../` is rejected. The file must exist at validation time.

## spec.tools

Each entry is a dict with an `mcp` key:

```yaml
tools:
  - mcp: builtin/web_search          # recognized builtin
  - mcp: https://internal.corp/mcp   # external MCP server
    auth:
      type: bearer
      env: MY_TOKEN                  # env var holding the credential
```

Auth types: `bearer`, `oauth`, `none`. For `bearer`, always provide `env`.

Recognized builtins: `filesystem`, `web_search`, `web_fetch`, `shell`, `code_interpreter`, `memory`. Others produce a validator warning.

## spec.memory

```yaml
memory:
  type: chroma          # none | chroma | pinecone | weaviate | sqlite | redis | custom
  config:
    collection: my-memory
    embedding_model: all-MiniLM-L6-v2
```

## spec.permissions

Advisory in v1. Runtimes should enforce; v2 will make enforcement mandatory.

```yaml
permissions:
  network:
    mode: allowlist     # allowlist | denylist | open
    hosts: [api.anthropic.com]
  filesystem:
    mode: read-only     # read-only | read-write | none
    paths: [./prompts]
```

## spec.env

Purely declarative — validators never read env values.

```yaml
env:
  required: [ANTHROPIC_API_KEY]
  optional: [OTEL_EXPORTER_ENDPOINT]
```

Runners should fail fast if any `required` var is missing.

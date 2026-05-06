# Agentfile v1 — schema quick reference

## Minimal valid Agentfile

```yaml
apiVersion: agentfile/v1
kind: Agent
metadata:
  name: my-agent          # kebab-case, ≥2 chars
  version: 0.1.0          # SemVer x.y.z
spec:
  model:
    provider: anthropic
    name: claude-sonnet-4-5
  system_prompt: You are a helpful assistant.
  env:
    required: [ANTHROPIC_API_KEY]
```

## Top-level keys

```
apiVersion   string    required   must be "agentfile/v1"
kind         string    required   must be "Agent"
metadata     object    required
spec         object    required
```

## metadata keys

```
name          string   required   ^[a-z][a-z0-9-]*[a-z0-9]$
version       string   required   SemVer 2.0.0
description   string   optional
authors       [string] optional
license       string   optional   SPDX
tags          [string] optional
homepage      string   optional   URL
```

## spec keys

```
model          object            required
system_prompt  string | {file}   required
tools          [{mcp, auth?}]    optional
memory         {type, config?}   optional
permissions    object            optional
env            {required, optional} optional
params         object            optional
```

## model providers

`anthropic` · `openai` · `google` · `bedrock` · `azure` · `local` · `custom`

`custom` requires an additional `endpoint` field.

## system_prompt forms

```yaml
system_prompt: "Inline text"       # string form
system_prompt:
  file: ./prompts/system.md        # file form
```

## tool entry

```yaml
- mcp: builtin/web_search              # builtin shorthand
- mcp: https://example.com/mcp        # external MCP URL
  auth:
    type: bearer                       # bearer | oauth | none
    env: MY_TOKEN                      # env var name
```

## memory types

`none` · `chroma` · `pinecone` · `weaviate` · `sqlite` · `redis` · `custom`

## permissions

```yaml
permissions:
  network:
    mode: allowlist    # allowlist | denylist | open
    hosts: [api.anthropic.com]
  filesystem:
    mode: read-only    # read-only | read-write | none
    paths: [./prompts]
```

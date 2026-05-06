# Debugging Agentfile validation errors

## Schema errors (from JSON Schema)

| Error message | Cause | Fix |
|---|---|---|
| `<root>: 'apiVersion' is a required property` | Missing top-level field | Add `apiVersion: agentfile/v1` |
| `<root>: 'spec' is a required property` | Missing spec block | Add `spec:` with `model` and `system_prompt` |
| `metadata.name: … does not match …` | Name not kebab-case | Use lowercase letters, digits, hyphens; start/end with letter or digit |
| `metadata.version: … does not match …` | Not valid SemVer | Use `x.y.z` format, e.g. `0.1.0` not `0.1` |
| `spec.model: 'provider' is a required property` | Missing model provider | Add `provider: anthropic` (or other supported value) |
| `spec.model.provider: … is not one of …` | Unsupported provider value | Use one of: `anthropic`, `openai`, `google`, `bedrock`, `azure`, `local`, `custom` |

## Semantic errors (from agentfile validator)

| Error message | Cause | Fix |
|---|---|---|
| `spec.model: when provider is 'custom', 'endpoint' is required` | Custom provider without endpoint | Add `endpoint: https://your-model-api/v1` |
| `spec.system_prompt.file: '…' not found relative to Agentfile` | Prompt file missing | Create the file or switch to inline `system_prompt:` |
| `spec.system_prompt.file: path '…' escapes the Agentfile directory` | `../` in path | Remove `..` components; keep paths inside the project |
| `spec.memory.config.file: '…' not found` | Memory config file missing | Create the file or use inline `config:` object |

## Warnings (soft issues)

| Warning | Cause | Fix |
|---|---|---|
| `looks like a anthropic-api-key` | Literal `sk-ant-...` in YAML | Move to `env.required: [ANTHROPIC_API_KEY]` |
| `'builtin/foo' is not in the reference set` | Unknown builtin tool name | Check spelling; use `builtin/web_search`, `builtin/filesystem`, etc. |
| `bearer auth declared without 'env' field` | Bearer auth missing env reference | Add `env: MY_TOKEN_VAR` under the `auth` block |

## Using strict mode

Pass `strict=True` to `validate_agentfile()` or `lint_inline()` to promote all warnings to errors. Useful in CI to prevent secret leaks before they reach version control.

## YAML parse errors

If `lint_inline()` returns a YAML parse error:
- Check for duplicate keys
- Ensure multiline strings use `|` or `>` properly
- Avoid smart quotes (`"` / `"`) — use plain ASCII `"`
- Colons in values must be quoted: `system_prompt: "Hello: world"` not `system_prompt: Hello: world`

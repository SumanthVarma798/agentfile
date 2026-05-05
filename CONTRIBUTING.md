# Contributing to Agentfile

Thanks for your interest. This project is small and early — your involvement matters disproportionately.

## How to help

| If you want to... | Do this |
|---|---|
| Report a bug | Open an [issue](https://github.com/YOUR-USERNAME/agentfile/issues) with a minimal repro |
| Suggest a small code change | Open a PR — keep it focused, include tests |
| Propose a spec change | Open a [Discussion](https://github.com/YOUR-USERNAME/agentfile/discussions) first (see RFC process below) |
| Add an example | PR welcome — examples live in `examples/` and must validate in CI |
| Fix typos / docs | PR welcome, no need to ask |

## Development setup

```bash
git clone https://github.com/YOUR-USERNAME/agentfile.git
cd agentfile
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run lint:

```bash
ruff check .
ruff format --check .
mypy src
```

## RFC process (for spec changes)

The Agentfile spec is the most stable surface of this project. Changing it affects every downstream user, so:

1. Open a Discussion titled `RFC: <change>`.
2. Describe motivation, proposed change, alternatives considered, and migration impact.
3. Wait at least **7 days** for community input before opening a PR.
4. The PR must update both `SPEC.md` and `schema/agentfile.v1.schema.json` together.
5. Backwards-incompatible changes require an `apiVersion` bump (`agentfile/v2`) and migration notes.

Most spec discussions get resolved in the Discussion thread. Don't be discouraged if a proposal evolves significantly — that's the point.

## PR checklist

- [ ] Tests pass (`pytest`)
- [ ] Lint passes (`ruff check . && ruff format --check .`)
- [ ] `CHANGELOG.md` updated under "Unreleased"
- [ ] If adding a feature: a test exercises it
- [ ] If changing the spec: SPEC.md and schema both updated

## Code style

- Type hints everywhere. We run `mypy --strict`.
- Prefer small, single-purpose functions over deep classes.
- Docstrings on every public function (Google style).
- Keep CLI output legible to humans first, machine-parseable second.

## Code of conduct

Be kind. Disagree about technical decisions, never about people. The spec serves the community, not any individual contributor.

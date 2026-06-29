# Contributing to Cairn — Agent Loop Engineering Platform
*Comprehensive documentation for Cairn, the universal DSL and runtime for **agent loop engineering**.*


## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 -m cairn.main validate cairnlang/examples/hello-world.crn
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

## Current Stage

This repository is in early foundation work. Please keep contributions tightly aligned with Phase 1 goals.

## What Helps Most

- Language spec clarifications
- Schema design
- Parser and validator improvements
- Example loops
- Tests and developer experience

## Contribution Guidelines

- Keep changes small and focused.
- Update docs when the spec changes.
- Add tests for parser, validator, or executor behavior changes.
- Prefer extending the MVP path before adding future-phase features.
- Use `python3 -m cairn.main validate <file>` when changing example loops or schema.
- Keep new handlers and plugin behavior documented in `cairnlang/SPEC.md`.

## Pull Request Checklist

- Explain what changed and why
- Add or update tests for behavior changes
- Keep Phase 1 scope tight
- Update docs when user-facing behavior changes
- Verify `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q` passes

## Phase 1 Guardrails

- Do not assume multi-framework support is ready.
- Do not add visual editor work before the runtime contract stabilizes.
- Do not expand the language without examples and validation rules.
- Do not add framework-specific magic that weakens portability contract.

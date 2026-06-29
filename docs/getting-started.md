# Getting Started

This repo is prepared for an implementation-first workflow. Use this guide to begin Phase 1 without reopening product-scoping questions every session.

## What To Build First

- The language contract
- The schema
- The parser and validator
- A minimal executor
- A single framework plugin proof-of-concept

## Suggested Order

1. Write `cairnlang/SPEC.md`.
2. Encode the spec in `cairnlang/schema/cairn-1.0.schema.json`.
3. Add example loops that represent the supported feature surface.
4. Build parser and validator against those fixtures.
5. Add CLI commands once core behavior is stable.

## Working Agreements

- Treat the PRD as product vision, not implementation truth.
- Keep Phase 1 intentionally small and testable.
- Do not add multi-framework behavior before the plugin contract is stable.
- Add examples and tests whenever the spec changes.

## Suggested Local Tooling

- Python 3.10+
- `uv` or `pip` for Python dependency management
- `pytest` for tests
- `ruff` for linting
- `mypy` for type checks
- Node.js only when work begins on `cairnstudio/`

## Useful Next Files To Create

- `pyproject.toml`
- `cairnlang/SPEC.md`
- `cairnlang/schema/cairn-1.0.schema.json`
- `cairnforge/models.py`
- `tests/unit/test_parser.py`
- `tests/unit/test_validator.py`

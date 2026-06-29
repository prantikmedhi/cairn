# MVP Architecture

This document captures the technical shape of the first Cairn implementation.

## Principles

- Keep the language portable and framework-agnostic.
- Separate parsing, validation, execution, and plugin translation.
- Build a thin but stable core before expanding plugins or UI.
- Favor explicit data contracts over framework-specific magic.

## MVP Runtime Flow

1. Load a `.crn` file from disk.
2. Parse YAML into a typed internal representation.
3. Validate schema, references, transitions, and budgets.
4. Build an execution plan from the validated AST.
5. Run states through a framework plugin or core handler.
6. Capture outputs, errors, and execution metadata.

## Core Components

### `cairnlang/`

- Language specification
- JSON schema for validation
- Example loops used by docs and tests

### `cairnforge/`

- `parser.py`: YAML to AST conversion
- `validator.py`: semantic validation
- `state_machine.py`: transition resolution
- `executor.py`: loop execution
- `budget.py`: max cost, duration, and iteration guards
- `plugins/base.py`: plugin contract

### `cairn/`

- Typer-based CLI entrypoint
- Commands for `init`, `validate`, and `run`
- Shared config and output utilities

## Suggested Data Model

- `LoopDefinition`
- `LoopInput`
- `LoopOutput`
- `LoopState`
- `LoopTransition`
- `LoopBudget`
- `ExecutionContext`
- `ExecutionResult`

Pydantic models are a sensible MVP choice because they help with validation, typing, and clean error reporting.

## Early Technical Decisions

- Spec format: YAML-first, JSON-compatible
- Runtime language: Python 3.10+
- CLI: Typer + Rich
- Validation: JSON Schema plus semantic validation layer
- Plugin loading: Python entry points after the core stabilizes

## Non-Goals For The First Slice

- Visual editor
- Registry backend
- Production observability stack
- Multi-framework parity
- Hot reload and collaborative editing

## Open Decisions

- Whether parser and schema should live behind a shared `models.py`
- How plugin handlers map generic Cairn state definitions to framework-native constructs
- Whether expression templating should be minimal string interpolation first, then expanded later

# Cairn

[![CI](https://github.com/prantikmedhi/cairn/actions/workflows/ci.yml/badge.svg)](https://github.com/prantikmedhi/cairn/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Cairn is an open runtime and DSL for building intelligent task loops across AI agent frameworks.

This repository now contains a working Phase 1 MVP: a CairnLang schema, parser, semantic validator, executor, built-in `langchain` target plugin, CLI commands, example loops, and automated tests.

## Why Cairn

- Define agent loops once in portable `.crn` files
- Validate loop structure before execution
- Run loops through stable runtime and plugin contract
- Keep orchestration logic separate from framework lock-in

## Project Status

- Status: Phase 1 MVP working
- Current focus: harden plugin contract and deepen framework integration
- Source of truth: [PRD.md](/Users/prantikpratimmedhi/Documents/Cairn/PRD.md)

## Core Goals

- Define the `cairn: 1.0` loop specification
- Build and validate `.crn` files
- Ship a Python runtime with plugin support
- Provide CLI commands for `init`, `validate`, and `run`
- Deliver example loops and test coverage for the MVP

## Repository Map

- [PRD.md](/Users/prantikpratimmedhi/Documents/Cairn/PRD.md): full product requirements
- [roadmap.md](/Users/prantikpratimmedhi/Documents/Cairn/roadmap.md): phased delivery plan
- [architecture.md](/Users/prantikpratimmedhi/Documents/Cairn/architecture.md): MVP technical direction
- [tasks.md](/Users/prantikpratimmedhi/Documents/Cairn/tasks.md): prioritized build backlog
- [docs/getting-started.md](/Users/prantikpratimmedhi/Documents/Cairn/docs/getting-started.md): implementation kickoff guide

## Initial Workspace Layout

- `cairnlang/`: language spec, schema, and examples
- `cairnforge/`: parser, validator, budget guard, executor, plugins
- `cairn/`: working Typer CLI
- `cairnhub/`: future registry backend
- `cairnstudio/`: future visual editor
- `tests/`: unit, integration, and e2e coverage
- `docs/`: supporting documentation

## Working Commands

```bash
pip install -e ".[dev]"
python3 -m cairn.main validate cairnlang/examples/hello-world.crn
python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge
python3 -m cairn.main init ./demo-loop
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

## Quickstart

```bash
git clone https://github.com/prantikmedhi/cairn.git
cd cairn
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 -m cairn.main validate cairnlang/examples/hello-world.crn
python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge
```

## Implemented MVP Surface

- YAML `.crn` parsing
- JSON Schema validation
- Semantic validation for states, transitions, and budgets
- Execution engine with transitions and hooks
- Budget enforcement for iterations, duration, and cost cap structure
- Built-in proof-of-concept `langchain` plugin target
- Example loops for happy path, branching, data pipeline, failure hook, budget hook
- CLI commands: `init`, `validate`, `run`
- Automated tests covering parser, validator, executor, and CLI

## Not Built Yet

- Real LangChain object graph compilation
- Multi-framework plugins beyond `langchain`
- Registry, publish/install workflow, tracing UI, visual editor
- Checkpoint/resume, retry engine, parallel execution, circuit breaker

## Contributing

Read [CONTRIBUTING.md](/Users/prantikpratimmedhi/Documents/Cairn/CONTRIBUTING.md) for Phase 1 guardrails and [CODE_OF_CONDUCT.md](/Users/prantikpratimmedhi/Documents/Cairn/CODE_OF_CONDUCT.md) for community expectations.

## Release

- Current version: `0.1.0`
- Release notes: [CHANGELOG.md](/Users/prantikpratimmedhi/Documents/Cairn/CHANGELOG.md)
- Release checklist: [docs/release-v0.1.0.md](/Users/prantikpratimmedhi/Documents/Cairn/docs/release-v0.1.0.md)

## Recommended First Build Slice

1. Finalize the minimal language spec.
2. Create the JSON schema and example `.crn` files.
3. Implement parser, validator, and a basic executor.
4. Add a LangChain plugin stub and CLI commands.
5. Add tests around parsing, validation, and budget enforcement.

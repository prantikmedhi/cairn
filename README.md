# Cairn

[![CI](https://github.com/prantikmedhi/cairn/actions/workflows/ci.yml/badge.svg)](https://github.com/prantikmedhi/cairn/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Cairn is an open runtime and DSL for building intelligent task loops across AI agent frameworks.

This repository now contains working local foundations through Phases 1-3: CairnLang schema, parser, semantic validator, multi-target runtime, local registry, checkpointing, retries, parallel fan-out, observability foundations, CLI commands, example loops, and automated tests.

## Why Cairn

- Define agent loops once in portable `.crn` files
- Validate loop structure before execution
- Run loops through stable runtime and plugin contract
- Keep orchestration logic separate from framework lock-in

## Project Status

- Status: Phases 1-3 code foundations complete for local repo scope
- Current focus: Phase 4 visual editor for non-developers
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
- `cairnhub/`: local registry foundation and future hosted backend
- `cairnstudio/`: upcoming visual editor
- `tests/`: unit, integration, and e2e coverage
- `docs/`: supporting documentation

## Working Commands

```bash
pip install -e ".[dev]"
pip install -e ".[langchain]"   # optional native langchain-core runnable path
python3 -m cairn.main validate cairnlang/examples/hello-world.crn
python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge
python3 -m cairn.main run cairnlang/examples/retry-recovery.crn
python3 -m cairn.main run cairnlang/examples/parallel-fanout.crn
python3 -m cairn.main run cairnlang/examples/hello-world.crn --target langgraph --input message=graph
python3 -m cairn.main init ./demo-loop
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --checkpoint-file /tmp/pipeline.json --max-steps 1
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --resume /tmp/pipeline.json
python3 -m cairn.main publish cairnlang/examples/hello-world.crn --registry .cairnhub
python3 -m cairn.main list --registry .cairnhub
python3 -m cairn.main search hello --registry .cairnhub
python3 -m cairn.main debug cairnlang/examples/retry-recovery.crn
python3 -m cairn.main cost cairnlang/examples/parallel-fanout.crn
python3 -m cairn.main test
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

## Quickstart

```bash
git clone https://github.com/prantikmedhi/cairn.git
cd cairn
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ".[langchain]"   # optional
python3 -m cairn.main validate cairnlang/examples/hello-world.crn
python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge
```

## Implemented MVP Surface

- YAML `.crn` parsing
- JSON Schema validation
- Semantic validation for states, transitions, and budgets
- Execution engine with transitions and hooks
- Budget enforcement for iterations, duration, and cost cap structure
- `langchain` plugin target with optional native `langchain-core` runnable execution and builtin fallback
- `langgraph`, `crewai`, `autogen`, and `openai` target adapters
- Local sub-loop composition with relative file imports
- Checkpoint/resume execution flow
- Retry guards and circuit breaker foundation
- Parallel fan-out execution
- Trace JSON export and replay-friendly CLI output
- Local CairnHub-style publish/install/list/search/inspect foundation
- Example loops for happy path, branching, data pipeline, failure hook, budget hook
- Composed example loop using imported sub-loop
- Retry and parallel example loops
- CLI commands: `init`, `validate`, `run`, `inspect`, `trace`, `publish`, `install`, `list`, `search`, `registry-inspect`, `debug`, `cost`, `test`, `watch`
- Automated tests covering parser, validator, executor, and CLI
- Optional Jinja templating path for template strings when `jinja2` is installed

## Not Built Yet

- Hosted registry backend, remote discovery, auth, ratings, and version APIs
- Visual editor app
- Rich observability stack and hosted CairnLens UI
- Community and hosted milestones from PRD that depend on external adoption

## Contributing

Read [CONTRIBUTING.md](/Users/prantikpratimmedhi/Documents/Cairn/CONTRIBUTING.md) for Phase 1 guardrails and [CODE_OF_CONDUCT.md](/Users/prantikpratimmedhi/Documents/Cairn/CODE_OF_CONDUCT.md) for community expectations.

## Release

- Current version: `0.1.0`
- Release notes: [CHANGELOG.md](/Users/prantikpratimmedhi/Documents/Cairn/CHANGELOG.md)
- Release checklist: [docs/release-v0.1.0.md](/Users/prantikpratimmedhi/Documents/Cairn/docs/release-v0.1.0.md)
- CLI reference: [docs/cli-reference.md](/Users/prantikpratimmedhi/Documents/Cairn/docs/cli-reference.md)
- Observability notes: [docs/observability.md](/Users/prantikpratimmedhi/Documents/Cairn/docs/observability.md)
- Plugin SDK notes: [docs/plugin-development.md](/Users/prantikpratimmedhi/Documents/Cairn/docs/plugin-development.md)
- Self-hosting notes: [docs/self-hosting.md](/Users/prantikpratimmedhi/Documents/Cairn/docs/self-hosting.md)

## Recommended First Build Slice

1. Finalize the minimal language spec.
2. Create the JSON schema and example `.crn` files.
3. Implement parser, validator, and a basic executor.
4. Add a LangChain plugin stub and CLI commands.
5. Add tests around parsing, validation, and budget enforcement.

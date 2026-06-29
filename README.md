# Cairn — The Universal Language for Agent Loop Engineering

[![CI](https://github.com/prantikmedhi/cairn/actions/workflows/ci.yml/badge.svg)](https://github.com/prantikmedhi/cairn/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/cairn/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

**Cairn** is the open-source DSL and runtime purpose-built for **agent loop engineering** — defining, validating, and executing portable AI agent task loops across any framework. Think of it as "Terraform for agent loops": write your loop definition once in `.crn` format and run it on LangChain, LangGraph, CrewAI, AutoGen, or OpenAI Agents SDK without rewriting.

```txt
┌─────────────────────────────────────────────────────┐
│  One loop definition → Any agent framework           │
│  "Write once, run anywhere" for AI agent loops       │
└─────────────────────────────────────────────────────┘
```

## Why Loop Engineering Matters

Every AI agent framework defines loops differently. LangGraph uses state graphs, CrewAI uses sequential tasks, AutoGen uses conversation loops. This fragmentation makes **loop engineering** a bottleneck — migrating between frameworks means rewriting your entire orchestration logic.

Cairn solves this with a **vendor-agnostic loop specification** that decouples loop structure from framework execution. Your agent loop becomes portable, testable, and shareable.

- Define **agent loops** once in portable `.crn` files
- Validate loop structure before execution
- Run loops through a stable runtime and plugin contract
- Keep orchestration logic separate from framework lock-in

## Quick Stats

| Metric | Value |
|--------|-------|
| Version | 0.1.0 |
| License | Apache 2.0 |
| Runtime | Python 3.10+ |
| DSL Format | YAML (`.crn`) |
| Frameworks | LangChain, LangGraph, CrewAI, AutoGen, OpenAI |
| CLI Commands | 17 |
| Status | Phases 1-3 complete, Phase 4 beta |

## Project Status

- **Phases 1-3**: Core loop engineering foundations complete — parser, validator, executor, plugins, CLI, checkpointing, parallel execution, observability
- **Phase 4 Beta**: CairnStudio visual loop editor — drag-and-drop loop engineering without raw YAML
- **On the roadmap**: hosted registry, team collaboration, VS Code extension, CI/CD loop validation

## Agent Loop Engineering — Core Concepts

Cairn treats loop engineering as a first-class discipline. A loop is defined declaratively in `.crn` format with:

| Concept | Description |
|---------|-------------|
| **States** | Individual steps in your agent loop (collect, template, condition, sub-loop) |
| **Transitions** | State-to-state routing for loop flow control |
| **Budget Guards** | Max iterations, duration, and cost caps to prevent runaway loops |
| **Retry & Circuit Breaker** | Resilient loop engineering with exponential backoff |
| **Parallel Fan-Out** | Fork/join patterns for concurrent agent execution |
| **Checkpoint/Resume** | Save and restore loop execution state |
| **Sub-loop Composition** | Import and compose loops from local files |

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  CairnLang   │ ──▶│  CairnForge  │ ──▶│   Plugins    │
│  (.crn DSL)  │    │  (Runtime)   │    │              │
│  Parser      │    │  Validator   │    │  LangChain   │
│  Schema      │    │  Executor    │    │  LangGraph   │
│  Examples    │    │  Budget      │    │  CrewAI      │
└─────────────┘    │  Checkpoint  │    │  AutoGen     │
                   │  Retry       │    │  OpenAI      │
                   └──────────────┘    └──────────────┘
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  Cairn CLI   │    │  CairnHub    │    │  CairnStudio │
│  17 commands │    │  Registry    │    │  Visual IDE  │
│  validate    │    │  publish     │    │  drag & drop │
│  run         │    │  install     │    │  live val.   │
│  trace       │    │  search      │    │  trace rep.  │
│  debug       │    │  inspect     │    │  collab sync │
└─────────────┘    └──────────────┘    └──────────────┘
```

## Repository Map

- [PRD.md](PRD.md): full product requirements
- [roadmap.md](roadmap.md): phased delivery plan
- [architecture.md](architecture.md): MVP technical direction
- [tasks.md](tasks.md): prioritized build backlog
- [docs/getting-started.md](docs/getting-started.md): implementation kickoff guide

## Workspace Layout

```
cairnlang/     Language spec, JSON Schema, and .crn examples
cairnforge/    Parser, validator, budget guard, executor, plugins
cairn/         Typer CLI (17 commands)
cairnhub/      Local registry for loop publishing/discovery
cairnstudio/   Visual loop editor (Phase 4 beta)
tests/         Unit, integration, and e2e coverage
docs/          Documentation and guides
```

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
python3 -m cairn.main studio --port 8787
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

## Quickstart — Loop Engineering in 30 Seconds

```bash
git clone https://github.com/prantikmedhi/cairn.git
cd cairn
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 -m cairn.main validate cairnlang/examples/hello-world.crn
python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge
```

## Implemented — Complete Agent Loop Engineering Toolkit

**Core Loop Engineering**
- YAML `.crn` parsing with full AST
- JSON Schema validation (CairnLang 1.0)
- Semantic validation for states, transitions, and budgets
- Execution engine with transition resolution and lifecycle hooks
- Budget enforcement: max iterations, duration, and cost caps
- State machine with configurable routing

**Multi-Framework Execution**
- `langchain` — native `langchain-core` runnable execution
- `langgraph` — state graph adapter
- `crewai` — sequential task adapter
- `autogen` — conversation loop adapter
- `openai` — agents SDK adapter
- Extensible plugin system for custom targets

**Resilient Loop Patterns**
- Sub-loop composition with relative file imports
- Checkpoint/resume for long-running loops
- Retry guards with exponential backoff
- Circuit breaker for repeated failures
- Parallel fan-out with fork/join patterns

**Developer Tooling**
- 17 CLI commands: `init`, `validate`, `run`, `inspect`, `trace`, `publish`, `install`, `list`, `search`, `registry-inspect`, `debug`, `cost`, `test`, `watch`, `studio`
- Trace JSON export with replay-friendly output
- Local CairnHub registry: publish, install, search, inspect
- Optional Jinja2 templating for dynamic expressions

**CairnStudio Visual Editor (Beta)**
- Drag-and-drop loop canvas
- Real-time YAML ↔ canvas synchronization
- Live validation with error feedback
- Preview execution with visual trace replay
- YAML import/export (.crn files)
- Local shared-session collaboration

**Examples**
- Hello world, branching review, data pipeline
- Budget guard, circuit breaker, retry recovery
- Parallel fan-out, failure hooks, composed sub-loops

## Roadmap

| Phase | Status | Focus |
|-------|--------|-------|
| 1 | ✅ Complete | Core DSL, parser, validator, basic executor |
| 2 | ✅ Complete | Plugins, CLI, local registry, checkpointing |
| 3 | ✅ Complete | Retry, circuit breaker, parallel execution, observability |
| 4 | 🚧 Beta | CairnStudio visual editor, collaboration sync |
| 5 | 📋 Planned | Hosted registry, remote discovery, auth, ratings |
| 6 | 📋 Planned | VS Code extension, CI/CD loop validation |

## Documentation

- [Getting Started](docs/getting-started.md) — start here
- [CLI Reference](docs/cli-reference.md) — all 17 commands
- [Plugin Development](docs/plugin-development.md) — build custom adapters
- [Observability](docs/observability.md) — trace export and Grafana dashboard
- [Self-Hosting](docs/self-hosting.md) — deploy your own registry
- [Language Spec](cairnlang/SPEC.md) — complete CairnLang specification
- [Architecture](architecture.md) — system design overview
- [Changelog](CHANGELOG.md) — v0.1.0 release notes

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

Apache 2.0 — see [LICENSE](LICENSE).

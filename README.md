# Cairn — The Universal Language for Agent Loop Engineering

[![CI](https://github.com/prantikmedhi/cairn/actions/workflows/ci.yml/badge.svg)](https://github.com/prantikmedhi/cairn/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/cairn/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

**Cairn** is the open-source Domain-Specific Language (DSL) and runtime purpose-built for **agent loop engineering**. It empowers you to define, validate, and execute portable AI agent task loops across any major framework. 

Think of Cairn as "Terraform for agent loops"—write your orchestration logic once in a portable `.crn` format and seamlessly run it on LangChain, LangGraph, CrewAI, AutoGen, or the OpenAI Agents SDK without rewriting a single line of code.

```text
┌─────────────────────────────────────────────────────┐
│  One loop definition → Any agent framework          │
│  "Write once, run anywhere" for AI agent loops      │
└─────────────────────────────────────────────────────┘
```

---

## 📖 Table of Contents

- [Why Loop Engineering Matters](#why-loop-engineering-matters)
- [Project Status](#project-status)
- [Core Concepts](#core-concepts)
- [Quickstart: Loop Engineering in 30 Seconds](#quickstart-loop-engineering-in-30-seconds)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## ⚡ Why Loop Engineering Matters

Every AI agent framework defines loops differently. LangGraph relies on state graphs, CrewAI uses sequential tasks, and AutoGen orchestrates conversational loops. This fragmentation makes **agent loop engineering** a massive bottleneck. Migrating between frameworks often means throwing away and rewriting your entire orchestration logic.

Cairn solves this problem by introducing a **vendor-agnostic loop specification** that decouples your loop structure from the underlying framework's execution engine.

With Cairn, you can:
- Define **portable agent loops** once in readable `.crn` files.
- Rigorously validate loop structure and data flow before execution.
- Run loops through a stable runtime that guarantees execution consistency.
- Eliminate framework lock-in and keep your orchestration logic purely declarative.

## 🚀 Project Status

Cairn is rapidly evolving to support the needs of modern AI engineering teams:

- **Phases 1-3 (Stable)**: Core loop engineering foundations are complete. This includes the parser, validator, executor, multi-framework plugins, CLI, checkpointing, parallel execution, and observability.
- **Phase 4 Beta**: The **CairnStudio visual loop editor** is in active beta—bringing drag-and-drop loop engineering to your browser without needing to write raw YAML.
- **On the Roadmap**: A hosted loop registry for sharing architectures, robust team collaboration features, a dedicated VS Code extension, and native CI/CD loop validation hooks.

## 🧠 Core Concepts

Cairn elevates agent loop engineering to a first-class discipline. A loop is defined declaratively in the `.crn` format using the following primitives:

| Concept | Description |
|---------|-------------|
| **States** | Individual steps in your agent loop (e.g., collect, template, condition, sub-loop). |
| **Transitions** | Explicit state-to-state routing for precise loop flow control. |
| **Budget Guards** | Hard caps on iterations, duration, and token cost to prevent runaway loops. |
| **Retry & Circuit Breakers** | Resilient loop engineering primitives with exponential backoff. |
| **Parallel Fan-Out** | Fork/join execution patterns for concurrent agent tasks. |
| **Checkpoint/Resume** | Native support for saving and restoring long-running loop execution states. |
| **Sub-loop Composition** | Modular engineering by importing and composing loops from local files. |

## ⏱️ Quickstart: Loop Engineering in 30 Seconds

Get up and running with Cairn's local development environment immediately:

```bash
# Clone the repository
git clone https://github.com/prantikmedhi/cairn.git
cd cairn

# Set up a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Cairn with developer dependencies
pip install -e ".[dev]"

# Validate your first agent loop
python3 -m cairn.main validate cairnlang/examples/hello-world.crn

# Run the loop through the local Forge runtime
python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge
```

## ✨ Key Features

Cairn provides a complete toolkit for professional agent orchestration:

### 1. Multi-Framework Execution
Execute your `.crn` loops natively on your preferred backend:
- **`langchain`** — Native `langchain-core` runnable execution
- **`langgraph`** — Advanced state graph adapter
- **`crewai`** — Sequential task orchestration adapter
- **`autogen`** — Conversation loop adapter
- **`openai`** — OpenAI Agents SDK adapter

### 2. Resilient Loop Patterns
- **Sub-loop Composition**: Break complex agents down into reusable modules.
- **Checkpoint/Resume**: Pause execution and pick up right where you left off.
- **Circuit Breakers**: Prevent systemic failures with robust retry guards and exponential backoff.
- **Parallel Fan-Out**: Execute independent agent tasks concurrently and join the results.

### 3. Developer Tooling
Cairn ships with a powerful Typer-based CLI providing 17 specialized commands, including `validate`, `run`, `trace`, `debug`, `cost`, and `studio`. 

Easily export JSON traces for replay, manage loops in your local **CairnHub** registry, and dynamically inject variables using Jinja2 templating.

## 🏗️ Architecture

Cairn's architecture is modular, ensuring high performance and extensibility across the AI ecosystem:

```text
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  CairnLang  │ ──▶│  CairnForge  │ ──▶│   Plugins    │
│  (.crn DSL) │    │  (Runtime)   │    │              │
│  Parser     │    │  Validator   │    │  LangChain   │
│  Schema     │    │  Executor    │    │  LangGraph   │
│  Examples   │    │  Budget      │    │  CrewAI      │
└─────────────┘    │  Checkpoint  │    │  AutoGen     │
                   │  Retry       │    │  OpenAI      │
                   └──────────────┘    └──────────────┘
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│  Cairn CLI  │    │  CairnHub    │    │  CairnStudio │
│ 17 commands │    │  Registry    │    │  Visual IDE  │
│  validate   │    │  publish     │    │  drag & drop │
│  run        │    │  install     │    │  live val.   │
│  trace      │    │  search      │    │  trace rep.  │
│  debug      │    │  inspect     │    │  collab sync │
└─────────────┘    └──────────────┘    └──────────────┘
```

## 📚 Documentation

Dive deeper into agent loop engineering with our comprehensive documentation:

- **[Getting Started](docs/getting-started.md)**: Your first steps with Cairn.
- **[CLI Reference](docs/cli-reference.md)**: Deep dive into all 17 CLI commands.
- **[Plugin Development](docs/plugin-development.md)**: Guide to building custom framework adapters.
- **[Observability](docs/observability.md)**: Trace exports and Grafana dashboards.
- **[Self-Hosting](docs/self-hosting.md)**: Deploy your own secure CairnHub registry.
- **[Language Spec](cairnlang/SPEC.md)**: The complete CairnLang `.crn` specification.
- **[Architecture Overview](architecture.md)**: System design and internal mechanics.
- **[Changelog](CHANGELOG.md)**: What's new in v0.1.0.

## 🤝 Contributing

We welcome contributions from the community! Please read our [Contributing Guide](CONTRIBUTING.md) and our [Code of Conduct](CODE_OF_CONDUCT.md) to get started.

## 📄 License

Cairn is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for more details.

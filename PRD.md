# Cairn — Universal DSL & Runtime for Agent Loop Engineering
*Comprehensive documentation for Cairn, the universal DSL and runtime for **agent loop engineering**.*


## Product Requirements Document

**Version:** 1.0
**Status:** Draft
**Date:** June 2026

---

## 1. Executive Summary

Cairn is an open-source, vendor-agnostic Domain-Specific Language (DSL) and runtime for defining, executing, and sharing AI agent loops. It abstracts loop definitions away from specific frameworks (LangChain, LangGraph, CrewAI, AutoGen, etc.) and provides a universal standard, think "Terraform for Agent Loops."

**Tagline:** *The universal language for agent loops.*
**Analogy:** If Terraform unified infrastructure-as-code across clouds, Cairn unifies loop-as-code across agent frameworks.

---

## 2. Problem Statement

### 2.1 Current Pain
Every agent framework reinvents loop definitions differently:
- LangGraph → Python graphs with nodes/edges
- CrewAI → Role-based YAML + Python decorators
- AutoGen → Conversational programming
- OpenAI Agents SDK → Handoff-based orchestration
- Smolagents → Code-as-policy

A developer building an agent loop in CrewAI cannot migrate to LangGraph without a full rewrite. There is no interoperability. No portability. No standard.

### 2.2 Market Timing
- Loop Engineering emerged as a discipline in 2025-2026
- Boris Cherny (Claude Code) coined: *"I don't prompt Claude anymore. I have loops that are running"*
- A2A (Agent-to-Agent) protocol stabilized at v1.0 — **loop standardization is the natural next step**
- The ecosystem is fragmented but hungry for unification
- **No universal loop DSL exists anywhere on the internet.**

### 2.3 Opportunity
The first project to establish a universal loop standard will capture the network effects: developers write Cairn loops, share on CairnHub, other developers adopt, more framework runtimes are added, more developers join. This is the same flywheel that made Terraform, Docker, and Kubernetes dominant.

---

## 3. Vision

Become the de facto standard for defining agent loops across all frameworks, enabling:
- **Write once, run anywhere** — one Cairn file executes on LangChain, CrewAI, AutoGen, etc.
- **Composable loops** — import and chain loops from CairnHub like npm packages
- **Observable loops** — built-in tracing, debugging, and visualization
- **Community-driven standards** — the open-source foundation for Loop Engineering

---

## 4. Product Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CAIRN ECOSYSTEM                                │
├─────────────┬───────────────┬──────────────┬────────────────┬─────────────┤
│   CairnLang │  CairnForge   │   CairnHub   │  CairnStudio   │  CairnLens  │
│     DSL     │   Runtime     │  Registry    │    (Visual)    │  (Observe)  │
│             │               │              │                │             │
│ • .crn      │ • Multi-fw    │ • Publish    │ • Visual       │ • Traces    │
│   files     │   executor    │ • Discover   │   designer     │ • Metrics   │
│ • Schema    │ • Loop engine │ • Compose    │ • Drag-drop    │ • Cost      │
│ • Validate  │ • Handlers    │ • Version    │ • Debug        │   tracking  │
│ • Compile   │ • Budgets     │ • Fork       │ • Simulate     │ • Alerts    │
│ • Generate  │ • Recovery    │ • Rate       │ • Deploy       │ • Export    │
│             │ • Plugins     │              │                │             │
└─────────────┴───────────────┴──────────────┴────────────────┴─────────────┘
```

---

## 5. Component Specifications

### 5.1 CairnLang — The DSL

**File extension:** `.crn` (preferred) or `.cairn` (readable alias)

**Core Concepts:**

| Concept | Description | Example |
|---------|-------------|---------|
| **Loop** | A complete agent loop definition | Top-level object |
| **State** | A discrete step in the loop | Fetch data, call LLM, check condition |
| **Transition** | Directed edge between states | Sequential, conditional, parallel |
| **Handler** | Action executed in a state | Tool call, LLM call, human-in-loop |
| **Guard** | Pre/post condition on a state | Budget check, timeout, retry policy |
| **Budget** | Resource constraints on the loop | Max tokens, max cost, max time |
| **Input** | Parameters the loop accepts | Typed, validated |
| **Output** | What the loop returns | Typed, structured |

**Minimal Example — Code Review Agent:**

```yaml
cairn: 1.0

loop:
  id: code-review-agent
  name: Automated Code Review
  version: 1.2.0
  description: Reviews pull requests with AI and posts feedback

  inputs:
    repo_url:
      type: string
      required: true
      description: GitHub repository URL
    pr_number:
      type: integer
      required: true
      description: Pull request number to review

  outputs:
    review:
      type: object
      properties:
        approved: boolean
        comments: array
        summary: string

  budget:
    max_cost_usd: 2.00
    max_duration: 5m
    max_iterations: 15

  states:
    - id: fetch_pr
      name: Fetch PR Data
      handler: github.fetch_pull_request
      inputs:
        repo_url: ${{ inputs.repo_url }}
        pr_number: ${{ inputs.pr_number }}
      timeout: 30s

    - id: analyze_code
      name: Analyze with LLM
      handler: llm.review
      model: claude-sonnet-4
      context:
        diff: ${{ states.fetch_pr.outputs.diff }}
        files: ${{ states.fetch_pr.outputs.files }}
      guard:
        retry: 3
        backoff: exponential

    - id: quality_gate
      name: Quality Check
      handler: eval.threshold
      condition: ${{ states.analyze_code.outputs.score }} > 0.8
      transitions:
        - to: post_review
          if: ${{ outputs.passed }}
        - to: request_changes
          if: ${{ !outputs.passed }}

    - id: post_review
      name: Post Approval
      handler: github.post_approval
      inputs:
        review: ${{ states.analyze_code.outputs }}

    - id: request_changes
      name: Request Changes
      handler: github.request_changes
      inputs:
        review: ${{ states.analyze_code.outputs }}

    - id: notify_team
      name: Notify on Slack
      handler: slack.send_message
      condition: ${{ states.quality_gate.outputs.passed }} == false
      inputs:
        channel: "#code-reviews"
        message: "PR #${{ inputs.pr_number }} needs attention"

  transitions:
    - from: fetch_pr
      to: analyze_code

    - from: analyze_code
      to: quality_gate

    - from: quality_gate
      to: post_review
      condition: passed

    - from: quality_gate
      to: request_changes
      condition: failed

    - from: request_changes
      to: notify_team

  on_error:
    handler: slack.send_message
    inputs:
      channel: "#alerts"
      message: "Code review loop failed for PR #${{ inputs.pr_number }}"

  on_budget_exceeded:
    handler: github.post_comment
    inputs:
      body: "Review exceeded budget. Manual review required."
```

**Advanced Example — Self-Healing Loop with Sub-loops:**

```yaml
cairn: 1.0

loop:
  id: self-healing-deployment
  name: Self-Healing Deployment Pipeline

  imports:
    - name: health-check
      source: cairnhub.com/cairnloops/health-check@v2.1.0
    - name: rollback
      source: cairnhub.com/cairnloops/k8s-rollback@v1.0.3

  inputs:
    image_tag:
      type: string
    namespace:
      type: string
      default: production

  states:
    - id: deploy
      handler: k8s.deploy
      inputs:
        image: myapp:${{ inputs.image_tag }}
        namespace: ${{ inputs.namespace }}

    - id: health_check
      loop: health-check  # imported sub-loop
      inputs:
        endpoint: "https://api.example.com/health"
        retries: 5

    - id: rollback
      loop: rollback  # imported sub-loop
      condition: ${{ states.health_check.outputs.healthy }} == false
      inputs:
        namespace: ${{ inputs.namespace }}

    - id: notify_success
      handler: slack.send
      condition: ${{ states.health_check.outputs.healthy }} == true

  transitions:
    - from: deploy
      to: health_check
    - from: health_check
      to: notify_success
      condition: healthy
    - from: health_check
      to: rollback
      condition: unhealthy
```

### 5.2 CairnForge — The Runtime

The runtime is a **multi-framework execution engine** that compiles CairnLang files and executes them on the target framework.

**Architecture:**

```
CairnLang File (.crn)
    ↓
[Parser] → AST (Abstract Syntax Tree)
    ↓
[Validator] → Schema + Guard Checks
    ↓
[Compiler] → Target Framework Code
    ↓
[Executor] → Running Loop
    ↓
[Observer] → Traces + Metrics
```

**Runtime Plugins (one per framework):**

| Plugin | Framework | Status |
|--------|-----------|--------|
| `cairn-langchain` | LangChain | Phase 1 |
| `cairn-langgraph` | LangGraph | Phase 2 |
| `cairn-crewai` | CrewAI | Phase 2 |
| `cairn-autogen` | AutoGen | Phase 2 |
| `cairn-openai` | OpenAI Agents SDK | Phase 2 |
| `cairn-smolagents` | HuggingFace Smolagents | Phase 3 |
| `cairn-pydantic-ai` | Pydantic AI | Phase 3 |
| `cairn-custom` | Custom HTTP/WebSocket | Phase 3 |

**Runtime Features:**
- **Budget Enforcement** — killswitch when cost/time/iterations exceeded
- **Circuit Breaker** — stops loop on repeated failures
- **Retry Engine** — configurable retry with exponential backoff
- **Parallel Execution** — fork/join patterns for parallel states
- **Checkpointing** — save/resume loop state for long-running loops
- **Hot Reload** — reload loop definition without restarting
- **Plugin Discovery** — auto-detect installed framework plugins

### 5.3 CairnHub — The Registry

A centralized registry for sharing and discovering loops. Think npm + Docker Hub for agent loops.

**Features:**
- `cairn publish` — publish a loop to CairnHub
- `cairn install <user>/<loop>` — install a loop
- `cairn search <query>` — search loops by tag, framework, use-case
- Loop versioning (semver)
- Dependency resolution (loops can depend on other loops)
- Verified publishers (checkmark for trusted authors)
- Usage statistics and ratings
- README rendering with examples

**CLI Commands:**
```bash
cairn init                    # Initialize a new loop project
cairn validate                # Validate .crn file syntax
cairn run my-loop.crn         # Execute a loop
cairn run --target=langgraph  # Execute on specific framework
cairn publish                 # Publish to CairnHub
cairn install acme/health-check # Install a loop from CairnHub
cairn list                    # List installed loops
cairn inspect <loop>          # Show loop details and transitions
cairn test                    # Run loop unit tests
cairn debug                   # Interactive debug mode with breakpoints
cairn trace <run-id>          # Show execution trace
cairn cost                    # Estimate loop cost before running
```

### 5.4 CairnStudio — Visual Editor (Phase 4)

A browser-based visual IDE for designing loops without writing YAML.

**Features:**
- Drag-and-drop state canvas
- Visual transition drawing
- Real-time validation
- One-click deploy to CairnForge
- Live execution preview
- Trace replay (watch the loop execute step by step)
- Export to `.crn` file
- Import from `.crn` file

### 5.5 CairnLens — Observability (Phase 3)

Built-in observability layer for running loops.

**Features:**
- Execution tracing (OpenTelemetry-compatible)
- Cost tracking per state and per loop
- Latency heatmaps
- Error rate dashboards
- Slack/PagerDuty alerts
- Prometheus metrics export
- Grafana dashboard templates

---

## 6. Technical Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **DSL Parser** | Rust (tree-sitter) | Fast, safe, portable |
| **Runtime Core** | Python 3.10+ | Agent ecosystem is Python-native |
| **CLI** | Python (Typer/Rich) | Rich terminal UI, Python ecosystem |
| **CairnHub API** | Rust (Actix) or Python (FastAPI) | Performance vs. ecosystem |
| **CairnHub Web** | Next.js + React | Modern, fast, component-rich |
| **CairnStudio** | React + ReactFlow | Best-in-class flow visualization |
| **Database** | PostgreSQL | Registry data, user accounts |
| **Cache** | Redis | Rate limiting, session cache |
| **Storage** | S3-compatible | Loop artifacts, traces |
| **Observability** | OpenTelemetry + Jaeger | Industry standard tracing |

---

## 7. File Structure

```
cairn/
├── README.md
├── LICENSE (Apache 2.0)
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── Makefile
├── docker-compose.yml
├── pyproject.toml
├── Cargo.toml
│
├── cairnlang/                    # DSL specification
│   ├── SPEC.md                   # Formal language specification
│   ├── schema/
│   │   └── cairn-1.0.schema.json # JSON Schema for validation
│   └── examples/
│       ├── code-review.crn
│       ├── data-pipeline.crn
│       ├── self-healing.crn
│       └── multi-agent.crn
│
├── cairnforge/                   # Core runtime (Python)
│   ├── __init__.py
│   ├── parser.py                 # CairnLang → AST
│   ├── validator.py              # AST validation
│   ├── compiler.py               # AST → framework code
│   ├── executor.py               # Loop execution engine
│   ├── state_machine.py          # State machine engine
│   ├── budget.py                 # Budget enforcement
│   ├── checkpoint.py             # Save/resume state
│   ├── tracing.py                # OpenTelemetry integration
│   └── plugins/                  # Framework plugins
│       ├── __init__.py
│       ├── base.py               # Abstract plugin interface
│       ├── langchain/
│       ├── langgraph/
│       ├── crewai/
│       ├── autogen/
│       └── openai/
│
├── cairn/                        # CLI (Python)
│   ├── __init__.py
│   ├── main.py                   # Typer CLI entrypoint
│   ├── commands/
│   │   ├── init.py
│   │   ├── validate.py
│   │   ├── run.py
│   │   ├── publish.py
│   │   ├── install.py
│   │   ├── test.py
│   │   ├── debug.py
│   │   └── trace.py
│   └── utils/
│       ├── config.py
       └── auth.py
│
├── cairnhub/                     # Registry backend
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── loops.py
│   │   │   ├── users.py
│   │   │   ├── search.py
│   │   │   └── versions.py
│   │   └── models.py
│   └── migrations/
│
├── cairnstudio/                  # Visual editor (React)
│   ├── package.json
│   ├── src/
│   │   ├── components/
│   │   │   ├── Canvas.tsx
│   │   │   ├── StateNode.tsx
│   │   │   ├── TransitionEdge.tsx
│   │   │   ├── PropertyPanel.tsx
│   │   │   └── Toolbar.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── public/
│
├── tests/                        # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── docs/                         # Documentation
    ├── getting-started.md
    ├── cairnlang-reference.md
    ├── plugin-development.md
    ├── cli-reference.md
    ├── self-hosting.md
    └── architecture/
```

---

## 8. Development Phases

### Phase 1: Foundation (Weeks 1-4)
**Goal:** A developer can write a CairnLang file and execute it on LangChain.

**Deliverables:**
- [ ] CairnLang v1.0 specification finalized
- [ ] JSON Schema for validation
- [ ] Python parser (`.crn` → AST)
- [ ] AST validator
- [ ] LangChain plugin (`cairn-langchain`)
- [ ] Basic CLI: `init`, `validate`, `run`
- [ ] 5 example loops
- [ ] README + documentation
- [ ] Apache 2.0 license
- [ ] GitHub repo open-sourced

**Milestone:** First GitHub stars, Hacker News launch, community feedback.

### Phase 2: Multi-Framework (Weeks 5-8)
**Goal:** Execute on any major framework. CairnHub MVP.

**Deliverables:**
- [ ] LangGraph plugin
- [ ] CrewAI plugin
- [ ] AutoGen plugin
- [ ] OpenAI Agents SDK plugin
- [ ] Plugin system documentation
- [ ] CairnHub registry (MVP)
- [ ] CLI: `publish`, `install`, `search`
- [ ] Loop composition (sub-loops)
- [ ] Checkpoint/resume
- [ ] Budget enforcement
- [ ] Initial test suite

**Milestone:** Framework authors start noticing. Blog posts about Cairn.

### Phase 3: Production (Weeks 9-14)
**Goal:** Production-ready with observability.

**Deliverables:**
- [ ] CairnLens observability (traces, metrics, cost tracking)
- [ ] Circuit breaker and retry policies
- [ ] Parallel state execution
- [ ] Hot reload
- [ ] CLI: `debug`, `trace`, `cost`, `test`
- [ ] CairnHub: verified publishers, ratings
- [ ] Self-hosting documentation
- [ ] Grafana dashboard templates
- [ ] 50+ community loops on CairnHub
- [ ] Plugin SDK for custom handlers

**Milestone:** Companies start using in production. Conference talks.

### Phase 4: Visual (Weeks 15-20)
**Goal:** Visual loop design for non-developers.

**Deliverables:**
- [ ] CairnStudio visual editor (beta)
- [ ] Drag-and-drop canvas
- [ ] Real-time validation
- [ ] Live execution preview
- [ ] Trace replay visualization
- [ ] Export/import `.crn` files
- [ ] Collaborative editing

**Milestone:** Product managers and non-coders can design loops.

### Phase 5: Ecosystem (Months 6-12)
**Goal:** Industry standard.

**Deliverables:**
- [ ] VS Code extension with IntelliSense
- [ ] GitHub Actions for CI/CD loop validation
- [ ] 500+ community loops
- [ ] Enterprise features (SSO, audit logs)
- [ ] Framework native support (frameworks ship with Cairn support)
- [ ] Loop Engineering certification program
- [ ] Annual Cairn conference

**Milestone:** "The Kubernetes of agent loops."

---

## 9. Open Questions

| Question | Proposed Approach | Status |
|----------|------------------|--------|
| YAML vs. JSON vs. HCL syntax? | YAML (readable) + JSON (machine) | To validate |
| Templating engine? | Jinja2 (familiar) or custom | To decide |
| Plugin architecture? | pip-installable packages with entry points | Draft |
| CairnHub hosting? | Start free (cairn.sh), later enterprise self-host | Draft |
| Governance model? | Open Governance (CNCF-style) when mature | Long-term |

---

## 10. Success Metrics

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 5 |
|--------|---------|---------|---------|---------|
| GitHub Stars | 500 | 2,000 | 5,000 | 20,000 |
| Framework Plugins | 1 | 4 | 6+ | 10+ |
| CairnHub Loops | 0 | 20 | 50+ | 500+ |
| Contributors | 5 | 15 | 30+ | 100+ |
| Companies Using | 0 | 5 | 20+ | 100+ |

---

## 11. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Frameworks build their own standard | Medium | High | Be first, be open, be community-driven |
| YAML fatigue (devs prefer code) | Medium | Medium | Support code-based definitions (Python DSL) |
| Not enough community adoption | Medium | High | Hacker News launch, blog posts, partnerships |
| Too complex for beginners | Low | Medium | Great docs, examples, visual editor |
| Performance overhead | Low | Medium | Rust parser, async execution, benchmarks |

---

## 12. Competitive Landscape

| Project | What It Does | What Cairn Does Differently |
|---------|-------------|---------------------------|
| LangGraph | Graph-based loops in Python | Cairn is framework-agnostic |
| CrewAI | Role-based agent teams | Cairn is framework-agnostic |
| AutoGen | Conversational agents | Cairn is framework-agnostic |
| `loop-audit` | CLI scaffolding tool | Cairn is a full DSL + runtime |
| AgentPrism | React visualization | Cairn has this built-in (CairnStudio) |
| Agent Time Traveler | LangGraph-specific debugger | Cairn works across all frameworks |
| Composio AO | Task orchestrator | Cairn is a standard, not a product |

**Cairn's moat:** Being the universal standard. Network effects make it harder to displace as it grows.

---

## 13. Go-to-Market

1. **Week 1:** GitHub repo + Hacker News "Show HN"
2. **Week 2:** Blog post: "Why We Need a Universal Loop Language"
3. **Week 3:** Partner with LangChain/LangGraph for shoutout
4. **Week 4:** "Build a code review agent in 5 minutes with Cairn" tutorial
5. **Month 2:** Submit talk to AI engineering conferences
6. **Month 3:** Launch CairnHub with 20 curated loops
7. **Month 4:** Podcast tour (Latent Space, Cognitive Revolution, etc.)
8. **Month 6:** Cairn 1.0 stable release

---

## 14. Funding / Sustainability

- **Phase 1-2:** Personal time + community contributions
- **Phase 3:** GitHub Sponsors + Open Collective
- **Phase 4+:** Enterprise support, managed CairnHub, consulting
- **Long-term:** CNCF-style foundation or Y Combinator for sustained development

---

**Next Step:** Begin Phase 1. Set up the GitHub repo, finalize the CairnLang spec, and build the parser plus LangChain plugin.

---

*This document is a living specification. It will evolve as the project grows and community feedback is incorporated.*

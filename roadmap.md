# Cairn Roadmap

This roadmap translates the PRD into an execution sequence that is practical for implementation.

## Phase 1: Foundation

Goal: run a valid `.crn` loop through the runtime and one framework plugin.

### Deliverables

- Language specification for `cairn: 1.0`
- JSON schema validation
- Parser from YAML to AST
- AST validator with budget and transition checks
- Runtime executor with a simple state machine
- Initial plugin interface and one target plugin
- CLI commands: `init`, `validate`, `run`
- Example loops and baseline tests

### Exit Criteria

- [x] A sample loop can be validated from the CLI.
- [x] A sample loop can be executed through the MVP runtime.
- [x] Runtime errors are surfaced with actionable messages.
- [x] Tests cover happy-path parsing plus core validation failures.

## Phase 2: Multi-Framework

Goal: make Cairn portable across major agent frameworks.

### Focus

- Expand plugin system
- Add sub-loop support
- Add checkpointing and budget enforcement
- Begin `cairn publish` and `cairn install`

## Phase 3: Production

Goal: make loops observable and safe in real workloads.

### Focus

- Tracing and metrics
- Retry and circuit breaker policies
- Parallel execution
- Debug and trace tooling

## Phase 4: Visual

Goal: support loop authoring beyond handwritten YAML.

### Focus

- Visual editor
- Import/export `.crn`
- Live simulation and trace replay

## Current Recommendation

Keep the first implementation narrow:

- One DSL format: YAML
- One runtime language: Python
- One plugin target to prove the abstraction
- One example loop that exercises transitions, guards, and outputs

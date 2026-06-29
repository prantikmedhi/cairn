# Build Tasks — Cairn Agent Loop Engineering Platform

This backlog is ordered to support fast MVP progress for the Cairn agent loop engineering platform.

## Now

- [x] Add Apache 2.0 license and contribution guidelines
- [x] Create `pyproject.toml` for the runtime and CLI workspace
- [x] Create a Python package layout for `cairn` and `cairnforge`
- [x] Draft `cairnlang/SPEC.md` with the minimal v1.0 grammar
- [x] Add `cairnlang/schema/cairn-1.0.schema.json`
- [x] Add example loops in `cairnlang/examples/`

## Next

- [x] Implement parser with clear validation errors
- [x] Implement semantic validator for state references and transitions
- [x] Implement budget rules for duration, iterations, and cost caps
- [x] Implement a simple sequential executor
- [x] Define plugin base interface
- [x] Add first plugin stub for a single framework target

## After That

- [x] Build CLI `validate` command
- [x] Build CLI `run` command
- [x] Build CLI `init` command for scaffolding new loops
- [x] Add unit tests for parser and validator
- [x] Add integration tests for example loop execution
- [x] Write contributor setup instructions

## Later

- [x] Checkpoint and resume support
- [x] Sub-loop imports
- [x] Local publish and install foundation
- [x] Local registry search
- [x] Trace export foundation
- [x] Retry engine and circuit breaker
- [x] Parallel execution
- [x] Additional framework adapter targets
- [x] CLI debug / cost / test / watch foundations
- [x] Visual editor bootstrap
- [x] Local collaborative editing
- [ ] Remote registry backend and search
- [ ] Hosted ratings and verified publishers
- [ ] Rich observability UI
- [ ] Rich multi-user hosted collaboration

## Suggested First Week Output

- A repo that installs locally
- One valid `.crn` file
- One invalid `.crn` test fixture
- One passing CLI validation command
- One executor smoke test

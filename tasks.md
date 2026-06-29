# Build Tasks

This backlog is ordered to support fast MVP progress.

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

- [ ] Checkpoint and resume support
- [ ] Sub-loop imports
- [ ] Publish and install workflow
- [ ] Tracing and metrics
- [ ] Visual editor bootstrap

## Suggested First Week Output

- A repo that installs locally
- One valid `.crn` file
- One invalid `.crn` test fixture
- One passing CLI validation command
- One executor smoke test

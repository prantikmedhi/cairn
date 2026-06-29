# Cairn MVP Feature Audit

This audit compares current repo state to PRD Phase 1 requirements.

## Delivered

- CairnLang v1.0 working subset documented in [cairnlang/SPEC.md](/Users/prantikpratimmedhi/Documents/Cairn/cairnlang/SPEC.md)
- JSON Schema in [cairnlang/schema/cairn-1.0.schema.json](/Users/prantikpratimmedhi/Documents/Cairn/cairnlang/schema/cairn-1.0.schema.json)
- Parser in [cairnforge/parser.py](/Users/prantikpratimmedhi/Documents/Cairn/cairnforge/parser.py)
- AST validator in [cairnforge/validator.py](/Users/prantikpratimmedhi/Documents/Cairn/cairnforge/validator.py)
- Budget enforcement in [cairnforge/budget.py](/Users/prantikpratimmedhi/Documents/Cairn/cairnforge/budget.py)
- Sequential executor in [cairnforge/executor.py](/Users/prantikpratimmedhi/Documents/Cairn/cairnforge/executor.py)
- Plugin contract in [cairnforge/plugins/base.py](/Users/prantikpratimmedhi/Documents/Cairn/cairnforge/plugins/base.py)
- First plugin target in [cairnforge/plugins/langchain.py](/Users/prantikpratimmedhi/Documents/Cairn/cairnforge/plugins/langchain.py)
- CLI `init`, `validate`, `run` in [cairn/main.py](/Users/prantikpratimmedhi/Documents/Cairn/cairn/main.py)
- Five example loops in [cairnlang/examples](/Users/prantikpratimmedhi/Documents/Cairn/cairnlang/examples)
- Automated tests in [tests](/Users/prantikpratimmedhi/Documents/Cairn/tests)
- Apache 2.0 license in [LICENSE](/Users/prantikpratimmedhi/Documents/Cairn/LICENSE)

## Partially Delivered

- LangChain plugin: target exists and executes Cairn built-in handlers, but not real LangChain graph compilation or external LangChain primitives yet
- Documentation: README/spec updated, but contributor/developer docs still thin

## Not Delivered

- Real multi-framework support
- Registry and `publish/install/search`
- `trace`, `debug`, `cost`, `test` CLI commands
- Checkpoint/resume
- Retry engine, circuit breaker, parallel execution
- Visual editor and observability stack

## Verification

Run:

```bash
python3 -m cairn.main validate cairnlang/examples/hello-world.crn
python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
```

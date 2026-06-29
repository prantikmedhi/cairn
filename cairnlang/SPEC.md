# CairnLang Specification

This is the working specification for `cairn: 1.0`.

## Purpose

CairnLang defines a portable loop format that can be parsed, validated, and executed across multiple AI agent runtimes.

## MVP Scope

The first implementation should support:

- Top-level `cairn` version
- One `loop` definition
- Inputs and outputs
- Budget constraints
- States
- Transitions
- Basic error hooks

## Supported Shape

```yaml
cairn: 1.0

loop:
  id: example-loop
  name: Example Loop
  version: 0.1.0
  description: Example description
  inputs: {}
  outputs: {}
  budget: {}
  states: []
  transitions: []
```

## Required Fields

- Top level: `cairn`, `loop`
- Loop: `id`, `name`, `version`, `states`
- State: `id`, `handler`
- Transition: `to`

## Supported Expressions

- Template form: `${{ inputs.message }}`
- Raw condition form: `outputs.passed`
- Supported names: `inputs`, `states`, `outputs`, `budget`, `loop`
- Supported operators: `==`, `!=`, `>`, `>=`, `<`, `<=`, `and`, `or`, `not`, `+`

## Supported Budget Units

- `max_iterations`: integer >= 1
- `max_cost_usd`: number >= 0
- `max_duration`: `ms`, `s`, `m`, `h`

## Supported Runtime Semantics

- First state in list is entry state
- Top-level and inline state transitions are both supported
- First matching transition wins
- `on_error` hook runs on execution failure
- `on_budget_exceeded` hook runs on budget exhaustion

## Built-in Phase 1 Handlers

- `core.collect`
- `core.set`
- `core.template`
- `core.condition`
- `core.echo`
- `core.fail`

## Deliberate Phase 1 Limits

- One loop per file
- YAML only
- No sub-loops
- No retries, parallel states, checkpoints, or tracing yet
- `langchain` target is proof-of-concept plugin surface, not full framework compiler
## Implementation Note

Keep initial grammar smaller than PRD. Better strict working subset than fake full surface.

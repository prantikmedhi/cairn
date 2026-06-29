# CairnLang Specification — Agent Loop DSL Reference (Agent Loop Engineering)

This is the working specification for `cairn: 1.0`, the portable DSL for agent loop engineering. CairnLang defines a framework-agnostic loop format that runs across LangChain, LangGraph, CrewAI, AutoGen, and OpenAI.

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
  imports: []
  inputs: {}
  outputs: {}
  budget: {}
  states: []
  transitions: []
```

## Required Fields

- Top level: `cairn`, `loop`
- Loop: `id`, `name`, `version`, `states`
- State: `id` plus exactly one of `handler` or `loop`
- Transition: `to`
- Import: `name`, `source`

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
- Local sub-loop imports are supported through `imports` plus state `loop`

## Built-in Phase 1 Handlers

- `core.collect`
- `core.set`
- `core.template`
- `core.condition`
- `core.echo`
- `core.fail`

## Local Sub-loop Shape

```yaml
loop:
  imports:
    - name: greeting
      source: ./shared/greeting-subloop.crn

  states:
    - id: greet
      loop: greeting
      inputs:
        name: ${{ inputs.name }}
```

## Current Limits

- One loop per file
- YAML only
- Only local file imports for sub-loops
- No retries, parallel states, checkpoints, or tracing yet
- `langchain` target can execute through `langchain-core` runnables when installed, but not full graph compilation yet

## Implementation Note

Keep initial grammar smaller than PRD. Better strict working subset than fake full surface.

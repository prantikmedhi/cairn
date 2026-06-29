# Plugin Development — Build Custom Agent Loop Framework Adapters (Agent Loop Engineering)

This document defines the Cairn plugin SDK surface for extending agent loop engineering to custom frameworks.

## Plugin Contract

Implement `BasePlugin` from [cairnforge/plugins/base.py](/Users/prantikpratimmedhi/Documents/Cairn/cairnforge/plugins/base.py).

Required method:

- `execute_state(state, resolved_inputs, runtime_context) -> dict`

Optional metadata:

- `get_metadata() -> dict`

## Runtime Context

Current runtime context may include:

- `loop`
- `inputs`
- `states`
- `current_condition`
- `attempt`
- `max_attempts`
- `backoff`

## Built-in Reference Targets

- `langchain`
- `langgraph`
- `crewai`
- `autogen`
- `openai`

## Current Limits

- Plugins execute one state at time
- Full framework-native graph compilation is only partial
- Discovery is repo-local, not entry-point based yet

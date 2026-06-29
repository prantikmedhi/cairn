# Phase 2-3 Audit (Agent Loop Engineering)
*Comprehensive documentation for Cairn, the universal DSL and runtime for **agent loop engineering**.*


This audit separates local repo-complete items from still-pending hosted or community items.

## Complete In Repo Scope

- framework adapter targets: `langchain`, `langgraph`, `crewai`, `autogen`, `openai`
- sub-loop composition
- checkpoint/resume
- local registry `publish/install/list/search/inspect`
- hosted CairnHub file-backed API `publish/list/search/inspect/source`
- verified publisher registry + API-key publish auth
- hosted loop ratings + per-version summaries
- shared remote index export/import + federated search
- retry guards
- circuit breaker foundation
- parallel fan-out execution
- trace export
- hosted trace ingest + CairnLens UI
- `debug`, `cost`, `test`, `watch`
- self-hosting docs
- plugin SDK notes
- Grafana starter dashboard

## Still Pending

- community/adoption milestones from PRD

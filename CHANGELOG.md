# Changelog — Cairn Agent Loop Engineering Platform

All notable changes to the Cairn agent loop engineering platform will be documented in this file.

Format follows Keep a Changelog style and project versions follow SemVer.

## [0.1.0] - 2026-06-29

### Added

- `cairnforge` runtime MVP with parser, validator, executor, state machine, budget tracking, and expression rendering
- built-in proof-of-concept `langchain` target plugin
- CLI commands for `init`, `validate`, and `run`
- CairnLang JSON Schema and working specification
- five example `.crn` loops covering happy path, branching, data pipeline, failure hook, and budget hook
- unit and integration test coverage for parser, validator, executor, and CLI
- CI workflow for Python 3.10, 3.11, and 3.12
- open source repo basics: Apache-2.0 license, contributing guide, code of conduct, feature audit docs

### Notes

- `langchain` target currently proves plugin contract and execution flow. It does not yet compile real LangChain graphs.
- full multi-framework support, registry, tracing, checkpoints, and visual tooling remain future phases.

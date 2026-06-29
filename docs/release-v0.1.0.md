# Release v0.1.0 Checklist

This checklist is for first public Cairn MVP release.

## Scope

- working parser, schema, validator, executor, and CLI
- one proof-of-concept plugin target
- docs and examples good enough for first external users

## Pre-release Checks

- [x] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q`
- [x] `python3 -m cairn.main validate cairnlang/examples/hello-world.crn`
- [x] `python3 -m cairn.main run cairnlang/examples/hello-world.crn --input message=forge`
- [x] CI workflow added for supported Python versions
- [x] README has clone, install, validate, run flow
- [x] license, contributing guide, and code of conduct present
- [x] changelog prepared

## GitHub Release Steps

1. Create annotated tag:
   `git tag -a v0.1.0 -m "Release v0.1.0"`
2. Push tag:
   `git push origin v0.1.0`
3. Create GitHub release titled `v0.1.0`
4. Use summary from `CHANGELOG.md`

## Suggested Release Notes

`v0.1.0` ships first working Cairn MVP: portable `.crn` loop format, JSON Schema validation, semantic validator, sequential executor, plugin contract, proof-of-concept `langchain` target, CLI commands (`init`, `validate`, `run`), examples, tests, and CI.

## Post-release Next Work

- replace proof-of-concept plugin behavior with real LangChain integration
- add issue triage and roadmap tracking
- add release automation and package publishing

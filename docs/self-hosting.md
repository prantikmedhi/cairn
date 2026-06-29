# Self Hosting

Current self-hosting scope is local-first.

## Runtime

```bash
pip install -e ".[dev]"
python3 -m cairn.main run cairnlang/examples/hello-world.crn
```

## Local Registry

```bash
python3 -m cairn.main publish cairnlang/examples/hello-world.crn --registry .cairnhub
python3 -m cairn.main list --registry .cairnhub
python3 -m cairn.main search hello --registry .cairnhub
python3 -m cairn.main install hello-world@0.1.0 ./installed-loops --registry .cairnhub
```

## Checkpointing

```bash
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --checkpoint-file /tmp/pipeline.json --max-steps 1
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --resume /tmp/pipeline.json
```

## Notes

- Hosted CairnHub API is not built yet
- Remote auth, ratings, verified publishers, and shared search remain future work

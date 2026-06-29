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

## Hosted CairnHub API Foundation

```bash
pip install -e ".[hub]"
uvicorn cairnhub.api:app --host 127.0.0.1 --port 8790
```

Publish loop:

```bash
curl -X POST http://127.0.0.1:8790/api/v1/loops \
  -H "Content-Type: application/json" \
  -d '{
    "yaml": "cairn: \"1.0\"\nloop:\n  id: hosted-hello\n  name: Hosted Hello\n  version: 0.1.0\n  states:\n    - id: finish\n      handler: core.collect\n      inputs:\n        message: hello\n",
    "source_file": "hosted-hello.crn",
    "publisher": "Cairn Labs",
    "topics": ["hello", "registry"]
  }'
```

## Checkpointing

```bash
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --checkpoint-file /tmp/pipeline.json --max-steps 1
python3 -m cairn.main run cairnlang/examples/data-pipeline.crn --resume /tmp/pipeline.json
```

## Notes

- Hosted CairnHub file-backed API foundation now built
- Remote auth, ratings, verified publishers, and shared search remain future work
